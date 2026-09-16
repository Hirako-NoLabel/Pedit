# Pedit OSS v0.1.0

Pedit is a local-first PDF visual editor with Original Glyph Reuse. It supports local PDF import, scanned/image PDF edits, region erase, original glyph capture/reuse, preview, PDF export and saved local progress.

Start with an empty workspace and import your own PDF. Saved progress is restored only through an explicit user action. No documents, preset projects or glyph libraries ship with the application.

Install from source with `python -m pip install .`, then run `pedit`. Core editing needs no account, API key or cloud service and operates offline after installation. Optional OCR engines run locally and require their own local models/language data.

Pedit is licensed under AGPL-3.0-or-later. Third-party licenses are in THIRD_PARTY_NOTICES.md. Distributions must include matching corresponding source and required notices.

Current limits: Chinese UI; suitable source glyphs and target geometry required for 1:1 reuse; OS-dependent font fallback; sessions depend on local files; visual erasure is not certified redaction. See docs/VALIDATION.md for actual checks and remaining scope.

This is prepared release text, not evidence of a published tag or release.
