from __future__ import annotations

"""High-fidelity PDF text replacement.

This module deliberately targets *visual fidelity*, not concealment of editing history.
It performs conservative in-place content-stream substitutions when all of the
following are true:

* the text style / position is unchanged;
* old and new text have the same Unicode length;
* the selected text can be located unambiguously in a page text operator;
* every replacement character already has an encoding in the active PDF font.

In that case the existing PDF font resource, text matrix, font size, spacing,
kerning and rendering state are left in place. Only the encoded character code
inside Tj/TJ is changed.
"""

from dataclasses import dataclass
import re
from typing import Iterable

import pymupdf as fitz


_NAME_CLEAN = re.compile(r"[^a-z0-9]")


def clean_font_name(name: str) -> str:
    return _NAME_CLEAN.sub("", (name or "").split("+")[-1].lower())


def font_match_score(a: str, b: str) -> int:
    a, b = clean_font_name(a), clean_font_name(b)
    if not a or not b:
        return 0
    if a == b:
        return 100
    if a in b or b in a:
        return 75
    return 0


def _decode_utf16_hex(hex_text: str) -> str:
    raw = bytes.fromhex(hex_text)
    try:
        return raw.decode("utf-16-be")
    except Exception:
        if len(raw) == 1:
            return chr(raw[0])
        return ""


