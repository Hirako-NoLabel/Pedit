# v2.3.32 测试报告

## 通过

- `node --check static/app.js`
- Python `py_compile`：`app.py`、`scan_engine.py`、`scan_revision_visual.py`、`scan_visual_match.py`、`ocr_subfield.py`、`high_fidelity.py`、`validation.py`、`scan_diff.py`
- DOM ID 检查：247 个 ID，0 个重复；JavaScript `$()` 选择器均存在对应 ID
- v2.3.32 专项与关键相关回归：22 passed
  - v2.3.31 稳定数字片段：`LH-K-100 -> LH-K-600` 自动规划为 `100 -> 600`
  - v2.3.32 整组数字片段复用：同页同排 `600` 会作为完整 RGBA 片段传入 patch，不再拆成 `6 + 0 + 0` 单字组合
  - v2.3.30 1:1 成品字复用回归
  - v2.3.29 修改记录 / 顶部工具栏回归
  - v2.3.28 字形预览 / WYSIWYG 回归
  - v2.3.7 质量门相关回归
- 全量 pytest：143 passed，14 failed
- 服务启动健康检查：`/api/health` 返回 `ok: true`、`version: 2.3.32`，OCR 可用。

## 全量失败项说明

剩余 14 项未算通过，原因与旧环境夹具一致：

- 12 项旧测试仍硬编码 `C:/Windows/Fonts/arial.ttf`，在当前 Linux 环境中触发 `OSError: cannot open resource`。
- 2 项旧 OCR 测试在当前 Linux/Tesseract 环境未识别到 `领海牌`，前置条件 `next(... if '领海牌' in line)` 停止。

本轮新增的 v2.3.32 整组数字片段复用专项测试已通过，没有新增功能失败。
