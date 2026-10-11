# v2.3.30 修改文件

- `scan_revision_visual.py`：新增 1:1 RGBA 成品字资产、源字符槽锚点、禁止隐式重采样和原样位置复用。
- `static/app.js`：自动成品字复用默认模式由 `fit` 改为 `original`；保存进度键升级到 v2.3.30 并兼容 v2.3.29。
- `static/index.html`：版本升级；“原样粘贴”改为“1:1 原文复用”，“适配目标字符槽”改为“允许缩放适配”，并补充行为说明。
- `app.py`：版本、工作目录、健康检查升级到 v2.3.30。
- `start_windows.bat`：版本标识升级并继续保持 UTF-8 BOM + CRLF。
- `build_portable_windows.bat`：构建名称升级到 v2.3.30。
- `tests/test_v2330_true_1to1_glyph_reuse.py`：新增 RGBA 像素一致性、锚点一致性、不隐式重采样和 UI 默认模式专项测试。
- 若干旧测试：仅更新最新版本断言到 v2.3.30。
- `README.md`：增加 v2.3.30 使用说明。
