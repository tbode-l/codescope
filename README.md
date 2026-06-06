# CodeScope

GitHub 代码增强工具自动化竞品分析系统。输入关键词，自动搜索同类工具、提取特征、评分排名、输出可视化报告。纯 Python 实现。

## 快速开始

```powershell
cd codescope
python engine.py
```

四步流水线依次执行，已下载的仓库自动跳过，重复运行只分析新增工具。

## 前置要求

- **Python 3.8+**
- **pip install -r requirements.txt**（只需安装 matplotlib）
- 网络能访问 `api.github.com` 和 `raw.githubusercontent.com`

## 目录结构

```
codescope/
├── engine.py              # 主控（四步流水线）
├── scripts/               # 实现脚本
│   ├── tracker.py         # 罗坚：搜索 + 下载 README
│   ├── analyzer.py        # 罗坚：特征提取
│   ├── scorer.py          # 洪锋烨：四维评分
│   └── visualizer.py      # 洪锋烨：Matplotlib 图表
├── config.json            # 搜索关键词 / Token / 上限
│
├── data/                  # 自动生成：JSON 数据和下载的 README
│   ├── raw_data/          # 自动生成：下载的 README
│   ├── known_competitors.json
│   ├── analysis.json      # 特征分析（→ 契约文件）
│   └── scores.json        # 评分结果
└── output/                # 自动生成：雷达图 / 散点图 / 柱状图
```

> 根目录保留 `engine.py` 作为唯一入口，实际实现脚本放在 `scripts/` 下。

## 流水线

| 步骤 | 模块 | 职责 | 负责人 |
|:--:|------|------|:----:|
| 1 | `tracker.py` | GitHub Search API 搜索 + 去重 + 下载 README | 罗坚 |
| 2 | `analyzer.py` | 读 README，提取技术栈、产品形态、安装复杂度、文档完整度 | 罗坚 |
| 3 | `scorer.py` | 四维评分：关注度、技术先进性、配置门槛与产品形态、生态开放性 | 洪锋烨 |
| 4 | `visualizer.py` | 雷达图 + 散点图 + 柱状图 + 终端排名报告（Matplotlib） | 洪锋烨 |

```
tracker ──→ data/known_competitors.json + data/raw_data/
    ↓
analyzer ──→ data/analysis.json  ← 模块间唯一契约
    ↓
scorer ──→ data/scores.json
    ↓
visualizer ──→ output/*.png
```

## 配置文件

`config.json` 中可自由调整，无需改代码：

| 字段 | 说明 |
|------|------|
| `search_queries` | GitHub Search API 查询列表，遵循 [API 语法](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories) |
| `max_per_query` | 单次搜索返回上限（最大 100） |
| `total_download_limit` | 本次最多下载几个新仓库 |
| `github_token` | GitHub PAT（留空则尝试环境变量 `GITHUB_TOKEN`，再留空则未认证运行） |
| `paths` | 生成文件路径，方便分类保存 JSON、README 和图表 |
| `scoring_weights` | 评分权重，可按自己的偏好调整 |

### 自定义文件路径

CodeScope 默认把运行数据放到 `data/`，图表放到 `output/`。如果想换目录，只需要修改 `config.json`：

```json
"paths": {
    "known_competitors": "data/known_competitors.json",
    "raw_data_dir": "data/raw_data",
    "analysis": "data/analysis.json",
    "scores": "data/scores.json",
    "output_dir": "output"
}
```

这样 JSON、README、图表的路径都由配置统一管理，不需要修改脚本代码。

### 自定义评分权重

CodeScope 默认用四个维度给工具打分。用户可以直接修改 `config.json` 里的 `scoring_weights`，让排序更贴近自己的需求。

```json
"scoring_weights": {
    "attention": 25,
    "tech_advancement": 30,
    "setup_product": 30,
    "ecosystem_openness": 15
}
```

字段含义：

| 字段 | 含义 | 适合提高权重的场景 |
|------|------|------|
| `attention` | 关注度，主要看 stars 等热度指标 | 想优先找成熟、热门工具 |
| `tech_advancement` | 技术先进性 | 想找新技术、Agent、RAG、插件化能力强的工具 |
| `setup_product` | 配置门槛与产品形态 | 想找更容易安装、能直接使用的工具 |
| `ecosystem_openness` | 生态开放性 | 想找方便扩展、二次开发、接入 API/SDK 的工具 |

权重不要求加起来正好等于 `100`，程序会自动归一化。例如只关心易用性，可以把 `setup_product` 调高；只关心热门程度，可以把 `attention` 调高。

### Token 配置（推荐）

1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. 权限勾选 `public_repo`（只读即可）
3. 填入 `config.json` 或设环境变量 `$env:GITHUB_TOKEN="ghp_xxxx"`

| 认证状态 | 搜索限额 | API 限额 |
|:---|:---:|:---:|
| 未认证 | 10 次/分钟 | 60 次/小时 |
| 已认证 | 30 次/分钟 | 5000 次/小时 |

## 单独运行

```powershell
python scripts/tracker.py      # 仅搜索下载
python scripts/analyzer.py     # 仅分析（需先跑 tracker）
python scripts/scorer.py       # 仅评分  （需先跑 analyzer）
python scripts/visualizer.py   # 仅出图  （需先跑 scorer）
```

## 分工

| 成员 | 负责 |
|------|------|
| 罗坚 | tracker.py + analyzer.py + engine.py + 论文全文 |
| 洪锋烨 | scorer.py + visualizer.py + PPT |

## 相关文档

- 产品设计：[py作业总体规划.md](文档/py作业总体规划.md)
- 接口契约：[codescope-接口契约.md](文档/codescope-接口契约.md)
- 评分规则：[评分规则.md](文档/评分规则.md)
- visualizer问题报告：[codescope-visualizer问题报告.md](文档/codescope-visualizer问题报告.md)
