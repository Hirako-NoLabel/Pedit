@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [OCR 自检 - v2.3.8]
python -c "from scan_engine import ocr_status; import json; print(json.dumps(ocr_status(), ensure_ascii=False, indent=2))"
if errorlevel 1 (
  echo.
  echo OCR 自检失败。请重新双击 start_windows.bat，让程序自动安装依赖。
)
pause
