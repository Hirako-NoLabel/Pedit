# Changelog

Public versioning starts at 0.1.0. No public tag is implied by this file.

## 0.1.0 - prepared for publication

- Package the local PDF visual editor with Original Glyph Reuse and a `pedit` entry point.
- Start with an empty workspace; import a PDF or explicitly restore saved local progress.
- Retain electronic/scanned PDF editing, region erase, glyph capture/reuse, preview, export and session persistence.
- License the project under AGPL-3.0-or-later and document third-party dependencies.
- Ship no PDFs, preset projects, glyph libraries, model weights or document-derived images.
- Generate synthetic PDFs only inside tests; provide test/lint/build CI and contribution/security guidance.

This release packages the established editing engine. Final publication cleanup changes startup policy, licensing, documentation and test data without redesigning glyph geometry, rendering or export algorithms.
