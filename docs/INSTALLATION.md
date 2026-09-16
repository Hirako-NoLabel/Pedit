# Installation and operation

Use an isolated Python environment. Install from the checkout with `python -m pip install .`, or install the wheel with `python -m pip install pedit_oss-0.1.0-py3-none-any.whl`. Run `pedit` or `python -m pedit`. No bundled EXE or package-index publication is assumed.

Every startup and refresh presents an empty workspace, including when saved progress exists. Import a local PDF to begin. To resume work explicitly, click **恢复进度** on the empty workspace. The saved filename, content and glyph library are not displayed before that action. Save progress before closing/refreshing to retain edits.

| Variable | Default / purpose |
| --- | --- |
| `PDF_EDITOR_PORT` | 8765; local HTTP port |
| `PEDIT_DATA_DIR` | OS temporary directory / pedit-oss-v1; set a private persistent location to retain sessions |
| `PEDIT_NO_BROWSER` | Set to 1 for headless startup |
| `TESSERACT_CMD` | Optional path to the local OCR executable |

Core editing operates offline after dependencies are installed. It needs no account, credentials or remote service. PDFs, baselines and progress remain local.

Install `.[ocr]` only for automatic recognition. RapidOCR/ONNX and Tesseract execute locally. Package/model downloads are separate setup steps; offline recognition needs local models. Tesseract also needs its executable and language data. `/api/health` reports recognition availability. Manual scan regions and electronic editing remain usable without OCR.

No font programs are redistributed. CJK font fallback needs suitable locally installed fonts. Original reuse requires compatible source glyphs and target geometry. Do not proxy the service to the internet. Saved progress depends on its local session folder, not JSON alone.
