# Validation for the final v0.1.0 source

Executed on Windows x64 / Python 3.12.14, 2026-09-16. Hosted GitHub CI has not been run.

| Check | Actual result |
| --- | --- |
| `python -m pytest -q` | 15 passed, no skips; 5 inherited Pillow deprecation warnings |
| `node --test tests/test_session.cjs` | 3 passed, no skips |
| `python -m ruff check .` | Passed, using the runtime-error baseline rules |
| `node --check src/pedit/static/app.js` | Passed |
| `python scripts/check_release.py` | Passed; no PDF assets, AGPL text/metadata checked |
| `python -m build` | Passed; wheel and source distribution built |
| `python -m twine check dist/*` | Both distributions passed |
| Installed wheel smoke check | Passed: startup, health, UI assets, import, render and export |
| Installed license metadata | `License-Expression: AGPL-3.0-or-later` verified |

Tests dynamically generate minimal PDF data in memory or temporary folders using tests/fixtures/pdf_factory.py. Core tests disable optional OCR and reject outbound socket connections; local HTTP calls remain enabled. They cover PDF import/render, electronic and scan replacement/export, unchanged-region preservation, exact RGBA asset persistence/reuse, scale guards, session reload, baseline commit/restore, invalid inputs and static traversal rejection. No stored PDFs are needed.

The JavaScript suite executes the actual save/restore functions and the complete UI startup script with DOM stubs. Even with saved progress present, startup performs zero storage reads and zero network requests; document, edits, glyph/block libraries and history stay empty. Explicit restore retains saved assets and older payload compatibility. This is not a full browser automation suite.

The installed wheel was also opened in a browser and refreshed. Both states showed an empty workspace, no document name or glyph/history content, disabled editing/export controls, and explicit open/restore controls. No browser console errors were observed.

All nine Python modules outside the local HTTP controller retain identical executable ASTs against the preceding candidate, after excluding docstrings. Controller changes remove optional annotation/summary marking only; existing production rendering/export operations remain. Glyph positioning, bbox, baselines and scan patch algorithms were not redesigned.

Actual test versions: PyMuPDF 1.28.2, Pillow 11.3.0, NumPy 2.3.5, OpenCV headless 4.14.0.94, pytest 9.1.1, Ruff 0.16.7. Dependency ranges remain bounded rather than fully locked.

## Build and remaining acceptance

The source distribution was rebuilt after final documentation corrections; archive contents and checksums are recorded in the delivery report. Hosted OS/Python matrices, optional OCR/model licensing and CJK/system-font coverage still need target-environment acceptance. Pillow warnings concern inherited mode arguments; the declared range remains below 12. Complete source-rights, maintainer contacts and corresponding-source checks before publication.
