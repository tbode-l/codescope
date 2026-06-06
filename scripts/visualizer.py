from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False


DIMENSIONS = ["attention", "tech_advancement", "setup_product", "ecosystem_openness"]
DIMENSION_LABELS = {
    "attention": "关注度",
    "tech_advancement": "技术先进性",
    "setup_product": "配置门槛与产品形态",
    "ecosystem_openness": "生态开放性",
}


def load_scores(path: str | Path) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("items", data.get("scores", data.get("repos", [])))
    if not isinstance(data, list):
        raise ValueError("Expected a list of score records or an object containing items/scores/repos.")
    return data


def load_config(path: str | Path = "config.json") -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        config_path = Path(__file__).with_name("config.json")
    if not config_path.exists():
        config_path = Path(__file__).resolve().parent.parent / "config.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def config_path(config: dict[str, Any], key: str, default: str) -> str:
    paths = config.get("paths") or {}
    return str(paths.get(key) or default)


def resolve_project_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return Path(__file__).resolve().parent.parent / p


def _ensure_dir(path: str | Path) -> Path:
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    return out


def _get_scores(item: dict[str, Any]) -> dict[str, float]:
    scores = dict(item.get("scores") or {})
    return {key: float(scores.get(key, 0.0)) for key in DIMENSIONS}


def _get_name(item: dict[str, Any], fallback_index: int) -> str:
    name = str(item.get("repo") or item.get("name") or "").strip()
    return name or f"repo-{fallback_index}"


def _sorted_items(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: float(item.get("overall", 0.0)), reverse=True)


def plot_bar_chart(items: list[dict[str, Any]], output: Path) -> Path:
    top = items[:10]
    names = [_get_name(item, idx + 1) for idx, item in enumerate(top)]
    totals = [float(item.get("overall", 0.0)) for item in top]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(top))[::-1], totals[::-1], color="#4c78a8")
    ax.set_yticks(range(len(top))[::-1], names[::-1])
    ax.set_xlabel("Total Score")
    ax.set_title("Top Repositories by Total Score")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", linestyle="--", alpha=0.3)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.8, bar.get_y() + bar.get_height() / 2, f"{width:.1f}", va="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_scatter(items: list[dict[str, Any]], output: Path) -> Path:
    scores = [_get_scores(item) for item in items]
    total = [float(item.get("overall", 0.0)) for item in items]
    setup = [s["setup_product"] for s in scores]
    attention = [s["attention"] for s in scores]
    names = [_get_name(item, idx + 1) for idx, item in enumerate(items)]

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(setup, total, c=attention, cmap="viridis", s=70, alpha=0.85, edgecolors="white", linewidths=0.5)
    ax.set_xlabel("Setup Score")
    ax.set_ylabel("Total Score")
    ax.set_title("Setup vs Total")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.grid(True, linestyle="--", alpha=0.25)
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Attention Score")

    for x, y, name in zip(setup, total, names):
        ax.annotate(name, (x, y), xytext=(5, 5), textcoords="offset points", fontsize=8)

    fig.tight_layout()
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_dimension_bars(items: list[dict[str, Any]], output: Path) -> Path:
    labels = [_get_name(item, idx + 1) for idx, item in enumerate(items)]
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(items))
    width = 0.18
    offsets = [-1.5 * width, -0.5 * width, 0.5 * width, 1.5 * width]
    colors = ["#4c78a8", "#f58518", "#54a24b", "#e45756"]

    for offset, key, color in zip(offsets, DIMENSIONS, colors):
        values = [_get_scores(item)[key] for item in items]
        ax.bar([i + offset for i in x], values, width=width, label=DIMENSION_LABELS[key], color=color)

    ax.set_xticks(list(x), labels, rotation=20, ha="right")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Score")
    ax.set_title("Dimension Comparison")
    ax.legend(ncol=2, frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.25)

    fig.tight_layout()
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_radar(items: list[dict[str, Any]], output: Path) -> Path:
    top = items[:5]
    labels = [DIMENSION_LABELS[key] for key in DIMENSIONS]
    angle_count = len(labels)
    angles = [n / float(angle_count) * 2 * math.pi for n in range(angle_count)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"polar": True})
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    for idx, item in enumerate(top):
        values = [_get_scores(item)[key] for key in DIMENSIONS]
        values += values[:1]
        name = _get_name(item, idx + 1)
        ax.plot(angles, values, linewidth=1.8, label=name)
        ax.fill(angles, values, alpha=0.08)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 100)
    ax.set_title("Top Repositories Radar", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), frameon=False)

    fig.tight_layout()
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output


def generate_charts(scores_path: str | Path, output_dir: str | Path = "output") -> list[Path]:
    items = _sorted_items(load_scores(resolve_project_path(scores_path)))
    out_dir = _ensure_dir(resolve_project_path(output_dir))
    outputs = [
        plot_bar_chart(items, out_dir / "top_scores_bar.png"),
        plot_scatter(items, out_dir / "setup_vs_total_scatter.png"),
        plot_dimension_bars(items[:8], out_dir / "dimension_comparison.png"),
        plot_radar(items, out_dir / "top5_radar.png"),
    ]
    return outputs


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    config = load_config()
    scores_path = resolve_project_path(argv[0]) if len(argv) >= 1 else resolve_project_path(config_path(config, "scores", "data/scores.json"))
    output_dir = resolve_project_path(argv[1]) if len(argv) >= 2 else resolve_project_path(config_path(config, "output_dir", "output"))
    outputs = generate_charts(scores_path, output_dir)
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
