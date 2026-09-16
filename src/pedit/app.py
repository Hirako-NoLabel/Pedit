from __future__ import annotations

import base64
import io
import difflib
import json
import mimetypes
import os
import re
import sys
import tempfile
import threading
from datetime import datetime
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

import pymupdf as fitz
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter
import numpy as np
import cv2

from . import __version__
from .high_fidelity import analyze_verified_edit, apply_verified_edit
from .scan_engine import diagnose_document, ocr_page, ocr_status, refine_structured_field_bbox
from .ocr_subfield import manual_region_from_page, select_subfield, selectable_fields
from .validation import page_changed, validate_field_boundary
from .scan_revision_visual import build_scan_revision_patch, compose_comparison

HOST = "127.0.0.1"
# Allows a separate test instance without taking over a user's running editor.
PORT = int(os.environ.get("PDF_EDITOR_PORT", "8765"))
ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
WORKDIR = Path(os.environ.get("PEDIT_DATA_DIR") or (Path(tempfile.gettempdir()) / "pedit-oss-v1"))
WORKDIR.mkdir(parents=True, exist_ok=True)
SESSIONS: dict[str, dict] = {}
MAX_UPLOAD = 300 * 1024 * 1024


def safe_name(name: str) -> str:
    name = Path(name or "document.pdf").name
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return re.sub(r"[\\/:*?\"<>|]", "_", name)


def output_name(name: str) -> str:
    p = Path(safe_name(name))
    return f"{p.stem}_修订版.pdf"


def parse_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    if length > MAX_UPLOAD * 2:
        raise ValueError("请求内容过大")
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8")) if raw else {}


def color_int_to_hex(value: int) -> str:
    value = int(value or 0)
    r = (value >> 16) & 255
    g = (value >> 8) & 255
    b = value & 255
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb01(value: str):
    value = (value or "#000000").strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    try:
        return tuple(int(value[i:i+2], 16) / 255 for i in (0, 2, 4))
    except Exception:
        return (0, 0, 0)


def rotation_from_dir(direction) -> int:
    try:
        x, y = float(direction[0]), float(direction[1])
    except Exception:
        return 0
    if abs(x - 1) < 0.05 and abs(y) < 0.05:
        return 0
    if abs(x) < 0.05 and y < -0.95:
        return 90
    if x < -0.95 and abs(y) < 0.05:
        return 180
    if abs(x) < 0.05 and y > 0.95:
        return 270
    return 0


def clean_font_name(name: str) -> str:
    name = (name or "").split("+")[-1]
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _font_match_score(span_name: str, base_name: str, resource_name: str) -> int:
    a = clean_font_name(span_name)
    b = clean_font_name(base_name)
    r = clean_font_name(resource_name)
    if not a:
        return 0
    if a == b or a == r:
        return 100
    if a in b or b in a:
        return 80
    if a in r or r in a:
        return 70
    return 0


def font_status(doc: fitz.Document, page: fitz.Page, span_font: str) -> dict:
    """Report whether the page/document contains the original embedded font program."""
    best = None
    for f in page.get_fonts(full=True):
        xref, ext, ftype, basefont, resource = f[:5]
        score = _font_match_score(span_font, basefont, resource)
        if score and (best is None or score > best[0]):
            best = (score, int(xref), str(ext), str(basefont), str(resource))
    if not best:
        return {"embedded": False, "basefont": span_font or ""}
    _, xref, ext, basefont, resource = best
    if xref <= 0:
        return {"embedded": False, "basefont": basefont, "resource": resource}
    try:
        info = doc.extract_font(xref)
        data = info[3]
        return {"embedded": bool(data), "basefont": basefont, "resource": resource, "xref": xref, "ext": ext}
    except Exception:
        return {"embedded": False, "basefont": basefont, "resource": resource}


