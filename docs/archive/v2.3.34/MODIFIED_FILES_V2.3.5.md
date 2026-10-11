# MODIFIED_FILES_V2.3.5

最新截图复核继续修改 `scan_revision_visual.py`（旧 `1` 擦除、字符单元中心定位、目标行灰度）与 `tests/test_v235_bug02.py`（两项定向回归），并重新生成 `visual_results_v235/`。

本清单以用户提供的 v2.3.4 ZIP 解压目录为基线逐文件比较。

| 文件 | 类型 | 内容 |
|---|---|---|
| `app.py` | 修改 | 版本号更新为 2.3.5；业务逻辑未改 |
| `check_ocr_windows.bat` | 修改 | 自检版本号 |
| `README.md` | 修改 | v2.3.5 范围、扫描融合链路、测试和限制 |
| `scan_revision_visual.py` | 修改 | 整行上下文拟合、同行数字尺寸约束、同页 glyph 墨迹参考、最小扩展补丁、replacement 布局指标 |
| `scan_visual_match.py` | 修改 | 按同行数字墨迹宽高重建目标 glyph，分离边缘软化与核心不透明度，并记录参考尺寸 |
| `start_windows.bat` | 修改 | 启动版本号 |
| `static/index.html` | 修改 | 页面版本号 |
| `tests/test_v235_bug02.py` | 新增 | `100 → 600` 单字符、视觉几何、核心不透明度、同页 `6`、邻字不变及独立期望图回归 |
| `tests/generate_v235_bug02_evidence.py` | 新增 | 五倍率 before/after/diff 和 300% 对比生成器 |
| `tests/ui_regression.cjs` | 修改 | 页面版本断言更新；实际扫描编辑值改为 `LH-K-600` |
| `CHANGELOG_V2.3.5.md` | 新增 | 本版本变更记录 |
| `TEST_REPORT_V2.3.5.md` | 新增 | 完整测试、视觉指标、结论和限制 |
| `MODIFIED_FILES_V2.3.5.md` | 新增 | 本清单 |
| `visual_results_v235/` | 新增 | 虚构/合成 PDF、五倍率 PNG、300% 对比、指标及 UI 回归证据 |
| `visual_results/ui/failure.png` | 删除 | 清除 v2.3.4 遗留的旧失败截图，避免与本轮通过结果混淆 |

以下冻结核心文件与 v2.3.4 逐字节一致：`high_fidelity.py`、`ocr_subfield.py`、`scan_diff.py`、`scan_engine.py`、`static/app.js`、`static/styles.css`、`validation.py`、`requirements.txt`、`demo_fictional_scan.pdf`。其中 `high_fidelity.py` SHA-256 为 `257F596FC34C20021CED1E3ACDFB4F9D468368BCA495AF78E19EE823A95B3B36`。
