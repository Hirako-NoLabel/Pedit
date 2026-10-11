# TEST_REPORT_V2.3.7

## 目标

按以下三项标准验证扫描文字局部替换：

1. 页面整体不被破坏；
2. 替换结果与同一行、同一字段附近文字视觉协调；
3. 不输出明显的白边、发虚、断笔、偏浅、粘连、字距突变等伪影。

所有新增视觉证据均来自虚构/合成测试 PDF。

## 已执行

### 1. Python 编译检查

- `scan_visual_match.py`: PASS
- `scan_revision_visual.py`: PASS
- `app.py`: PASS

### 2. v2.3.7 专项测试

`tests/test_v237_quality_gate.py`

结果：**6 passed**

覆盖：

- 同行 profile 包含 stroke / edge / density / contrast；
- 非目标像素保护为 0 违规；
- tight patch 明显小于整字段；
- replacement style / color / placement 指标有效；
- 行级离群样本被过滤；
- `app.analyze_scan_revision()` 只在质量门通过时返回可执行 scanrevision。

### 3. 兼容测试

执行全量 `pytest -q`：

- **39 passed**
- **14 failed**

14 个失败均属于当前 Linux 环境无法复现原 Windows 测试前提：

- 12 项 fixture 写死 `C:/Windows/Fonts/...`，Linux 无法打开对应字体；
- 2 项依赖原 Windows OCR 对 `visual_results/ui_scan.pdf` 的特定中文识别结果，本环境 Tesseract 未返回同一行。

未把这些环境失败计为产品回归，也未伪造 Windows 结果。

### 4. API 启动自检

`GET /api/health`：PASS

返回版本：`2.3.7`；Demo Mode：`false`。

## 虚构视觉证据

目录：`visual_results_v237/`

核心案例：

`LH-K-100 → LH-K-600`

300% 合成 ground-truth 对比结果：

- `qualityGatePassed`: true
- `preservationViolationPixels`: 0
- `neighbourOverlapPixels`: 0
- `color_score`: 99.3
- `replacement_style_score`: 92.4
- expected crop MAE @300%: 0.9759

视觉文件：

- `before_100.png` / `after_100.png`
- `before_200.png` / `after_200.png`
- `before_300.png` / `after_300.png`
- `expected_300.png`
- `diff_300.png`
- `comparison_300.png`

## 这版解决的重点

### 页面不破坏

- patch 内非目标像素强制回写原值；
- 页面级插入测试确认 overlay 外变化像素为 0；
- overlay 从“字符周围大块区域”收缩为实际变化 tight patch。

### 视觉协调

- 不再依赖任意第一个 donor；
- 行级几何统计使用稳健样本；
- 局部灰度/边缘优先使用目标附近数字；
- 实际输出色彩而非参数色彩参与评分。

### 伪影控制

- 邻字重叠超过阈值直接阻止；
- 质量门失败时不输出；
- alpha 合成黑度补偿降低“新字明显偏浅/浮在纸面上”的风险。

## 仍存在的客观限制

- 单张扫描图中，被旧黑字完全遮住的背景内容无法被真实观测，只能局部推断；
- 若目标行没有足够可靠的同类字符，style confidence 会降低并回退到字段上下文字体拟合；
- 不同扫描仪、JPEG 压缩、极低分辨率、严重倾斜或复杂重叠背景仍需在 Windows 实际样本中继续验收；
- 本报告不宣称对任意扫描字体均达到像素级不可区分。