def page_data(doc: fitz.Document, page_no: int, pdf_path: str | None = None, cache_dir: str | Path | None = None, diagnosis: dict | None = None) -> dict:
    page = doc.load_page(page_no)
    data = page.get_text("rawdict")
    text_items = []
    for bi, block in enumerate(data.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for li, line in enumerate(block.get("lines", [])):
            rot = rotation_from_dir(line.get("dir", (1, 0)))
            for si, span in enumerate(line.get("spans", [])):
                chars = span.get("chars", []) or []
                text = "".join(str(c.get("c", "")) for c in chars)
                if not text.strip():
                    continue
                bbox = [round(float(v), 3) for v in span.get("bbox", (0, 0, 0, 0))]
                origin = span.get("origin", (bbox[0], bbox[3]))
                char_items = []
                for ci, ch in enumerate(chars):
                    cb = ch.get("bbox", (0, 0, 0, 0))
                    co = ch.get("origin", (cb[0], origin[1]))
                    char_items.append({
                        "i": ci,
                        "c": str(ch.get("c", "")),
                        "bbox": [round(float(v), 3) for v in cb],
                        "origin": [round(float(co[0]), 3), round(float(co[1]), 3)],
                    })
                fstat = font_status(doc, page, span.get("font", ""))
                text_items.append({
                    "id": f"t-{bi}-{li}-{si}",
                    "text": text,
                    "bbox": bbox,
                    "origin": [round(float(origin[0]), 3), round(float(origin[1]), 3)],
                    "font": span.get("font", ""),
                    "size": round(float(span.get("size", 11)), 3),
                    "color": color_int_to_hex(span.get("color", 0)),
                    "alpha": int(span.get("alpha", 255) or 255),
                    "flags": int(span.get("flags", 0)),
                    "rotation": rot,
                    "chars": char_items,
                    "fontEmbedded": bool(fstat.get("embedded")),
                    "fontBase": fstat.get("basefont", span.get("font", "")),
                    "engine": "electronic",
                })

    images = []
    try:
        infos = page.get_image_info(xrefs=True)
        for i, info in enumerate(infos):
            bbox = info.get("bbox")
            if not bbox:
                continue
            # PyMuPDF image bboxes on rotated scan pages can be expressed in the
            # unrotated coordinate space.  Keep them for image replacement, but the
            # scan OCR overlay below uses rotated display coordinates.
            pdf_rect = fitz.Rect(*bbox)
            display_rect = pdf_rect * page.rotation_matrix if page.rotation else pdf_rect
            images.append({
                "id": f"i-{i}-{info.get('xref', 0)}",
                "bbox": [round(float(v), 3) for v in display_rect],
                "pdfBbox": [round(float(v), 3) for v in pdf_rect],
                "xref": int(info.get("xref", 0) or 0),
                "width": int(info.get("width", 0) or 0),
                "height": int(info.get("height", 0) or 0),
                "digest": (info.get("digest").hex() if isinstance(info.get("digest"), (bytes, bytearray)) else str(info.get("digest") or "")),
            })
    except Exception:
        pass

    page_kind = "electronic" if text_items else "unknown"
    ocr_payload = None
    if diagnosis:
        try:
            page_kind = str(diagnosis.get("pages", [])[page_no].get("kind", page_kind))
        except Exception:
            pass
    if not text_items and pdf_path and page_kind == "scan":
        ocr_payload = ocr_page(pdf_path, page_no, cache_dir)
        if ocr_payload.get("ok"):
            text_items = ocr_payload.get("text", [])
            # A complete OCR line remains selectable, but structured children are
            # exposed separately so the editor never proposes a whole-line rewrite.
            for item in text_items:
                item["subfields"] = selectable_fields(item)
                child = select_subfield(item)
                if child:
                    item["subfield"] = child

    return {
        "page": page_no,
        "width": round(float(page.rect.width), 3),
        "height": round(float(page.rect.height), 3),
        "text": text_items,
        "images": images,
        "pageKind": page_kind,
        "scanMode": page_kind == "scan",
        "ocrAvailable": bool(ocr_payload.get("available")) if ocr_payload is not None else None,
        "ocrReason": str(ocr_payload.get("reason", "")) if ocr_payload is not None else "",
        "ocrLang": str(ocr_payload.get("lang", "")) if ocr_payload is not None else "",
        "ocrBackend": str(ocr_payload.get("backend", "")) if ocr_payload is not None else "",
        "ocrBackendLabel": str(ocr_payload.get("backendLabel", "")) if ocr_payload is not None else "",
    }

def _bbox_center(bbox):
    try:
        x0, y0, x1, y1 = [float(v) for v in bbox]
        return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
    except Exception:
        return (0.0, 0.0)


def find_matching_text_items(doc: fitz.Document, source: dict, same_position: bool = True, pdf_path: str | None = None, cache_dir: str | Path | None = None, diagnosis: dict | None = None) -> list[dict]:
    """Find repeated template fields across pages.

    Default rule is deliberately conservative: exact old text plus nearby position,
    similar font and similar size.  This prevents a date repeated in body text from
    being changed when the user intended the fixed header/footer field.
    """
    old_text = str(source.get("oldText", ""))
    if not old_text:
        return []
    src_bbox = source.get("bbox") or (0, 0, 0, 0)
    sx, sy = _bbox_center(src_bbox)
    src_size = float(source.get("size", 0) or 0)
    src_font = str(source.get("font", ""))
    src_engine = str(source.get("engine", "electronic"))
    # PDF template elements can shift by a few points between pages because of crop boxes
    # or producer rounding.  Keep the tolerance strict enough to avoid body-text matches.
    pos_tol = max(7.0, src_size * 0.8 if src_size else 7.0)
    size_tol = max(0.75, src_size * 0.08 if src_size else 0.75)

    matches = []
    for pno in range(doc.page_count):
        pdata = page_data(doc, pno, pdf_path=pdf_path, cache_dir=cache_dir, diagnosis=diagnosis)
        page_candidates = []
        for item in pdata.get("text", []):
            if str(item.get("text", "")) != old_text:
                continue
            ix, iy = _bbox_center(item.get("bbox") or (0, 0, 0, 0))
            dx, dy = abs(ix - sx), abs(iy - sy)
            if src_engine == "scan":
                if str(item.get("engine", "")) != "scan":
                    continue
                font_score = 100
            else:
                font_score = _font_match_score(src_font, str(item.get("font", "")), str(item.get("fontBase", ""))) if src_font else 100
            size_delta = abs(float(item.get("size", 0) or 0) - src_size) if src_size else 0.0
            if same_position:
                if dx > pos_tol or dy > pos_tol or size_delta > size_tol:
                    continue
                if src_engine != "scan" and src_font and font_score < 70:
                    continue
            score = dx + dy + size_delta * 2.0 - font_score * 0.01
            page_candidates.append((score, item, dx, dy, size_delta, font_score))
        if page_candidates:
            page_candidates.sort(key=lambda x: x[0])
            _, item, dx, dy, size_delta, font_score = page_candidates[0]
            matches.append({
                "page": pno,
                "item": item,
                "positionDelta": [round(dx, 3), round(dy, 3)],
                "sizeDelta": round(size_delta, 3),
                "fontScore": int(font_score),
            })
    return matches



def _page_number_candidate_item(pdata: dict, physical_page_no: int) -> dict | None:
    """Return the most likely *existing* page-number token near a page margin.

    This detector is deliberately conservative: it never fabricates a page-number
    location.  It accepts common footer/header forms (``5``, ``第 5 页``,
    ``Page 5``, ``5 / 20``) only in the outer page bands, then returns just the
    numeric token so the normal text-revision engine replaces the original digits
    in place.
    """
    width=float(pdata.get('width') or 0); height=float(pdata.get('height') or 0)
    if width <= 0 or height <= 0:
        return None
    patterns=[
        (re.compile(r'第\s*(\d{1,5})\s*页',re.I),'第 N 页'),
        (re.compile(r'\bpage\s*(\d{1,5})\b',re.I),'Page N'),
        (re.compile(r'(?<!\d)(\d{1,5})\s*/\s*\d{1,5}(?!\d)'),'N / Total'),
        (re.compile(r'^\s*(\d{1,5})\s*$'),'纯数字'),
    ]
    candidates=[]
    for item in pdata.get('text',[]) or []:
        text=str(item.get('text',''))
        bbox=item.get('bbox') or [0,0,0,0]
        try:x0,y0,x1,y1=map(float,bbox)
        except Exception:continue
        cy=(y0+y1)/2; cx=(x0+x1)/2
        # Page numbers are usually in header/footer. Keep a broad band for odd templates.
        margin=min(cy, height-cy)
        if not (cy <= height*.20 or cy >= height*.80):
            continue
        for pat,style in patterns:
            m=pat.search(text)
            if not m:continue
            digits=m.group(1); a,b=m.span(1)
            chars=item.get('chars') or []
            picked=[]
            # OCR/electronic char arrays normally map one-to-one to the item text.
            if len(chars) >= b:
                picked=[dict(c) for c in chars[a:b] if str(c.get('c','')).isdigit()]
            if picked:
                xs=[float(c['bbox'][0]) for c in picked]+[float(c['bbox'][2]) for c in picked]
                ys=[float(c['bbox'][1]) for c in picked]+[float(c['bbox'][3]) for c in picked]
                nb=[min(xs),min(ys),max(xs),max(ys)]
                origin=[float(picked[0].get('origin',[nb[0],nb[3]])[0]),float(picked[0].get('origin',[nb[0],nb[3]])[1])]
                newchars=[]
                for i,c in enumerate(picked):
                    cc=dict(c);cc['i']=i;newchars.append(cc)
            else:
                # Fallback proportional subdivision is only used when the OCR backend
                # omitted char geometry; scan feasibility will still validate it.
                frac0=a/max(1,len(text));frac1=b/max(1,len(text));nb=[x0+(x1-x0)*frac0,y0,x0+(x1-x0)*frac1,y1];origin=[nb[0],float((item.get('origin') or [nb[0],nb[3]])[1])];newchars=[]
            # Prefer the outermost position, simple page-like text, and expected-value proximity
            # only as a weak tie-breaker (the document's displayed page number may be wrong).
            expected=physical_page_no+1
            value_delta=abs(int(digits)-expected)
            center_bonus=abs(cx-width/2)/max(width,1)
            style_penalty={'第 N 页':0,'Page N':0.2,'N / Total':0.35,'纯数字':0.5}.get(style,1)
            score=(margin/max(height,1))*5 + style_penalty + center_bonus*.15 + min(value_delta,20)*.002
            sub=dict(item)
            sub.update({'id':f"{item.get('id','pn')}-page-number",'text':digits,'bbox':[round(v,3) for v in nb],'tokenBbox':[round(v,3) for v in nb],'origin':[round(origin[0],3),round(origin[1],3)],'chars':newchars,'sourceText':text,'characterGeometry':bool(newchars),'requiresIsolation':True})
            candidates.append((score,sub,style,text))
            break
    if not candidates:return None
    candidates.sort(key=lambda x:x[0]);score,item,style,source=candidates[0]
    return {'item':item,'oldText':item['text'],'style':style,'sourceText':source,'score':round(float(score),4)}



def _page_number_placeholder_roles(fmt: str) -> list[str]:
    return re.findall(r"\{(current|total|pdfpage)\}", str(fmt or ""))


def _valid_page_number_box(rect) -> list[float] | None:
    if not isinstance(rect, (list, tuple)) or len(rect) != 4:
        return None
    try:
        x0, y0, x1, y1 = map(float, rect)
    except Exception:
        return None
    if x1 <= x0 or y1 <= y0:
        return None
    return [x0, y0, x1, y1]


def _page_number_box_capture(pdata: dict, rect) -> dict | None:
    """Resolve a user-drawn page-number rectangle to the text actually inside it.

    v2.3.19 makes the rectangle authoritative.  We first collect real character
    geometry inside the box (even when OCR split the footer into several tokens),
    and only fall back to overlapping text items when character boxes are absent.
    The returned ``bbox`` is the *actual* detected ink/text bounds while
    ``selectionBbox`` preserves the user's template rectangle for blank-page adds.
    """
    box = _valid_page_number_box(rect)
    if not box:
        return None
    x0, y0, x1, y1 = box
    pad_x = max(1.2, (x1 - x0) * .025)
    pad_y = max(.8, (y1 - y0) * .10)
    sx0, sy0, sx1, sy1 = x0 - pad_x, y0 - pad_y, x1 + pad_x, y1 + pad_y
    char_rows = []
    overlapping = []
    for item in pdata.get('text', []) or []:
        ib = _valid_page_number_box(item.get('bbox'))
        if not ib:
            continue
        ix0, iy0, ix1, iy1 = ib
        ow = max(0.0, min(sx1, ix1) - max(sx0, ix0))
        oh = max(0.0, min(sy1, iy1) - max(sy0, iy0))
        overlap = ow * oh
        if overlap > 0:
            overlapping.append((overlap / max(1.0, (ix1 - ix0) * (iy1 - iy0)), item))
        for ch in item.get('chars') or []:
            cb = _valid_page_number_box(ch.get('bbox'))
            if not cb:
                continue
            cx = (cb[0] + cb[2]) / 2.0
            cy = (cb[1] + cb[3]) / 2.0
            if sx0 <= cx <= sx1 and sy0 <= cy <= sy1:
                char_rows.append((cx, cy, dict(ch), item))

    base = None
    chars = []
    text = ''
    actual = None
    if char_rows:
        # Page numbers are a single visual row.  Sort left-to-right and preserve
        # the OCR character boxes so numeric subfields get their real coordinates.
        char_rows.sort(key=lambda v: (v[0], v[1]))
        chars = [row[2] for row in char_rows]
        for i, ch in enumerate(chars):
            ch['i'] = i
        text = ''.join(str(ch.get('c', '')) for ch in chars).strip()
        boxes = [_valid_page_number_box(ch.get('bbox')) for ch in chars]
        boxes = [b for b in boxes if b]
        if boxes:
            actual = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
        # Use the parent item contributing most selected characters for style.
        counts = {}
        parents = {}
        for _, _, _, parent in char_rows:
            key = str(parent.get('id') or id(parent))
            counts[key] = counts.get(key, 0) + 1
            parents[key] = parent
        if counts:
            base = parents[max(counts, key=counts.get)]
    elif overlapping:
        overlapping.sort(key=lambda x: (-x[0], float((x[1].get('bbox') or [0,0,0,0])[0])))
        selected = [item for ratio, item in overlapping if ratio >= .20]
        if selected:
            selected.sort(key=lambda item: (float((item.get('bbox') or [0,0,0,0])[0]), float((item.get('bbox') or [0,0,0,0])[1])))
            text = ''.join(str(item.get('text') or '').strip() for item in selected).strip()
            boxes = [_valid_page_number_box(item.get('bbox')) for item in selected]
            boxes = [b for b in boxes if b]
            if boxes:
                actual = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
            base = selected[0]

    if base is None:
        engine = 'scan' if str(pdata.get('pageKind') or '') == 'scan' else 'electronic'
        base = {'id': 'pn-box-empty', 'engine': engine, 'font': '', 'size': max(6.0, (y1-y0)*.72), 'color': '#000000', 'alpha': 255, 'rotation': 0}
    out = dict(base)
    actual = actual or box
    origin = list((chars[0].get('origin') if chars else None) or base.get('origin') or [actual[0], actual[3]])
    out.update({
        'id': f"pn-box-{base.get('id','field')}",
        'text': text,
        'bbox': [round(float(v), 3) for v in actual],
        'selectionBbox': [round(float(v), 3) for v in box],
        'tokenBbox': [round(float(v), 3) for v in actual],
        'origin': [round(float(origin[0]), 3), round(float(origin[1]), 3)],
        'chars': chars,
        'sourceText': text,
        'characterGeometry': bool(chars),
        'requiresIsolation': True,
        'manualSelection': True,
        'captureMode': 'box',
    })
    groups = []
    for idx, m in enumerate(re.finditer(r'\d+', text)):
        child = _page_number_child_item(out, m.start(), m.end(), f'box-{idx}')
        groups.append({
            'index': idx, 'text': m.group(0),
            'bbox': list((child or {}).get('bbox') or []),
        })
    out['numberGroups'] = groups
    return out


def _page_number_child_item(item: dict, start: int, end: int, suffix: str) -> dict | None:
    """Return a numeric sub-item while keeping fixed page-number text untouched."""
    text = str(item.get("text", ""))
    if start < 0 or end <= start or end > len(text):
        return None
    piece = text[start:end]
    chars = list(item.get("chars") or [])
    selected = []
    if len(chars) >= end and "".join(str(c.get("c", "")) for c in chars[:len(text)]) == text:
        selected = [dict(c) for c in chars[start:end] if len(c.get("bbox") or []) == 4]
    if selected:
        xs = [float(c["bbox"][0]) for c in selected] + [float(c["bbox"][2]) for c in selected]
        ys = [float(c["bbox"][1]) for c in selected] + [float(c["bbox"][3]) for c in selected]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
        origin = list(selected[0].get("origin") or [bbox[0], bbox[3]])
        for i, c in enumerate(selected):
            c["i"] = i
        geometry = True
    else:
        base = item.get("bbox") or [0, 0, 0, 0]
        try:
            x0, y0, x1, y1 = map(float, base)
        except Exception:
            return None
        frac0 = start / max(1, len(text))
        frac1 = end / max(1, len(text))
        bbox = [x0 + (x1 - x0) * frac0, y0, x0 + (x1 - x0) * frac1, y1]
        origin = [bbox[0], float((item.get("origin") or [bbox[0], bbox[3]])[1])]
        geometry = False
    out = dict(item)
    out.update({
        "id": f"{item.get('id', 'pn')}-pn-{suffix}",
        "text": piece,
        "bbox": [round(float(v), 3) for v in bbox],
        "tokenBbox": list(item.get("bbox") or bbox),
        "origin": [round(float(origin[0]), 3), round(float(origin[1]), 3)],
        "chars": selected,
        "sourceText": text,
        "characterGeometry": geometry,
        "requiresIsolation": True,
    })
    return out


def _page_number_numeric_children(item: dict):
    """Yield numeric sub-items from a larger OCR/text item.

    OCR engines sometimes merge a visual page number with a prefix / suffix
    within a combined page-number label. A position template selected from a
    pure numeric field should still be able to lock onto the actual digits,
    instead of treating the neighbouring fixed text as the page-number field.
    """
    text = str(item.get("text", ""))
    for idx, m in enumerate(re.finditer(r"\d+", text)):
        child = _page_number_child_item(item, m.start(), m.end(), f"digit-{idx}")
        if child:
            child["numericSubfield"] = True
            yield child


def _iter_page_number_candidates(pdata: dict):
    """Yield full OCR/text items plus structured and numeric subfields."""
    for item in pdata.get("text", []) or []:
        yield item
        seen = set()
        for sf in item.get("subfields", []) or []:
            bbox = sf.get("bbox")
            if not bbox:
                continue
            child = dict(item)
            child.update({
                "id": f"{item.get('id', 'pn')}::{sf.get('start', 0)}-{sf.get('end', 0)}",
                "text": str(sf.get("text", "")),
                "bbox": list(bbox),
                "tokenBbox": list(item.get("bbox") or bbox),
                "origin": list((sf.get("chars") or [{}])[0].get("origin") or [bbox[0], bbox[3]]) if sf.get("chars") else [bbox[0], bbox[3]],
                "chars": list(sf.get("chars") or []),
                "sourceText": str(item.get("text", "")),
                "characterGeometry": sf.get("geometry") == "character",
                "requiresIsolation": True,
            })
            seen.add((str(child.get("text")), tuple(round(float(v), 2) for v in child.get("bbox") or [])))
            yield child
        for child in _page_number_numeric_children(item):
            sig = (str(child.get("text")), tuple(round(float(v), 2) for v in child.get("bbox") or []))
            if sig not in seen:
                yield child


def _page_number_text_skeleton(text: str) -> str:
    return re.sub(r"\d+", "{#}", str(text or "")).replace(" ", "").lower()

def _project_page_number_bbox(template: dict, pdata: dict) -> list[float]:
    # v2.3.21 may feed a per-page preferred box based on the previous successful
    # page.  This is intentionally page-local and takes precedence over the
    # original template projection so page footers that drift a few points do not
    # get forced back to one fixed coordinate.
    preferred = template.get("preferredBbox") or []
    if isinstance(preferred, (list, tuple)) and len(preferred) == 4:
        try:
            return [float(v) for v in preferred]
        except Exception:
            pass
    src = template.get("bbox") or [0, 0, 0, 0]
    try:
        x0, y0, x1, y1 = map(float, src)
        sw = max(1.0, float(template.get("pageWidth") or pdata.get("width") or 1))
        sh = max(1.0, float(template.get("pageHeight") or pdata.get("height") or 1))
        tw = max(1.0, float(pdata.get("width") or sw))
        th = max(1.0, float(pdata.get("height") or sh))
        return [x0 / sw * tw, y0 / sh * th, x1 / sw * tw, y1 / sh * th]
    except Exception:
        return [0.0, 0.0, 0.0, 0.0]


def _page_number_position_match(pdata: dict, template: dict) -> dict | None:
    """Match a page-number slot primarily by the user-selected geometry.

    v2.3.19 prioritizes the user-drawn box and the actual per-page character geometry.
    This prevents a nearby body token such as ``第1`` from being selected merely
    because it contains digits.  Numeric subfields are considered explicitly so
    OCR grouping differences do not hide the real page number digits.
    """
    expected = _project_page_number_bbox(template, pdata)
    ex0, ey0, ex1, ey1 = expected
    ew, eh = max(1.0, ex1 - ex0), max(1.0, ey1 - ey0)
    ecx, ecy = (ex0 + ex1) / 2.0, (ey0 + ey1) / 2.0
    needs_digits = bool(_page_number_placeholder_roles(template.get("format") or "{current}"))
    source_engine = str(template.get("engine") or "")
    source_text = str(template.get("sourceText") or "")
    source_skeleton = _page_number_text_skeleton(source_text)
    source_pure_numeric = bool(re.fullmatch(r"\s*\d+\s*", source_text))
    source_digit_groups = len(re.findall(r"\d+", source_text))

    # v2.3.19: for a user-drawn page-number box, read the content *inside that
    # projected box first*.  This handles OCR that split ``第 92 页 共 92 页``
    # into several tokens and keeps the actual per-page character coordinates.
    if str(template.get('captureMode') or '') == 'box':
        px = max(2.0, ew * .08)
        py = max(1.5, eh * .22)
        search = [ex0 - px, ey0 - py, ex1 + px, ey1 + py]
        boxed = _page_number_box_capture(pdata, search)
        if boxed and re.search(r'\d', str(boxed.get('text') or '')):
            roles = _page_number_placeholder_roles(template.get('format') or '{current}')
            group_count = len(re.findall(r'\d+', str(boxed.get('text') or '')))
            source_group_count = int(template.get('sourceGroupCount') or len(re.findall(r'\d+', str(template.get('sourceText') or ''))) or 0)
            # v2.3.23: a whole-field template with two numeric roles must not stop
            # on the first nearby number. A one-number user box still remains valid.
            required_groups = max(1, min(len(roles) if roles else 1, source_group_count or (len(roles) if roles else 1)))
            if not roles or group_count >= required_groups:
                boxed['pageNumberMatchScore'] = -100.0
                boxed['pageNumberOverlap'] = 1.0
                boxed['templateSelectionBbox'] = [round(float(v), 3) for v in expected]
                return boxed

    candidates = []
    for item in _iter_page_number_candidates(pdata):
        text = str(item.get("text", ""))
        if needs_digits and not re.search(r"\d", text):
            continue
        if source_engine == "scan" and str(item.get("engine", "")) != "scan":
            continue
        box = item.get("bbox") or []
        if len(box) != 4:
            continue
        try:
            x0, y0, x1, y1 = map(float, box)
        except Exception:
            continue
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        iw, ih = max(1.0, x1 - x0), max(1.0, y1 - y0)
        dx, dy = abs(cx - ecx), abs(cy - ecy)
        overlap_w = max(0.0, min(ex1, x1) - max(ex0, x0))
        overlap_h = max(0.0, min(ey1, y1) - max(ey0, y0))
        overlap = overlap_w * overlap_h
        overlap_ratio = overlap / max(1.0, min(ew * eh, iw * ih))
        vertical_overlap = overlap_h / max(1.0, min(eh, ih))
        # v2.3.21: the user-selected box is a *starting anchor*, not a rigid
        # coordinate.  Real report / scan pages often shift the footer by several
        # points.  Search a bounded neighbourhood and let shape / size / distance
        # scoring decide the best candidate.  A previous-page anchor (when
        # available) makes this wider tolerance safe and stable.
        tolx = max(14.0, ew * 2.60)
        toly = max(9.0, eh * 1.90)
        if dx > tolx or dy > toly:
            continue
        if vertical_overlap < 0.12 and dy > max(4.5, eh * 1.05):
            continue
        if overlap_ratio < 0.04 and dx > tolx * 0.82:
            continue
        width_ratio = max(iw / ew, ew / iw)
        height_ratio = max(ih / eh, eh / ih)
        size_penalty = abs(width_ratio - 1.0) * 1.6 + abs(height_ratio - 1.0) * 2.5
        cand_skeleton = _page_number_text_skeleton(text)
        shape_penalty = 0.0
        if source_text:
            if cand_skeleton == source_skeleton:
                shape_penalty -= 7.0
            elif source_pure_numeric and re.fullmatch(r"\s*\d+\s*", text):
                shape_penalty -= 5.0
            else:
                shape_penalty += 5.0
            cand_groups = len(re.findall(r"\d+", text))
            if source_digit_groups:
                shape_penalty += abs(cand_groups - source_digit_groups) * 1.8
        if item.get("numericSubfield") and source_pure_numeric:
            shape_penalty -= 2.5
        score = dx + dy * 1.8 + size_penalty - overlap_ratio * 10.0 + shape_penalty
        candidates.append((score, item, overlap_ratio))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    best = dict(candidates[0][1])
    best["pageNumberMatchScore"] = round(float(candidates[0][0]), 3)
    best["pageNumberOverlap"] = round(float(candidates[0][2]), 3)
    return best

def _page_number_parts(item: dict, fmt: str) -> list[dict]:
    """Map numeric groups to page-number roles without repainting fixed literals.

    v2.3.20 deliberately refuses guessed sub-field geometry for formatted page
    numbers within a combined page-number label when real character boxes are not
    available.  Falling back to a full-field rewrite can duplicate the fixed
    Chinese / punctuation, which is worse than asking the user to re-box once.
    Pure numeric fields are still allowed to use the older proportional fallback.
    """
    roles = _page_number_placeholder_roles(fmt)
    if not roles:
        return []
    text = str(item.get("text", ""))
    groups = list(re.finditer(r"\d+", text))
    if len(groups) < len(roles):
        return []
    literal = re.sub(r"\{(?:current|total|pdfpage)\}", "", str(fmt or ""))
    literal = re.sub(r"\s+", "", literal)
    formatted = bool(literal)
    parts = []
    for idx, role in enumerate(roles):
        g = groups[idx]
        sub = _page_number_child_item(item, g.start(), g.end(), f"{role}-{idx}")
        if not sub:
            return []
        if formatted and not bool(sub.get("characterGeometry")):
            return []
        parts.append({"role": role, "item": sub, "oldText": sub.get("text", "")})
    return parts


def analyze_page_number_replace(edit: dict) -> dict:
    old = str(edit.get("oldText") or "")
    new = str(edit.get("newText") or edit.get("text") or "")
    bbox = edit.get("bbox") or []
    outbox = edit.get("outputBbox") or bbox
    if not old.strip():
        return {"mode": "blocked", "visualVerified": False, "reason": "未识别到原页码文字"}
    if not new.strip():
        return {"mode": "blocked", "visualVerified": False, "reason": "新页码内容为空"}
    for label, box in (("原页码", bbox), ("输出", outbox)):
        if len(box) != 4:
            return {"mode": "blocked", "visualVerified": False, "reason": f"{label}区域无效"}
        try:
            x0, y0, x1, y1 = map(float, box)
        except Exception:
            return {"mode": "blocked", "visualVerified": False, "reason": f"{label}坐标无效"}
        if x1 <= x0 or y1 <= y0:
            return {"mode": "blocked", "visualVerified": False, "reason": f"{label}区域尺寸无效"}
    return {
        "mode": "page-number-replace",
        "visualVerified": True,
        "reason": "页码结构或字符数量变化，将使用页码专用原位替换",
        "fieldBbox": [float(v) for v in outbox],
    }


def _measure_page_number_text(text: str, font_name: str, fontsize: float) -> float:
    try:
        font_file = find_font_file(font_name)
        if font_file:
            return float(fitz.Font(fontfile=font_file).text_length(text, fontsize=fontsize))
    except Exception:
        pass
    try:
        builtin = _builtin_font_name(font_name, text) or ("china-s" if contains_cjk(text) else "helv")
        return float(fitz.Font(fontname=builtin).text_length(text, fontsize=fontsize))
    except Exception:
        units = sum(1.0 if ord(c) > 127 else (0.34 if c.isspace() else 0.58) for c in text)
        return max(fontsize * .5, units * fontsize)


def _page_number_anchor_x(box: list[float], page_width: float) -> str:
    cx = (float(box[0]) + float(box[2])) / 2.0
    if cx < page_width * .38:
        return "left"
    if cx > page_width * .62:
        return "right"
    return "center"


def _insert_page_number_text(doc: fitz.Document, page: fitz.Page, edit: dict, bbox: list[float]) -> None:
    text = str(edit.get("newText") or edit.get("text") or "")
    font_name = str(edit.get("font") or ("SimSun" if contains_cjk(text) else "Times New Roman"))
    fontsize = max(4.5, float(edit.get("size") or max(6.0, (bbox[3] - bbox[1]) * .78)))
    color = hex_to_rgb01(str(edit.get("color") or "#000000"))
    width = max(3.0, float(bbox[2]) - float(bbox[0]))
    # Numeric subfield replacements are anchored to the old digit box itself.
    # Do not consume 1.5 pt of artificial side padding or same-width values such
    # as 92 -> 82 would be unnecessarily shrunk and visibly drift from the row.
    available = width if edit.get("tightNumeric") else max(3.0, width - 1.5)
    measured = _measure_page_number_text(text, font_name, fontsize)
    if measured > available and measured > 0:
        fontsize = max(4.2, fontsize * available / measured)
        measured = _measure_page_number_text(text, font_name, fontsize)
    anchor = str(edit.get("anchor") or _page_number_anchor_x(bbox, float(page.rect.width)))
    if anchor == "right":
        x = float(bbox[2]) - measured - .6
    elif anchor == "center":
        x = (float(bbox[0]) + float(bbox[2]) - measured) / 2.0
    else:
        x = float(bbox[0]) + .6
    baseline_offset = float(edit.get("originOffsetY") or max(fontsize, (bbox[3] - bbox[1]) * .80))
    y = min(float(bbox[3]) - .3, float(bbox[1]) + baseline_offset)
    point_display = fitz.Point(x, y)
    point_pdf = point_display * page.derotation_matrix if page.rotation else point_display
    _insert_text_precise(
        doc, page, point_pdf, text, fontsize=fontsize, font_name=font_name,
        color=color, rotation=int(edit.get("rotation") or 0), alpha=int(edit.get("alpha") or 255),
        font_seq=9950 + page.number,
    )


def apply_page_number_replace(doc: fitz.Document, edit: dict, original_path: str | None) -> tuple[bool, dict]:
    plan = analyze_page_number_replace(edit)
    if plan.get("mode") != "page-number-replace":
        return False, plan
    pno = int(edit.get("page", -1))
    if pno < 0 or pno >= doc.page_count:
        return False, {"mode": "blocked", "visualVerified": False, "reason": "页码页码无效"}
    old_bbox = [float(v) for v in (edit.get("bbox") or [])]
    out_bbox = [float(v) for v in (edit.get("outputBbox") or old_bbox)]
    page = doc.load_page(pno)
    try:
        if str(edit.get("engine") or "electronic") == "scan":
            if not original_path:
                raise ValueError("扫描页码缺少原始 PDF 路径")
            patch = build_delete_patch(original_path, pno, old_bbox, "text")
            rect = _display_rect_to_pdf(page, patch["overlayBbox"])
            page.insert_image(rect, stream=patch["png"], overlay=True, rotate=int(page.rotation or 0), keep_proportion=False)
            add_edit = dict(edit)
            add_edit.update({"type": "page-number-add", "bbox": out_bbox, "text": str(edit.get("newText") or "")})
            png = _render_scan_page_number_png(add_edit)
            out_rect = _display_rect_to_pdf(page, out_bbox)
            page.insert_image(out_rect, stream=png, overlay=True, rotate=int(page.rotation or 0), keep_proportion=False)
        else:
            # Remove text objects only. Images and vector graphics inside the slot stay intact.
            redact_rect = _display_rect_to_pdf(page, old_bbox)
            page.add_redact_annot(redact_rect, fill=None, cross_out=False)
            page.apply_redactions(images=0, graphics=0, text=0)
            page = doc.load_page(pno)
            _insert_page_number_text(doc, page, edit, out_bbox)
        return True, plan
    except Exception as ex:
        return False, {"mode": "blocked", "visualVerified": False, "reason": f"页码原位替换失败：{ex}"}


def analyze_page_number_add(edit: dict) -> dict:
    text = str(edit.get("text") or edit.get("newText") or "")
    bbox = edit.get("bbox") or []
    if not text:
        return {"mode": "blocked", "visualVerified": False, "reason": "新增页码内容为空"}
    if len(bbox) != 4:
        return {"mode": "blocked", "visualVerified": False, "reason": "新增页码位置无效"}
    try:
        x0, y0, x1, y1 = map(float, bbox)
    except Exception:
        return {"mode": "blocked", "visualVerified": False, "reason": "新增页码坐标无效"}
    if x1 <= x0 or y1 <= y0:
        return {"mode": "blocked", "visualVerified": False, "reason": "新增页码区域尺寸无效"}
    return {"mode": "page-number-add", "visualVerified": True, "reason": "空白页码位置将按模板新增", "fieldBbox": [x0, y0, x1, y1]}


def _page_number_scan_font(edit: dict) -> str:
    adjust = edit.get("visualAdjust") or {}
    choice = str(adjust.get("fontChoice") or "auto").lower()
    mapping = {
        "times": "Times New Roman", "arial": "Arial", "calibri": "Calibri",
        "cambria": "Cambria", "simsun": "SimSun", "msyh": "Microsoft YaHei",
    }
    if choice in mapping:
        return mapping[choice]
    text = str(edit.get("text") or "")
    if contains_cjk(text):
        return "SimSun"
    return "Times New Roman"


def _render_scan_page_number_png(edit: dict) -> bytes:
    """Render a transparent scan-like page-number overlay for pages where the slot is blank."""
    text = str(edit.get("text") or "")
    bbox = edit.get("bbox") or [0, 0, 1, 1]
    x0, y0, x1, y1 = map(float, bbox)
    scale = 4.0
    w = max(8, int(round((x1 - x0) * scale)))
    h = max(8, int(round((y1 - y0) * scale)))
    adjust = edit.get("visualAdjust") or {}
    size_scale = max(.5, min(1.5, float(adjust.get("sizeScale", 1.0) or 1.0)))
    width_scale = max(.5, min(1.5, float(adjust.get("widthScale", 1.0) or 1.0)))
    font_name = _page_number_scan_font(edit)
    font_path = find_font_file(font_name)
    if not font_path:
        fallbacks = [
            Path('/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'),
            Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'),
        ]
        font_path = next((str(f) for f in fallbacks if f.exists()), None)
    font_px = max(7, int(round(h * .78 * size_scale)))
    if font_path:
        font = ImageFont.truetype(font_path, font_px)
    else:
        font = ImageFont.load_default()
    pad = max(4, h // 5)
    tmp = Image.new("L", (max(w * 4, 256), max(h * 3, 96)), 0)
    draw = ImageDraw.Draw(tmp)
    stroke = float(adjust.get("strokePx", 0.0) or 0.0)
    stroke_width = max(0, min(3, int(round(max(0.0, stroke)))))
    draw.text((pad, pad), text, font=font, fill=255, stroke_width=stroke_width, stroke_fill=255)
    box = tmp.getbbox()
    if not box:
        raise ValueError("新增页码无法生成字形")
    alpha = tmp.crop(box)
    if abs(width_scale - 1.0) > 1e-4:
        alpha = alpha.resize((max(1, int(round(alpha.width * width_scale))), alpha.height), Image.Resampling.LANCZOS)
    if alpha.width > w - 2 or alpha.height > h - 2:
        factor = min((w - 2) / max(1, alpha.width), (h - 2) / max(1, alpha.height))
        alpha = alpha.resize((max(1, int(round(alpha.width * factor))), max(1, int(round(alpha.height * factor))),), Image.Resampling.LANCZOS)
    soften = float(adjust.get("softenPx", 0.0) or 0.0)
    if soften > .01:
        alpha = alpha.filter(ImageFilter.GaussianBlur(radius=min(4.0, soften)))
    elif soften < -.01:
        alpha = alpha.filter(ImageFilter.UnsharpMask(radius=.8, percent=int(65 + min(2.5, abs(soften)) * 35), threshold=1))
    if stroke < -.5:
        alpha = alpha.filter(ImageFilter.MinFilter(3))
    canvas = Image.new("L", (w, h), 0)
    x = int(round((w - alpha.width) / 2 + float(adjust.get("xOffsetPx", 0.0) or 0.0)))
    y = int(round((h - alpha.height) / 2 + float(adjust.get("yOffsetPx", 0.0) or 0.0)))
    canvas.paste(alpha, (x, y))
    darkness = float(adjust.get("darkness", 0.0) or 0.0)
    base = max(0, min(255, int(round(55 - darkness))))
    rgba = Image.new("RGBA", (w, h), (base, base, base, 0))
    rgba.putalpha(canvas)
    out = io.BytesIO()
    rgba.save(out, format="PNG", optimize=True)
    return out.getvalue()


def apply_page_number_add(doc: fitz.Document, edit: dict) -> tuple[bool, dict]:
    plan = analyze_page_number_add(edit)
    if plan.get("mode") != "page-number-add":
        return False, plan
    pno = int(edit.get("page", -1))
    if pno < 0 or pno >= doc.page_count:
        return False, {"mode": "blocked", "visualVerified": False, "reason": "新增页码页码无效"}
    page = doc.load_page(pno)
    bbox = list(plan.get("fieldBbox") or edit.get("bbox") or [])
    text = str(edit.get("text") or edit.get("newText") or "")
    try:
        rect = _display_rect_to_pdf(page, bbox)
        if str(edit.get("engine") or "electronic") == "scan":
            png = _render_scan_page_number_png(edit)
            page.insert_image(rect, stream=png, overlay=True, rotate=int(page.rotation or 0), keep_proportion=False)
        else:
            color = hex_to_rgb01(str(edit.get("color") or "#000000"))
            size = float(edit.get("size") or max(5.0, (bbox[3] - bbox[1]) * .78))
            font_name = str(edit.get("font") or ("SimSun" if contains_cjk(text) else "Times New Roman"))
            ox = float(edit.get("originOffsetX") or 0.0)
            oy = float(edit.get("originOffsetY") or max(1.0, (bbox[3] - bbox[1]) * .82))
            point_display = fitz.Point(float(bbox[0]) + ox, float(bbox[1]) + oy)
            point_pdf = point_display * page.derotation_matrix if page.rotation else point_display
            _insert_text_precise(doc, page, point_pdf, text, fontsize=size, font_name=font_name, color=color,
                                 rotation=int(edit.get("rotation") or 0), alpha=int(edit.get("alpha") or 255), font_seq=9900 + pno)
    except Exception as ex:
        return False, {"mode": "blocked", "visualVerified": False, "reason": f"新增页码失败：{ex}"}
    return True, plan

def analyze_free_text(edit: dict) -> dict:
    """Validate a user-positioned text block.

    v2.3.21 treats manual additions as first-class editable objects.  The block
    owns its output rectangle, so it may be moved/resized without pretending it
    replaces an OCR token.
    """
    text = str(edit.get("text") or edit.get("newText") or "")
    bbox = edit.get("bbox") or []
    if not text.strip():
        return {"mode": "blocked", "visualVerified": False, "reason": "新增文字内容为空"}
    if len(bbox) != 4:
        return {"mode": "blocked", "visualVerified": False, "reason": "新增文字区域无效"}
    try:
        x0, y0, x1, y1 = map(float, bbox)
    except Exception:
        return {"mode": "blocked", "visualVerified": False, "reason": "新增文字坐标无效"}
    if x1 <= x0 or y1 <= y0:
        return {"mode": "blocked", "visualVerified": False, "reason": "新增文字区域尺寸无效"}
    return {"mode": "free-text", "visualVerified": True, "reason": "自由文字块位置有效", "fieldBbox": [x0, y0, x1, y1]}


def apply_free_text(doc: fitz.Document, edit: dict) -> tuple[bool, dict]:
    plan = analyze_free_text(edit)
    if plan.get("mode") != "free-text":
        return False, plan
    pno = int(edit.get("page", -1))
    if pno < 0 or pno >= doc.page_count:
        return False, {"mode": "blocked", "visualVerified": False, "reason": "新增文字页码无效"}
    page = doc.load_page(pno)
    bbox = list(plan.get("fieldBbox") or edit.get("bbox") or [])
    text = str(edit.get("text") or edit.get("newText") or "")
    try:
        rect = _display_rect_to_pdf(page, bbox)
        sprite = str(edit.get("dataUrl") or "")
        if sprite.startswith("data:image/"):
            page.insert_image(rect, stream=data_url_bytes(sprite), overlay=True,
                              rotate=int(page.rotation or 0), keep_proportion=False)
        elif str(edit.get("engine") or "electronic") == "scan":
            # Reuse the scan-like transparent renderer.  It only paints the new
            # foreground, so moving the block never copies the old paper pixels.
            png = _render_scan_page_number_png({**edit, "text": text})
            page.insert_image(rect, stream=png, overlay=True,
                              rotate=int(page.rotation or 0), keep_proportion=False)
        else:
            _insert_page_number_text(doc, page, {**edit, "text": text, "newText": text}, bbox)
        return True, plan
    except Exception as ex:
        return False, {"mode": "blocked", "visualVerified": False, "reason": f"自由文字块生成失败：{ex}"}


def render_page(doc: fitz.Document, page_no: int, scale: float = 1.7) -> bytes:
    page = doc.load_page(page_no)
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    return pix.tobytes("png")


def data_url_bytes(data_url: str) -> bytes:
    if not data_url or "," not in data_url:
        raise ValueError("无效图片数据")
    _, encoded = data_url.split(",", 1)
    return base64.b64decode(encoded)


def contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u3400-\u9fff\uf900-\ufaff]", text or ""))


_FONT_CACHE: dict[str, str | None] = {}


def font_dirs() -> list[Path]:
    dirs = []
    if os.name == "nt":
        dirs.append(Path(os.environ.get("WINDIR") or (Path.home().anchor + "Windows")) / "Fonts")
        local = os.environ.get("LOCALAPPDATA")
        if local:
            dirs.append(Path(local) / "Microsoft" / "Windows" / "Fonts")
    elif sys.platform == "darwin":
        dirs += [Path("/System/Library/Fonts"), Path("/Library/Fonts"), Path.home() / "Library/Fonts"]
    else:
        dirs += [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), Path.home() / ".fonts"]
    return [p for p in dirs if p.exists()]


