# TEST REPORT v2.3.9

## 本轮目标

在 v2.3.8 自动视觉匹配基础上增加人工微调，同时继续满足：只改目标区域、非目标内容不被破坏、明显邻字碰撞必须阻止。

## 专项验证

执行：

```text
pytest -q tests/test_v239_manual_tuning.py tests/test_v238_gate_behavior.py tests/test_v237_quality_gate.py tests/test_v236_line_style_profile.py
```

结果：**17 passed**。

其中 v2.3.9 新增专项测试覆盖：

1. 手动参数默认值与越界 clamp。
2. 大小/宽度/位置/深浅/笔画/柔化/清理/融合参数成功进入 patch 引擎。
3. 人工微调后 `preservationViolationPixels == 0`。
4. 人工微调后邻字重叠仍受硬门约束。
5. `app.py` 正确将 `visualAdjust` 传递到扫描 patch。

## 默认行为兼容验证

在同一 Linux 合成扫描样本执行：

`LH-K-100 → LH-K-600`

分别使用原 v2.3.8 与 v2.3.9 默认参数生成 patch：

```text
v2.3.8 SHA-256  06be490435fd5af1c40e8d5a7b2a216aca749e4058eeed69b0aad13dffdd42c8
v2.3.9 SHA-256  06be490435fd5af1c40e8d5a7b2a216aca749e4058eeed69b0aad13dffdd42c8
changed pixels: 1772 / 1772
overlay bbox: [126.5, 113.0, 136.5, 128.0] / identical
```

因此：**未进行人工微调时，v2.3.9 不改变该已验证 v2.3.8 默认扫描结果。**

## 全量 pytest

在加入最后一项字体候选专项测试前完成的一次全量运行为：**47 passed / 14 failed**。新增字体候选专项测试已单独通过；随后再次全量运行在当前会话超时，因此不虚报新的全量总数。

14 个失败均来自旧测试的环境依赖：

- 多项测试写死 `C:/Windows/Fonts/arial.ttf`，Linux 无法加载；
- 两项真实 UI/OCR 测试在当前 OCR 结果中找不到预期 Windows 样本字段而 `StopIteration`。

未把这些环境限制计为通过。

## 静态与服务烟测

- `python -m py_compile app.py scan_revision_visual.py`：通过。
- `node --check static/app.js`：通过。
- 本地 HTTP 首页成功加载并包含“视觉微调”面板。
- `/api/health` 在新进程返回版本 `2.3.9`。

## Windows 建议回归

重点用用户现有样本测试同一字段：

`LH-K-100 → LH-K-600`

操作顺序建议：

1. 先保持全部参数为自动，运行一次。
2. 若新 `6` 偏宽：只调“宽度”。
3. 若大小不协调：调“大小”。
4. 若偏浅/偏黑：调“深浅”。
5. 若笔画过细/过粗：调“笔画”。
6. 若边缘太锐：少量增加“扫描柔化”。
7. 若旧 `1` 有残影：逐步提高“旧字清理”。
8. 若清理边界有硬边：少量增加“背景边缘融合”。
9. 每次调整后点击“应用微调并重新预览”。

如果水印、横线附近出现风险，应优先降低“旧字清理”，而不是继续增强。
