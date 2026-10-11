# PDF 精准编辑器 v2.3.22 测试报告

## 结论

本轮新增的“修改清单可逆”“所有批量页码对象可人工删除/修改”“页码人工接管”已完成专项回归与浏览器交互验证。

## 静态 / 语法检查

- `node --check static/app.js`：PASS
- Python `py_compile`：PASS
  - `app.py`
  - `scan_engine.py`
  - `scan_revision_visual.py`
  - `scan_visual_match.py`
  - `ocr_subfield.py`
  - `high_fidelity.py`
  - `validation.py`
- DOM ID 检查：
  - JS 引用但 HTML 缺失：0
  - HTML 重复 ID：0

## 专项及相关回归

执行 v2.3.22、v2.3.21、页码 v2.3.17～v2.3.20、历史、成品字、删除流程和人工微调等相关测试：

**60 passed**

覆盖重点包括：

- 修改清单存在“撤销选中修改 / 回到选中修改前”入口
- 每条修改存在“定位 / 撤销此项 / 回到此项前”
- 批量页码 `text` 类型也被识别为一等可编辑页码对象
- 人工移动页码 `text` 后转换为 `page-number-replace`，保留原区域作为清理源区域
- 人工接管页/位置会从后续批量页码构建结果中剔除
- 页码人工接管状态、页面级删除入口存在
- 当前版本号与启动脚本一致

## 浏览器交互烟测

使用系统 Chromium 在静态 UI harness 中实际执行了以下操作链：

1. 注入一个与真实批量页码相同结构的 `type:'text' + pageNumberSlot` 对象。
2. 页面成功出现可点击页码生成框。
3. 单击后右侧识别为“页码字块”，总页数内容可读取和编辑。
4. 点击“恢复此处原文”后，对应编辑对象从状态中移除。
5. 修改清单创建两条修改后，“撤销此项”只移除目标项。
6. 复选后“撤销选中修改”可批量移除选中项。
7. “回到此项前”验证：C → D 两次修改，回到 D 之前后仅保留 C。
8. 人工接管前，空白页码模板会生成 1 个候选编辑；接管后生成数变为 0，并标记 `manual-takeover`。
9. 额外验证页码 `text` 对象拖动后转为 `page-number-replace`，`outputBbox` 更新到新位置。
10. 浏览器烟测未出现 JavaScript page error / console error。

## 本地 HTTP 服务检查

- `/`：正常返回 v2.3.22 页面
- `/api/health`：返回 `version: 2.3.22`

## 全量测试

执行：

`pytest -q -x --tb=short`

结果：

- 前 **73 项通过**
- 第 74 项在旧测试 `tests/synthetic_fixture.py` 失败
- 原因：测试硬编码 Windows 字体路径 `C:/Windows/Fonts/arial.ttf`
- 当前测试环境为 Linux，Pillow 报 `OSError: cannot open resource`

因此没有宣称全量测试全部通过；该停止点不是 v2.3.22 本轮前端交互改造产生的功能异常。
