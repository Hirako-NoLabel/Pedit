# v2.3.30 测试报告

## 通过

- `node --check static/app.js`
- Python `py_compile`：`app.py`、`scan_engine.py`、`scan_revision_visual.py`、`scan_visual_match.py`、`ocr_subfield.py`、`high_fidelity.py`、`validation.py`
- DOM ID 检查：247 个 ID，0 个重复；JavaScript `$()` ID 引用无缺失。
- v2.3.30 + 成品字 / Native Scan / WYSIWYG / 修改记录相关回归：20 passed。
- v2.3.30 专项验证：
  - assetVersion 2 生成背景透明 RGBA 字形资产。
  - 1:1 复用后的 RGBA 字形与源资产逐像素一致。
  - 源字符槽 X/Y 锚点在复用后保持一致。
  - `reuseResampled = false`，`reusePixelMode = rgba-1to1`。
  - 自动复用默认使用 `original`，不会自动进入 `fit`。
- 实际启动服务：`/api/health` 返回 `ok: true`、`version: 2.3.30`，OCR 可用。

## 全量测试

- 139 passed，14 failed。
- 14 项失败均为既有测试环境限制，没有新增 v2.3.30 功能失败：
  - 12 项旧扫描夹具仍硬编码 `C:/Windows/Fonts/arial.ttf`，Linux 环境无法打开该 Windows 字体。
  - 2 项旧视觉 OCR 测试要求 Linux OCR 必须识别出 `领海牌`，当前 OCR 结果未满足该前置条件，因此 `StopIteration`。

未将上述环境失败虚报为通过。
