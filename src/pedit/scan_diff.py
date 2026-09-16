"""Character geometry and minimal edit planning; no page pixels are changed here."""
from difflib import SequenceMatcher
import math


def aligned_chars(text, chars):
    ordered = sorted(chars or [], key=lambda c: (c.get('bbox', [0, 0])[0], c.get('bbox', [0, 0])[1]))
    ordered = [c for c in ordered if not str(c.get('c', '')).isspace()]
    compact = ''.join(c for c in text if not c.isspace())
    sequence = ''.join(str(c.get('c', '')) for c in ordered)
    if sequence.count(compact) == 1 and sequence != compact:
        start=sequence.index(compact)
        ordered=ordered[start:start+len(compact)]
        sequence=''.join(c['c'] for c in ordered)
    if sequence != compact:
        raise ValueError('字符文本与坐标序列不一致，请重新识别或框选准确字段')
    out = {}; cursor = 0
    for index, value in enumerate(text):
        if value.isspace():
            continue
        char = ordered[cursor]; cursor += 1
        b = char.get('bbox', [])
        if len(b) != 4 or not all(math.isfinite(float(v)) for v in b) or b[2] <= b[0] or b[3] <= b[1] or char.get('geometry') == 'estimated':
            raise ValueError('缺少可靠字符坐标，已阻止估算区域擦除')
        out[index] = char
    return out


def _expand_same_length_stable_ranges(old, new):
    """Plan visually stable local replacements for equal-length edits.

    OCR may return a whole structured token when only its numeric suffix
    changes. A wider replacement glyph can exceed the original character cell.
    For a change inside a contiguous numeric run, rebuild the whole numeric
    fragment while preserving the surrounding token pixels.  Non-numeric changes remain character-local.
    """
    changed = [i for i, (a, b) in enumerate(zip(old, new)) if a != b]
    if not changed:
        return []

    ranges = []
    consumed = set()
    for i in changed:
        if i in consumed:
            continue
        # If both old/new at the changed position are digits, expand to the
        # maximal contiguous run that is numeric in both strings.  This keeps
        # numeric edits visually stable without redrawing prefixes/suffixes.
        if old[i].isdigit() and new[i].isdigit():
            a = i
            b = i + 1
            while a > 0 and old[a-1].isdigit() and new[a-1].isdigit():
                a -= 1
            while b < len(old) and old[b].isdigit() and new[b].isdigit():
                b += 1
            # A one-digit run gains nothing from fragment expansion.
            if b - a >= 2:
                ranges.append((a, b, a, b))
                consumed.update(range(a, b))
                continue
        ranges.append((i, i + 1, i, i + 1))
        consumed.add(i)

    # Multiple changed glyphs in the same expanded fragment may have produced
    # duplicate ranges; canonicalize while retaining reading order.
    out = []
    seen = set()
    for r in sorted(ranges, key=lambda x: (x[0], x[1])):
        key = (r[0], r[1], r[2], r[3])
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def plan_changes(old, new, chars):
    mapping = aligned_chars(old, chars)
    if old == new:
        return []
    if len(old) == len(new):
        ranges = _expand_same_length_stable_ranges(old, new)
    else:
        # Preserve the unchanged prefix. A changed advance shifts the suffix, so
        # include only that necessary tail, never the earlier line content.
        op = next(x for x in SequenceMatcher(None, old, new, autojunk=False).get_opcodes() if x[0] != 'equal')
        start = op[1]
        if start == len(old):
            start = max(0, start-1)
        ranges = [(start, len(old), start, len(new))]
    result = []
    for a,b,c,d in ranges:
        selected = [mapping[i] for i in range(a,b) if i in mapping]
        if not selected:
            raise ValueError('空白字符缺少安全修改区域，请选择包含相邻字符的字段')
        boxes = [v['bbox'] for v in selected]
        box = [min(x[0] for x in boxes), min(x[1] for x in boxes), max(x[2] for x in boxes), max(x[3] for x in boxes)]
        # Reject overlaps with preserved neighbours: an OCR cell may swallow them.
        for i,ch in mapping.items():
            if a <= i < b:
                continue
            cb=ch['bbox']
            if min(box[2],cb[2])-max(box[0],cb[0]) > .5:
                raise ValueError('修改字符框与未修改字符重叠，请重新框选')
        if len(old) == len(new):
            actual_changed = [i for i in range(a, b) if old[i] != new[i]]
        else:
            actual_changed = list(range(a, b))
        result.append({'oldStart':a,'oldEnd':b,'newStart':c,'newEnd':d,
                       'changed_char_indices':actual_changed,
                       'replacement_char_indices':list(range(a,b)),
                       'stableFragment': (b-a) > max(1, len(actual_changed)),
                       'bbox':box,'old':old[a:b],'new':new[c:d]})
    return result
