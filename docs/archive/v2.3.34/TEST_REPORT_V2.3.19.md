# TEST REPORT v2.3.19

## 本轮专项回归

执行：

- `tests/test_v2312_workflow.py`
- `tests/test_v2314_finished_glyph_reuse.py`
- `tests/test_v2315_version_history.py`
- `tests/test_v2316_tune_inputs_and_docglyph_priority.py`
- `tests/test_v2317_page_number_templates.py`
- `tests/test_v2318_page_number_recognition.py`
- `tests/test_v2319_page_number_box_anchor.py`

结果：**28 passed**。

## v2.3.19 新增验证

- 框选区域能识别完整页码文本及两个数字组。
- 框选能合并被 OCR 拆开的两个页码 token。
- 后续页面发生 3pt 横向偏移时，返回的是该页真实数字 bbox，而不是源模板 bbox。
- 空白框可作为“新增页码”模板位置。
- `Page 92 of 92 → Page 82 of 96` 的两个数字子字段可独立替换；测试中替换后两个新数字的 bbox 与原数字 bbox 偏差均小于 **0.05 pt**，固定 `Page / of` 文本保留。

## 静态 / 编译检查

- `node --check static/app.js`：PASS
- `python -m py_compile app.py scan_engine.py scan_revision_visual.py high_fidelity.py ocr_subfield.py`：PASS
- DOM ID 引用检查：**0 个缺失 ID**

## 全量测试说明

运行全量 `pytest` 时，前 **53** 项通过，随后遇到项目既有测试夹具写死 Windows 字体：

`C:/Windows/Fonts/arial.ttf`

当前执行环境为 Linux，因此 Pillow 报 `OSError: cannot open resource`。这属于测试环境字体路径限制，不是 v2.3.19 页码框选 / 原位锚定逻辑失败。
