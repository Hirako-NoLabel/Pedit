# v2.3.29 修改文件

- `static/index.html`：工具栏重排、短文案、统一修改记录弹窗与两个 Tab。
- `static/app.js`：统一入口和 Tab 切换；复用原有修改清单、历史版本、保存基线和导出函数。
- `static/styles.css`：统一修改记录 Tab 布局样式。
- `app.py`：版本标识和临时工作目录升级至 v2.3.29。
- `tests/test_v2329_revision_records_toolbar.py`：新增本轮专项回归测试。
- 既有版本/跨平台字体测试：更新版本断言，并使扫描夹具在 Windows 与 Linux 都可运行。
- `build_portable_windows.bat`：Windows x64 免安装构建脚本。
- `README.md`：使用说明与免安装版说明。
