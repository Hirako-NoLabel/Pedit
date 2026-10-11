# v2.3.33 测试报告

## 本轮专项

- `node --check static/app.js`：通过。
- Python `py_compile`：`app.py`、`scan_engine.py`、`scan_revision_visual.py`、`scan_visual_match.py`、`ocr_subfield.py`、`high_fidelity.py`、`validation.py`：通过。
- DOM ID：247 个，0 个重复；JavaScript `getElementById` 引用缺失 0 个。
- v2.3.33 稳定数字片段宽度策略 + v2.3.31/v2.3.32 相关回归：6 passed。
  - `LH-K-100 -> LH-K-600` 仍规划为稳定片段 `100 -> 600`。
  - 稳定片段标志已传入局部 patch。
  - 稳定片段在找不到完整字组时先走独立等比例适配分支，不会先触发普通输入模式 4% 横向保护。
  - 普通输入模式 4% 保护仍保留。
  - 同排完整 `600` 字组优先 1:1 复用逻辑继续通过。

## 全量 pytest

- 145 passed，14 failed。
- 14 项失败均为已知 Linux 测试环境问题：
  - 12 项旧合成夹具硬编码 `C:/Windows/Fonts/arial.ttf`，当前 Linux 环境无法加载。
  - 2 项旧 OCR 视觉测试在当前 Linux OCR 环境未识别到 `领海牌`，因此前置查找触发 `StopIteration`。
- 本轮没有新增 v2.3.33 功能失败。

## 本轮修复结论

v2.3.32 中出现的“扫描文字视觉布局检查失败：保持输入字形：新文字超出当前字段宽度”逻辑冲突已解除。稳定数字片段不再被普通 WYSIWYG 4% 横向保护直接拦截；缺少完整目标字组时，改为在数字片段内部进行等比例整体适配，同时保持未修改前后缀原扫描像素不动。
