# 洪锋烨Worklog

### 脚本目录调整

- 保留 `engine.py` 在根目录作为唯一入口。
- 将真正实现脚本移动到 `codescope/scripts/`。
- `engine.py` 现在指向：
  - `scripts/tracker.py`
  - `scripts/analyzer.py`
  - `scripts/scorer.py`
  - `scripts/visualizer.py`
- 脚本继续通过 `config.json` 读取路径配置。

### 评分规则

- 新建 `评分规则.md`，记录 CodeScope 的四维评分方案。
- 评分总分为 `0-100`。
- 四个维度为：
  - 关注度
  - 技术先进性
  - 配置门槛与产品形态
  - 生态开放性
- 默认权重为 `25 / 30 / 30 / 15`。

### scorer.py

- 新建并完善 `scorer.py`。
- 支持读取 `analysis.json`。
- 输出 `scores.json`。
- 将评分字段对齐组员的接口契约：
  - `repo`
  - `stars`
  - `tech_stack`
  - `product_form`
  - `install_complexity`
  - `doc_completeness`
  - `readme_length`
- 输出格式使用 `0-100` 分制。
- 让 `scorer.py` 可被 `engine.py` 无参数调用：
  - 默认输入：`analysis.json`
  - 默认输出：`scores.json`
- 新增从 `config.json` 读取 `scoring_weights` 的能力。
- 权重会自动归一化，用户不需要保证总和等于 `100`。

### visualizer.py

- 新建并完善 `visualizer.py`。
- 支持读取 `scores.json` 并生成图表。
- 默认输出目录改为 `output/`，与 README 和 `engine.py` 保持一致。
- 修复 Radar 图维度不匹配问题。
- 添加 Matplotlib 中文字体配置，减少中文 Glyph 缺失警告。
- 当前图表输出包括：
  - `top_scores_bar.png`
  - `setup_vs_total_scatter.png`
  - `dimension_comparison.png`
  - `top5_radar.png`

### config.json

- 新增 `scoring_weights` 配置项。
- 用户可以通过修改权重，让排序更贴近自己的需求。
- 新增 `paths` 配置项。
- 生成文件路径现在由 `config.json` 统一管理：
  - `data/known_competitors.json`
  - `data/raw_data/`
  - `data/analysis.json`
  - `data/scores.json`
  - `output/`
- 已将 `github_token` 保持为空，避免把个人 Token 写进代码变更记录或补丁。
- 默认配置：

```json
"scoring_weights": {
    "attention": 25,
    "tech_advancement": 30,
    "setup_product": 30,
    "ecosystem_openness": 15
}
```

### README.md

- 将评分描述从“五维评分”统一为“四维评分”。
- 新增“自定义评分权重”说明。
- 说明用户可以在 `config.json` 中调整 `scoring_weights`。
- 补充四个权重字段的含义和适用场景。
- 新增“自定义文件路径”说明。
- 更新目录结构，将生成数据统一说明为 `data/` 下的文件。

### 路径配置化

- 将生成文件路径从脚本硬编码改为由 `config.json` 统一管理。
- 修改 `codescope/tracker.py`：
  - 默认写入 `data/known_competitors.json`
  - 默认下载 README 到 `data/raw_data/`
  - 保留原有搜索、过滤和下载逻辑
- 修改 `codescope/analyzer.py`：
  - 默认读取 `data/known_competitors.json`
  - 默认输出 `data/analysis.json`
  - 保留原有特征提取逻辑
- 修改 `codescope/scorer.py`：
  - 默认读取 `data/analysis.json`
  - 默认输出 `data/scores.json`
- 修改 `codescope/visualizer.py`：
  - 默认读取 `data/scores.json`
  - 默认输出到 `output/`
- 修改 `codescope/.gitignore`：
  - 新增忽略 `data/`

### visualizer 问题报告

- 阅读 `codescope/文档/codescope-visualizer问题报告.md`。
- 确认并修复报告中的两个问题：
  - Radar 图维度不匹配
  - 中文字体 Glyph 缺失警告
- 在问题报告末尾追加“修复简要汇报”。

### 组员对接

- 新建 `组员补充清单.md`。
- 记录需要组员补充的字段：
  - `forks`
  - `open_issues` 或 `issues`
  - `updated_at`
  - `readme_path`
- 记录可选增强字段：
  - `has_api`
  - `has_cli`
  - `has_plugins`
  - `has_sdk`
  - `has_examples`
  - `has_hooks`
  - `has_quick_start`
  - `supports_one_command_run`

### 验证

- 对以下文件做过语法检查：
  - `codescope/scorer.py`
  - `codescope/visualizer.py`
  - `codescope/engine.py`
  - `codescope/tracker.py`
  - `codescope/analyzer.py`
- 对以下脚本目录文件做过语法检查：
  - `codescope/scripts/tracker.py`
  - `codescope/scripts/analyzer.py`
  - `codescope/scripts/scorer.py`
  - `codescope/scripts/visualizer.py`
- 目前 Python 文件语法检查通过。
- 已运行 `python engine.py` 完整验证真实数据链路。
- 验证结果：
  - `data/known_competitors.json` 已生成
  - `data/raw_data/` 已生成
  - `data/analysis.json` 已生成
  - `data/scores.json` 已生成
  - `output/*.png` 已生成
- 路径指向与生成位置正确。

### 代码变更导出

- 使用 `git diff` 导出当前代码变更。
- 导出补丁文件：
  - `codescope-code-changes.patch`
- 新建人工说明文件：
  - `codescope-代码变更记录.md`
- 说明文件中明确标注：
  - 修改到了组员负责的 `tracker.py`
  - 修改到了组员负责的 `analyzer.py`
  - 修改目的主要是统一生成文件路径
- 导出前检查并清空了 `config.json` 中的 GitHub Token，避免泄露密钥。
