# CHANGELOG_V2.3.6

## BUG-02 专项：统一同行数字视觉风格

### 修复

- 移除 v2.3.5 “取第一个可用 donor 数字”的不稳定策略。
- 新增目标行数字统计 profile：统一宽度、高度、灰度、stroke 与 edge softness。
- 对 `1 → 6/5/...`：存在同行其他数字时，目标数字宽度由非 `1` 数字的中位数决定。
- 同页目标字符 exemplar 改为严格同行策略；跨行字符不再直接成为视觉模板。
- 同一编辑字段中的数字替换共享同一个 style profile，减少位置差异导致的输出漂移。
- 在视觉指标中增加 `styleProfile`、`digitProfileCount`、`digitProfileCharacters`、`digitStrokeMetric`、`digitEdgeSoftnessMetric`、`exemplarPolicy`。

### 保留

- 字符级 diff 与最小修改区域。
- v2.3.5 的旧 `1` 完整擦除修复。
- OCR 字符单元中心定位。
- 目标行灰度取样原则。
- 表格线保护和局部背景修复。
