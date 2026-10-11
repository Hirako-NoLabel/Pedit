# TEST REPORT v2.3.20

## Focus

This release fixes duplicate / overlapping fixed page-number text such as `第3页，共6页` when the numeric sub-fields cannot be reliably isolated.

## Automated checks

- `node --check static/app.js`: PASS
- `python -m py_compile app.py scan_engine.py scan_revision_visual.py scan_visual_match.py`: PASS
- Page-number regression tests (`v2.3.17` - `v2.3.20`): **20 passed**

## Visual regression

A synthetic electronic PDF containing `第3页，共6页` was edited by replacing only the two numeric sub-fields. The rendered result was inspected and shows the fixed Chinese text and punctuation only once, with the new digits positioned in the original numeric locations.

## New safety behavior

- Formatted page numbers with fixed text no longer fall back to whole-phrase repainting when digit coordinates are unreliable.
- Such pages are marked for re-boxing / manual check instead of producing overlapping text.
- Page-number template A/B boxes are checked for material overlap before scanning.
