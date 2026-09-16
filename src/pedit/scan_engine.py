from __future__ import annotations

import io
import json
import math
import os
import shutil
from pathlib import Path
from typing import Any

import pymupdf as fitz
from PIL import Image

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

try:
    import pytesseract
    from pytesseract import Output
except Exception:  # pragma: no cover
    pytesseract = None
    Output = None

try:
    import onnxruntime  # noqa: F401
except Exception:  # pragma: no cover
    onnxruntime = None

try:
    from rapidocr import RapidOCR
except Exception:  # pragma: no cover
    RapidOCR = None

OCR_SCALE = 3.0
MIN_WORD_CONF = 35.0
_OCR_MEM_CACHE: dict[tuple[str, int, float], dict] = {}
_CHAR_MEM_CACHE: dict[tuple[str, int, float], list[dict]] = {}
_RENDER_MEM_CACHE: dict[tuple[str, int, float], Any] = {}
_RAPID_ENGINE = None
_RAPID_ENGINE_ERROR: str | None = None


def _find_tesseract() -> str | None:
    explicit = os.environ.get("TESSERACT_CMD")
    candidates = [explicit, shutil.which("tesseract")]
    if os.name == "nt":
        candidates += [
            str(Path(os.environ.get("ProgramFiles") or (Path.home().anchor + "Program Files")) / "Tesseract-OCR" / "tesseract.exe"),
            str(Path(os.environ.get("ProgramFiles(x86)") or (Path.home().anchor + "Program Files (x86)")) / "Tesseract-OCR" / "tesseract.exe"),
            str(Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe"),
        ]
    for p in candidates:
        if p and Path(p).exists():
            return str(Path(p))
    return None


def _get_rapid_engine():
    """Lazy-load the built-in OCR engine.

    RapidOCR and ONNX Runtime are optional local recognition dependencies.
    Tesseract remains a fallback when its executable and language data exist.
    """
    global _RAPID_ENGINE, _RAPID_ENGINE_ERROR
    if _RAPID_ENGINE is not None:
        return _RAPID_ENGINE
    if _RAPID_ENGINE_ERROR:
        return None
    if RapidOCR is None or onnxruntime is None:
        missing = []
        if RapidOCR is None:
            missing.append("rapidocr")
        if onnxruntime is None:
            missing.append("onnxruntime")
        _RAPID_ENGINE_ERROR = "缺少内置 OCR 组件：" + "、".join(missing)
        return None
    try:
        _RAPID_ENGINE = RapidOCR(params={
            "Global.log_level": "critical",
            "Global.return_word_box": True,
            "Global.return_single_char_box": True,
            "Global.text_score": 0.35,
        })
        return _RAPID_ENGINE
    except Exception as ex:  # pragma: no cover - depends on local runtime
        _RAPID_ENGINE_ERROR = f"内置 RapidOCR 初始化失败：{ex}"
        return None


def _tesseract_status() -> dict:
    if pytesseract is None:
        return {"available": False, "reason": "缺少 pytesseract Python 组件", "languages": [], "lang": "", "backend": ""}
    cmd = _find_tesseract()
    if not cmd:
        return {"available": False, "reason": "未检测到本机 Tesseract OCR", "languages": [], "lang": "", "backend": ""}
    pytesseract.pytesseract.tesseract_cmd = cmd
    try:
        langs = list(pytesseract.get_languages(config=""))
    except Exception as ex:
        return {"available": False, "reason": f"Tesseract 无法启动：{ex}", "languages": [], "lang": "", "backend": ""}
    if "chi_sim" in langs and "eng" in langs:
        lang = "chi_sim+eng"
    elif "HanS" in langs and "eng" in langs:
        lang = "HanS+eng"
    elif "chi_sim" in langs:
        lang = "chi_sim"
    elif "HanS" in langs:
        lang = "HanS"
    elif "eng" in langs:
        lang = "eng"
    elif langs:
        lang = langs[0]
    else:
        return {"available": False, "reason": "Tesseract 没有可用语言包", "languages": [], "lang": "", "backend": ""}
    return {"available": True, "reason": "", "languages": langs, "lang": lang, "command": cmd, "backend": "tesseract", "backendLabel": "Tesseract OCR"}


def ocr_status() -> dict:
    # Prefer a pip-installable OCR backend so the Windows user does not have to
    # separately install an EXE and Chinese language pack.
    engine = _get_rapid_engine()
    if engine is not None:
        return {
            "available": True,
            "reason": "",
            "languages": ["ch", "en"],
            "lang": "中英混合",
            "backend": "rapidocr",
            "backendLabel": "内置 RapidOCR",
        }
    ts = _tesseract_status()
    if ts.get("available"):
        return ts
    reasons = [x for x in (_RAPID_ENGINE_ERROR, ts.get("reason")) if x]
    return {
        "available": False,
        "reason": "；".join(reasons) or "OCR 引擎不可用",
        "languages": [],
        "lang": "",
        "backend": "",
        "backendLabel": "",
    }


def _image_coverage(page: fitz.Page) -> float:
    base = abs(float(page.mediabox.width) * float(page.mediabox.height)) or 1.0
    total = 0.0
    try:
        for info in page.get_image_info(xrefs=True):
            b = info.get("bbox")
            if not b:
                continue
            r = fitz.Rect(*b)
            total += max(0.0, r.width) * max(0.0, r.height)
    except Exception:
        return 0.0
    return min(1.0, total / base)


def diagnose_document(doc: fitz.Document) -> dict:
    pages = []
    text_pages = scan_pages = vector_pages = 0
    for pno in range(doc.page_count):
        p = doc.load_page(pno)
        raw_text = (p.get_text("text") or "").strip()
        text_chars = len(raw_text)
        try:
            images = p.get_image_info(xrefs=True)
        except Exception:
            images = []
        image_cov = _image_coverage(p)
        try:
            drawings = len(p.get_drawings())
        except Exception:
            drawings = 0
        if text_chars:
            kind = "electronic"
            text_pages += 1
        elif images and image_cov >= 0.75:
            kind = "scan"
            scan_pages += 1
        elif drawings > 25:
            kind = "vector"
            vector_pages += 1
        else:
            kind = "unknown"
        pages.append({
            "page": pno,
            "kind": kind,
            "textChars": text_chars,
            "images": len(images),
            "imageCoverage": round(image_cov, 3),
            "drawings": drawings,
            "rotation": int(p.rotation or 0),
        })
    if scan_pages == doc.page_count:
        kind = "scan"
    elif text_pages == doc.page_count:
        kind = "electronic"
    elif text_pages and scan_pages:
        kind = "mixed"
    elif vector_pages and not text_pages:
        kind = "vector"
    elif scan_pages:
        kind = "mixed"
    else:
        kind = "unknown"
    status = ocr_status()
    return {
        "kind": kind,
        "pages": pages,
        "electronicPages": text_pages,
        "scanPages": scan_pages,
        "vectorPages": vector_pages,
        "ocrAvailable": bool(status.get("available")),
        "ocrReason": status.get("reason", ""),
        "ocrLang": status.get("lang", ""),
        "ocrBackend": status.get("backend", ""),
        "ocrBackendLabel": status.get("backendLabel", ""),
    }


def _render_page_rgb(pdf_path: str, page_no: int, scale: float = OCR_SCALE):
    if np is None:
        raise RuntimeError("缺少 numpy，无法运行扫描文字引擎")
    key = (str(pdf_path), int(page_no), float(scale))
    cached = _RENDER_MEM_CACHE.get(key)
    if cached is not None:
        return cached.copy()
    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_no)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n >= 3:
            arr = arr[:, :, :3].copy()
        else:
            arr = np.repeat(arr[:, :, :1], 3, axis=2).copy()
    _RENDER_MEM_CACHE[key] = arr
    return arr.copy()


