# v2.3.32 修改文件

- `scan_revision_visual.py`：新增同页同排完整数字片段查找与整组 RGBA 原生像素复用；稳定数字片段优先走 `600` 整组复用，而非 `6+0+0` 单字组合。
- `app.py`：版本号与临时工作目录升级至 v2.3.32。
- `static/index.html`：版本显示升级至 v2.3.32。
- `README.md`：版本说明升级至 v2.3.32。
- `tests/test_v2332_whole_fragment_reuse.py`：新增整组数字片段 1:1 复用专项测试。
- `tests/` 既有版本断言：同步升级至 v2.3.32。
- `start_windows.bat`：启动横幅版本同步升级至 v2.3.32，继续保持 UTF-8 BOM + CRLF。
- `CHANGELOG_V2.3.32.md`、`MODIFIED_FILES_V2.3.32.md`、`TEST_REPORT_V2.3.32.md`：本版记录与测试报告。