FONT_FILE_HINTS = {
    "microsoftyahei": ["msyh.ttf", "msyh.ttc", "msyhbd.ttf"],
    "microsoftyaheilight": ["msyhl.ttc", "msyhl.ttf"],
    "simsun": ["simsun.ttc", "simsun.ttf"],
    "simhei": ["simhei.ttf"],
    "kaiti": ["simkai.ttf"],
    "fangsong": ["simfang.ttf"],
    "arial": ["arial.ttf"],
    "arialbold": ["arialbd.ttf"],
    "timesnewroman": ["times.ttf"],
    "calibri": ["calibri.ttf"],
    "lato": ["Lato-Regular.ttf", "lato-regular.ttf"],
}


def find_font_file(font_name: str) -> str | None:
    key = clean_font_name(font_name)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    dirs = font_dirs()
    for hint_key, names in FONT_FILE_HINTS.items():
        if hint_key in key or (key and key in hint_key):
            for root in dirs:
                for fname in names:
                    direct = root / fname
                    if direct.exists():
                        _FONT_CACHE[key] = str(direct)
                        return str(direct)
                    try:
                        for found in root.rglob(fname):
                            _FONT_CACHE[key] = str(found)
                            return str(found)
                    except Exception:
                        pass
    for root in dirs:
        try:
            for pattern in ("*.ttf", "*.ttc", "*.otf"):
                for file in root.rglob(pattern):
                    stem = clean_font_name(file.stem)
                    if key and (key in stem or stem in key):
                        _FONT_CACHE[key] = str(file)
                        return str(file)
        except Exception:
            continue
    _FONT_CACHE[key] = None
    return None


