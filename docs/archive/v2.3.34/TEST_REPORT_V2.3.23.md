# TEST REPORT v2.3.23

## 本轮目标

验证两项用户反馈回归：

1. v2.3.22 页码批量扫描后大量/全部页面提示无法定位数字子区域。
2. PDF 刚导入后页面初始位置偶发不居中。

## 已运行检查

### JavaScript 语法

- `node --check static/app.js`
- 结果：PASS

### Python 编译

- `python -m py_compile app.py scan_engine.py scan_revision_visual.py scan_visual_match.py ocr_subfield.py high_fidelity.py validation.py`
- 结果：PASS

### DOM ID 检查

- JavaScript `$('#...')` 引用：222
- HTML ID：225
- 缺失引用：0
- 重复 ID：0

### 页码 / 人工接管 / 历史相关回归

运行：

`pytest -q tests/test_v2311_features.py tests/test_v2312_workflow.py tests/test_v2314_finished_glyph_reuse.py tests/test_v2315_version_history.py tests/test_v2316_tune_inputs_and_docglyph_priority.py tests/test_v2317_page_number_templates.py tests/test_v2318_page_number_recognition.py tests/test_v2319_page_number_box_anchor.py tests/test_v2320_page_number_overlap_guard.py tests/test_v2321_manual_control.py tests/test_v2321_page_number_takeover.py tests/test_v2322_revision_undo_and_manual_takeover.py tests/test_v2323_recognition_and_centering.py`

结果：**56 passed**

### 全量测试首个失败点

运行：

`pytest -q -x --tb=short`

结果：前 **77 项通过**，第 78 项在旧测试夹具 `tests/synthetic_fixture.py` 中失败。

失败原因：该旧测试硬编码 Windows 字体路径：

`C:/Windows/Fonts/arial.ttf`

当前测试环境为 Linux，Pillow 报 `OSError: cannot open resource`。因此未把该项及其后的测试计为通过。

## v2.3.23 新增专项覆盖

- 两角色页码模板不能被单个附近数字提前抢占。
- 手动框选页码在缺少字符级数字坐标时存在可信安全整段替换兜底。
- 单数字区域含“共 / 总 / 合计 / of / total”时推断为总页数。
- 初始视图使用基于真实 pageWrap 几何的居中算法，并在布局稳定后再次居中。

## 浏览器实机说明

尝试在当前容器中使用 Chromium + Playwright 访问本机测试服务时，被容器浏览器策略以 `ERR_BLOCKED_BY_ADMINISTRATOR` 阻止。因此本报告不声称完成真实浏览器交互回归；前端相关部分由语法、DOM、静态逻辑和已有自动化测试覆盖。
