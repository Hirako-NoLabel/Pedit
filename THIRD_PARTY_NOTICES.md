# Third-party notices

Pedit is distributed under AGPL-3.0-or-later. Dependencies retain their own licenses; the project license does not relicense them. Pedit uses the open-source PyMuPDF/MuPDF distribution. No commercial license, paid SDK, cloud API or remote processing service is required or purchased.

| Dependency | Role | Upstream license and source |
| --- | --- | --- |
| PyMuPDF / MuPDF | Required local PDF engine | GNU AGPL v3 open-source distribution; [official licensing](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright), [source](https://github.com/pymupdf/PyMuPDF). Follow each resolved component's own version/notice terms. |
| Pillow | Images | HPND-style Pillow license; [license](https://github.com/python-pillow/Pillow/blob/main/LICENSE) |
| NumPy | Arrays | BSD-3-Clause; [license](https://github.com/numpy/numpy/blob/main/LICENSE.txt) |
| OpenCV Python headless | Images | Wrapper MIT; modern OpenCV Apache-2.0; native binaries include additional notices; [licensing](https://github.com/opencv/opencv-python#licensing) |
| RapidOCR (optional) | Local OCR orchestration | Apache-2.0 code; [upstream](https://github.com/RapidAI/RapidOCR). Model terms are separate. |
| ONNX Runtime (optional) | Local model execution | MIT; [license](https://github.com/microsoft/onnxruntime/blob/main/LICENSE) |
| pytesseract / Tesseract (optional) | Local OCR fallback | Apache-2.0; [wrapper](https://github.com/madmaze/pytesseract), [engine](https://github.com/tesseract-ocr/tesseract). Language data has its own provenance. |

Dependencies are declared in pyproject.toml and installed separately. This repository and the Pedit wheel do not vendor native dependency binaries, fonts or OCR weights. User-installed fonts retain their own terms. Glyph capture does not grant rights to redistribute user documents.

For distribution, preserve copyright/license notices and provide the complete corresponding source and build instructions required by applicable AGPL terms. Supply matching Pedit source alongside its wheel; an unrelated or newer source revision is insufficient. A future distributor bundling dependencies or offering modified software over a network must also satisfy applicable source-availability obligations for those components and uses. See the [GNU AGPL text](https://www.gnu.org/licenses/agpl-3.0.html).

Optional OCR runs locally, but model acquisition may need network access. Verify exact model versions, provenance, terms and required notices before bundling any weights. No models are included or exercised by core release tests. This direct-dependency inventory is not a complete binary SBOM for a future bundled executable.

The test generator uses standard PDF Base-14 font references without embedded font programs and original geometric digits. It reads no customer PDF, system-font binary, copied artwork or model file. Generated PDFs exist only in memory or temporary test directories.
