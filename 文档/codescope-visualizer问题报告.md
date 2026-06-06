# CodeScope visualizer 问题报告

## 问题概述

visualizer 模块存在两个问题。

---

## 问题1：Radar 图维度不匹配崩溃

| 项目 | 内容 |
|------|------|
| **错误信息** | `ValueError: x and y must have same first dimension, but have shapes (5,) and (4,)` |
| **位置** | [visualizer.py L137](file:///E:/PKB/codescope/visualizer.py#L137) |
| **根因** | `values = [_get_scores(item)[key] for key in DIMENSIONS[:-1]]` 只取前3个维度，但 `angles` 按4个维度生成 |
| **建议修复** | 去掉 `[:-1]`，改为 `values = [_get_scores(item)[key] for key in DIMENSIONS]` |

---

## 问题2：中文字体 Glyph 缺失警告

| 项目 | 内容 |
|------|------|
| **警告信息** | `UserWarning: Glyph xxx missing from font(s) DejaVu Sans` |
| **位置** | [visualizer.py](file:///E:/PKB/codescope/visualizer.py) 开头 |
| **根因** | matplotlib 默认字体不支持中文字符 |
| **建议修复** | 在 `import matplotlib.pyplot as plt` 后添加：
```python
import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
```

---

## 依赖清单

已在 [requirements.txt](file:///E:/PKB/codescope/requirements.txt) 明确列出：
```
matplotlib>=3.7.0
```
安装命令：`pip install -r requirements.txt`

---

## 修复简要汇报

已按问题报告完成修复：

1. Radar 图维度不匹配问题已修复
   - 将 `values = [_get_scores(item)[key] for key in DIMENSIONS[:-1]]` 改为使用完整 `DIMENSIONS`
   - 现在雷达图的角度数量和分数数量一致

2. 中文字体 Glyph 缺失警告已处理
   - 在 `visualizer.py` 中添加 Matplotlib 中文字体配置
   - 优先使用 `Microsoft YaHei`、`SimHei`、`WenQuanYi Micro Hei`
   - 同时设置 `axes.unicode_minus = False`，避免负号显示异常

3. 额外同步修复
   - `visualizer.py` 默认读取 `scores.json`
   - 默认输出目录统一为 `output/`
   - 已通过 `python -m py_compile visualizer.py` 语法检查
