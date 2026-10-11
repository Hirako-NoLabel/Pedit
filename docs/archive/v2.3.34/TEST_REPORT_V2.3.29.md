# v2.3.29 测试报告

## 通过

- `node --check static/app.js`
- Python `py_compile`：`app.py`、渲染、OCR、验证模块
- DOM ID 检查：247 个 ID，0 个重复；JavaScript 选择器均存在对应 ID
- v2.3.29 专项与相关回归：43 passed
  - 顶部顺序与短文案
  - 不再存在“修改历史”“修改清单”的独立顶部入口
  - 修改记录的两 Tab 和原有操作绑定
  - 保存并编辑、批量页码、导出绑定
  - Native Scan Renderer、清晰度、页码数字槽、保存进度/高清预览、基线回退
- Windows x64 免安装版：在独立端口 `9876` 启动后，`/api/health` 返回 `version: 2.3.29`，并报告 PyMuPDF 1.28.2 与内置 RapidOCR 可用。

## 环境说明

扫描图像夹具原先固定使用 Linux Liberation 字体路径；已调整为优先 Linux 字体、否则使用 Windows Times/Arial，不改变生产渲染代码。
