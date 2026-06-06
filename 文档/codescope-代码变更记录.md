# CodeScope 代码变更记录

> 记录本次对 `F:\大学\26.6\codescope` 的代码修改，方便与组员对接。

## 导出文件

- 补丁文件：`codescope-code-changes.patch`

## 修改范围

### 修改到组员负责代码

1. `tracker.py`
   - 支持从 `config.json` 的 `paths` 读取生成路径。
   - `known_competitors.json` 默认改为写入 `data/known_competitors.json`。
   - README 默认改为下载到 `data/raw_data/`。
   - 保留原有 GitHub 搜索和 README 下载逻辑。

2. `analyzer.py`
   - 支持从 `config.json` 的 `paths` 读取输入/输出路径。
   - 默认从 `data/known_competitors.json` 读取仓库清单。
   - 默认输出 `data/analysis.json`。
   - 保留原有特征提取逻辑。

### 修改到洪锋烨负责代码

1. `scorer.py`
   - 默认读取 `data/analysis.json`。
   - 默认输出 `data/scores.json`。
   - 支持从 `config.json` 读取 `scoring_weights`。
   - 权重自动归一化，用户不需要保证权重和为 `100`。

2. `visualizer.py`
   - 默认读取 `data/scores.json`。
   - 默认输出图表到 `output/`。
   - 修复 Radar 图维度不匹配问题。
   - 添加 Matplotlib 中文字体配置。

### 配置和文档

1. `config.json`
   - 新增 `paths`，统一管理生成文件路径。
   - 新增 `scoring_weights`，允许用户自定义评分权重。
   - `github_token` 保持为空，避免泄露密钥。

2. `README.md`
   - 更新目录结构。
   - 补充自定义文件路径说明。
   - 补充自定义评分权重说明。
   - 将评分口径统一为四维评分。

3. `.gitignore`
   - 新增忽略 `data/`。

4. `文档/codescope-visualizer问题报告.md`
   - 追加修复简要汇报。

## 验证情况

- 已运行语法检查：
  - `tracker.py`
  - `analyzer.py`
  - `scorer.py`
  - `visualizer.py`
- 语法检查通过。
- 尚未完整运行 `python engine.py` 验证真实 GitHub 数据链路。

## 注意事项

- 本次确实修改了组员负责的 `tracker.py` 和 `analyzer.py`。
- 修改目的主要是让生成文件路径由 `config.json` 统一管理。
- 如果组员不同意改路径管理方式，可以只保留 `scorer.py` / `visualizer.py` 的修改，再回退 `tracker.py` / `analyzer.py` 的路径配置部分。