def _parse_boxes(text: str, image_height: int, scale: float) -> list[dict]:
    out = []
    for line in (text or "").splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        c = parts[0]
        try:
            x0, y0, x1, y1 = map(int, parts[1:5])
        except Exception:
            continue
        top, bottom = image_height - y1, image_height - y0
        if x1 <= x0 or bottom <= top:
            continue
        out.append({
            "c": c,
            "pixelBbox": [x0, top, x1, bottom],
            "bbox": [round(x0 / scale, 3), round(top / scale, 3), round(x1 / scale, 3), round(bottom / scale, 3)],
            "origin": [round(x0 / scale, 3), round(bottom / scale, 3)],
        })
    return out


def _center(b):
    return ((float(b[0]) + float(b[2])) / 2.0, (float(b[1]) + float(b[3])) / 2.0)


def _overlap_area(a, b) -> float:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _assign_chars(word_pixel_bbox, chars: list[dict]) -> list[dict]:
    selected = []
    wx0, wy0, wx1, wy1 = word_pixel_bbox
    for ch in chars:
        b = ch["pixelBbox"]
        cx, cy = _center(b)
        inside = wx0 - 2 <= cx <= wx1 + 2 and wy0 - 2 <= cy <= wy1 + 2
        overlap = _overlap_area(word_pixel_bbox, b)
        area = max(1.0, (b[2] - b[0]) * (b[3] - b[1]))
        if inside or overlap / area >= 0.45:
            selected.append(ch)
    selected.sort(key=lambda z: (z["pixelBbox"][0], z["pixelBbox"][1]))
    return selected

