# v2.3.12 修改文件

- `static/index.html`
  - 每项微调独立复位按钮
  - 复制/粘贴参数按钮
  - 文字/图片删除入口
  - 删除预览/批量选择弹窗
  - 版本号

- `static/app.js`
  - 参数逐项复位
  - 全量参数复制/粘贴
  - 删除 edit 数据结构
  - 相同项扫描、复选、页范围筛选
  - 删除预览提交
  - 删除 edit 跳过普通文字 feasibility
  - 修订清单删除项展示

- `static/styles.css`
  - 复位按钮
  - 删除按钮
  - 删除匹配卡片/弹窗样式

- `app.py`
  - 图片 digest 暴露
  - 图片 pHash 相似匹配
  - 相同文字全量匹配
  - `/api/delete/matches`
  - 局部背景 inpaint 删除 patch
  - 删除 edit 的 preview/export 应用路径
  - v2.3.12 服务版本

- `tests/test_v2312_workflow.py`
  - v2.3.12 专项回归测试

- `tests/test_v2310_manual_tuning_ui.py`
- `tests/test_v239_manual_tuning.py`
  - 同步 v2.3.11 已扩大后的参数范围期望

- `README.md`
- `CHANGELOG_V2.3.12.md`
- `TEST_REPORT_V2.3.12.md`
- `MODIFIED_FILES_V2.3.12.md`
