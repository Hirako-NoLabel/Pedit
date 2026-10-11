# TEST REPORT v2.3.17

## 本轮目标

重做批量页码编辑：由“自动猜页码”改为“用户先指定 1～2 个页码位置模板，再逐页修改/新增”。

覆盖重点：

- 位置 A / B 两个模板位；
- `{current}` / `{total}` / `{pdfpage}` 模板变量；
- 当前页、当前/总页数、中文与自定义格式；
- 总页数按范围 / PDF 总页数 / 手动输入；
- 不同页面旧页码文字不同但位置相同的定位；
- `Page 5 of 12` 等字段拆成 current / total 数字子字段；
- 空白模板位置新增页码；
- 扫描页空白位置透明 PNG 页码渲染；
- 逐页 feasibility + 逐页 preview 渲染；
- 单位置失败不阻断后续页面；
- 页码批量操作作为一个历史版本节点保存。

## 专项 / 回归测试

执行：

```text
pytest -q \
  tests/test_v2317_page_number_templates.py \
  tests/test_v2311_features.py \
  tests/test_v2315_version_history.py \
  tests/test_v2316_tune_inputs_and_docglyph_priority.py \
  tests/test_v2314_finished_glyph_reuse.py \
  tests/test_v239_manual_tuning.py
```

结果：

**21 passed**

## 语法 / 编译检查

- `node --check static/app.js`：PASS
- `python -m py_compile app.py scan_engine.py scan_revision_visual.py scan_visual_match.py ocr_subfield.py high_fidelity.py validation.py`：PASS
- 前端 JS 引用的 DOM ID 与 `index.html` 对照：0 个缺失，0 个重复 ID。

## 全量测试说明

执行 `pytest -q -x --tb=short` 时：

- 前 **41 项通过**；
- 随后停止在已有 Windows 专用测试夹具：`tests/synthetic_fixture.py` 写死 `C:/Windows/Fonts/arial.ttf`；当前 Linux 测试环境无法打开该字体资源。

因此本报告不声明全量测试全部通过。该首个失败属于测试环境差异，不是 v2.3.17 页码模板专项测试失败。
