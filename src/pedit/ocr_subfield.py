"""Structured subfield detection for scan OCR tokens.

This module deliberately consumes OCR geometry when it exists.  It never derives a
field rectangle by dividing a line width by its character count.
"""
from __future__ import annotations

import re
from typing import Iterable

MODEL = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9]+(?:[-_/.][A-Za-z0-9]+)+(?![A-Za-z0-9])")
DATE = re.compile(r"\d{4}(?:[-/.]|年)\d{1,2}(?:[-/.]|月)\d{1,2}(?:日)?")
IDENTIFIER = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{0,3}\d{6,}(?:-[A-Za-z0-9]+)*(?![A-Za-z0-9])")
PHONE = re.compile(r"(?<!\d)(?:1\d{10}|\d{3,4}[- ]?\d{7,8})(?!\d)")
AMOUNT = re.compile(r"(?:¥|￥)?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?(?:元)?")


def _rank(text: str, start: int, end: int, kind: str) -> tuple:
    # Prefer model/date/identifier fields embedded in Chinese prose, then longer
    # structured values.  Bare numbers are only a final fallback.
    weights = {"model": 60, "date": 55, "identifier": 50, "phone": 48, "amount": 25, "number": 5}
    chinese_context = int(bool(re.search(r"[\u3400-\u9fff]", text[:start] + text[end:])))
    return (weights[kind] + chinese_context * 20, end - start, -start)


def extract_structured_fields(text: str) -> list[dict]:
    """Return non-overlapping candidates with offsets in the original OCR token."""
    text = str(text or "")
    matches = []
    for kind, pattern in (("model", MODEL), ("date", DATE), ("identifier", IDENTIFIER), ("phone", PHONE), ("amount", AMOUNT)):
        for m in pattern.finditer(text):
            value = m.group(0)
            # Slash-separated watermark prose is
            # not a model. A model/identifier candidate must carry a digit.
            if kind in {"model", "identifier"} and not any(ch.isdigit() for ch in value):
                continue
            if kind == "amount" and value.isdigit() and len(value) < 3:
                continue
            matches.append({"text": value, "start": m.start(), "end": m.end(), "kind": kind})
    # Numeric candidates are useful only when no stronger field was found.
    if not matches:
        for m in re.finditer(r"(?<![A-Za-z0-9])\d+(?:\.\d+)?(?![A-Za-z0-9])", text):
            matches.append({"text": m.group(0), "start": m.start(), "end": m.end(), "kind": "number"})
    matches.sort(key=lambda x: _rank(text, x["start"], x["end"], x["kind"]), reverse=True)
    chosen = []
    for item in matches:
        if not any(item["start"] < old["end"] and old["start"] < item["end"] for old in chosen):
            chosen.append(item)
    return chosen


def _valid_box(value) -> list[float] | None:
    try:
        x0, y0, x1, y1 = map(float, value)
        return [x0, y0, x1, y1] if x1 > x0 and y1 > y0 else None
    except Exception:
        return None


