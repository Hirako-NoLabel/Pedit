@echo off
setlocal
cd /d "%~dp0"
py -m PyInstaller --noconfirm --clean --onedir --windowed --name "PDF精准编辑器_v2.3.31" --add-data "static;static" --collect-all rapidocr --collect-all onnxruntime app.py
if errorlevel 1 exit /b %errorlevel%
echo.
echo Portable build created in dist\PDF精准编辑器_v2.3.31
endlocal
