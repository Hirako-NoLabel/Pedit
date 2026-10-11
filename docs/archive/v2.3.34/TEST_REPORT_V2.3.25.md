# PDF 精准编辑器 v2.3.25 测试报告

## 本轮目标

验证新的“数字槽”页码工作流不会把 OCR 识别值当成目标值，并且能够分别处理当前页序列与固定总页数，同时保持此前的页码人工接管、撤销和框选能力。

## 已执行检查

### 1. v2.3.25 新增专项

`tests/test_v2325_numeric_slot_page_numbers.py`

结果：**4 passed**。

覆盖：
- 数字槽 UI 与角色选择；
- 当前页起始数字 + 步长；
- 总页数固定用户输入；
- 中文 `第57页，共96页` 拆分为 current / total 两个真实数字子区域。

### 2. 页码与人工控制相关回归

执行 v2.3.11、v2.3.14-v2.3.25 相关页码、历史、手动控制测试。

结果：**61 passed**。

### 3. 语法与 DOM

- `node --check static/app.js`：PASS
- Python `py_compile`：PASS
- JavaScript 引用但 HTML 缺失的 ID：**0**
- HTML 重复 ID：**0**

### 4. 本地服务启动

启动 v2.3.25 后请求 `/api/health`：PASS。
返回版本 `2.3.25`，OCR 状态正常。

### 5. 全量 pytest

执行：`pytest -q -x --tb=short`

结果：**前 86 项通过**，随后在旧测试 `tests/test_v234_regression.py` 停止。

停止原因：旧合成测试固定读取 Windows 字体 `C:/Windows/Fonts/arial.ttf`，当前测试环境为 Linux，Pillow 报 `OSError: cannot open resource`。该失败发生在测试夹具生成阶段，不是 v2.3.25 数字槽页码逻辑断言失败。未执行到的后续测试不计为通过。

## 结论

本轮新增数字槽逻辑及其相关回归测试均通过。当前页目标值由用户配置的序列计算，总页数由用户固定输入；OCR 只用于定位原数字。对未能可靠定位数字的页面，仍走重新框选/人工接管，不做整句重绘。