def _quad_rect(box) -> list[float] | None:
    try:
        pts = list(box)
        xs = [float(p[0]) for p in pts]
        ys = [float(p[1]) for p in pts]
        if not xs or not ys:
            return None
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        if x1 <= x0 or y1 <= y0:
            return None
        return [x0, y0, x1, y1]
    except Exception:
        return None


def _rapid_chars_from_word_results(word_results, scale: float) -> list[dict]:
    out: list[dict] = []
    if not word_results:
        return out
    # RapidOCR returns a tuple of (text, score, quadrilateral) entries per line.
    if isinstance(word_results, (list, tuple)) and len(word_results) == 3 and isinstance(word_results[0], str):
        word_results = [word_results]
    for entry in word_results or []:
        try:
            txt, _score, box = entry
        except Exception:
            continue
        txt = str(txt or "")
        rect = _quad_rect(box)
        if not txt or not rect:
            continue
        x0, y0, x1, y1 = rect
        # return_single_char_box=True normally makes each entry one character.
        # If an engine/model still returns a multi-character token, subdivide it
        # only for hit-testing; high-consistency feasibility remains conservative.
        if len(txt) == 1:
            parts = [(txt, x0, x1)]
        else:
            step = (x1 - x0) / max(1, len(txt))
            parts = [(c, x0 + i * step, x0 + (i + 1) * step) for i, c in enumerate(txt)]
        for c, ax0, ax1 in parts:
            pb = [int(round(ax0)), int(round(y0)), int(round(ax1)), int(round(y1))]
            out.append({
                "c": c,
                "geometry": "character" if len(txt) == 1 else "estimated",
                "pixelBbox": pb,
                "bbox": [round(ax0 / scale, 3), round(y0 / scale, 3), round(ax1 / scale, 3), round(y1 / scale, 3)],
                "origin": [round(ax0 / scale, 3), round(y1 / scale, 3)],
            })
    out.sort(key=lambda z: (z["pixelBbox"][0], z["pixelBbox"][1]))
    return out


