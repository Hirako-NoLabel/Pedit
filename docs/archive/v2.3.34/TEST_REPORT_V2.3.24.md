# PDF 精准编辑器 v2.3.24 测试报告

## 本轮修复验证目标

1. 已识别到原页码时，优先修改原数字，而不是新增页码。
2. `第 / 页 / 共 / /` 等固定内容不得因兜底逻辑被整段重新绘制。
3. 原印刷页码和 PDF 页序不连续时，不得因“模板连续关系”阻止修改。
4. `{current}` / `{total}` 的目标数值必须来自用户批量设置，而不是 OCR 识别到的旧数字。
5. v2.3.22 的撤销 / 人工接管能力和 v2.3.23 的初始居中能力继续保留。

## 专项及相关回归

执行页码、人工接管、历史、框选、视觉微调等相关测试：

- 结果：**62 passed**

另执行 v2.3.24 新增专项 + 最近页码回归：

- 结果：**45 passed**

新增专项覆盖：

- 默认工作流是修改已有页码，不是新增。
- 只有 `allowBlankAdd` 明确开启时才进入新增路径。
- 格式化页码不存在整句 fallback。
- 模板连续关系不再作为阻断条件。
- v2.3.24 运行版本标记一致。

## 静态检查

- `node --check static/app.js`：**PASS**
- Python `py_compile`：**PASS**
  - `app.py`
  - `scan_engine.py`
  - `scan_revision_visual.py`
  - `scan_visual_match.py`
  - `ocr_subfield.py`
  - `high_fidelity.py`
  - `validation.py`
- JavaScript `$()` 引用的 DOM ID 缺失：**0**
- HTML 重复 ID：**0**

## 全量测试

执行：

```text
pytest -q -x --tb=short
```

结果：

- **78 passed**
- 第 79 个执行到的测试失败并停止。

首个失败来自旧测试 fixture：

```text
ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 24)
OSError: cannot open resource
```

当前测试环境为 Linux，不存在该 Windows 字体路径。因此不能据此声称剩余未运行测试全部通过；本报告只记录实际执行结果。

## 说明

本轮没有用户实际 96 页 PDF 文件本体，无法对用户原文件进行逐页渲染复测；修复依据现有代码回归、合成页码测试及用户截图所暴露的逻辑问题完成。建议实际验证时先运行少量页，确认 `第1页，共96页` 一类字段只替换数字，再执行全范围。
