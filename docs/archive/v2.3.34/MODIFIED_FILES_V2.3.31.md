# v2.3.31 修改文件

- `scan_diff.py`：新增等长数字修改的稳定片段扩展规则；`LH-K-100 -> LH-K-600` 自动规划为 `100 -> 600`。
- `scan_revision_visual.py`：输出稳定片段相关指标，供预览/测试确认实际重建范围。
- `static/app.js`：版本升级，并保留 v2.3.30 保存进度兼容回退。
- `static/index.html`：版本升级。
- `app.py`：版本与工作目录升级到 v2.3.31。
- `start_windows.bat`、`build_portable_windows.bat`：版本升级。
- `tests/test_v2331_stable_numeric_fragment.py`：新增稳定数字片段专项测试。
- 相关旧回归测试：按 v2.3.31 新策略更新预期，同时继续保留单字符 1:1 成品字复用测试。
- `README.md`：版本升级。