def _find_embedded_font(doc: fitz.Document, page: fitz.Page, span_font: str, needed_text: str):
    candidates = []
    for f in page.get_fonts(full=True):
        xref, ext, ftype, basefont, resource = f[:5]
        score = _font_match_score(span_font, str(basefont), str(resource))
        if score:
            candidates.append((score, int(xref), str(basefont), str(resource)))
    candidates.sort(reverse=True)
    for _, xref, basefont, resource in candidates:
        if xref <= 0:
            continue
        try:
            info = doc.extract_font(xref)
            buf = info[3]
            if not buf:
                continue
            font = fitz.Font(fontbuffer=buf)
            if all(ch.isspace() or font.has_glyph(ord(ch)) for ch in needed_text):
                return buf, basefont, resource
        except Exception:
            continue
    return None


def _builtin_font_name(font_name: str, text: str) -> str | None:
    key = clean_font_name(font_name)
    if contains_cjk(text):
        # PyMuPDF built-in CJK font: useful fallback, but not considered exact.
        return "china-s"
    if "courier" in key:
        return "cour"
    if "times" in key:
        return "tiro"
    if "helvetica" in key or "arial" in key:
        return "helv"
    return None


def _insert_text_precise(doc: fitz.Document, page: fitz.Page, point, text: str, *, fontsize: float,
                         font_name: str, color, rotation: int, alpha: int, font_seq: int) -> str:
    """Insert text using the original embedded font when possible.

    Returns a source label: embedded / local / builtin.
    """
    if not text:
        return "none"
    embedded = _find_embedded_font(doc, page, font_name, text)
    opacity = min(1.0, max(0.0, float(alpha or 255) / 255.0))
    if embedded:
        buf, _, _ = embedded
        res = f"PE{page.number}_{font_seq}"
        page.insert_font(fontname=res, fontbuffer=buf)
        page.insert_text(point, text, fontsize=fontsize, fontname=res, color=color, rotate=rotation,
                         overlay=True, fill_opacity=opacity, stroke_opacity=opacity)
        return "embedded"
    font_file = find_font_file(font_name)
    if font_file:
        res = f"PL{page.number}_{font_seq}"
        page.insert_font(fontname=res, fontfile=font_file)
        page.insert_text(point, text, fontsize=fontsize, fontname=res, color=color, rotate=rotation,
                         overlay=True, fill_opacity=opacity, stroke_opacity=opacity)
        return "local"
    fallback = _builtin_font_name(font_name, text) or ("china-s" if contains_cjk(text) else "helv")
    page.insert_text(point, text, fontsize=fontsize, fontname=fallback, color=color, rotate=rotation,
                     overlay=True, fill_opacity=opacity, stroke_opacity=opacity)
    return "builtin"


