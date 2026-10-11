# TEST REPORT v2.3.28

## 1. Static checks

- `node --check static/app.js`: PASS
- `python -m py_compile app.py scan_engine.py scan_revision_visual.py scan_visual_match.py ocr_subfield.py high_fidelity.py validation.py`: PASS
- DOM ID check: 246 IDs, no duplicates
- JS -> HTML ID references: 240, no missing IDs

## 2. v2.3.28 + related regression set

Command covered:
- `test_v2328_toolbar_and_glyph_wysiwyg.py`
- `test_v2327_native_scan_ui.py`
- `test_v2325_numeric_slot_page_numbers.py`
- `test_v2324_existing_page_number_only.py`
- `test_v2323_recognition_and_centering.py`

Result: **23 passed**.

Covered items include compact toolbar labels, final glyph preview, default input-glyph policy, v2.3.27 native scan renderer / clarity control, page-number numeric slots, existing-page-number-only behavior and import centering.

## 3. Full pytest

Result: **131 passed, 14 failed**.

The 14 failures are the same environment limitations documented in v2.3.27:

- 12 failures are fixture paths hard-coded to Windows fonts such as `C:/Windows/Fonts/arial.ttf` while tests run on Linux, producing `OSError: cannot open resource`.
- 2 failures are legacy OCR visual tests that require Linux OCR to return a line containing `领海牌`; current environment does not return that line and the fixture stops with `StopIteration`.

No v2.3.28 focused/related regression failed.

## 4. Runtime smoke test

Started `python app.py` and requested `/api/health`.

Result:
- `ok: true`
- `version: 2.3.28`
- PyMuPDF and Tesseract OCR loaded successfully.

## 5. v2.3.28 acceptance

- Viewer controls use `整页 / 页宽 / 预览 / 净图`, with full descriptions in tooltips.
- New scan text edits default to `保持输入字形（所见即所得）`.
- Final glyph preview updates before running the edit.
- Input-glyph mode fixes the font family instead of silently switching to a serif candidate.
- If preserving the chosen glyph would require more than 4% automatic horizontal squeezing, generation is blocked with an actionable message instead of distorting the glyph.
- `自动匹配 / 同行同字优先` remains available as an explicit alternative.
