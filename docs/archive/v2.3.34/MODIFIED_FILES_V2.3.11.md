# v2.3.11 修改文件

- `static/index.html`：版本号、默认微调范围、双向边缘融合、进度 UI、页码重编号入口与弹窗。
- `static/app.js`：默认 fit-width、视觉微调进度、页码扫描/预览/批量应用逻辑。
- `static/styles.css`：进度遮罩与页码重编号弹窗样式。
- `scan_revision_visual.py`：扩大手动参数范围，背景边缘融合支持 -100~+100。
- `app.py`：版本号、页码候选检测、`/api/page-numbers/scan`。
- `start_windows.bat`：版本号。
- `README.md`：v2.3.11 使用说明。
- `tests/test_v2311_features.py`：本轮专项测试。