def _rapid_ocr_page(pdf_path: str, page_no: int, cache_dir: str | Path | None, scale: float, status: dict) -> dict:
    engine = _get_rapid_engine()
    if engine is None:
        return {"ok": False, "available": False, "reason": _RAPID_ENGINE_ERROR or "内置 OCR 不可用", "text": [], "chars": [], "lang": "", "backend": ""}
    arr = _render_page_rgb(pdf_path, page_no, scale)
    h, w = arr.shape[:2]
    # RapidOCR commonly consumes OpenCV BGR arrays.
    img = arr[:, :, ::-1].copy()
    try:
        result = engine(img, return_word_box=True, return_single_char_box=True, text_score=0.35)
    except Exception as ex:
        return {"ok": False, "available": True, "reason": f"内置 OCR 识别失败：{ex}", "text": [], "chars": [], "lang": status.get("lang", ""), "backend": "rapidocr"}

    boxes = getattr(result, "boxes", None)
    txts = getattr(result, "txts", None)
    scores = getattr(result, "scores", None)
    word_results = getattr(result, "word_results", None)
    if boxes is None or txts is None:
        return {"ok": True, "available": True, "reason": "", "text": [], "chars": [], "lang": status.get("lang", ""), "backend": "rapidocr", "scale": scale, "widthPx": w, "heightPx": h}

    items: list[dict] = []
    all_chars: list[dict] = []
    for i, text in enumerate(list(txts)):
        text = str(text or "").strip()
        if not text:
            continue
        rect = _quad_rect(boxes[i]) if i < len(boxes) else None
        if not rect:
            continue
        try:
            score = float(scores[i]) if scores is not None and i < len(scores) else 1.0
        except Exception:
            score = 1.0
        if score < 0.35:
            continue
        wr = word_results[i] if word_results is not None and i < len(word_results) else None
        line_chars = _rapid_chars_from_word_results(wr, scale)
        # Fallback: evenly split the detected line. This still enables selecting
        # scanned text; exact glyph replacement will only succeed when mapping
        # and source glyph checks pass later.
        if not line_chars:
            x0, y0, x1, y1 = rect
            step = (x1 - x0) / max(1, len(text))
            line_chars = []
            for j, c in enumerate(text):
                ax0, ax1 = x0 + j * step, x0 + (j + 1) * step
                line_chars.append({
                    "c": c,
                    "geometry": "estimated",
                    "pixelBbox": [int(round(ax0)), int(round(y0)), int(round(ax1)), int(round(y1))],
                    "bbox": [round(ax0 / scale, 3), round(y0 / scale, 3), round(ax1 / scale, 3), round(y1 / scale, 3)],
                    "origin": [round(ax0 / scale, 3), round(y1 / scale, 3)],
                })
        all_chars.extend(line_chars)
        x0, y0, x1, y1 = rect
        bbox = [round(x0 / scale, 3), round(y0 / scale, 3), round(x1 / scale, 3), round(y1 / scale, 3)]
        items.append({
            "id": f"r-{i}",
            "text": text,
            "bbox": bbox,
            "origin": [bbox[0], bbox[3]],
            "font": "扫描原像素",
            "fontBase": "扫描原像素",
            "fontEmbedded": False,
            "size": round(max(1.0, bbox[3] - bbox[1]), 3),
            "color": "#000000",
            "alpha": 255,
            "flags": 0,
            "rotation": 0,
            "chars": [{"i": j, **{k: v for k, v in ch.items() if k != "pixelBbox"}} for j, ch in enumerate(line_chars)],
            "engine": "scan",
            "ocrConf": round(score * 100.0, 1),
            "ocrBackend": "rapidocr",
        })
    return {
        "ok": True,
        "available": True,
        "reason": "",
        "lang": status.get("lang", "中英混合"),
        "backend": "rapidocr",
        "backendLabel": "内置 RapidOCR",
        "scale": scale,
        "widthPx": w,
        "heightPx": h,
        "text": items,
        "chars": all_chars,
    }


def ocr_chars_page(pdf_path: str, page_no: int, cache_dir: str | Path | None = None, scale: float = OCR_SCALE) -> list[dict]:
    """Character OCR used when searching the document glyph bank."""
    key = (str(pdf_path), int(page_no), float(scale))
    full = _OCR_MEM_CACHE.get(key)
    if full and full.get("ok"):
        return json.loads(json.dumps(full.get("chars", []), ensure_ascii=False))
    if key in _CHAR_MEM_CACHE:
        return json.loads(json.dumps(_CHAR_MEM_CACHE[key], ensure_ascii=False))
    cache_file = None
    if cache_dir:
        cache_file = Path(cache_dir) / f"ocr_chars_{page_no}_{str(scale).replace('.', '_')}.json"
        if cache_file.exists():
            try:
                chars = json.loads(cache_file.read_text("utf-8"))
                _CHAR_MEM_CACHE[key] = chars
                return json.loads(json.dumps(chars, ensure_ascii=False))
            except Exception:
                pass
    status = ocr_status()
    if not status.get("available"):
        return []
    if status.get("backend") == "rapidocr":
        payload = ocr_page(pdf_path, page_no, cache_dir, scale)
        chars = payload.get("chars", []) if payload.get("ok") else []
    else:
        arr = _render_page_rgb(pdf_path, page_no, scale)
        try:
            raw = pytesseract.image_to_boxes(arr, lang=status["lang"], config="--psm 11")
            chars = _parse_boxes(raw, arr.shape[0], scale)
        except Exception:
            chars = []
    _CHAR_MEM_CACHE[key] = chars
    if cache_file:
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(chars, ensure_ascii=False), "utf-8")
        except Exception:
            pass
    return json.loads(json.dumps(chars, ensure_ascii=False))


