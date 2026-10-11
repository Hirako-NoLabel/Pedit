# v2.3.25 修改文件

- `static/index.html`
  - 页码弹窗重构为“数字槽批量页码编辑”。
  - 新增当前页/总页数角色选择与递增步长。
  - 总页数改为固定填充值的主流程。
- `static/harness.html`
  - 同步 v2.3.25 测试界面。
- `static/app.js`
  - 新增数字槽角色解析、当前页序列计算、固定总页数、按角色过滤原位数字替换。
  - 扫描结果展示改为“识别数字 → 目标数字”。
  - 动态 C/D… 页码位置同步支持数字角色。
- `app.py`
  - 运行版本号升级到 2.3.25。
- `start_windows.bat`
  - 启动提示升级到 v2.3.25。
- `tests/test_v2325_numeric_slot_page_numbers.py`
  - 新增数字槽 UI、前端目标值逻辑、中文双数字子区域和版本标记测试。
- `README.md` / `CHANGELOG_V2.3.25.md` / `TEST_REPORT_V2.3.25.md`
  - 更新说明与测试结果。
