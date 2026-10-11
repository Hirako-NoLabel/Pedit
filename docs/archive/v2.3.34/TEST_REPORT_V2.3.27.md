# TEST REPORT v2.3.27

## 1. Static checks

Passed:

- `node --check static/app.js`
- `python -m py_compile app.py scan_engine.py scan_revision_visual.py scan_visual_match.py ocr_subfield.py high_fidelity.py validation.py`
- DOM duplicate ID check: 0 duplicates
- JavaScript `$('#id')` references missing from `index.html`: 0
- `scanTuneSection` defaults to collapsed (`<details>` without `open`)
- `start_windows.bat`: UTF-8 BOM present; CRLF-only line endings confirmed

## 2. v2.3.27 scan/UI focused tests

Command:

```bash
PYTHONPATH=. pytest -q tests/test_v2327_native_scan_ui.py tests/test_v236_line_style_profile.py tests/test_v237_quality_gate.py tests/test_v239_manual_tuning.py tests/test_v2326_save_render_hd.py
```

Result: **25 passed**.

Coverage includes:

- native scan px/pt detection from dominant embedded page image;
- default patch render scale follows native scan scale;
- no old `native_step` downsample/upscale pixelation pass;
- replacement `blurRadiusPx == 0` in automatic mode;
- actual sharpness metric and preservation gate;
- clarity -80 vs +80 produces different patch bytes;
- visual tuning default collapse and direction labels;
- Windows launcher BOM/CRLF;
- toolbar no-wrap/overflow protection;
- local row style profile / page preservation / finished tuning;
- v2.3.26 save/render/HD regression.

## 3. Broad regression excluding known environment fixtures

Command:

```bash
PYTHONPATH=. pytest -q --ignore=tests/test_v234_regression.py --ignore=tests/test_v235_bug02.py
```

Result: **112 passed**.

## 4. Full pytest run

Command:

```bash
PYTHONPATH=. pytest -q
```

Result: **127 passed, 14 failed**.

The 14 failures are limited to the two previously environment-sensitive suites:

### `tests/test_v234_regression.py` - 9 failures

The shared fixture still hard-codes:

```text
C:/Windows/Fonts/arial.ttf
```

On the Linux test host, Pillow raises `OSError: cannot open resource` before the tested editor behavior runs.

### `tests/test_v235_bug02.py` - 5 failures

- 3 failures use the same Windows-only synthetic font fixture and stop at `OSError: cannot open resource`.
- 2 failures depend on OCR finding `领海牌` in the stored `visual_results/ui_scan.pdf`; the current Linux OCR result does not contain that line, so the test stops at `StopIteration` before the target assertion.

These failures were **not counted as passed**.

## 5. Runtime smoke test

Started `python app.py` and requested:

```text
GET http://127.0.0.1:8765/api/health
```

Returned `200` JSON with:

- `ok: true`
- `version: 2.3.27`
- PyMuPDF available
- OCR available on the current host

## 6. v2.3.27 acceptance notes

Validated in synthetic scan tests:

- `LH-K-100 -> LH-K-600` remains a one-character local patch;
- non-target pixel preservation gate remains 0 violations;
- native scan renderer reports source/render px-per-pt;
- automatic replacement glyph does not inherit Gaussian blur;
- replacement sharpness is measured on the actual composed output;
- manual clarity changes are observable in generated patch data;
- page-number numeric-slot regressions remain covered by the broad suite;
- visual micro-adjustment UI is collapsed by default and secondary property areas follow the same pattern.

## 7. Important limitation

The new renderer substantially removes the known software-side blur chain, but visual equality with every real-world scanner/font cannot be proven from synthetic fixtures alone. Real scanned reports should still be checked at 100%, 200% and 400% after export. The new `actualSharpnessScore` is intended to make visibly softer replacements detectable instead of silently accepting them.
