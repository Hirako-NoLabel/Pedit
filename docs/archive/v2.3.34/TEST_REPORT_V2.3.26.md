# PDF 精准编辑器 v2.3.26 测试报告

## 1. 语法与 DOM

- `node --check static/app.js`：PASS。
- `python -m py_compile app.py scan_engine.py scan_revision_visual.py scan_visual_match.py ocr_subfield.py high_fidelity.py validation.py`：PASS。
- HTML ID 数量：241。
- HTML 重复 ID：0。
- JavaScript `$('#id')` 引用但 HTML 缺失的 ID：0。

## 2. v2.3.26 专项测试

执行：

`pytest -q tests/test_v2326_save_render_hd.py`

结果：**5 passed**。

覆盖：

- 保存进度 / 保存并继续编辑 / baseline / resume 接口标记；
- 单页渲染与下一异常页流程；
- 自动 / 标准 / 高清预览 UI；
- 8× 后端渲染上限与 6× 页面渲染；
- 高清 region crop；
- 导出选择按钮；
- 图片 DPI 提示；
- DOM ID 完整性；
- v2.3.25 数字槽“默认不新增”逻辑仍存在；
- 修改对象 `objectId / batchId / role` 元数据。

## 3. 关键回归

执行 v2.3.14～v2.3.26 的成品字、版本历史、页码模板、页码识别、位置锚点、重叠保护、人工控制、人工接管、数字槽与 v2.3.26 专项测试。

结果：**62 passed**。

说明：首轮运行旧测试时曾有 4 个失败，均为旧测试硬编码要求 UI/服务端仍显示 `v2.3.25`。将这些“当前运行版本号”断言同步到 2.3.26 后，功能断言全部通过。

## 4. 真实本地 HTTP 运行验证

使用合成单页 PDF 启动本地服务并实际请求接口：

- `/api/health`：返回 `version=2.3.26`，PASS。
- `/api/open`：成功创建 session，初始 `baselineId=0`。
- `/api/page?...&scale=6`：612×792 pt 页面实际返回 **3672×4752 px**，证明高倍页面渲染生效。
- `/api/region-crop`：170×35 pt bbox、6× 实际返回 **1020×210 px**，PASS。
- `/api/save-progress`：成功生成 `editor_progress.json`。
- `/api/commit-baseline`：实际写入 1 项自由文字修改并生成 `baseline_1.pdf`。
- 打开 `baseline_1.pdf` 验证新增文本存在：PASS。
- `/api/baseline/restore`：从 baseline #1 恢复 baseline #0：PASS。
- 完全停止并重新启动本地服务后调用 `/api/resume-progress`：成功从磁盘重新挂载 session，恢复 `baselineId=0`、预览模式 `high` 与原文件名：PASS。

## 5. 全量 pytest

执行：

`pytest -q -x --tb=short`

结果：**前 91 项通过**，随后停止于：

`tests/test_v234_regression.py::test_10_11_18_20_background_and_no_mark[False-True]`

失败原因仍为旧合成夹具固定读取：

`C:/Windows/Fonts/arial.ttf`

当前测试环境为 Linux，Pillow 报：

`OSError: cannot open resource`

该错误发生在测试 PDF/图片夹具生成阶段，并非 v2.3.26 的页面渲染、保存基线或数字槽逻辑断言失败。未执行到的后续测试不计为通过。

## 6. 浏览器自动化限制

当前 Linux 环境没有安装 Node `playwright` 模块，因此没有虚报 `tests/ui_regression.cjs` 浏览器自动化为通过。本轮使用语法、DOM、pytest 与真实 HTTP 接口运行替代验证；Windows 端仍建议打开实际扫描 PDF 做一次 100% / 150% / 200% / 300% 视觉复核。

## 结论

v2.3.26 的核心新增链路已通过专项、关键回归与真实服务端运行验证；v2.3.25 的页码数字槽规则保持不变。全量测试仍受历史 Windows 字体路径夹具阻塞，已明确记录，不计为产品回归失败。
