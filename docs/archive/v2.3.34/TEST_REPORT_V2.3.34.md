# v2.3.34 测试报告

- `node --check static/app.js`：通过。
- Python `py_compile`（app、扫描渲染、OCR、保真模块）：通过。
- DOM ID：248 个，无重复；JS 选择器均有对应元素。
- pytest：39 passed，5 warnings。覆盖 v2.3.34 连续笔画/清晰度、稳定数字片段、整段/1:1 复用、Native Scan Renderer、页码槽、保存/历史、高清预览和质量门。
- 警告均为 Pillow 未来版本的 `mode` 参数弃用提示，不影响当前运行结果。
