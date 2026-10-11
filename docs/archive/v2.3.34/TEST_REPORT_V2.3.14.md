# TEST REPORT v2.3.14

## Scope

本轮仅新增“成品字复用”，并保留 v2.3.13 的删除、视觉微调、页码重编号、页面保护等行为。

## New behavior verified

- 已运行成功的扫描单字符会在视觉检查结果中输出背景透明的 `reusableGlyph` 资产。
- 资产仅包含最终字符 alpha / 前景色信息，不包含源位置纸张、水印、横线或表格背景。
- 后端能够接收 `reusableGlyph` 并走 `reusedFinishedGlyph` 路径，不再重新进行字体候选匹配。
- “原样粘贴”保留成品字尺寸与字形；“适配目标字符槽”仅做受限比例适配。
- 粘贴后仍重新执行目标位置旧字清理、页面像素保护、邻字碰撞检查。
- 当前 PDF 字库按字符保存最近一次成品，导入新 PDF 时自动清空。
- 复制参数 / 粘贴参数与成品字复制 / 粘贴互不冲突。

## Tests

### v2.3.14 + related regression subset

`14 passed`

包含：
- v2.3.14 成品字资产导出与复用
- reusableGlyph 从 app 到扫描 patch 引擎的透传
- v2.3.9 视觉微调
- v2.3.10 微调 UI
- v2.3.12 工作流

### Full pytest

`61 passed / 14 environment-limited failures`

14 个失败均来自既有 Windows 专用视觉/OCR测试：
- 多项测试固定引用 `C:/Windows/Fonts/arial.ttf` 等 Windows 字体，本环境为 Linux，Pillow 报 `cannot open resource`。
- 2 项 UI 扫描 OCR 用例在当前 OCR 环境没有得到 Windows 环境相同的中文识别行，因此出现 `StopIteration`。

这些失败与本轮成品字复用代码无直接关系。

### Syntax

- `python -m py_compile app.py scan_revision_visual.py`: PASS
- `node --check static/app.js`: PASS

## Known limits

- 当前成品字复用仅针对“单字符替换”开放，这是为了保证目标字符槽与页面保护边界可靠。
- 字库默认仅存在于当前 PDF 会话中，不跨文档持久化。
- “原样粘贴”在字号差异明显的位置可能不合适，应切换“适配目标字符槽”。
- 目标位置的旧背景仍由目标页面自身恢复，不会复制源位置背景；这是刻意的页面保护设计。
