# TEST REPORT v2.3.21

## 本轮重点

本轮验证两类功能：

1. v2.3.21 通用人工接管能力：任意框选、自由新增文字、拖动/缩放、0.1 坐标、锁定、吸附、局部放大、成品字组、对象层、3 页试运行。
2. 针对最新页码问题的补强：页段独立位置、单页重定位、逻辑异常阻断、空白新增默认关闭、生成页码可二次编辑/删除、撤销整轮页码批量。

## 已执行检查

### 语法 / 静态结构

- `node --check static/app.js`：PASS
- `python -m py_compile app.py scan_engine.py scan_revision_visual.py scan_visual_match.py ocr_subfield.py high_fidelity.py validation.py`：PASS
- HTML DOM ID 检查：
  - 重复 ID：0
  - JavaScript `$()` 引用缺失：0

### 专项 / 相关回归

执行：

- `test_v2321_manual_control.py`
- `test_v2321_page_number_takeover.py`
- `test_v2320_page_number_overlap_guard.py`
- `test_v2319_page_number_box_anchor.py`
- `test_v2318_page_number_recognition.py`
- `test_v2317_page_number_templates.py`
- `test_v2316_tune_inputs_and_docglyph_priority.py`
- `test_v2315_version_history.py`
- `test_v2314_finished_glyph_reuse.py`
- `test_v2312_workflow.py`

结果：**43 passed**。

### HTTP 端到端页码模板测试

新增测试会实际启动本地 `ThreadingHTTPServer`，创建 3 页合成电子 PDF，并通过真实 HTTP 接口执行：

- `/api/open`
- `/api/page-number-template/capture`
- `/api/page-number-template/scan`

验证：

- 同一个位置模板 A 可通过单页 override 在第 3 页跟随大幅位置变化。
- 位置 B 设置为仅适用第 3 页时，第 1/2 页不会出现 B，只有第 3 页参与扫描。

该专项文件结果：**3 passed**。

## 全量测试

执行：

`pytest -q -x --tb=short`

结果：前 **68 项通过**，随后第一个失败发生在旧版合成测试：

`tests/synthetic_fixture.py` 写死 `C:/Windows/Fonts/arial.ttf`。

当前运行环境为 Linux，因此 Pillow 报 `OSError: cannot open resource`。本报告不将该失败计为 v2.3.21 新功能通过，也不声称其后的全部测试均可通过。

## 本轮针对用户反馈的行为变化

- 类似 `893` 这种与模板连续关系明显不一致的当前页 OCR 结果，会在扫描结果阶段标红并阻止自动写入。
- 如果 91 页开始页码位置突然变化，可对该页“此页重定位”，或另建位置模板并把适用范围设为 91-96。
- 找不到原页码时默认不再自动新增，避免在旧位置产生重复页码；确实需要空白新增时需显式开启。
- 批量生成后的当前页/总页数字对象可通过页面生成框或对象层选中，再修改文字、移动、缩放或删除。
- 支持删除“此页此组”，以及一键“撤销上次页码批量”。
