# v2.3.26 修改文件

## 运行代码

- `app.py`
  - 版本升级到 2.3.26。
  - 页面与修改预览最高渲染倍率提高到 8×。
  - 新增保存进度、恢复进度、提交基线、恢复基线、高清 region crop 接口。
  - session 支持从已保存 progress 在本地服务重启后重新挂载。
- `static/app.js`
  - 动态高清预览。
  - 单页渲染与跳下一异常页。
  - 修改清单状态筛选与已撤销记录。
  - 导出选择体系。
  - 保存进度 / 保存并继续编辑 / baseline 历史恢复。
  - 6× 成品字 crop、高清局部编辑 crop。
  - 图片尺寸 / DPI 提示。
  - 编辑对象元数据补齐。
- `static/index.html`
  - 新增保存按钮、预览质量选择、清单筛选、单页渲染、导出选择、图片 DPI 信息区。
  - 版本号升级到 2.3.26。
- `static/styles.css`
  - 新增 v2.3.26 控件、状态标签、导出选择与 DPI 警告样式。
- `static/harness.html`
  - 测试界面版本号升级。
- `start_windows.bat`
  - 启动提示版本号升级。

## 测试

- `tests/test_v2326_save_render_hd.py`
  - 新增 v2.3.26 专项测试。
- `tests/test_v2315_version_history.py` 等旧回归测试
  - 仅把“当前运行版本号”硬编码断言从 2.3.25 同步到 2.3.26；功能断言不变。
- `tests/ui_regression.cjs`
  - UI 版本标题断言同步到 2.3.26。

## 文档

- `README.md`
- `CHANGELOG_V2.3.26.md`
- `MODIFIED_FILES_V2.3.26.md`
- `TEST_REPORT_V2.3.26.md`
