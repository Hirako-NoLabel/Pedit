# v2.3.32

## 修改

- 修复稳定数字片段复用后大小不一致的问题。
- 对 `LH-K-100 -> LH-K-600` 这类同长度数字片段替换，继续保留 OCR 整串识别，但优先在同页同视觉行查找完整目标数字片段 `600`。
- 找到完整同排片段时，保存并复用整组 `600` 的 RGBA 原生像素、统一字符槽偏移、行高和内部字距，而不是把 `6`、`0`、`0` 三个单字分别紧裁后再组合。
- 整组片段复用默认只做平移，不重新选字体、不重新渲染、不逐字归一化、不单字缩放。
- 新增 `reusedWholeFragment`、`reusedFragmentText`、`fragmentPixelMode`、`fragmentExemplarPolicy` 等指标，方便检查是否走到整组 1:1 复用链路。

## 未改动

- Native Scan Renderer、页码数字槽、保存/基线、高清预览、bbox crop、修改记录双 Tab、Windows BAT 编码修复等既有稳定逻辑保持不变。
