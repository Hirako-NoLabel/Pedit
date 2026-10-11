# v2.3.33 修改文件

- `scan_revision_visual.py`：为稳定数字片段增加独立宽度适配策略，绕开普通输入字形 4% 保护；回退时仅允许等比例整体缩放。
- `tests/test_v2333_stable_fragment_width_policy.py`：新增稳定片段宽度策略专项测试。
- `app.py`、`static/index.html`、`static/app.js`：版本标识升级至 v2.3.33。
- `README.md`：版本说明更新。
