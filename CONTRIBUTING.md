# Contributing

Use Python 3.10+ and Node.js 22+ for development. Follow the install and validation commands in the README. Prefer a small PR with a concrete reproduction, expected behavior and meaningful tests. Preserve the current PDF engines unless an engine change is explicitly needed; avoid broad rewrites or formatting unrelated to the change.

Tests must construct synthetic documents, use temporary directories and work without personal paths, paid fonts, external OCR services or customer documents. Add test coverage for fidelity boundaries when touching glyph positioning, resampling or replacement. Never attach session files, private document snippets, real client screenshots, keys or tokens.

Before a PR, run pytest, the Node session tests, Ruff, the JavaScript syntax check and the release hygiene script. For packaging changes, build and install the wheel into a clean environment and run `scripts/smoke_install.py` outside the checkout. Baseline Ruff rules catch syntax/undefined-name/control-flow errors; legacy style cleanup is a separate task.

Describe new dependencies and assets in THIRD_PARTY_NOTICES.md, with the upstream URL, exact license and redistribution evidence. Contributions to Pedit-owned code are submitted under AGPL-3.0-or-later; this does not relicense third-party dependencies. Confirm you have the right to contribute your code. Maintainers review correctness, resource rights and scope before merging. See SECURITY.md for private vulnerability reports.