def _parse_tounicode(stream: bytes) -> tuple[dict[bytes, str], set[int]]:
    """Parse the common bfchar/bfrange forms used by ToUnicode CMaps."""
    text = stream.decode("latin1", "ignore")
    mapping: dict[bytes, str] = {}
    code_lengths: set[int] = set()

    for m in re.finditer(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*$", text, re.M):
        # This broad form appears inside bfrange blocks; filter by range size.
        start_h, end_h, dst_h = m.groups()
        if len(start_h) != len(end_h):
            continue
        start, end = int(start_h, 16), int(end_h, 16)
        if end < start or end - start > 65535:
            continue
        src_len = len(start_h) // 2
        dst_raw = bytes.fromhex(dst_h)
        if len(dst_raw) not in (1, 2, 4):
            continue
        # Only use it when it is located in a beginbfrange...endbfrange region.
        pos = m.start()
        b0 = text.rfind("beginbfrange", 0, pos)
        e0 = text.rfind("endbfrange", 0, pos)
        if b0 < 0 or b0 < e0:
            continue
        try:
            base = ord(_decode_utf16_hex(dst_h))
        except Exception:
            continue
        for off, code in enumerate(range(start, end + 1)):
            mapping[code.to_bytes(src_len, "big")] = chr(base + off)
            code_lengths.add(src_len)

    # bfrange with explicit destination arrays.
    for block in re.finditer(r"beginbfrange(.*?)endbfrange", text, re.S):
        body = block.group(1)
        for m in re.finditer(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", body, re.S):
            start_h, end_h, arr = m.groups()
            start, end = int(start_h, 16), int(end_h, 16)
            src_len = len(start_h) // 2
            vals = re.findall(r"<([0-9A-Fa-f]+)>", arr)
            for off, code in enumerate(range(start, end + 1)):
                if off >= len(vals):
                    break
                u = _decode_utf16_hex(vals[off])
                if u:
                    mapping[code.to_bytes(src_len, "big")] = u
                    code_lengths.add(src_len)

    for block in re.finditer(r"beginbfchar(.*?)endbfchar", text, re.S):
        body = block.group(1)
        for m in re.finditer(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", body):
            src_h, dst_h = m.groups()
            try:
                src = bytes.fromhex(src_h)
                u = _decode_utf16_hex(dst_h)
            except Exception:
                continue
            if src and u:
                mapping[src] = u
                code_lengths.add(len(src))

    # codespacerange is more authoritative about code width.
    cs_lengths: set[int] = set()
    for block in re.finditer(r"begincodespacerange(.*?)endcodespacerange", text, re.S):
        for m in re.finditer(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block.group(1)):
            if len(m.group(1)) == len(m.group(2)):
                cs_lengths.add(len(m.group(1)) // 2)
    if cs_lengths:
        code_lengths = cs_lengths
    return mapping, code_lengths


@dataclass
class FontCodec:
    resource: str
    basefont: str
    xref: int
    mode: str
    code_len: int
    code_to_unicode: dict[bytes, str]
    unicode_to_code: dict[str, bytes]

    def split(self, raw: bytes) -> list[bytes] | None:
        if self.code_len <= 0 or len(raw) % self.code_len:
            return None
        return [raw[i:i + self.code_len] for i in range(0, len(raw), self.code_len)]

    def decode_units(self, raw: bytes) -> list[tuple[str, bytes]] | None:
        codes = self.split(raw)
        if codes is None:
            return None
        out: list[tuple[str, bytes]] = []
        for code in codes:
            if self.mode == "utf16":
                try:
                    ch = code.decode("utf-16-be")
                except Exception:
                    return None
            elif self.mode == "single":
                try:
                    ch = code.decode("cp1252")
                except Exception:
                    ch = code.decode("latin1", "replace")
            else:
                ch = self.code_to_unicode.get(code)
                if ch is None:
                    return None
            # Exact mode deliberately requires one glyph code -> one Unicode char.
            if len(ch) != 1:
                return None
            out.append((ch, code))
        return out

    def encode_char(self, ch: str) -> bytes | None:
        if len(ch) != 1:
            return None
        if self.mode == "utf16":
            try:
                raw = ch.encode("utf-16-be")
                return raw if len(raw) == self.code_len else None
            except Exception:
                return None
        if self.mode == "single":
            try:
                raw = ch.encode("cp1252")
                return raw if len(raw) == self.code_len else None
            except Exception:
                return None
        return self.unicode_to_code.get(ch)


def page_font_codecs(doc: fitz.Document, page: fitz.Page) -> dict[str, FontCodec]:
    codecs: dict[str, FontCodec] = {}
    for f in page.get_fonts(full=True):
        xref, _ext, _ftype, basefont, resource = f[:5]
        resource = str(resource)
        basefont = str(basefont)
        xref = int(xref)
        if not resource:
            continue
        obj = doc.xref_object(xref, compressed=False) if xref > 0 else ""
        enc_m = re.search(r"/Encoding\s*/([^\s<>\[\]()]+)", obj)
        encoding = enc_m.group(1) if enc_m else ""
        tu_m = re.search(r"/ToUnicode\s+(\d+)\s+0\s+R", obj)
        if tu_m:
            try:
                cmap = doc.xref_stream(int(tu_m.group(1))) or b""
                c2u, lengths = _parse_tounicode(cmap)
            except Exception:
                c2u, lengths = {}, set()
            if c2u and len(lengths) == 1:
                clen = next(iter(lengths))
                inv: dict[str, bytes] = {}
                for code, uni in c2u.items():
                    if len(uni) == 1 and uni not in inv:
                        inv[uni] = code
                codecs[resource] = FontCodec(resource, basefont, xref, "cmap", clen, c2u, inv)
                continue
        if encoding in {"UniGB-UTF16-H", "UniGB-UTF16-V", "UniCNS-UTF16-H", "UniJIS-UTF16-H", "UniKS-UTF16-H"}:
            codecs[resource] = FontCodec(resource, basefont, xref, "utf16", 2, {}, {})
        elif encoding in {"WinAnsiEncoding", "MacRomanEncoding", "StandardEncoding", ""} and "Type0" not in obj:
            codecs[resource] = FontCodec(resource, basefont, xref, "single", 1, {}, {})
    return codecs


def _decode_literal(token: bytes) -> bytes:
    # token includes surrounding parentheses
    src = token[1:-1]
    out = bytearray()
    i = 0
    esc = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12}
    while i < len(src):
        b = src[i]
        if b != 0x5C:  # backslash
            out.append(b); i += 1; continue
        i += 1
        if i >= len(src):
            break
        b = src[i]
        if b in esc:
            out.append(esc[b]); i += 1; continue
        if b in (0x28, 0x29, 0x5C):
            out.append(b); i += 1; continue
        if b in (10, 13):
            if b == 13 and i + 1 < len(src) and src[i + 1] == 10:
                i += 1
            i += 1
            continue
        if 48 <= b <= 55:
            digs = bytearray([b]); i += 1
            while i < len(src) and len(digs) < 3 and 48 <= src[i] <= 55:
                digs.append(src[i]); i += 1
            out.append(int(digs.decode("ascii"), 8) & 0xFF)
            continue
        out.append(b); i += 1
    return bytes(out)


def _token_data(token: bytes) -> bytes | None:
    token = token.strip()
    if token.startswith(b"<") and token.endswith(b">") and not token.startswith(b"<<"):
        h = re.sub(rb"\s+", b"", token[1:-1])
        if len(h) % 2:
            h += b"0"
        try:
            return bytes.fromhex(h.decode("ascii"))
        except Exception:
            return None
    if token.startswith(b"(") and token.endswith(b")"):
        return _decode_literal(token)
    return None


def _hex_token(data: bytes) -> bytes:
    return b"<" + data.hex().upper().encode("ascii") + b">"


_EVENT_RE = re.compile(
    rb"/(?P<font>[^\s<>\[\]()/%]+)\s+(?P<size>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s+Tf"
    rb"|(?P<tj>(?:<[^>]*>|\((?:\\.|[^\\)])*\))\s*Tj)"
    rb"|(?P<TJ>\[(?:\\.|[^\]])*\]\s*TJ)",
    re.S,
)
_STRING_RE = re.compile(rb"<[^>]*>|\((?:\\.|[^\\)])*\)", re.S)


@dataclass
class TokenRef:
    start: int
    end: int
    codes: list[bytes]
    chars: list[str]


@dataclass
class TextOp:
    resource: str
    basefont: str
    tokens: list[TokenRef]
    text: str


def scan_text_ops(content: bytes, codecs: dict[str, FontCodec], initial_font: str | None = None) -> tuple[list[TextOp], str | None]:
    current = initial_font
    out: list[TextOp] = []
    for m in _EVENT_RE.finditer(content):
        if m.group("font") is not None:
            try:
                current = m.group("font").decode("latin1")
            except Exception:
                current = None
            continue
        if not current or current not in codecs:
            continue
        codec = codecs[current]
        grp = m.group("tj") if m.group("tj") is not None else m.group("TJ")
        if grp is None:
            continue
        group_abs_start = m.start("tj") if m.group("tj") is not None else m.start("TJ")
        toks: list[TokenRef] = []
        for sm in _STRING_RE.finditer(grp):
            token = sm.group(0)
            data = _token_data(token)
            if data is None:
                continue
            units = codec.decode_units(data)
            if units is None:
                continue
            toks.append(TokenRef(
                start=group_abs_start + sm.start(),
                end=group_abs_start + sm.end(),
                codes=[code for _, code in units],
                chars=[ch for ch, _ in units],
            ))
        if toks:
            text = "".join("".join(t.chars) for t in toks)
            out.append(TextOp(current, codec.basefont, toks, text))
    return out, current


def _candidate_for_edit(doc: fitz.Document, page: fitz.Page, edit: dict):
    old = str(edit.get("oldText", ""))
    new = str(edit.get("newText", ""))
    if not edit.get("sameStyle", False):
        return None, {"mode": "redraw", "level": "medium", "reason": "字号、颜色或位置发生变化，需要整段重绘"}
    if old == new:
        return None, {"mode": "none", "level": "exact", "reason": "内容未变化"}
    if len(old) != len(new):
        return None, {"mode": "redraw", "level": "medium", "reason": "字符数量发生变化，无法保持原文字指令结构"}

    codecs = page_font_codecs(doc, page)
    if not codecs:
        return None, {"mode": "redraw", "level": "medium", "reason": "未找到可直接编码的页面字体资源"}

    wanted_font = str(edit.get("font", ""))
    candidates = []
    active_font = None
    for content_xref in page.get_contents() or []:
        try:
            content = doc.xref_stream(int(content_xref)) or b""
        except Exception:
            continue
        ops, active_font = scan_text_ops(content, codecs, active_font)
        for op in ops:
            starts = [m.start() for m in re.finditer(re.escape(old), op.text)]
            if not starts:
                continue
            if wanted_font and font_match_score(wanted_font, op.basefont) == 0:
                continue
            codec = codecs[op.resource]
            for start in starts:
                replacement_codes = [codec.encode_char(ch) for ch in new]
                if any(c is None for c in replacement_codes):
                    continue
                # Build flat unit map: (token index, unit index, char)
                flat = []
                for ti, tok in enumerate(op.tokens):
                    for ui, ch in enumerate(tok.chars):
                        flat.append((ti, ui, ch))
                if start + len(old) > len(flat):
                    continue
                if "".join(x[2] for x in flat[start:start + len(old)]) != old:
                    continue
                candidates.append({
                    "xref": int(content_xref), "content": content, "op": op,
                    "codec": codec, "start": start, "flat": flat,
                    "replacement_codes": replacement_codes,
                })
    if len(candidates) == 1:
        c = candidates[0]
        return c, {
            "mode": "stream", "level": "exact",
            "resource": c["op"].resource,
            "font": c["op"].basefont,
            "reason": "直接修改原 PDF 文字指令；字体资源、字号、字距、位置和渲染状态全部保留",
        }
    if len(candidates) > 1:
        return None, {"mode": "redraw", "level": "medium", "reason": "页面中存在多个相同文本，无法安全确定底层文字指令"}

    # More specific diagnostic: see whether the old text is visible in a matching font op,
    # but one or more new characters are missing from the font's existing encoding.
    missing = set()
    for content_xref in page.get_contents() or []:
        try:
            content = doc.xref_stream(int(content_xref)) or b""
        except Exception:
            continue
        ops, _ = scan_text_ops(content, codecs)
        for op in ops:
            if old in op.text and (not wanted_font or font_match_score(wanted_font, op.basefont)):
                codec = codecs[op.resource]
                for ch in new:
                    if codec.encode_char(ch) is None:
                        missing.add(ch)
    if missing:
        chars = "、".join(sorted(missing))
        return None, {"mode": "redraw", "level": "medium", "reason": f"原字体当前编码中没有目标字符：{chars}"}
    return None, {"mode": "redraw", "level": "medium", "reason": "未能把所选文字唯一映射到 Tj/TJ 原始文字指令"}


def analyze_edit(doc: fitz.Document, edit: dict) -> dict:
    pno = int(edit.get("page", -1))
    if pno < 0 or pno >= doc.page_count:
        return {"mode": "redraw", "level": "medium", "reason": "页码无效"}
    page = doc.load_page(pno)
    _, info = _candidate_for_edit(doc, page, edit)
    return info


def apply_stream_edit(doc: fitz.Document, edit: dict) -> tuple[bool, dict]:
    """Try an exact content-stream edit. Returns (applied, analysis)."""
    pno = int(edit.get("page", -1))
    if pno < 0 or pno >= doc.page_count:
        return False, {"mode": "redraw", "level": "medium", "reason": "页码无效"}
    page = doc.load_page(pno)
    cand, info = _candidate_for_edit(doc, page, edit)
    if not cand:
        return False, info

    op: TextOp = cand["op"]
    flat = cand["flat"]
    start = cand["start"]
    replacement_codes: list[bytes] = cand["replacement_codes"]
    token_codes = [list(t.codes) for t in op.tokens]
    for off, new_code in enumerate(replacement_codes):
        ti, ui, _ = flat[start + off]
        old_code = token_codes[ti][ui]
        # Keeping code width is important for conservative stream surgery.
        if len(new_code) != len(old_code):
            return False, {"mode": "redraw", "level": "medium", "reason": "目标字符编码宽度不同，改用整段重绘"}
        token_codes[ti][ui] = new_code

    content = cand["content"]
    patches = []
    for ti, tok in enumerate(op.tokens):
        if token_codes[ti] != tok.codes:
            patches.append((tok.start, tok.end, _hex_token(b"".join(token_codes[ti]))))
    if not patches:
        return False, {"mode": "none", "level": "exact", "reason": "没有需要修改的文字代码"}
    for a, b, repl in sorted(patches, reverse=True):
        content = content[:a] + repl + content[b:]
    doc.update_stream(cand["xref"], content)
    return True, info

# ---------------- verified visual-fidelity layer ----------------

from io import BytesIO
from PIL import Image, ImageChops


def _hex_rgb(value: str):
    v = (value or "#000000").strip().lstrip("#")
    if len(v) == 3:
        v = "".join(ch * 2 for ch in v)
    try:
        return tuple(int(v[i:i+2], 16) / 255 for i in (0, 2, 4))
    except Exception:
        return (0.0, 0.0, 0.0)


def _matching_embedded_font(doc: fitz.Document, page: fitz.Page, span_font: str, needed: str):
    """Return the exact embedded font program only when it contains every target glyph.

    The verified path intentionally does not use a local or substitute font in the high-fidelity path.
    """
    wanted = clean_font_name(span_font)
    candidates = []
    for f in page.get_fonts(full=True):
        xref, _ext, _ftype, basefont, resource = f[:5]
        score = font_match_score(span_font, str(basefont))
        if wanted and not score:
            score = font_match_score(span_font, str(resource))
        if score:
            candidates.append((score, int(xref), str(basefont), str(resource)))
    candidates.sort(reverse=True)
    for _score, xref, basefont, resource in candidates:
        if xref <= 0:
            continue
        try:
            info = doc.extract_font(xref)
            buf = info[3]
            if not buf:
                continue
            font = fitz.Font(fontbuffer=buf)
            if all(ch.isspace() or font.has_glyph(ord(ch)) for ch in needed):
                return {"buffer": buf, "basefont": basefont, "resource": resource, "xref": xref}
        except Exception:
            continue
    return None


def _changed_indices(edit: dict) -> list[int]:
    old = str(edit.get("oldText", ""))
    new = str(edit.get("newText", ""))
    if len(old) != len(new):
        return []
    return [i for i, (a, b) in enumerate(zip(old, new)) if a != b]


def _char_redact_rect(ch: dict) -> fitz.Rect:
    r = fitz.Rect(*[float(v) for v in ch.get("bbox", (0, 0, 0, 0))])
    # Preserve neighbouring glyphs while still removing anti-aliased edges of the target.
    # A tiny vertical / horizontal expansion is safer than the old whole-span redaction.
    dx = min(0.18, max(0.03, r.width * 0.025))
    dy = min(0.12, max(0.02, r.height * 0.015))
    r.x0 -= dx; r.x1 += dx; r.y0 -= dy; r.y1 += dy
    return r


def apply_embedded_glyph_edit(doc: fitz.Document, edit: dict) -> tuple[bool, dict]:
    """Second high-fidelity path: replace only changed glyphs using the PDF's own embedded font.

    This is used only when stream surgery is unavailable. No system/local fallback font is allowed.
    A separate pixel verifier must approve the result before the UI calls it high consistency.
    """
    pno = int(edit.get("page", -1))
    if pno < 0 or pno >= doc.page_count:
        return False, {"mode": "blocked", "reason": "页码无效"}
    if not edit.get("sameStyle", False):
        return False, {"mode": "blocked", "reason": "字号、颜色或位置发生变化"}
    if int(edit.get("rotation", 0) or 0) % 360 != 0:
        return False, {"mode": "blocked", "reason": "字形复用暂不支持旋转文字"}
    old = str(edit.get("oldText", ""))
    new = str(edit.get("newText", ""))
    chars = edit.get("chars") or []
    idxs = _changed_indices(edit)
    if not idxs or len(chars) < len(old):
        return False, {"mode": "blocked", "reason": "无法取得变化字符的原始坐标"}

    page = doc.load_page(pno)
    embedded = _matching_embedded_font(doc, page, str(edit.get("font", "")), "".join(new[i] for i in idxs))
    if not embedded:
        return False, {"mode": "blocked", "reason": "原 PDF 的嵌入字体程序中没有所需目标字形"}

    # Remove only the old changed glyph(s).
    for i in idxs:
        page.add_redact_annot(_char_redact_rect(chars[i]), fill=None, cross_out=False)
    page.apply_redactions(images=0, graphics=0, text=0)
    page = doc.load_page(pno)

    res = f"HF14_{pno}_{abs(hash((edit.get('id',''), new))) % 100000}"
    try:
        page.insert_font(fontname=res, fontbuffer=embedded["buffer"])
    except Exception as ex:
        return False, {"mode": "blocked", "reason": f"无法复用原嵌入字体：{ex}"}

    size = max(1.0, float(edit.get("size", 11)))
    color = _hex_rgb(str(edit.get("color", "#000000")))
    opacity = min(1.0, max(0.0, float(edit.get("alpha", 255) or 255) / 255.0))

    for i in idxs:
        ci = chars[i]
        origin = ci.get("origin") or edit.get("origin") or [0, 0]
        try:
            page.insert_text(
                (float(origin[0]), float(origin[1])),
                new[i],
                fontsize=size,
                fontname=res,
                color=color,
                overlay=True,
                fill_opacity=opacity,
                stroke_opacity=opacity,
            )
        except Exception as ex:
            return False, {"mode": "blocked", "reason": f"原字形复用失败：{ex}"}

    return True, {
        "mode": "glyph",
        "level": "high",
        "font": embedded["basefont"],
        "resource": embedded["resource"],
        "reason": "原始文字指令无法直改，已仅替换变化字符并复用 PDF 自带嵌入字体",
    }



# ---------------- v1.5 document glyph bank ----------------

def _line_rotation(direction) -> int:
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
    return -1


def _find_document_glyph_sources(doc: fitz.Document, edit: dict) -> tuple[dict[int, dict], str | None]:
    """Find already-rendered target characters elsewhere in the same PDF.

    This is the v1.5 escape hatch for subset fonts and Form XObjects: instead of asking
    MuPDF to re-encode a missing character, we reuse a character the document already
    renders with the same font and size.  show_pdf_page() later preserves it as vector PDF
    content, so there is no substitute-font redraw.
    """
    idxs = _changed_indices(edit)
    if not idxs:
        return {}, "没有可克隆的变化字符"
    if int(edit.get("rotation", 0) or 0) % 360 != 0:
        return {}, "文档字形克隆暂只支持水平文字"

    wanted_font = str(edit.get("font", ""))
    wanted_size = max(0.01, float(edit.get("size", 0) or 0))
    chars = edit.get("chars") or []
    new = str(edit.get("newText", ""))
    if len(chars) < max(idxs) + 1:
        return {}, "无法取得目标字符原始坐标"

    needed = {i: new[i] for i in idxs}
    best: dict[int, tuple[float, dict]] = {}

    for pno in range(doc.page_count):
        page = doc.load_page(pno)
        raw = page.get_text("rawdict")
        for block in raw.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                rot = _line_rotation(line.get("dir", (1, 0)))
                if rot != 0:
                    continue
                for span in line.get("spans", []):
                    span_font = str(span.get("font", ""))
                    fscore = font_match_score(wanted_font, span_font)
                    if wanted_font and fscore < 75:
                        continue
                    ssize = float(span.get("size", 0) or 0)
                    if wanted_size and ssize:
                        rel = abs(ssize - wanted_size) / wanted_size
                        # Exact / near-exact sizes only.  Scaling a donor from a very different
                        # size can change hinting and defeats the point of this mode.
                        if rel > 0.035:
                            continue
                    else:
                        rel = 0.0

                    for ch in span.get("chars", []) or []:
                        c = str(ch.get("c", ""))
                        for idx, wanted_ch in needed.items():
                            if c != wanted_ch:
                                continue
                            sb = fitz.Rect(*[float(v) for v in ch.get("bbox", (0, 0, 0, 0))])
                            tb = fitz.Rect(*[float(v) for v in chars[idx].get("bbox", (0, 0, 0, 0))])
                            if sb.width <= 0 or sb.height <= 0 or tb.width <= 0 or tb.height <= 0:
                                continue
                            # Prefer identical character-cell metrics.  Digits in dates / amounts
                            # usually score almost perfectly here.
                            wd = abs(sb.width - tb.width) / max(tb.width, 0.01)
                            hd = abs(sb.height - tb.height) / max(tb.height, 0.01)
                            if wd > 0.10 or hd > 0.06:
                                continue
                            score = fscore * 10.0 - rel * 800.0 - wd * 120.0 - hd * 120.0
                            cand = {
                                "page": pno,
                                "bbox": [float(sb.x0), float(sb.y0), float(sb.x1), float(sb.y1)],
                                "font": span_font,
                                "size": ssize,
                                "char": c,
                            }
                            if idx not in best or score > best[idx][0]:
                                best[idx] = (score, cand)

    missing = [needed[i] for i in idxs if i not in best]
    if missing:
        uniq = "、".join(dict.fromkeys(missing))
        return {}, f"整份 PDF 中未找到同字体、同字号的目标字形：{uniq}"
    return {i: best[i][1] for i in idxs}, None


def apply_document_glyph_clone(doc: fitz.Document, edit: dict, pdf_bytes: bytes) -> tuple[bool, dict]:
    """Replace changed characters by clipping the document's own glyphs as vector Form XObjects.

    This avoids font re-encoding entirely.  It is especially useful for PDF subset fonts and
    text inside Form XObjects, both of which can make Tj/TJ surgery unavailable even though the
    document already contains the desired character elsewhere.
    """
    pno = int(edit.get("page", -1))
    if pno < 0 or pno >= doc.page_count:
        return False, {"mode": "blocked", "reason": "页码无效"}
    if not edit.get("sameStyle", False):
        return False, {"mode": "blocked", "reason": "字号、颜色或位置发生变化"}

    idxs = _changed_indices(edit)
    chars = edit.get("chars") or []
    if not idxs or len(chars) < max(idxs) + 1:
        return False, {"mode": "blocked", "reason": "无法取得变化字符坐标"}

    with fitz.open(stream=pdf_bytes, filetype="pdf") as source_doc:
        sources, reason = _find_document_glyph_sources(source_doc, edit)
        if reason:
            return False, {"mode": "blocked", "reason": reason}

        page = doc.load_page(pno)
        for i in idxs:
            page.add_redact_annot(_char_redact_rect(chars[i]), fill=None, cross_out=False)
        page.apply_redactions(images=0, graphics=0, text=0)
        page = doc.load_page(pno)

        used_pages = set()
        for i in idxs:
            src = sources[i]
            target = fitz.Rect(*[float(v) for v in chars[i].get("bbox", (0, 0, 0, 0))])
            clip = fitz.Rect(*[float(v) for v in src["bbox"]])
            try:
                page.show_pdf_page(target, source_doc, int(src["page"]), clip=clip, keep_proportion=False, overlay=True)
                used_pages.add(int(src["page"]) + 1)
            except Exception as ex:
                return False, {"mode": "blocked", "reason": f"文档原字形克隆失败：{ex}"}

    return True, {
        "mode": "docglyph",
        "level": "exact",
        "font": str(edit.get("font", "")),
        "sourcePages": sorted(used_pages),
        "reason": "从同一 PDF 中复用同字体同字号的原始字形，未重新生成字体",
    }

def _render_pil(doc: fitz.Document, pno: int, scale: float = 3.0) -> Image.Image:
    page = doc.load_page(pno)
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    return Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")


def _expected_pixel_rect(edit: dict, scale: float, image_size: tuple[int, int]):
    idxs = _changed_indices(edit)
    chars = edit.get("chars") or []
    if not idxs or len(chars) < max(idxs) + 1:
        return None
    rect = None
    for i in idxs:
        r = fitz.Rect(*[float(v) for v in chars[i].get("bbox", (0, 0, 0, 0))])
        # Allow the replacement glyph to be somewhat wider / taller than the old outline.
        margin_pt = max(1.25, r.height * 0.10, r.width * 0.12)
        r.x0 -= margin_pt; r.x1 += margin_pt; r.y0 -= margin_pt; r.y1 += margin_pt
        rect = r if rect is None else (rect | r)
    w, h = image_size
    x0 = max(0, int(rect.x0 * scale)); y0 = max(0, int(rect.y0 * scale))
    x1 = min(w, int(rect.x1 * scale + 1)); y1 = min(h, int(rect.y1 * scale + 1))
    return (x0, y0, x1, y1)


def verify_visual_change(original_doc: fitz.Document, modified_doc: fitz.Document, edit: dict, scale: float = 3.0) -> dict:
    """Reject a candidate if pixels changed outside the intended changed-glyph area.

    This catches the v1.3 bug where the engine silently re-rendered an entire date/line.
    """
    pno = int(edit.get("page", -1))
    if pno < 0:
        return {"ok": False, "reason": "页码无效"}
    before = _render_pil(original_doc, pno, scale)
    after = _render_pil(modified_doc, pno, scale)
    if before.size != after.size:
        return {"ok": False, "reason": "修改导致页面渲染尺寸变化"}
    diff = ImageChops.difference(before, after)
    diff_bbox = diff.getbbox()
    if diff_bbox is None:
        return {"ok": False, "reason": "修改后没有检测到任何像素变化"}
    expected = _expected_pixel_rect(edit, scale, before.size)
    if expected is None:
        return {"ok": False, "reason": "无法建立目标字符的视觉校验区域"}

    # Mask out the expected target area. Any remaining changed pixel means an untouched
    # character/background was altered and the candidate is rejected.
    outside = diff.copy()
    outside.paste((0, 0, 0), expected)
    outside_bbox = outside.getbbox()
    if outside_bbox is not None:
        return {
            "ok": False,
            "reason": "视觉校验失败：目标字符以外也发生了像素变化",
            "diffBBox": list(diff_bbox),
            "outsideBBox": list(outside_bbox),
            "expectedBBox": list(expected),
            "scale": scale,
        }
    return {
        "ok": True,
        "reason": "视觉校验通过：变化仅位于目标字符区域",
        "diffBBox": list(diff_bbox),
        "expectedBBox": list(expected),
        "scale": scale,
    }


def analyze_verified_edit(pdf_bytes: bytes, edit: dict) -> dict:
    """v1.5 feasibility analysis with mandatory pixel verification.

    Order:
      1) original Tj/TJ stream surgery;
      2) same-document glyph clone (vector Form XObject);
      3) exact embedded-font glyph reuse;
      4) block.  There is no substitute-font / whole-line fallback in this path.
    """
    old = str(edit.get("oldText", ""))
    new = str(edit.get("newText", ""))
    if old == new and edit.get("sameStyle", False):
        return {"mode": "none", "level": "exact", "visualVerified": True, "reason": "内容未变化"}

    with fitz.open(stream=pdf_bytes, filetype="pdf") as original:
        # Level 1: exact original content-stream edit.
        with fitz.open(stream=pdf_bytes, filetype="pdf") as candidate:
            applied, info = apply_stream_edit(candidate, edit)
            if applied:
                check = verify_visual_change(original, candidate, edit)
                if check.get("ok"):
                    return {**info, "mode": "stream", "visualVerified": True, "validation": check,
                            "grade": "原生级", "reason": "原始 Tj/TJ 指令直改，并通过像素一致性校验"}
                return {"mode": "blocked", "level": "blocked", "visualVerified": False,
                        "reason": check.get("reason", "原指令修改未通过视觉校验"), "validation": check}
            stream_reason = info.get("reason", "无法修改原始文字指令")

        # Level 2: clone an already-rendered target glyph from the same document.
        # This works even when the selected text lives inside a Form XObject or the active
        # subset font cannot encode the new Unicode character directly.
        with fitz.open(stream=pdf_bytes, filetype="pdf") as candidate:
            applied, dinfo = apply_document_glyph_clone(candidate, edit, pdf_bytes)
            if applied:
                check = verify_visual_change(original, candidate, edit)
                if check.get("ok"):
                    return {**dinfo, "mode": "docglyph", "visualVerified": True, "validation": check,
                            "grade": "文档原字形", "reason": "从同一 PDF 复用原始目标字形，并通过像素一致性校验"}
                docglyph_reason = check.get("reason", "文档原字形克隆未通过视觉校验")
            else:
                docglyph_reason = dinfo.get("reason", "整份 PDF 中没有可复用的目标字形")

        # Level 3: only changed glyphs, exact PDF-embedded font, then pixel validation.
        with fitz.open(stream=pdf_bytes, filetype="pdf") as candidate:
            applied, ginfo = apply_embedded_glyph_edit(candidate, edit)
            if applied:
                check = verify_visual_change(original, candidate, edit)
                if check.get("ok"):
                    return {**ginfo, "mode": "glyph", "visualVerified": True, "validation": check,
                            "grade": "原字形复用", "reason": "复用 PDF 自带嵌入字体，仅修改目标字符，并通过像素一致性校验"}
                return {"mode": "blocked", "level": "blocked", "visualVerified": False,
                        "reason": check.get("reason", "原字形复用未通过视觉校验"), "validation": check,
                        "details": ginfo.get("reason")}
            glyph_reason = ginfo.get("reason", "无法复用原嵌入字体")

    return {
        "mode": "blocked",
        "level": "blocked",
        "visualVerified": False,
        "reason": f"高一致性编辑不可用：{stream_reason}；{docglyph_reason}；{glyph_reason}",
    }


def apply_verified_edit(doc: fitz.Document, edit: dict, mode: str, pdf_bytes: bytes | None = None) -> tuple[bool, dict]:
    if mode == "stream":
        return apply_stream_edit(doc, edit)
    if mode == "docglyph":
        if pdf_bytes is None:
            return False, {"mode": "blocked", "reason": "缺少原始 PDF 数据，无法执行文档字形克隆"}
        return apply_document_glyph_clone(doc, edit, pdf_bytes)
    if mode == "glyph":
        return apply_embedded_glyph_edit(doc, edit)
    if mode == "none":
        return True, {"mode": "none", "reason": "无变化"}
    return False, {"mode": "blocked", "reason": "该编辑没有通过高一致性校验"}
