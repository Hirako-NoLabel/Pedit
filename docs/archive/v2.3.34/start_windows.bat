@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [PDF 精准编辑器 v2.3.34]
echo 正在检查运行环境...

python -c "import pymupdf, PIL, numpy, cv2" >nul 2>&1
if errorlevel 1 goto install_deps
python -c "import rapidocr, onnxruntime" >nul 2>&1
if errorlevel 1 goto install_deps
goto start_app

:install_deps
echo 首次运行：正在安装 PDF 编辑与 OCR 依赖...
echo 这一步需要联网，可能需要几分钟。
python -m pip install -r requirements.txt
if errorlevel 1 goto install_failed

:start_app
echo.
echo 正在启动本地编辑器...
python app.py
pause
exit /b 0

:install_failed
echo.
echo 依赖安装失败，请检查 Python 和网络连接后重试。
pause
exit /b 1
