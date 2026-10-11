# v2.3.31 测试报告

## 通过

- `node --check static/app.js`
- Python `py_compile`：`app.py`、`scan_engine.py`、`scan_revision_visual.py`、`scan_visual_match.py`、`ocr_subfield.py`、`high_fidelity.py`、`validation.py`、`scan_diff.py`
- DOM ID 检查：247 个 ID，0 个重复；JavaScript `getElementById` 引用 0 个缺失。
- v2.3.31 + 1:1 原文复用 + Native Scan Renderer + 字形所见即所得 + 修改记录 + 页码数字槽 + 保存/高清预览相关回归：41 passed。
- 新增专项：
  - `LH-K-100 -> LH-K-600` 自动规划为 `100 -> 600`。
  - 实际变化字符仍记录为 `[5]`，但重建片段记录为 `[5, 6, 7]`。
  - `ABC-100-X -> ABC-660-X` 合并为一个 `100 -> 660` 片段。
  - 非数字等长修改仍保持单字符局部替换。
  - 单字符数字片段仍保留 v2.3.30 的 RGBA 1:1 原文复用能力。

## 全量测试

- `142 passed, 14 failed`
- 14 个失败均为已有 Linux 测试环境限制，没有新增 v2.3.31 功能失败：
  - 12 项旧扫描夹具仍硬编码 `C:/Windows/Fonts/arial.ttf`，Linux 下 `OSError: cannot open resource`。
  - 2 项旧 UI OCR 测试在当前 Linux OCR 环境未识别出 `领海牌`，在测试前置条件处 `StopIteration`。

## 本版行为变化

v2.3.31 有意改变旧版“最小单字符数字替换”的默认策略。对于连续多位数字中的等长修改，默认使用最小稳定数字片段，而不是最小单字符框。这是为了解决 `1 -> 6` 这类宽度差异较大的字形在窄字符槽中出现位置、比例和视觉不协调的问题。