def _minimal_text_plan(edit: dict) -> dict:
    """Build a visual-fidelity plan.

    The highest-fidelity case is same-length content-only replacement: only changed glyphs are
    removed and reinserted; unchanged glyphs remain the original PDF objects.
    """
    old = str(edit.get("oldText", ""))
    new = str(edit.get("newText", ""))
    chars = edit.get("chars") or []
    same_style = bool(edit.get("sameStyle", False))
    if same_style and len(old) == len(new) and len(chars) >= len(old):
        changes = []
        for i, (a, b) in enumerate(zip(old, new)):
            if a != b:
                changes.append({"index": i, "old": a, "new": b, "char": chars[i]})
        if changes:
            return {"mode": "glyph", "changes": changes}
        return {"mode": "none", "changes": []}

    if same_style and chars and old != new:
        # Preserve the unchanged prefix exactly. Redraw only from first difference onward.
        matcher = difflib.SequenceMatcher(a=old, b=new)
        prefix = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal" and i1 == 0 and j1 == 0:
                prefix = i2
            else:
                break
        prefix = min(prefix, len(chars))
        if prefix < len(chars):
            return {
                "mode": "tail",
                "start": prefix,
                "oldTail": old[prefix:],
                "newTail": new[prefix:],
                "chars": chars[prefix:],
            }

    return {"mode": "span"}


def _redact_rect_for_char(char: dict) -> fitz.Rect:
    rect = fitz.Rect(*[float(v) for v in char.get("bbox", (0, 0, 0, 0))])
    # Slightly shrink horizontally so an adjacent touching glyph is not removed.
    if rect.width > 1.0:
        inset = min(0.16, rect.width * 0.04)
        rect.x0 += inset
        rect.x1 -= inset
    return rect



def _contains_cjk(text: str) -> bool:
    return any("\u3400" <= ch <= "\u9fff" for ch in str(text or ""))


def _display_rect_to_pdf(page: fitz.Page, bbox) -> fitz.Rect:
    rect = fitz.Rect(*[float(v) for v in bbox])
    return rect * page.derotation_matrix if page.rotation else rect


def _map_scan_text_chars(old_text: str, chars: list[dict]) -> dict[int, dict]:
    """Align the selected OCR text to per-character boxes without trusting one bad box.

    OCR backends sometimes return a correct token but one character box stretches into
    the following Chinese text. We first try an exact substring, then an LCS alignment.
    This is geometry-only: it does not alter the scanned pixels.
    """
    old_text = str(old_text or "")
    chars = sorted((c for c in (chars or []) if len(str(c.get("c", ""))) == 1 and len(c.get("bbox", [])) == 4), key=lambda c: (c["bbox"][0], c["bbox"][1]))
    if not old_text or not chars:
        return {}
    seq = "".join(str(c.get("c", "")) for c in chars)
    pos = seq.find(old_text)
    if pos >= 0 and pos + len(old_text) <= len(chars):
        return {i: chars[pos + i] for i in range(len(old_text))}

    n, m = len(old_text), len(chars)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if old_text[i] == str(chars[j].get("c", "")):
                dp[i][j] = 1 + dp[i + 1][j + 1]
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])
    out = {}
    i = j = 0
    while i < n and j < m:
        if old_text[i] == str(chars[j].get("c", "")) and dp[i][j] == 1 + dp[i + 1][j + 1]:
            out[i] = chars[j]
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1
        else:
            j += 1
    return out


def _refine_scan_display_bbox(edit: dict) -> list[float]:
    """Return a field-level OCR rectangle, never the whole surrounding text line.

    Derive the rectangle from aligned character cells and clamp outlier widths
    so a malformed OCR box cannot cover adjacent text.
    """
    raw = edit.get("bbox") or [0, 0, 0, 0]
    try:
        base = [float(v) for v in raw]
    except Exception:
        return [0.0, 0.0, 0.0, 0.0]
    old = str(edit.get("oldText", ""))
    chars = list(edit.get("chars") or [])
    if not old or not chars:
        return base

    mapping = _map_scan_text_chars(old, chars)
    valid = []
    for idx, c in mapping.items():
        b = c.get("bbox") or []
        if len(b) != 4:
            continue
        try:
            x0, y0, x1, y1 = [float(v) for v in b]
        except Exception:
            continue
        if x1 > x0 and y1 > y0:
            valid.append((idx, [x0, y0, x1, y1]))
    if len(valid) < max(2, int(len(old) * 0.6)):
        return base

    widths = sorted(max(0.5, b[2] - b[0]) for _, b in valid)
    typical = widths[len(widths) // 2]
    # Reject OCR outlier widths. A normal Latin/digit cell in the same token should
    # not be several times wider than its neighbours.
    max_w = max(typical * 1.30, 3.0)
    fixed = []
    for idx, b in valid:
        x0, y0, x1, y1 = b
        if x1 - x0 > max_w:
            x1 = x0 + max_w
        fixed.append((idx, [x0, y0, x1, y1]))

    # For missing characters, interpolate from the nearest mapped neighbours so the
    # selected field can still be isolated from the rest of the OCR word box.
    by_idx = {i: b for i, b in fixed}
    for i in range(len(old)):
        if i in by_idx:
            continue
        left = max((k for k in by_idx if k < i), default=None)
        right = min((k for k in by_idx if k > i), default=None)
        if left is not None and right is not None:
            lc = (by_idx[left][0] + by_idx[left][2]) / 2
            rc = (by_idx[right][0] + by_idx[right][2]) / 2
            frac = (i - left) / max(1, right - left)
            cx = lc + (rc - lc) * frac
        elif left is not None:
            cx = (by_idx[left][0] + by_idx[left][2]) / 2 + typical * (i - left)
        elif right is not None:
            cx = (by_idx[right][0] + by_idx[right][2]) / 2 - typical * (right - i)
        else:
            continue
        y0 = min(b[1] for b in by_idx.values())
        y1 = max(b[3] for b in by_idx.values())
        by_idx[i] = [cx - typical * 0.5, y0, cx + typical * 0.5, y1]

    boxes = [by_idx[i] for i in sorted(by_idx) if 0 <= i < len(old)]
    if not boxes:
        return base
    tight = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]

    # Small padding keeps the old glyphs covered, while remaining field-local.
    pad_x = min(1.4, typical * 0.12)
    pad_y = min(1.2, max(0.5, (tight[3] - tight[1]) * 0.08))
    tight = [tight[0] - pad_x, tight[1] - pad_y, tight[2] + pad_x, tight[3] + pad_y]

    # Never grow outside the OCR token vertically, and only allow a tiny horizontal
    # tolerance beyond it. Most importantly, block suspiciously wide refinements.
    tight[0] = max(base[0] - 1.0, tight[0])
    tight[1] = max(base[1] - 1.5, tight[1])
    tight[2] = min(base[2] + 1.0, tight[2])
    tight[3] = min(base[3] + 1.5, tight[3])
    expected_max = max(typical * max(2.0, len(old) * 1.65), 10.0)
    if tight[2] <= tight[0] or tight[3] <= tight[1] or (tight[2] - tight[0]) > expected_max:
        return base
    return [round(v, 3) for v in tight]


def _single_changed_glyph(edit: dict) -> dict | None:
    """Return a safely-addressable one-glyph substitution, if this edit is one.

    Scanned PDF revisions normally redraw the selected field.  That is necessary
    when text length changes, but a single-glyph change should preserve the
    raster pixels of untouched glyphs. We only activate this
    narrower path when OCR supplied a character box for the exact changed glyph.
    """
    old = str(edit.get("oldText", ""))
    new = str(edit.get("newText", ""))
    if not old or len(old) != len(new):
        return None
    changed = [i for i, (before, after) in enumerate(zip(old, new)) if before != after]
    if len(changed) != 1:
        return None
    index = changed[0]
    mapping = _map_scan_text_chars(old, list(edit.get("chars") or []))
    char = mapping.get(index)
    if not char or str(char.get("c", "")) != old[index]:
        return None
    bbox = char.get("bbox") or []
    if len(bbox) != 4:
        return None
    try:
        x0, y0, x1, y1 = [float(v) for v in bbox]
    except Exception:
        return None
    if x1 <= x0 or y1 <= y0:
        return None
    return {
        "glyph_bbox": [x0, y0, x1, y1],
        "glyph_old": old[index],
        "glyph_new": new[index],
        "glyph_index": index,
    }


def _scan_patch_kwargs(edit: dict) -> dict:
    """Pass scan-only, non-destructive visual tuning to the raster patch engine.

    The browser stores these values on each edit so an exported PDF uses exactly
    the same appearance as the preview.  Unknown / out-of-range values are
    clamped in ``scan_revision_visual``; keeping the raw dictionary here also
    makes older saved edits fully backward compatible.
    """
    return {
        "chars": edit.get("chars") or [],
        "visual_adjust": edit.get("visualAdjust") or {},
        "reusable_glyph": edit.get("reusableGlyph") or None,
    }


def analyze_scan_revision(edit: dict, pdf_path: str | None = None) -> dict:
    old = str(edit.get("oldText", ""))
    new = str(edit.get("newText", ""))
    if old == new:
        return {"mode": "none", "visualVerified": True, "reason": "未修改"}
    bbox = _refine_scan_display_bbox(edit)
    manual = bool(edit.get("manualSelection"))
    token_bbox = edit.get("tokenBbox") or edit.get("bbox") or bbox
    boundary_ok, boundary_reason = validate_field_boundary(bbox, token_bbox, manual=manual or not bool(edit.get("requiresIsolation")))
    if not boundary_ok:
        return {"mode": "blocked", "visualVerified": False, "reason": boundary_reason, "fieldBbox": bbox}
    # A v2.3.2 subfield already has a verified character-geometry rectangle. The
    # legacy pixel refiner was designed for whole OCR words and can shrink that
    # rectangle onto only part of a model number, causing a shifted overlay.
    if pdf_path and not bool(edit.get("characterGeometry")):
        pixel_bbox = refine_structured_field_bbox(pdf_path, int(edit.get("page", -1)), old, bbox)
        if pixel_bbox:
            bbox = pixel_bbox
    if len(bbox) != 4:
        return {"mode": "blocked", "visualVerified": False, "reason": "OCR 文字区域无效，请重新选择文字块"}
    try:
        x0, y0, x1, y1 = [float(v) for v in bbox]
    except Exception:
        return {"mode": "blocked", "visualVerified": False, "reason": "OCR 文字坐标无效"}
    if x1 <= x0 or y1 <= y0:
        return {"mode": "blocked", "visualVerified": False, "reason": "OCR 文字区域尺寸无效"}
    if not new.strip():
        return {"mode": "blocked", "visualVerified": False, "reason": "修订文字不能为空"}

    # If refinement did not actually isolate a field, do not touch neighbouring text.
    raw = edit.get("bbox") or bbox
    try:
        raw_w = max(0.1, float(raw[2]) - float(raw[0]))
    except Exception:
        raw_w = x1 - x0
    mapping = _map_scan_text_chars(old, list(edit.get("chars") or []))
    coverage = len(mapping) / max(1, len(old))
    if coverage < 0.6 and not manual:
        return {
            "mode": "blocked",
            "visualVerified": False,
            "reason": "未能自动定位结构化字段，请使用‘框选字段’。",
        }
    # A refined field may be much smaller than the OCR token; that is expected. But if
    # the refined box is still almost the whole large token, refuse a broad rewrite.
    if raw_w > (x1 - x0) * 1.8 and (x1 - x0) > 0 and coverage < 0.9 and not manual:
        return {
            "mode": "blocked",
            "visualVerified": False,
            "reason": "字段边界仍不可靠，已阻止覆盖旁边文字",
        }
    layout_metrics = None
    if pdf_path:
        try:
            patch = build_scan_revision_patch(
                pdf_path, int(edit.get("page", -1)), bbox, old, new,
                **_scan_patch_kwargs(edit),
            )
            layout_metrics = patch.get("metrics") or {}
            # v2.3.10: only destructive-risk failures are hard blockers.  A visual
            # score below the suggested threshold must still be previewable so the
            # internal tester can judge the real page at 100%/200% instead of being
            # trapped by an over-sensitive heuristic.
            hard_safety = layout_metrics.get("hardSafetyPassed")
            if hard_safety is None:
                hard_safety = (
                    int(layout_metrics.get("preservationViolationPixels") or 0) == 0
                    and int(layout_metrics.get("neighbourOverlapPixels") or 0)
                    <= int(layout_metrics.get("neighbourOverlapLimit") or 0)
                )
            if hard_safety is False:
                return {
                    "mode": "blocked",
                    "visualVerified": False,
                    "reason": layout_metrics.get("qualityWarning") or "检测到页面保护或邻字重叠风险，已阻止生成",
                    "fieldBbox": bbox,
                    "layoutMetrics": layout_metrics,
                }
        except Exception as ex:
            return {
                "mode": "blocked",
                "visualVerified": False,
                "reason": f"扫描文字视觉布局检查失败：{ex}",
                "fieldBbox": bbox,
            }
    return {
        "mode": "scanrevision",
        "visualVerified": True,
        "reason": (layout_metrics or {}).get("qualityWarning") or "页面保护检查已通过；建议在 100%/200% 下确认视觉协调",
        "revisionMarked": False,
        "fieldBbox": bbox,
        "charCoverage": round(coverage, 3),
        "layoutMetrics": layout_metrics,
    }


