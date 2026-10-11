# Pedit

**Local-first PDF visual editor with Original Glyph Reuse.**

Pedit is a local PDF editing tool for electronic, scanned and image-based documents. It starts with an empty workspace. Import your own PDF to begin editing; files are processed on your computer.

## Features

- **PDF import:** open a local PDF and inspect its pages.
- **Scanned/image PDF editing:** select a region and apply local visual changes.
- **Region erase:** remove a selected visual region while preserving surrounding content.
- **Original glyph capture:** capture a glyph or fragment from the current document.
- **Original glyph reuse:** reuse captured appearance with its original pixels and placement information where possible.
- **Local editing:** preview changes without uploading the PDF to a service.
- **PDF export:** save the edited document as a new PDF.
- **Session persistence:** save progress, edits, glyph/block libraries and baselines locally, then restore them explicitly.

Region erase is a visual edit, not a certified confidential-data redaction operation. Underlying content may remain extractable.

## Original Glyph Reuse

Original text → capture original glyph → reuse glyph elsewhere.

Pedit 从原 PDF 中采样原始字形，以像素级方式复用，尽可能避免系统字体替换导致的字体、宽度、基线、清晰度不一致。

Electronic PDFs can reuse original content streams, embedded fonts and document glyphs. Scanned pages use local raster patches and captured RGBA glyphs or fragments. In 1:1 mode, reuse preserves captured pixels and character-cell anchors without automatic resampling. A suitable source glyph, compatible scale and sufficient target space are required. Explicit fit mode or font fallback can alter appearance; fidelity is not guaranteed for every document.

## Install and run

Requires Python 3.10+ and a modern desktop browser. The UI currently uses Chinese. Install from the source checkout or a release wheel; package-index availability is not assumed.

```sh
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
python -m pip install .
pedit
# Alternative: python -m pedit
```

Open [the local editor](http://127.0.0.1:8765).

**Start Pedit → empty workspace → import a PDF → edit → export.**

Startup and refresh do not open a document or restore previous content automatically. To continue saved work, choose **恢复进度** (Restore progress) from the empty workspace. A saved session depends on its local PDF/baseline files and is not a portable standalone project archive. Use `PEDIT_DATA_DIR` for a private persistent directory. See [installation](docs/INSTALLATION.md) and [data handling](docs/ARCHITECTURE.md).

## Local-first and offline-capable

Core editing works locally after dependencies are installed. It needs no account, API key, remote AI, online PDF service or paid SDK. The server binds to `127.0.0.1`; do not expose it to a public network.

Automatic recognition is optional:

```sh
python -m pip install ".[ocr]"
```

The optional OCR engines run locally. Package/model installation may need a download; offline OCR requires the models or Tesseract language data to be available beforehand. Basic installation does not include OCR packages or weights. Manual scan regions and electronic editing remain available without OCR. System-font fallback, especially CJK, depends on locally installed fonts.

## Development

```sh
python -m pip install -e ".[dev]"
python -m pytest -q
node --test tests/test_session.cjs
python -m ruff check .
node --check src/pedit/static/app.js
python scripts/check_release.py
python -m build
python -m twine check dist/*
```

Node.js 22+ is only needed for JavaScript checks. The UI is packaged static HTML/CSS/JS and needs no frontend bundler. Tests generate minimal synthetic PDFs at runtime; no PDF files ship in the repository or application.

```text
src/pedit/          PDF engine and packaged static UI
tests/fixtures/    synthetic fixture generators, used only by tests
docs/              installation, architecture and release guidance
scripts/           release checks and installed-package smoke test
.github/           issue/PR templates and test/lint/build workflows
```

See [CONTRIBUTING](CONTRIBUTING.md), [SECURITY](SECURITY.md), [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md), [CHANGELOG](CHANGELOG.md), [ROADMAP](ROADMAP.md) and [validation](docs/VALIDATION.md). Public versioning starts at v0.1.0.

## This repository

Public home of the PDF editor (AGPL-3.0-or-later). `docs/archive/` keeps older pre-Pedit snapshots (local v2.3.x / former private `pdf-precision-editor`) only where they differ from the current code — not part of a release; excluded from release checks and lint. See [docs/history.md](docs/history.md).

## License

Pedit is licensed under AGPL-3.0-or-later.

See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md).
