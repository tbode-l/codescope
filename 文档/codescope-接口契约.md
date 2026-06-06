# CodeScope 接口契约

> 罗坚（tracker + analyzer）↔ 洪锋烨（scorer + visualizer）之间的数据契约 | 2026-06-06

## 数据流向

```
罗坚 负责       洪锋烨 负责
─────────       ─────────

tracker.py ──→ known_competitors.json ──┐
                 raw_data/*.md         │  洪锋烨如需
                                       │  查看原始 README
analyzer.py ──→ analysis.json ──────────→ scorer.py ──→ scores.json ──→ visualizer.py ──→ output/*.png
                 ↑ 契约文件              ↑ 洪锋烨产出       ↑ 洪锋烨产出
```

**analysis.json 是唯一的跨模块契约文件。**

## analysis.json 格式

```json
[
  {
    "repo": "reviewdog/reviewdog",
    "stars": 9339,
    "language": "Go",
    "description": "Automated code review tool integrated with any analysis tools",
    "tech_stack": ["go", "shell"],
    "product_form": ["cli"],
    "install_complexity": 1,
    "doc_completeness": 4,
    "readme_length": 9856
  }
]
```

### 字段约定

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `repo` | string | GitHub owner/repo 全名 | `"reviewdog/reviewdog"` |
| `stars` | number | GitHub Stars 数 | `9339` |
| `language` | string | GitHub 标注的主要编程语言 | `"Go"` |
| `description` | string | GitHub 仓库描述 | `"Automated code review..."` |
| `tech_stack` | string[] | 检测到的技术栈语言（从 README 和 language 字段综合判定） | `["go", "python"]` |
| `product_form` | string[] | 检测到的产品形态 | `["cli"]` |
| `install_complexity` | number | 安装复杂度 1-4 | `1` |
| `doc_completeness` | number | 文档完整度 0-5 | `4` |
| `readme_length` | number | README 原始字符数 | `9856` |

### `tech_stack` 可选值

`go` | `rust` | `python` | `javascript` | `typescript` | `java` | `c` | `ruby` | `shell`

> 每个工具通常只有 1-2 个值。数组非空，如果无法检测则退回 `[language 字段的小写值]`。

### `product_form` 可选值

`cli` | `ide-plugin` | `mcp-server`

> 数组可能为空 `[]`（表示未检测到明确的形态标识）。

### `install_complexity` 含义

| 值 | 含义 | 示例 |
|:--:|------|------|
| 1 | 一行命令安装 | `pip install`、`npm install`、`go get` |
| 2 | 需 git clone 或 docker | `git clone`、`docker run` |
| 3 | 需编译（cmake/make） | `cmake`、`make install` |
| 4 | 手动配置 | `configure`、`manual` |

> 取值逻辑：取所有匹配模式中的**最低**复杂度（最容易的安装方式）。

### `doc_completeness` 含义

| 值 | 判定条件 |
|:--:|------|
| 0-1 | README < 500 字符 |
| 2 | 500-2000 字符，含安装说明或示例 |
| 3 | 500-2000 字符，含安装说明和示例 |
| 4 | > 2000 字符，含安装说明和示例 |
| 5 | > 2000 字符，含安装说明+示例+许可证 |

## known_competitors.json 格式（辅助文件，非必需契约）

```json
{
  "reviewdog/reviewdog": {
    "status": "NEW",
    "stars": 9339,
    "language": "Go",
    "description": "Automated code review tool...",
    "readme_path": "raw_data\\reviewdog_reviewdog_README.md"
  }
}
```

洪锋烨如果需要直接查看原始 README，可按 `readme_path` 读取本地文件。

## scores.json 格式约定（由评分规则.md确定）

实际格式（由评分规则.md确定，使用0-100分制）：

```json
[
  {
    "repo": "reviewdog/reviewdog",
    "stars": 9339,
    "overall": 78.5,
    "scores": {
      "attention": 70.2,
      "tech_advancement": 82.0,
      "setup_product": 88.0,
      "ecosystem_openness": 60.0
    }
  } 
]
```

> `overall` 和 `scores.*` 均为 **0-100 之间的浮点数**。

## 输出文件目录约定

| 文件 | 路径 | 产出者 | 消费者 |
|------|------|:----:|:----:|
| `known_competitors.json` | `codescope/` | tracker | analyzer, 洪锋烨(可选) |
| `raw_data/*.md` | `codescope/raw_data/` | tracker | analyzer, 洪锋烨(可选) |
| `analysis.json` | `codescope/` | analyzer | scorer |
| `scores.json` | `codescope/` | scorer | visualizer |
| `output/*.png` | `codescope/output/` | visualizer | 论文 |

## 库的选择

| 模块 | 库 | 说明 |
|------|------|------|
| scorer.py | Python 标准库 | 纯数学计算，无需额外依赖 |
| visualizer.py | **Matplotlib**（设计文档指定） | 见 `spec/competitor-tool-for-course-report.md`：产出「4 张 Matplotlib 图表」 |