def ocr_page(pdf_path: str, page_no: int, cache_dir: str | Path | None = None, scale: float = OCR_SCALE) -> dict:
    key = (str(pdf_path), int(page_no), float(scale))
    if key in _OCR_MEM_CACHE:
        return json.loads(json.dumps(_OCR_MEM_CACHE[key], ensure_ascii=False))

    cache_file = None
    if cache_dir:
        cache_file = Path(cache_dir) / f"ocr_page_{page_no}_{str(scale).replace('.', '_')}.json"
        if cache_file.exists():
            try:
                payload = json.loads(cache_file.read_text("utf-8"))
                # Old v1.8 cache entries that only say OCR unavailable must not
                # survive after the built-in OCR backend is installed.
                if payload.get("ok") or payload.get("available"):
                    _OCR_MEM_CACHE[key] = payload
                    return json.loads(json.dumps(payload, ensure_ascii=False))
            except Exception:
                pass

    status = ocr_status()
    if not status.get("available"):
        payload = {"ok": False, "available": False, "reason": status.get("reason", "OCR 不可用"), "text": [], "chars": [], "lang": "", "backend": ""}
        _OCR_MEM_CACHE[key] = payload
        return payload

    if status.get("backend") == "rapidocr":
        payload = _rapid_ocr_page(pdf_path, page_no, cache_dir, scale, status)
    else:
        arr = _render_page_rgb(pdf_path, page_no, scale)
        h, w = arr.shape[:2]
        config = "--psm 11"
        try:
            data = pytesseract.image_to_data(arr, lang=status["lang"], config=config, output_type=Output.DICT)
            boxes_raw = pytesseract.image_to_boxes(arr, lang=status["lang"], config=config)
        except Exception as ex:
            payload = {"ok": False, "available": True, "reason": f"OCR 识别失败：{ex}", "text": [], "chars": [], "lang": status.get("lang", ""), "backend": "tesseract"}
        else:
            chars = _parse_boxes(boxes_raw, h, scale)
            items = []
            n = len(data.get("text", []))
            for i in range(n):
                text = str(data["text"][i] or "").strip()
                if not text:
                    continue
                try:
                    conf = float(data["conf"][i])
                except Exception:
                    conf = -1
                if conf < MIN_WORD_CONF:
                    continue
                left = int(data["left"][i]); top = int(data["top"][i]); width = int(data["width"][i]); height = int(data["height"][i])
                if width < 2 or height < 3:
                    continue
                pb = [left, top, left + width, top + height]
                word_chars = _assign_chars(pb, chars)
                box_text = "".join(x["c"] for x in word_chars)
                if box_text and len(box_text) == len(text) and any(ch.isdigit() for ch in text):
                    text = box_text
                bbox = [round(left / scale, 3), round(top / scale, 3), round((left + width) / scale, 3), round((top + height) / scale, 3)]
                items.append({
                    "id": f"s-{i}", "text": text, "bbox": bbox, "origin": [bbox[0], bbox[3]],
                    "font": "扫描原像素", "fontBase": "扫描原像素", "fontEmbedded": False,
                    "size": round(max(1.0, bbox[3] - bbox[1]), 3), "color": "#000000", "alpha": 255,
                    "flags": 0, "rotation": 0,
                    "chars": [{"i": j, **{k: v for k, v in ch.items() if k != "pixelBbox"}} for j, ch in enumerate(word_chars)],
                    "engine": "scan", "ocrConf": round(conf, 1), "ocrBackend": "tesseract",
                })
            payload = {
                "ok": True, "available": True, "reason": "", "lang": status["lang"],
                "backend": "tesseract", "backendLabel": "Tesseract OCR",
                "scale": scale, "widthPx": w, "heightPx": h, "text": items, "chars": chars,
            }

    _OCR_MEM_CACHE[key] = payload
    if cache_file and payload.get("ok"):
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(payload, ensure_ascii=False), "utf-8")
        except Exception:
            pass
    return json.loads(json.dumps(payload, ensure_ascii=False))



# v2.0 intentionally stops here.
# Scanned/image PDF editing is handled by app.py in explicit revision mode.
# Legacy pixel-glyph fusion functions are not included in the v2.0 package.

