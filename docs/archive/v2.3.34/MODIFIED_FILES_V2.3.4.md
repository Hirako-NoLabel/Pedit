# MODIFIED_FILES_V2.3.4

根据输入 ZIP 实际逐文件比较生成；不把未修改文件列为变更。

| 文件 | 类型 | 内容 |
|---|---|---|
| `app.py` | 修改 | OCR 字段数据、补丁应用/重叠检查、Demo 默认关闭、版本与中文搜索层 |
| `CHANGELOG_V2.3.4.md` | 新增 | 版本交付文档 |
| `check_ocr_windows.bat` | 修改 | 自检版本号 |
| `ocr_subfield.py` | 修改 | 完整行结构化分段、重复字段偏移、真实几何、手动区域 |
| `README.md` | 修改 | v2.3.4 使用、Demo 开关、测试及明确限制 |
| `scan_diff.py` | 新增 | 新增：严格坐标匹配与字符差异规划 |
| `scan_engine.py` | 修改 | 字符排序及估算坐标标识，OCR 引擎保留 |
| `scan_revision_visual.py` | 修改 | 字符局部补丁、墨迹边界校验、长线保护、背景/采样/指标 |
| `scan_visual_match.py` | 新增 | 新增：源字视觉参数候选拟合 |
| `start_windows.bat` | 修改 | 启动版本号 |
| `static/app.js` | 修改 | 按点选择、整行入口、视图模式/坐标、质量提示、重做后重新校验与预览请求代次 |
| `static/index.html` | 修改 | 整行与适应整页按钮、版本文案、favicon |
| `static/styles.css` | 修改 | 页面布局参与实际缩放尺寸；净预览按钮 hover 可读性 |
| `TEST_REPORT_V2.3.4.md` | 新增 | 版本交付文档 |
| `tests/generate_visual_evidence.py` | 新增 | 新增多倍率 before/after/diff 与像素证据生成器 |
| `tests/synthetic_fixture.py` | 新增 | 新增确定性虚构扫描材料生成器 |
| `tests/test_v20_revision_mode.py` | 修改 | 旧标记/清单预期明确放到 Demo Mode 验证 |
| `tests/test_v21_field_isolation.py` | 修改 | 默认模式不出现标记的预期 |
| `tests/test_v22_synthetic_visual_match.py` | 修改 | 默认无标记；保留字高及左右未改字符回归 |
| `tests/test_v234_regression.py` | 新增 | 新增字符、背景、原字残留、电子/图片及完整行回归 |
| `tests/ui_regression.cjs` | 新增 | 新增真实浏览器操作/净预览/导出回归 |

新增 `MODIFIED_FILES_V2.3.4.md` 本清单。`visual_results/` 为新增测试交付资料，未计入代码清单。

旧版报告不再混放于新版根目录：TEST_REPORT_V2.3.3.md。原件保留于原版 ZIP。

`high_fidelity.py`、`validation.py`、`requirements.txt`、自带虚构 PDF 及未列出的旧测试未修改。
