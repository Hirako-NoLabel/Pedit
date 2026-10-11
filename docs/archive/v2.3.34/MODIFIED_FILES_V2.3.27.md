# MODIFIED_FILES v2.3.27

- `scan_visual_match.py` - 超采样单次降采样；替换字禁止自动 GaussianBlur；记录源 blur 估计。
- `scan_revision_visual.py` - 原生扫描 DPI 检测、Native Scan Renderer、清晰度控制、实际锐度指标，删除旧 native_step 二次采样链路。
- `static/index.html` / `static/harness.html` - 视觉微调方向标签、清晰度参数、折叠式二级功能区、v2.3.27 标识。
- `static/app.js` - clarity 参数读写/复位/摘要、保存进度 key 升级。
- `static/styles.css` - 折叠面板、方向标签、工具栏防溢出响应式样式。
- `app.py` - 服务端与页面版本升级到 2.3.27。
- `start_windows.bat` / `启动编辑器.bat` - Windows BOM/CRLF 与依赖检查修复。
- `tests/test_v2327_native_scan_ui.py` - v2.3.27 专项测试。
- 历史测试版本断言更新到 v2.3.27；旧 scanSoften UI 断言更新为 scanClarity。
- `README.md`, `CHANGELOG_V2.3.27.md`, `TEST_REPORT_V2.3.27.md` - 文档。