def _fit_revision_text(page: fitz.Page, display_rect: fitz.Rect, text: str, fontname: str, color=(0.08, 0.08, 0.08)) -> float:
    """Fit revision text into one isolated field without letter stretching.

    The function only changes font size; it never inserts inter-character spacing and
    never expands the field into adjacent OCR content.
    """
    text = str(text or "").replace("\r", " ").replace("\n", " ")
    pad_x = max(1.0, min(display_rect.height * 0.10, 2.2))
    pad_y = max(0.8, min(display_rect.height * 0.08, 1.8))
    avail_w = max(3.0, float(display_rect.width) - pad_x * 2)
    avail_h = max(3.0, float(display_rect.height) - pad_y * 2)
    fs = max(5.0, min(avail_h * 0.82, 26.0))
    try:
        width = float(fitz.get_text_length(text, fontname=fontname, fontsize=fs))
        if width > avail_w and width > 0:
            fs *= avail_w / width
    except Exception:
        pass
    if fs < 4.5:
        raise ValueError("新文字在原字段范围内无法清晰排版，请缩短文字或重新选择字段")

    # Visual-space baseline. For typical report scans the ASCII field is serif, so
    # Times gives a more natural revision appearance while remaining visibly edited.
    baseline_display = fitz.Point(display_rect.x0 + pad_x, display_rect.y0 + pad_y + fs * 0.93)
    baseline_pdf = baseline_display * page.derotation_matrix if page.rotation else baseline_display
    page.insert_text(
        baseline_pdf,
        text,
        fontsize=fs,
        fontname=fontname,
        color=color,
        rotate=int(page.rotation or 0),
        overlay=True,
    )
    return fs


def apply_scan_revision_edit(doc: fitz.Document, edit: dict, original_path: str | None = None) -> tuple[bool, dict]:
    plan = analyze_scan_revision(edit, original_path)
    if plan.get("mode") == "none":
        return True, plan
    if plan.get("mode") != "scanrevision":
        return False, plan
    if not original_path:
        return False, {"mode": "blocked", "visualVerified": False, "reason": "扫描文字引擎缺少原始 PDF 路径"}
    pno = int(edit.get("page", -1))
    if pno < 0 or pno >= doc.page_count:
        return False, {"mode": "blocked", "visualVerified": False, "reason": "扫描文字页码无效"}
    page = doc.load_page(pno)
    display_bbox = list(plan.get("fieldBbox") or _refine_scan_display_bbox(edit))
    try:
        patch = build_scan_revision_patch(
            original_path, pno, display_bbox,
            str(edit.get("oldText", "")), str(edit.get("newText", "")),
            **_scan_patch_kwargs(edit),
        )
        for local_patch in patch.get("patches", [patch]):
            overlay_bbox = local_patch.get("overlayBbox") or display_bbox
            rect = _display_rect_to_pdf(page, overlay_bbox)
            page.insert_image(rect, stream=local_patch["png"], overlay=True,
                rotate=int(page.rotation or 0), keep_proportion=False)
        # Keep scan revisions searchable/accessibility-friendly without changing
        # appearance.
        search_box = fitz.Rect(*display_bbox)
        fs = max(4.5, min(18.0, float(search_box.height) * 0.72))
        anchor_display = fitz.Point(search_box.x0, search_box.y0 + fs)
        anchor_pdf = anchor_display * page.derotation_matrix if page.rotation else anchor_display
        page.insert_text(
            anchor_pdf, str(edit.get("newText", "")), fontsize=fs,
            fontname="china-s" if contains_cjk(str(edit.get("newText", ""))) else "helv", color=(0, 0, 0), render_mode=3,
            rotate=int(page.rotation or 0), overlay=True
        )
    except Exception as ex:
        return False, {"mode": "blocked", "visualVerified": False, "reason": f"扫描文字字段排版失败：{ex}"}
    return True, {**plan, "layoutMetrics": patch.get("metrics") or {}}


def apply_edits_to_doc(doc: fitz.Document, edits: list[dict], original_bytes: bytes, original_path: str | None = None, cache_dir: str | Path | None = None, only_page: int | None = None):
    """Apply edits in explicit revision mode.

    Electronic text keeps the established engine. Scan/image PDF text uses a field-local
    raster revision patch with automatic layout checks.
    """
    by_page: dict[int, list[dict]] = {}
    for edit in edits or []:
        p = int(edit.get("page", -1))
        if p < 0 or p >= doc.page_count:
            continue
        if only_page is not None and p != only_page:
            continue
        by_page.setdefault(p, []).append(edit)

    plans: dict[tuple[int, str], dict] = {}
    occupied_scan_regions: dict[int, list] = {}
    for pno, page_edits in by_page.items():
        for e in page_edits:
            if e.get('action') == 'delete':
                continue
            if e.get("type") != "text":
                continue
            engine = str(e.get("engine", "electronic"))
            if engine == "scan":
                if not original_path:
                    raise ValueError("扫描文字引擎缺少原始 PDF 路径")
                info = analyze_scan_revision(e, original_path)
                if info.get("mode") not in {"scanrevision", "none"} or not info.get("visualVerified", False):
                    raise ValueError(info.get("reason", "该扫描文字无法生成稳定修订"))
                for region in (info.get('layoutMetrics') or {}).get('regions', []):
                    box=fitz.Rect(region['blend_bbox'])
                    if any((box & previous).get_area()>.25 for previous in occupied_scan_regions.get(pno, [])):
                        raise ValueError('多个修改覆盖同一字符，请先恢复重叠修改，再编辑整行')
                    occupied_scan_regions.setdefault(pno, []).append(box)
            else:
                info = analyze_verified_edit(original_bytes, e)
                if info.get("mode") not in {"stream", "docglyph", "glyph", "none"} or not info.get("visualVerified", False):
                    raise ValueError(info.get("reason", "该文字未通过电子文本修订检查"))
            plans[(pno, str(e.get("id", "")))] = info

    for pno, page_edits in by_page.items():
        # Deletions are local raster inpaint patches and are intentionally user-previewed.
        for e in [x for x in page_edits if x.get('action') == 'delete']:
            applied, dinfo = apply_delete_edit(doc, e, original_path or '')
            if not applied: raise ValueError(dinfo.get('reason','删除失败'))
        # Existing page-number fields with structural / length changes use a
        # dedicated local replacement path instead of the normal same-glyph engine.
        for e in [x for x in page_edits if x.get("type") == "page-number-replace"]:
            applied, pinfo = apply_page_number_replace(doc, e, original_path)
            if not applied:
                raise ValueError(pinfo.get("reason", "页码替换失败"))
        # Blank page-number slots are explicit additions.
        for e in [x for x in page_edits if x.get("type") == "page-number-add"]:
            applied, pinfo = apply_page_number_add(doc, e)
            if not applied:
                raise ValueError(pinfo.get("reason", "新增页码失败"))
        # User-positioned free text blocks are independent from OCR replacement.
        for e in [x for x in page_edits if x.get("type") == "free-text"]:
            applied, finfo = apply_free_text(doc, e)
            if not applied:
                raise ValueError(finfo.get("reason", "自由文字块生成失败"))
        # Text edits are applied by their respective engine.
        for e in [x for x in page_edits if x.get("type") == "text" and x.get('action') != 'delete']:
            plan = plans[(pno, str(e.get("id", "")))]
            if str(e.get("engine", "electronic")) == "scan":
                applied, info = apply_scan_revision_edit(doc, e, original_path)
            else:
                applied, info = apply_verified_edit(doc, e, str(plan.get("mode")), original_bytes)
            if not applied:
                raise ValueError(info.get("reason", "文字修订应用失败"))

        page = doc.load_page(pno)
        for e in [x for x in page_edits if x.get("type") == "image" and x.get('action') != 'delete']:
            if not e.get("dataUrl"):
                continue
            bbox = e.get("pdfBbox") or e.get("bbox")
            if not bbox or len(bbox) != 4:
                continue
            rect = fitz.Rect(*[float(v) for v in bbox])
            try:
                img = data_url_bytes(e["dataUrl"])
                keep = e.get("fit", "contain") != "cover"
                page.insert_image(rect, stream=img, keep_proportion=keep, overlay=True)
            except Exception as ex:
                raise ValueError(f"图片替换失败：{ex}")


def _image_phash(doc: fitz.Document, xref: int) -> int | None:
    """Small perceptual hash for repeated-image discovery."""
    try:
        data=doc.extract_image(int(xref or 0)).get("image")
        if not data:return None
        arr=np.frombuffer(data,np.uint8);img=cv2.imdecode(arr,cv2.IMREAD_GRAYSCALE)
        if img is None:return None
        img=cv2.resize(img,(32,32),interpolation=cv2.INTER_AREA)
        dct=cv2.dct(np.float32(img));low=dct[:8,:8];med=float(np.median(low[1:]))
        bits=(low>med).flatten();v=0
        for b in bits:v=(v<<1)|int(bool(b))
        return int(v)
    except Exception:return None

def _phash_similarity(a: int | None,b: int | None)->float:
    if a is None or b is None:return 0.0
    dist=(int(a)^int(b)).bit_count();return max(0.0,100.0*(1.0-dist/64.0))

def find_delete_matches(doc: fitz.Document, source: dict, kind: str, pdf_path: str | None=None, cache_dir=None, diagnosis=None) -> list[dict]:
    """Find exact text or visually-similar embedded images for user-reviewed deletion."""
    out=[]
    if kind=='text':
        target=str(source.get('oldText') or source.get('text') or '').strip()
        if not target:return []
        for pno in range(doc.page_count):
            pdata=page_data(doc,pno,pdf_path=pdf_path,cache_dir=cache_dir,diagnosis=diagnosis)
            for item in pdata.get('text',[]) or []:
                if str(item.get('text','')).strip()==target:
                    out.append({'page':pno,'item':item,'similarity':100})
        return out
    src_xref=int(source.get('xref') or 0);src_digest=str(source.get('digest') or '')
    src_hash=_image_phash(doc,src_xref) if src_xref else None
    for pno in range(doc.page_count):
        pdata=page_data(doc,pno,pdf_path=pdf_path,cache_dir=cache_dir,diagnosis=diagnosis)
        for item in pdata.get('images',[]) or []:
            digest=str(item.get('digest') or '')
            if src_digest and digest and digest==src_digest:sim=100.0
            else:
                h=_image_phash(doc,int(item.get('xref') or 0));sim=_phash_similarity(src_hash,h)
            if sim>=88.0:out.append({'page':pno,'item':item,'similarity':round(sim,1)})
    return out

