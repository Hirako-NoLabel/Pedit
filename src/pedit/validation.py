"""Small, scan-only validation gates used before a raster revision is written."""
from __future__ import annotations

def validate_field_boundary(field_bbox, token_bbox, *, manual: bool = False) -> tuple[bool, str]:
    try:
        fx0, fy0, fx1, fy1 = map(float, field_bbox)
        tx0, ty0, tx1, ty1 = map(float, token_bbox)
    except Exception:
        return False, "OCR 文字坐标无效"
    if fx1 <= fx0 or fy1 <= fy0:
        return False, "OCR 文字区域尺寸无效"
    if manual:
        return True, "手动框选字段边界已锁定"
    # An automatically selected subfield must be materially narrower than its
    # surrounding OCR token. Equality indicates it would redraw the whole phrase.
    if (fx1 - fx0) >= (tx1 - tx0) * .94 and (tx1 - tx0) > 0:
        return False, "当前字段范围包含相邻文字，请缩小框选区域。"
    return True, "字段边界已锁定"


def page_changed(before, after, minimum_changed_pixels: int = 1) -> bool:
    """Works with PIL images or difference images without hiding no-op output."""
    diff = before if after is None else __import__("PIL.ImageChops", fromlist=["difference"]).difference(before, after)
    bbox = diff.getbbox()
    if not bbox:
        return False
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) >= minimum_changed_pixels
