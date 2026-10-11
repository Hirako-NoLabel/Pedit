# TEST REPORT v2.3.18

## 本轮问题

针对 v2.3.17 批量页码编辑中出现的两类问题进行修复：

1. 模板位置扫描可能匹配到附近其他带数字的文字，导致“没有识别到本来的页码”。
2. `第1 -> 1/96`、`9 -> 10` 等页码结构/位数变化时，普通高一致性文字引擎会因字符数量变化而阻止修改。

## 修复验证

执行：

- `tests/test_v2318_page_number_recognition.py`
- `tests/test_v2317_page_number_templates.py`
- `tests/test_v2316_tune_inputs_and_docglyph_priority.py`
- `tests/test_v2315_version_history.py`
- `tests/test_v2314_finished_glyph_reuse.py`
- `tests/test_v239_manual_tuning.py`

结果：**22 passed**

另外：

- `node --check static/app.js`：PASS
- `python -m py_compile app.py scan_revision_visual.py scan_engine.py high_fidelity.py`：PASS

## 重点覆盖

- 页码位置匹配携带源文字结构并使用更严格的几何匹配。
- 纯数字页码可从 OCR 合并文本中提取数字子字段。
- 页码结构变化自动使用 `page-number-replace` 专用原位替换。
- 电子 PDF 页码替换只删除目标区域文本对象，图片/矢量图形保持不处理。
- 更长的新页码内容可按模板锚点扩展输出区域。
