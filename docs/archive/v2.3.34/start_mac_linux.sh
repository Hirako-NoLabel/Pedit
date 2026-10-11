#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 - <<'PY' >/dev/null 2>&1 || python3 -m pip install -r requirements.txt
import pymupdf
from PIL import Image
import numpy, cv2, rapidocr, onnxruntime
PY
python3 app.py
