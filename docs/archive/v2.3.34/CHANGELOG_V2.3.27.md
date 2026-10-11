# CHANGELOG v2.3.27

## 扫描文字清晰度重构
- 新增 Native Scan Renderer v1：默认读取页面主扫描图真实像素/pt，按原生扫描 DPI 构建局部 patch。
- 移除替换字自动 blur 搜索结果向新字的传递；`blurRadiusPx` 默认固定为 0，源扫描柔度仅作为诊断值 `sourceBlurEstimatePx`。
- 移除旧版 `native_step` 的“降采样 -> NEAREST 放大”像素化链路。
- 字体替换候选改为 4x 超采样栅格后一次 Lanczos 降到目标原生像素尺寸。
- 新增实际清晰度指标与软质量门：sourceSharpness、replacementSharpness、sharpnessRatio、actualSharpnessScore。
- 保留成品字优先复用；默认“原样粘贴”保持 1:1，只有用户选择适配时才缩放。

## 视觉微调
- “扫描柔化”改为更直接的“清晰度（边缘软硬）”，范围 -100..100；0 为完全中性，不自动模糊。
- 所有微调滑杆增加左右方向标签，明确视觉结果。
- 折叠标题显示“自动 · 未调整”或“已调整 N 项”。
- 视觉微调默认折叠；人工接管、局部前后对比、图片高级设置也改为默认折叠。
- 后端保留旧 `softenPx` 兼容映射，旧保存进度仍可恢复。

## Windows / UI
- `start_windows.bat` 与 `启动编辑器.bat` 改为 UTF-8 BOM + CRLF。
- 依赖检查拆成两条较短的 Python import 命令，降低 CMD 误解析风险。
- 顶部工具栏按钮禁止中文自动换行，空间不足时工具栏内部横向滚动，不再向下溢出按钮框。

## 保持不变
- v2.3.25 数字槽页码逻辑不变。
- v2.3.26 单页渲染、异常页跳转、保存进度、保存并继续编辑/基线、导出选择、高清预览与高清 bbox crop 继续保留。
