# TEST REPORT v2.3.11

## 本轮专项验证

- JavaScript `node --check static/app.js`：PASS。
- Python `py_compile app.py scan_revision_visual.py`：PASS。
- v2.3.11 + 视觉门/行风格相关测试：**16 passed**。
- 新建 3 页电子 PDF（原显示 `Page 5 / Page 6 / Page 7`）验证页码检测：3/3 正确定位原数字 token。
- 端到端原位页码替换：`Page 5,6,7 -> Page 1,2,3`，3 页均走原内容流高保真修订，导出文本验证 PASS。

## 旧测试说明

抽取 v2.3.10 旧测试时，有两类非回归失败：
1. 旧测试把 v2.3.10 的 UI 范围（如 60~140、edgeBlend 0~100）写成固定断言，本版按需求扩大范围，因此这些旧断言应更新。
2. 部分视觉测试写死 `C:/Windows/Fonts/arial.ttf` / 宋体路径；当前 Linux 环境不存在 Windows 字体，属于环境限制。

## 功能验收

1. 导入默认适应宽度：PASS（state/open 初始化均为 `fit-width`，loadPage 调用 applyViewMode(true)）。
2. 背景边缘融合双向：PASS（UI/后端 -100~+100）。
3. 其他微调参数自由度：PASS（前后端限制一致）。
4. 应用微调运行状态：PASS（主页面转圈 + 百分比 + 进度条，跟随原五阶段）。
5. 原页码批量修改：PASS（识别现有 token 后原位替换；未识别不新增）。

## 已知限制

- 页码自动识别采用保守规则，默认只在页面顶部/底部 20% 区域识别常见页码形式；复杂装饰页码或纯图片 OCR 失败时会跳过，不会盲目新增。
- 扫描 PDF 页码替换的最终视觉质量仍取决于 OCR 字符坐标与扫描字形匹配，可继续使用现有视觉微调。
