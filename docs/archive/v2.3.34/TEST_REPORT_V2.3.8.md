# TEST_REPORT_V2.3.8

## 修复目标

修正 v2.3.7 在实际扫描页中频繁把“软视觉评分不足”当成“运行失败”的问题。

## 根因

1. v2.3.7 将页面保护风险与视觉评分放在同一个 `qualityGatePassed` 中；任一软评分稍低都会由 `app.py` 直接返回 `blocked`。
2. 只要新 glyph 比 OCR 字符单元略宽，即使只缩放约 5%~8%，也会写入“新字符受可用宽度约束”的质量不足警告。
3. 实际用户需要先看到预览再判断视觉协调，软评分不应阻止内部测试预览。

## v2.3.8 行为

- `hardSafetyPassed`：页面保护 + 邻字不重叠。失败仍阻止生成。
- `visualQualityPassed`：几何 + 色彩 + 局部扫描风格。失败只提示，不再报“运行失败”。
- `qualityGatePassed` 仍保留为综合指标，便于诊断，但不再直接决定是否可预览。
- 宽度适配因子 >= 0.84 时仅记录 `widthConstraintNote`，不显示质量不足；< 0.84 时显示软提示；< 0.70 仍硬阻止。

## 测试

运行：

`pytest -q tests/test_v238_gate_behavior.py tests/test_v237_quality_gate.py tests/test_v236_line_style_profile.py`

结果：**12 passed**。

另运行旧 v2.3.4 回归：**14 passed / 9 failed**。9 个失败均来自测试固定依赖 `C:/Windows/Fonts/arial.ttf` 的 Linux 环境限制，不是本轮逻辑断言失败。

旧 v2.3.5 BUG-02 测试：1 passed / 5 environment-limited failures，其中 3 个依赖 Windows 字体，2 个依赖当前 Linux 环境无法复现的中文 OCR 行。

## 预期用户体验

以前：

`视觉匹配质量不足 -> qualityGatePassed=false -> 运行失败`

现在：

`硬安全通过 + 软视觉不足 -> 正常生成预览 + 给出放大检查提示`

只有页面保护违规、邻字明显重叠、严重越界等会继续阻止运行。