def find_subfield_bbox(token: dict, candidate: dict) -> tuple[list[float] | None, list[dict]]:
    """Locate a candidate in geometry order, never by OCR-array index.

    RapidOCR can return a complete line in reading order while its independently
    generated character boxes arrive in an arbitrary order.  Indexing ``chars`` by
    offsets in the line then selects unrelated Chinese glyphs.  Sort valid boxes by
    their physical position and require the exact candidate sequence in that order.
    If that proof is unavailable, return no geometry and force a local/manual OCR
    path rather than making a destructive guess.
    """
    positioned = []
    for char in list(token.get("chars") or []):
        box = _valid_box(char.get("bbox"))
        value = str(char.get("c", ""))
        if box and value:
            positioned.append({**char, "c": value, "bbox": box})
    # OCR text tokens are individual lines. Vertical jitter between glyph boxes is
    # common, so x is the authoritative reading order for a single token.
    positioned.sort(key=lambda c: (c["bbox"][0], c["bbox"][1]))
    needle = str(candidate.get("text", ""))
    sequence = "".join(c["c"] for c in positioned)
    # Match occurrence offsets in the complete line (spaces may be absent in OCR
    # character geometry). Never silently select the first repeated value.
    compact = lambda value: "".join(c for c in value if not c.isspace())
    full = str(token.get("text", ""))
    positioned = [c for c in positioned if not c["c"].isspace()]
    sequence = "".join(c["c"] for c in positioned)
    needle = compact(needle)
    start = len(compact(full[:candidate.get("start", 0)]))
    if compact(full) != sequence:
        return None, []
    if start < 0:
        return None, []
    selected = positioned[start:start + len(needle)]
    if len(selected) != len(needle) or "".join(c["c"] for c in selected) != needle:
        return None, []
    if any(c.get("geometry") == "estimated" for c in selected):
        return None, []
    return [min(c["bbox"][0] for c in selected), min(c["bbox"][1] for c in selected), max(c["bbox"][2] for c in selected), max(c["bbox"][3] for c in selected)], selected


def selectable_fields(token: dict) -> list[dict]:
    """Partition the line into structured fields and editable prose spans."""
    text = str(token.get("text", ""))
    structured = sorted(extract_structured_fields(text), key=lambda s: s["start"])
    spans = []
    cursor = 0
    for field in structured + [{"start": len(text), "end": len(text)}]:
        for m in re.finditer(r"\S(?:.*?\S)?(?=\s*$)", text[cursor:field["start"]]):
            spans.append({"text": m.group(), "start": cursor+m.start(), "end": cursor+m.end(), "kind": "prose"})
        if field["end"] > field["start"]:
            spans.append(field)
        cursor = field["end"]
    for span in spans:
        bbox, chars = find_subfield_bbox(token, span)
        span.update(bbox=bbox, chars=chars, geometry="character" if bbox else "needs-local-ocr")
    return spans


def select_subfield(token: dict) -> dict | None:
    """Find the best editable structured field in a complete OCR token."""
    for candidate in extract_structured_fields(token.get("text", "")):
        bbox, chars = find_subfield_bbox(token, candidate)
        return {**candidate, "bbox": bbox, "chars": chars, "geometry": "character" if bbox else "needs-local-ocr"}
    return None


def manual_region_from_page(page_items: Iterable[dict], rect) -> dict | None:
    """Resolve a manual rectangle from OCR boxes, requiring contained text only."""
    box = _valid_box(rect)
    if not box:
        return None
    x0, y0, x1, y1 = box
    contained=[]
    for item in page_items:
        for char in item.get('chars') or []:
            b=_valid_box(char.get('bbox'))
            if b and b[0]>=x0 and b[1]>=y0 and b[2]<=x1 and b[3]<=y1:
                contained.append(char)
    if contained:
        contained.sort(key=lambda c:(c['bbox'][0],c['bbox'][1]))
        return {'text':''.join(c['c'] for c in contained),'bbox':box,'chars':contained,'source':'manual'}
    candidates = []
    for item in page_items:
        b = _valid_box(item.get("bbox"))
        if not b:
            continue
        ix0, iy0, ix1, iy1 = b
        overlap = max(0, min(x1, ix1) - max(x0, ix0)) * max(0, min(y1, iy1) - max(y0, iy0))
        if overlap / max(1, (ix1 - ix0) * (iy1 - iy0)) >= .55:
            candidates.append(item)
    if not candidates:
        return None
    candidates.sort(key=lambda v: (v["bbox"][1], v["bbox"][0]))
    item = candidates[0]
    # The manual rectangle is the authoritative boundary; use OCR text only when
    # it is contained.  A backend local-OCR endpoint may refine it further.
    return {"text": str(item.get("text", "")).strip(), "bbox": box, "chars": list(item.get("chars") or []), "source": "manual"}