def build_delete_patch(pdf_path: str,page_no: int,display_bbox,kind: str='text',scale: float=3.0) -> dict:
    """Create a local inpaint patch. It never rewrites the whole page."""
    with fitz.open(pdf_path) as doc:
        page=doc.load_page(page_no);pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
        img=np.array(Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB'))
        H,W=img.shape[:2]
        x0,y0,x1,y1=[float(v) for v in display_bbox]
        pad=max(5,int(round(6*scale)))
        ax0=max(0,int(round(x0*scale))-pad);ay0=max(0,int(round(y0*scale))-pad);ax1=min(W,int(round(x1*scale))+pad);ay1=min(H,int(round(y1*scale))+pad)
        crop=img[ay0:ay1,ax0:ax1].copy();mask=np.zeros(crop.shape[:2],np.uint8)
        tx0=max(0,int(round(x0*scale))-ax0);ty0=max(0,int(round(y0*scale))-ay0);tx1=min(crop.shape[1],int(round(x1*scale))-ax0);ty1=min(crop.shape[0],int(round(y1*scale))-ay0)
        if tx1<=tx0 or ty1<=ty0:raise ValueError('删除区域无效')
        if kind=='image':
            mask[ty0:ty1,tx0:tx1]=255
        else:
            roi=crop[ty0:ty1,tx0:tx1]
            gray=cv2.cvtColor(roi,cv2.COLOR_RGB2GRAY)
            # Estimate nearby paper/background from a ring around the selected token.
            border=np.concatenate([crop[:max(1,ty0),:,:].reshape(-1,3),crop[min(crop.shape[0],ty1):,:,:].reshape(-1,3),crop[:, :max(1,tx0),:].reshape(-1,3),crop[:, min(crop.shape[1],tx1):,:].reshape(-1,3)],axis=0) if crop.size else np.empty((0,3))
            bg=np.median(border,axis=0) if border.size else np.array([245,245,245])
            diff=np.max(np.abs(roi.astype(np.int16)-bg.astype(np.int16)),axis=2)
            bggray=float(np.mean(bg));dark=(gray < max(245,bggray)-12)
            local=((diff>16)|dark).astype(np.uint8)*255
            local=cv2.morphologyEx(local,cv2.MORPH_CLOSE,np.ones((2,2),np.uint8))
            local=cv2.dilate(local,np.ones((3,3),np.uint8),iterations=1)
            mask[ty0:ty1,tx0:tx1]=local
            # Very light / low-contrast OCR text can evade thresholding. Keep a conservative fallback.
            if cv2.countNonZero(local)<max(4,int(local.size*.01)):
                mask[ty0:ty1,tx0:tx1]=255
        radius=max(2.0,min(9.0,3.0*scale))
        bgr=cv2.cvtColor(crop,cv2.COLOR_RGB2BGR);filled=cv2.inpaint(bgr,mask,radius,cv2.INPAINT_TELEA);out=cv2.cvtColor(filled,cv2.COLOR_BGR2RGB)
        buff=io.BytesIO();Image.fromarray(out).save(buff,format='PNG',optimize=True)
        return {'png':buff.getvalue(),'overlayBbox':[ax0/scale,ay0/scale,ax1/scale,ay1/scale]}

def apply_delete_edit(doc: fitz.Document,edit: dict,original_path: str)->tuple[bool,dict]:
    try:
        pno=int(edit.get('page',-1));bbox=edit.get('bbox') or []
        if pno<0 or pno>=doc.page_count or len(bbox)!=4:return False,{'reason':'删除区域无效'}
        patch=build_delete_patch(original_path,pno,bbox,'image' if edit.get('type')=='image' else 'text')
        page=doc.load_page(pno);rect=_display_rect_to_pdf(page,patch['overlayBbox'])
        page.insert_image(rect,stream=patch['png'],overlay=True,rotate=int(page.rotation or 0),keep_proportion=False)
        return True,{'mode':'delete','visualVerified':True,'reason':'已生成局部删除补丁'}
    except Exception as ex:return False,{'mode':'blocked','visualVerified':False,'reason':f'删除失败：{ex}'}

def _render_crop_png(doc: fitz.Document, page_no: int, display_bbox, scale: float = 3.0, padding: float = 5.0) -> bytes:
    page = doc.load_page(page_no)
    x0, y0, x1, y1 = [float(v) for v in display_bbox]
    box = [max(0.0, x0-padding), max(0.0, y0-padding), min(float(page.rect.width), x1+padding), min(float(page.rect.height), y1+padding)]
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    crop = img.crop(tuple(int(round(v*scale)) for v in box))
    out = io.BytesIO(); crop.save(out, format="PNG", optimize=True)
    return out.getvalue()


def _load_saved_session(sid: str):
    if not re.fullmatch(r"[0-9a-f]{32}", str(sid or "")):
        return None
    folder = WORKDIR / sid
    progress_path = folder / "editor_progress.json"
    original = folder / "original.pdf"
    if not progress_path.exists() or not original.exists():
        return None
    try:
        payload = json.loads(progress_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    baseline_paths = {0: str(original)}
    seq = 0
    for item in folder.glob("baseline_*.pdf"):
        m = re.fullmatch(r"baseline_(\d+)\.pdf", item.name)
        if m:
            n = int(m.group(1)); baseline_paths[n] = str(item); seq = max(seq, n)
    baseline_id = int(payload.get("baselineId", 0) or 0)
    path = baseline_paths.get(baseline_id, str(original))
    cache_dir = folder / "scan_cache"; cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        with fitz.open(path) as doc: diagnosis = diagnose_document(doc)
    except Exception:
        return None
    info = {"path": path, "originalPath": str(original), "name": payload.get("name") or "document.pdf", "diagnosis": diagnosis, "cacheDir": str(cache_dir), "baselineSeq": seq, "currentBaselineId": baseline_id, "baselinePaths": baseline_paths, "progressPath": str(progress_path)}
    SESSIONS[sid] = info
    return info


def get_session(sid: str):
    info = SESSIONS.get(sid) or _load_saved_session(sid)
    if not info or not Path(info["path"]).exists():
        raise KeyError("文件会话已失效，请重新导入 PDF")
    return info


def reset_session_cache(info: dict):
    cache = Path(info.get("cacheDir") or "")
    if cache.exists():
        for child in cache.iterdir():
            try:
                if child.is_dir():
                    import shutil
                    shutil.rmtree(child)
                else:
                    child.unlink()
            except Exception:
                pass
    cache.mkdir(parents=True, exist_ok=True)


def session_document_meta(info: dict) -> dict:
    with fitz.open(info["path"]) as doc:
        diagnosis = diagnose_document(doc)
        page_count = doc.page_count
    info["diagnosis"] = diagnosis
    return {
        "pageCount": page_count,
        "documentType": diagnosis.get("kind", "unknown"),
        "diagnosis": diagnosis,
        "ocrAvailable": diagnosis.get("ocrAvailable", False),
        "ocrReason": diagnosis.get("ocrReason", ""),
        "ocrLang": diagnosis.get("ocrLang", ""),
        "ocrBackend": diagnosis.get("ocrBackend", ""),
        "ocrBackendLabel": diagnosis.get("ocrBackendLabel", ""),
        "baselineId": int(info.get("currentBaselineId", 0)),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "PeditOSS/" + __version__

    def log_message(self, fmt, *args):
        print("[PDF Editor]", fmt % args)

    def send_bytes(self, data: bytes, content_type: str, status=200, headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, obj, status=200):
        self.send_bytes(json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def fail(self, message: str, status=400):
        self.send_json({"ok": False, "error": message}, status)

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            q = parse_qs(parsed.query)

            if path == "/api/page":
                sid = q.get("id", [""])[0]
                pno = int(q.get("page", ["0"])[0])
                scale = min(8.0, max(0.25, float(q.get("scale", ["1.7"])[0])))
                info = get_session(sid)
                with fitz.open(info["path"]) as doc:
                    if pno < 0 or pno >= doc.page_count:
                        return self.fail("页码无效", 404)
                    png = render_page(doc, pno, scale)
                return self.send_bytes(png, "image/png")

            if path == "/api/page-data":
                sid = q.get("id", [""])[0]
                pno = int(q.get("page", ["0"])[0])
                info = get_session(sid)
                with fitz.open(info["path"]) as doc:
                    if pno < 0 or pno >= doc.page_count:
                        return self.fail("页码无效", 404)
                    payload = page_data(doc, pno, pdf_path=info["path"], cache_dir=info.get("cacheDir"), diagnosis=info.get("diagnosis"))
                return self.send_json({"ok": True, **payload})

            if path == "/api/health":
                return self.send_json({"ok": True, "version": __version__, "pymupdf": fitz.VersionBind, "ocr": ocr_status()})

            if path == "/api/resume-progress":
                sid = q.get("id", [""])[0]
                info = get_session(sid)
                progress_path = Path(info.get("progressPath") or (Path(info["path"]).parent / "editor_progress.json"))
                if not progress_path.exists():
                    return self.fail("没有已保存进度", 404)
                payload = json.loads(progress_path.read_text(encoding="utf-8"))
                wanted_baseline = int(payload.get("baselineId", 0) or 0)
                target = (info.get("baselinePaths") or {}).get(wanted_baseline)
                if target and Path(target).exists() and wanted_baseline != int(info.get("currentBaselineId", 0)):
                    info["path"] = str(target); info["currentBaselineId"] = wanted_baseline; reset_session_cache(info)
                meta = session_document_meta(info)
                return self.send_json({"ok": True, "id": sid, "name": info.get("name", "document.pdf"), "outputName": output_name(info.get("name", "document.pdf")), **meta, "progress": payload.get("state") or {}, "savedAt": payload.get("savedAt", "")})

            if path == "/":
                path = "/index.html"
            target = (STATIC / path.lstrip("/")).resolve()
            if not target.is_relative_to(STATIC.resolve()) or not target.exists() or not target.is_file():
                return self.send_error(404)
            mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            return self.send_bytes(target.read_bytes(), mime)
        except KeyError as e:
            self.fail(str(e), 404)
        except Exception as e:
            self.fail(str(e), 500)

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            if path == "/api/open":
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0:
                    return self.fail("没有收到 PDF 文件")
                if length > MAX_UPLOAD:
                    return self.fail("PDF 超过 300MB，暂不支持", 413)
                raw = self.rfile.read(length)
                name_header = self.headers.get("X-Filename", "document.pdf")
                try:
                    from urllib.parse import unquote
                    name = safe_name(unquote(name_header))
                except Exception:
                    name = "document.pdf"
                try:
                    doc = fitz.open(stream=raw, filetype="pdf")
                    page_count = doc.page_count
                    if page_count < 1:
                        raise ValueError("PDF 没有页面")
                    first = doc.load_page(0)
                    first_rect = [float(first.rect.width), float(first.rect.height)]
                    diagnosis = diagnose_document(doc)
                    doc.close()
                except Exception as ex:
                    return self.fail(f"无法打开 PDF：{ex}")
                sid = uuid.uuid4().hex
                folder = WORKDIR / sid
                folder.mkdir(parents=True, exist_ok=True)
                pdf_path = folder / "original.pdf"
                pdf_path.write_bytes(raw)
                cache_dir = folder / "scan_cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                SESSIONS[sid] = {
                    "path": str(pdf_path), "originalPath": str(pdf_path), "name": name,
                    "diagnosis": diagnosis, "cacheDir": str(cache_dir),
                    "baselineSeq": 0, "currentBaselineId": 0, "baselinePaths": {0: str(pdf_path)},
                }
                return self.send_json({
                    "ok": True,
                    "id": sid,
                    "name": name,
                    "outputName": output_name(name),
                    "pageCount": page_count,
                    "firstPageSize": first_rect,
                    "documentType": diagnosis.get("kind", "unknown"),
                    "diagnosis": diagnosis,
                    "ocrAvailable": diagnosis.get("ocrAvailable", False),
                    "ocrReason": diagnosis.get("ocrReason", ""),
                    "ocrLang": diagnosis.get("ocrLang", ""),
                    "ocrBackend": diagnosis.get("ocrBackend", ""),
                    "ocrBackendLabel": diagnosis.get("ocrBackendLabel", ""),
                    "baselineId": 0,
                })


            if path == "/api/page-number-template/capture":
                body = parse_json(self)
                sid = body.get("id", "")
                info = get_session(sid)
                pno = int(body.get("page", -1))
                rect = body.get("bbox") or []
                with fitz.open(info["path"]) as doc:
                    if pno < 0 or pno >= doc.page_count:
                        return self.fail("页码页码无效")
                    pdata = page_data(doc, pno, pdf_path=info["path"], cache_dir=info.get("cacheDir"), diagnosis=info.get("diagnosis"))
                field = _page_number_box_capture(pdata, rect)
                if not field:
                    return self.fail("框选区域无效，请重新框选")
                return self.send_json({
                    "ok": True,
                    "field": field,
                    "pageWidth": pdata.get("width"),
                    "pageHeight": pdata.get("height"),
                    "pageKind": pdata.get("pageKind"),
                })

            if path == "/api/page-number-template/scan":
                body = parse_json(self)
                sid = body.get("id", "")
                templates = [t for t in (body.get("templates") or []) if isinstance(t, dict) and t.get("bbox")]
                if not templates:
                    return self.fail("请先设置至少一个页码位置模板")
                if len(templates) > 12:
                    return self.fail("一次最多支持 12 个页码框选位置")
                overrides = [t for t in (body.get("overrides") or []) if isinstance(t, dict) and t.get("bbox")]
                override_map = {}
                for override in overrides:
                    try:
                        opage = int(override.get("page", -1))
                        oslot = str(override.get("slot") or "")
                    except Exception:
                        continue
                    if opage >= 0 and oslot:
                        override_map[(opage, oslot)] = override
                info = get_session(sid)
                with fitz.open(info["path"]) as doc:
                    first = max(0, int(body.get("from", 0)))
                    last = min(doc.page_count - 1, int(body.get("to", doc.page_count - 1)))
                    if last < first:
                        return self.fail("页码范围无效")
                    if last - first + 1 > 250:
                        return self.fail("一次最多处理 250 页，请分批处理")
                    results = []
                    # Per-slot normalized center of the previous successful page.
                    # This lets the search follow gradual footer / scan drift while
                    # still falling back to the original user box when a page is
                    # genuinely different.
                    last_center_norm: dict[str, tuple[float, float]] = {}
                    for pno in range(first, last + 1):
                        pdata = page_data(doc, pno, pdf_path=info["path"], cache_dir=info.get("cacheDir"), diagnosis=info.get("diagnosis"))
                        slots = []
                        pw = max(1.0, float(pdata.get("width") or 1))
                        ph = max(1.0, float(pdata.get("height") or 1))
                        for template in templates:
                            slot = str(template.get("slot") or "A")
                            try:
                                apply_from = int(template.get("applyFrom", first))
                                apply_to = int(template.get("applyTo", last))
                            except Exception:
                                apply_from, apply_to = first, last
                            if pno < apply_from or pno > apply_to:
                                continue
                            base_template = override_map.get((pno, slot), template)
                            projected = _project_page_number_bbox(base_template, pdata)
                            work = dict(base_template)
                            if slot in last_center_norm and (pno, slot) not in override_map:
                                nx, ny = last_center_norm[slot]
                                ew = max(1.0, projected[2] - projected[0])
                                eh = max(1.0, projected[3] - projected[1])
                                cx, cy = nx * pw, ny * ph
                                work["preferredBbox"] = [cx - ew / 2, cy - eh / 2, cx + ew / 2, cy + eh / 2]
                            expected = _project_page_number_bbox(work, pdata)
                            item = _page_number_position_match(pdata, work)
                            # If tracked drift misses, retry from this page's base
                            # template. A page-specific manual override always wins.
                            if not item and slot in last_center_norm and (pno, slot) not in override_map:
                                expected = projected
                                item = _page_number_position_match(pdata, base_template)
                            if item:
                                ib = item.get("bbox") or expected
                                if len(ib) == 4:
                                    try:
                                        icx = (float(ib[0]) + float(ib[2])) / 2.0
                                        icy = (float(ib[1]) + float(ib[3])) / 2.0
                                        last_center_norm[slot] = (icx / pw, icy / ph)
                                    except Exception:
                                        pass
                                fmt = str(base_template.get("format") or template.get("format") or "{current}")
                                parts = _page_number_parts(item, fmt)
                                slots.append({
                                    "slot": slot,
                                    "found": True,
                                    "expectedBbox": [round(float(v), 3) for v in expected],
                                    "item": item,
                                    "oldText": str(item.get("text", "")),
                                    "parts": parts,
                                    "tracked": slot in last_center_norm,
                                })
                            else:
                                slots.append({
                                    "slot": slot,
                                    "found": False,
                                    "expectedBbox": [round(float(v), 3) for v in expected],
                                    "pageKind": str(pdata.get("pageKind") or "unknown"),
                                })
                        results.append({"page": pno, "slots": slots})
                return self.send_json({"ok": True, "results": results})

            if path == "/api/page-numbers/scan":
                body = parse_json(self)
                sid = body.get("id", "")
                info = get_session(sid)
                with fitz.open(info["path"]) as doc:
                    first=max(0,int(body.get("from",0)));last=min(doc.page_count-1,int(body.get("to",doc.page_count-1)))
                    if last < first:return self.fail("页码范围无效")
                    if last-first+1 > 250:return self.fail("一次最多扫描 250 页，请分批处理")
                    results=[]
                    for pno in range(first,last+1):
                        pdata=page_data(doc,pno,pdf_path=info["path"],cache_dir=info.get("cacheDir"),diagnosis=info.get("diagnosis"))
                        found=_page_number_candidate_item(pdata,pno)
                        if found:results.append({"page":pno,"found":True,**found})
                        else:results.append({"page":pno,"found":False})
                return self.send_json({"ok":True,"results":results})

            if path == "/api/delete/matches":
                body=parse_json(self);sid=body.get("id","");kind=str(body.get("type","")).strip();source=body.get("source") or {};info=get_session(sid)
                if kind not in {"text","image"}:return self.fail("删除对象类型无效")
                with fitz.open(info["path"]) as doc:
                    matches=find_delete_matches(doc,source,kind,pdf_path=info["path"],cache_dir=info.get("cacheDir"),diagnosis=info.get("diagnosis"))
                return self.send_json({"ok":True,"matches":matches,"count":len(matches)})

            if path == "/api/find-matches":
                body = parse_json(self)
                sid = body.get("id", "")
                source = body.get("source") or {}
                same_position = bool(body.get("samePosition", True))
                info = get_session(sid)
                raw = Path(info["path"]).read_bytes()
                with fitz.open(stream=raw, filetype="pdf") as doc:
                    matches = find_matching_text_items(doc, source, same_position, pdf_path=info["path"], cache_dir=info.get("cacheDir"), diagnosis=info.get("diagnosis"))
                return self.send_json({"ok": True, "matches": matches, "count": len(matches)})

            if path == "/api/manual-region":
                body = parse_json(self)
                info = get_session(body.get("id", ""))
                pno = int(body.get("page", -1))
                rect = body.get("bbox") or []
                with fitz.open(info["path"]) as doc:
                    pdata = page_data(doc, pno, pdf_path=info["path"], cache_dir=info.get("cacheDir"), diagnosis=info.get("diagnosis"))
                result = manual_region_from_page(pdata.get("text", []), rect)
                allow_empty = bool(body.get("allowEmpty", False))
                if not result:
                    if not allow_empty:
                        return self.fail("局部 OCR 无法稳定识别该字段，请重新框选。")
                    result = {"text": "", "bbox": [float(v) for v in rect], "chars": [], "source": "manual-empty"}
                if not result.get("text") and not allow_empty:
                    return self.fail("局部 OCR 无法稳定识别该字段，请重新框选。")
                result["bbox"] = [float(v) for v in rect]
                return self.send_json({"ok": True, "field": result, "pageKind": pdata.get("pageKind", "unknown")})

            if path == "/api/batch-feasibility":
                body = parse_json(self)
                sid = body.get("id", "")
                edits = body.get("edits") or []
                if len(edits) > 250:
                    return self.fail("一次最多校验 250 页，请分批处理")
                info = get_session(sid)
                raw = Path(info["path"]).read_bytes()
                results = []
                for edit in edits:
                    if str(edit.get("type", "text")) == "page-number-add":
                        result = analyze_page_number_add(edit)
                    elif str(edit.get("type", "text")) == "free-text":
                        result = analyze_free_text(edit)
                    elif str(edit.get("type", "text")) == "page-number-replace":
                        result = analyze_page_number_replace(edit)
                    elif str(edit.get("engine", "electronic")) == "scan":
                        result = analyze_scan_revision(edit, info["path"])
                    else:
                        result = analyze_verified_edit(raw, edit)
                    results.append({"page": int(edit.get("page", -1)), "id": str(edit.get("id", "")), "result": result})
                return self.send_json({"ok": True, "results": results})

            if path == "/api/feasibility":
                body = parse_json(self)
                sid = body.get("id", "")
                edit = body.get("edit") or {}
                info = get_session(sid)
                raw = Path(info["path"]).read_bytes()
                if str(edit.get("type", "text")) == "page-number-add":
                    result = analyze_page_number_add(edit)
                elif str(edit.get("type", "text")) == "free-text":
                    result = analyze_free_text(edit)
                elif str(edit.get("type", "text")) == "page-number-replace":
                    result = analyze_page_number_replace(edit)
                elif str(edit.get("engine", "electronic")) == "scan":
                    result = analyze_scan_revision(edit, info["path"])
                else:
                    result = analyze_verified_edit(raw, edit)
                return self.send_json({"ok": True, **result})

            if path == "/api/save-progress":
                body = parse_json(self)
                sid = body.get("id", "")
                info = get_session(sid)
                folder = Path(info["path"]).parent
                payload = {
                    "version": __version__,
                    "savedAt": datetime.now().isoformat(timespec="seconds"),
                    "baselineId": int(info.get("currentBaselineId", 0)),
                    "name": info.get("name", "document.pdf"),
                    "state": body.get("state") or {},
                }
                progress_path = folder / "editor_progress.json"
                progress_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                info["progressPath"] = str(progress_path)
                return self.send_json({"ok": True, "savedAt": payload["savedAt"], "baselineId": payload["baselineId"]})

            if path == "/api/commit-baseline":
                body = parse_json(self)
                sid = body.get("id", "")
                info = get_session(sid)
                edits = body.get("edits") or []
                raw = Path(info["path"]).read_bytes()
                with fitz.open(stream=raw, filetype="pdf") as doc:
                    apply_edits_to_doc(doc, edits, raw, original_path=info["path"], cache_dir=info.get("cacheDir"))
                    out = doc.tobytes(garbage=3, deflate=True)
                seq = int(info.get("baselineSeq", 0)) + 1
                folder = Path(info["path"]).parent
                baseline_path = folder / f"baseline_{seq}.pdf"
                baseline_path.write_bytes(out)
                info["baselineSeq"] = seq
                info["currentBaselineId"] = seq
                info.setdefault("baselinePaths", {})[seq] = str(baseline_path)
                info["path"] = str(baseline_path)
                reset_session_cache(info)
                meta = session_document_meta(info)
                return self.send_json({"ok": True, **meta, "baselineId": seq, "appliedEdits": len(edits)})

            if path == "/api/baseline/restore":
                body = parse_json(self)
                sid = body.get("id", "")
                baseline_id = int(body.get("baselineId", 0))
                info = get_session(sid)
                paths = info.get("baselinePaths") or {}
                target = paths.get(baseline_id)
                if not target or not Path(target).exists():
                    return self.fail("找不到该基线文件", 404)
                info["path"] = str(target)
                info["currentBaselineId"] = baseline_id
                reset_session_cache(info)
                meta = session_document_meta(info)
                return self.send_json({"ok": True, **meta})

            if path == "/api/region-crop":
                body = parse_json(self)
                sid = body.get("id", "")
                pno = int(body.get("page", 0))
                bbox = body.get("bbox") or []
                if len(bbox) != 4:
                    return self.fail("裁切区域无效")
                scale = min(8.0, max(1.0, float(body.get("scale", 5.0))))
                padding = min(30.0, max(0.0, float(body.get("padding", 3.0))))
                info = get_session(sid)
                raw = Path(info["path"]).read_bytes()
                with fitz.open(stream=raw, filetype="pdf") as doc:
                    edits = body.get("edits") or []
                    if edits:
                        apply_edits_to_doc(doc, edits, raw, original_path=info["path"], cache_dir=info.get("cacheDir"), only_page=pno)
                    png = _render_crop_png(doc, pno, bbox, scale, padding)
                return self.send_bytes(png, "image/png")

            if path == "/api/preview":
                body = parse_json(self)
                sid = body.get("id", "")
                pno = int(body.get("page", 0))
                scale = min(8.0, max(0.4, float(body.get("scale", 1.7))))
                info = get_session(sid)
                raw = Path(info["path"]).read_bytes()
                with fitz.open(stream=raw, filetype="pdf") as doc:
                    apply_edits_to_doc(doc, body.get("edits", []), raw, original_path=info["path"], cache_dir=info.get("cacheDir"), only_page=pno)
                    png = render_page(doc, pno, scale)
                return self.send_bytes(png, "image/png")

            if path == "/api/compare-crop":
                body = parse_json(self)
                sid = body.get("id", "")
                pno = int(body.get("page", 0))
                bbox = body.get("bbox") or []
                if len(bbox) != 4:
                    return self.fail("对比区域无效")
                info = get_session(sid)
                raw = Path(info["path"]).read_bytes()
                with fitz.open(stream=raw, filetype="pdf") as original_doc:
                    before = _render_crop_png(original_doc, pno, bbox, 3.2, 5.0)
                with fitz.open(stream=raw, filetype="pdf") as revised_doc:
                    apply_edits_to_doc(revised_doc, body.get("edits", []), raw, original_path=info["path"], cache_dir=info.get("cacheDir"), only_page=pno)
                    after = _render_crop_png(revised_doc, pno, bbox, 3.2, 5.0)
                bimg = Image.open(io.BytesIO(before)).convert("RGB")
                aimg = Image.open(io.BytesIO(after)).convert("RGB")
                changed = 1 if page_changed(bimg, aimg) else 0
                combined = compose_comparison(before, after)
                return self.send_bytes(combined, "image/png", headers={"X-Page-Changed": str(changed)})

            if path == "/api/export":
                body = parse_json(self)
                sid = body.get("id", "")
                info = get_session(sid)
                raw = Path(info["path"]).read_bytes()
                with fitz.open(stream=raw, filetype="pdf") as doc:
                    edits = body.get("edits", [])
                    apply_edits_to_doc(doc, edits, raw, original_path=info["path"], cache_dir=info.get("cacheDir"))
                    out = doc.tobytes(garbage=3, deflate=True)
                filename = output_name(info["name"])
                headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"}
                return self.send_bytes(out, "application/pdf", headers=headers)

            return self.fail("接口不存在", 404)
        except KeyError as e:
            self.fail(str(e), 404)
        except ValueError as e:
            self.fail(str(e), 400)
        except Exception as e:
            self.fail(f"处理失败：{e}", 500)


def open_browser():
    webbrowser.open(f"http://{HOST}:{PORT}")


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print("=" * 58)
    print("Pedit OSS v" + __version__)
    print(f"本地地址：http://{HOST}:{PORT}")
    print("双引擎：电子 PDF 精准修订 + 扫描 PDF 字段级稳定修订。")
    print("所有 PDF 仅在本机处理。按 Ctrl+C 退出。")
    print("=" * 58)
    if os.environ.get("PEDIT_NO_BROWSER") != "1":
        threading.Timer(0.7, open_browser).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
