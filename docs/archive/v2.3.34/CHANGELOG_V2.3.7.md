# CHANGELOG_V2.3.7

## 扫描文字视觉质量门

- 新增 `qualityGatePassed`，扫描替换必须同时满足页面保护、邻字不重叠、几何、色彩和局部扫描风格阈值。
- 质量门失败时 `analyze_scan_revision()` 返回 blocked，不再继续导出明显不协调结果。

## 页面保护

- 非目标像素在 raster patch 中强制恢复为原始像素。
- 新增 `preservationViolationPixels`、`suppressedNonTargetChanges`。
- 最终 PDF overlay 改为 tight patch，只覆盖实际变化区域及极小边界。
- 保留表格长线保护；新字符与未修改邻字碰撞时直接阻止输出。

## 局部风格匹配

- 行级数字 profile 新增离群过滤。
- 几何统计使用同行可靠数字稳健中位数。
- 灰度、边缘软化、曝光优先使用目标字段附近数字。
- 新增 `digitInkDensityMetric`、`digitContrastMetric`、`styleConfidence`。
- 新字符生成新增 stroke / blur / 微小宽高候选搜索。
- 新增 `replacement_style_score`、`replacementStrokeMetric`、`replacementEdgeSoftnessMetric`、`replacementInkDensityMetric`。

## 黑度修复

- 修复“参数 RGB 看起来正确，但 alpha 合成后实际字符仍偏浅”的问题。
- 根据核心 alpha 和局部背景反解前景色，使最终实际输出黑度接近同行扫描文字。
- 新增 `foregroundCompensationRGB`、`actualForegroundRGB`、`color_score`。

## 版本

- UI、API、启动脚本版本更新为 v2.3.7。