# --- v2.1: field-level geometry refinement for structured scan text ----------
def refine_structured_field_bbox(pdf_path: str, page_no: int, text: str, bbox, scale: float = OCR_SCALE) -> list[float] | None:
    """Refine an OCR bbox for short structured fields using the scan pixels.

    This is used for short structured fields, dates and identifiers.
    OCR may return the correct text while the final character box swallows the
    following Chinese phrase.  We inspect only dark connected components in the
    target line and use the first N components for an N-character structured
    field.  The function is intentionally conservative and returns ``None`` when
    it cannot isolate the field reliably.
    """
    text = str(text or "")
    if not text or len(text) > 40:
        return None
    # Limit pixel-based segmentation to characters that normally form one dark
    # connected component each. Other text uses the generic OCR geometry path.
    import re as _re
    if not _re.fullmatch(r"[A-Z0-9][A-Z0-9._/+\-]*", text):
        return None
    if np is None or cv2 is None:
        return None
    try:
        x0, y0, x1, y1 = [float(v) for v in bbox]
    except Exception:
        return None
    if x1 <= x0 or y1 <= y0:
        return None
    try:
        img = _render_page_rgb(pdf_path, int(page_no), float(scale))
    except Exception:
        return None

    h_pt = max(2.0, y1 - y0)
    mx = max(2, int(round(h_pt * scale * 0.15)))
    my = max(2, int(round(h_pt * scale * 0.22)))
    px0 = max(0, int(math.floor(x0 * scale)) - mx)
    py0 = max(0, int(math.floor(y0 * scale)) - my)
    px1 = min(img.shape[1], int(math.ceil(x1 * scale)) + mx)
    py1 = min(img.shape[0], int(math.ceil(y1 * scale)) + my)
    if px1 <= px0 or py1 <= py0:
        return None
    crop = img[py0:py1, px0:px1]
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY) if crop.ndim == 3 else crop
    # Black report text is substantially darker than the light grey watermark.
    mask = (gray < 145).astype(np.uint8) * 255
    # Remove isolated one-pixel noise while preserving thin hyphens.
    kernel = np.ones((1, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    core_y0 = int(round((y0 * scale) - py0))
    core_y1 = int(round((y1 * scale) - py0))
    target_x = (x0 * scale) - px0
    comps = []
    for i in range(1, n):
        cx, cy, cw, ch, area = [int(v) for v in stats[i]]
        if area < 2 or cw < 1 or ch < 1:
            continue
        # Component must intersect the OCR line vertically. Hyphens are short,
        # so do not require a minimum height.
        if cy + ch < core_y0 - 2 or cy > core_y1 + 2:
            continue
        if cx + cw < target_x - max(3, mx):
            continue
        # Ignore huge components (stamps / rules) inside a malformed OCR bbox.
        if cw > max(8, int((x1 - x0) * scale * 0.40)):
            continue
        comps.append([cx, cy, cw, ch, area])
    comps.sort(key=lambda z: (z[0], z[1]))
    if not comps:
        return None

    # Start at the first component whose left edge is near the OCR field start.
    start = None
    tolerance = max(5, int(h_pt * scale * 0.45))
    for idx, c in enumerate(comps):
        if c[0] + c[2] >= target_x - tolerance:
            start = idx
            break
    if start is None:
        return None
    comps = comps[start:]

    # Merge fragments that strongly overlap in X (e.g. anti-aliased pieces of
    # the same glyph). Keep truly separated punctuation as its own component.
    groups = []
    for c in comps:
        x, y, w, h, area = c
        if groups and x <= groups[-1][0] + groups[-1][2] - 1:
            gx, gy, gw, gh, ga = groups[-1]
            nx0, ny0 = min(gx, x), min(gy, y)
            nx1, ny1 = max(gx + gw, x + w), max(gy + gh, y + h)
            groups[-1] = [nx0, ny0, nx1 - nx0, ny1 - ny0, ga + area]
        else:
            groups.append(c[:])

    need = len(text)
    if len(groups) < need:
        return None
    selected = groups[:need]
    # Reject a suspicious jump within the selected field. A following Chinese
    # character often produces a much wider component after the true field.
    widths = sorted(max(1, g[2]) for g in selected)
    med_w = widths[len(widths) // 2]
    if selected[-1][2] > med_w * 2.2:
        return None

    sx0 = min(g[0] for g in selected) + px0
    sy0 = min(g[1] for g in selected) + py0
    sx1 = max(g[0] + g[2] for g in selected) + px0
    sy1 = max(g[1] + g[3] for g in selected) + py0
    # Ensure we did not drift implausibly far from the OCR start.
    if abs((sx0 / scale) - x0) > max(4.0, h_pt * 0.6):
        return None
    pad_x = min(1.0, h_pt * 0.07)
    pad_y = min(1.0, h_pt * 0.07)
    out = [sx0 / scale - pad_x, sy0 / scale - pad_y, sx1 / scale + pad_x, sy1 / scale + pad_y]
    if out[2] <= out[0] or out[3] <= out[1]:
        return None
    return [round(float(v), 3) for v in out]
