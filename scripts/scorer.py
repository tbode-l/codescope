from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None
    text = value.strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _days_since(value: Any, now: datetime | None = None) -> float | None:
    dt = _parse_datetime(value)
    if dt is None:
        return None
    now = now or datetime.now(timezone.utc)
    return max(0.0, (now - dt).total_seconds() / 86400.0)


def _log_score(value: int, scale: float) -> float:
    if value <= 0:
        return 0.0
    return 100.0 * math.log1p(value) / math.log1p(scale)


def _count_signals(text: str, keywords: Iterable[str]) -> int:
    low = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in low)


@dataclass
class RepoInput:
    repo: str = ""
    stars: int = 0
    forks: int = 0
    issues: int = 0
    updated_at: str | None = None
    language: str = ""
    description: str = ""
    tech_stack: list[str] = field(default_factory=list)
    product_form: list[str] = field(default_factory=list)
    install_complexity: int = 4
    doc_completeness: int = 0
    readme_length: int = 0
    readme_text: str = ""
    readme_summary: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepoInput":
        return cls(
            repo=str(data.get("repo") or data.get("name") or ""),
            stars=_safe_int(data.get("stars")),
            forks=_safe_int(data.get("forks")),
            issues=_safe_int(data.get("issues") or data.get("open_issues")),
            updated_at=data.get("updated_at") or data.get("last_update"),
            language=str(data.get("language", "")),
            description=str(data.get("description", "")),
            tech_stack=list(data.get("tech_stack") or []),
            product_form=list(data.get("product_form") or []),
            install_complexity=_safe_int(data.get("install_complexity"), 4),
            doc_completeness=_safe_int(data.get("doc_completeness")),
            readme_length=_safe_int(data.get("readme_length")),
            readme_text=str(data.get("readme_text", "")),
            readme_summary=dict(data.get("readme_summary") or {}),
            config=dict(data.get("config") or {}),
        )


@dataclass
class ScoreBreakdown:
    attention: float
    tech_advancement: float
    setup_product: float
    ecosystem_openness: float
    overall: float

    def as_dict(self) -> dict[str, float]:
        return {
            "attention": round(self.attention, 2),
            "tech_advancement": round(self.tech_advancement, 2),
            "setup_product": round(self.setup_product, 2),
            "ecosystem_openness": round(self.ecosystem_openness, 2),
        }


class Scorer:
    """
    Score code-enhancement tools on a 0-100 scale.

    Expected inputs:
      - GitHub metadata: stars, forks, issues, updated_at
      - README analysis output: feature flags / counts / textual hints
    """

    DEFAULT_WEIGHTS = {
        "attention": 0.25,
        "tech_advancement": 0.30,
        "setup_product": 0.30,
        "ecosystem_openness": 0.15,
    }

    STAR_SCALE = 50000
    FORK_SCALE = 10000
    ISSUE_SCALE = 5000

    def __init__(self, weights: dict[str, Any] | None = None) -> None:
        self.weights = self._normalize_weights(weights or self.DEFAULT_WEIGHTS)

    def _normalize_weights(self, weights: dict[str, Any]) -> dict[str, float]:
        cleaned = {}
        for key, default in self.DEFAULT_WEIGHTS.items():
            try:
                value = float(weights.get(key, default))
            except (TypeError, ValueError):
                value = default
            cleaned[key] = max(0.0, value)

        total = sum(cleaned.values())
        if total <= 0:
            return dict(self.DEFAULT_WEIGHTS)
        return {key: value / total for key, value in cleaned.items()}

    def score(self, repo: RepoInput | dict[str, Any]) -> dict[str, Any]:
        item = repo if isinstance(repo, RepoInput) else RepoInput.from_dict(repo)
        breakdown = self._score_breakdown(item)
        return {
            "repo": item.repo,
            "stars": item.stars,
            "overall": round(breakdown.overall, 2),
            "scores": breakdown.as_dict(),
        }

    def score_many(self, repos: Iterable[RepoInput | dict[str, Any]]) -> list[dict[str, Any]]:
        scored = [self.score(repo) for repo in repos]
        scored.sort(key=lambda x: x["overall"], reverse=True)
        for index, item in enumerate(scored, start=1):
            item["rank"] = index
        return scored

    def _score_breakdown(self, repo: RepoInput) -> ScoreBreakdown:
        attention = self._score_attention(repo)
        tech_advancement = self._score_tech_advancement(repo)
        setup_product = self._score_setup_product(repo)
        ecosystem_openness = self._score_ecosystem_openness(repo)
        overall = (
            attention * self.weights["attention"]
            + tech_advancement * self.weights["tech_advancement"]
            + setup_product * self.weights["setup_product"]
            + ecosystem_openness * self.weights["ecosystem_openness"]
        )
        return ScoreBreakdown(attention, tech_advancement, setup_product, ecosystem_openness, overall)

    def _score_attention(self, repo: RepoInput) -> float:
        stars = _log_score(repo.stars, self.STAR_SCALE)
        forks = _log_score(repo.forks, self.FORK_SCALE)
        issues = _log_score(repo.issues, self.ISSUE_SCALE)

        update_days = _days_since(repo.updated_at)
        if update_days is None:
            freshness = 50.0
        elif update_days <= 30:
            freshness = 100.0
        elif update_days <= 90:
            freshness = 85.0
        elif update_days <= 180:
            freshness = 70.0
        elif update_days <= 365:
            freshness = 55.0
        else:
            freshness = max(10.0, 55.0 - min(45.0, (update_days - 365.0) / 30.0))

        score = 0.65 * stars + 0.15 * forks + 0.10 * issues + 0.10 * freshness
        return _clamp(score)

    def _score_tech_advancement(self, repo: RepoInput) -> float:
        text = " ".join([repo.description, repo.readme_text, " ".join(repo.tech_stack)]).lower()
        summary = repo.readme_summary

        modern_languages = {"go", "rust", "typescript"}
        stack = {str(item).lower() for item in repo.tech_stack}
        base = 20.0 if stack else 10.0
        base += min(20.0, len(stack) * 8.0)
        if stack & modern_languages:
            base += 10.0

        signals = [
            ["auto", "automation", "automate", "pipeline"],
            ["multi-repo", "multi repo", "multi-language", "multi language", "multi-model", "multi model"],
            ["search", "index", "retrieve", "retrieval"],
            ["agent", "rag", "llm", "embeddings"],
            ["plugin", "extension", "extensible", "hook"],
        ]
        for keywords in signals:
            hits = _count_signals(text, keywords)
            base += min(10.0, hits * 4.0)

        if repo.doc_completeness >= 4:
            base += 5.0
        if summary.get("recent_update"):
            base += 10.0
        if repo.updated_at and _days_since(repo.updated_at) is not None and _days_since(repo.updated_at) <= 180:
            base += 10.0

        return _clamp(base)

    def _score_setup_product(self, repo: RepoInput) -> float:
        text = repo.readme_text.lower()
        summary = repo.readme_summary

        complexity_scores = {
            1: 95.0,
            2: 78.0,
            3: 58.0,
            4: 38.0,
        }
        complexity_score = complexity_scores.get(repo.install_complexity, 38.0)
        forms = {str(item).lower() for item in repo.product_form}
        form_score = 35.0
        if "cli" in forms:
            form_score += 25.0
        if "ide-plugin" in forms:
            form_score += 30.0
        if "mcp-server" in forms:
            form_score += 20.0
        if forms:
            form_score += min(10.0, len(forms) * 4.0)

        api_key_hits = _count_signals(text, ["api key", "apikey", "secret", "token", "environment variable", "env var"])
        docker_hits = _count_signals(text, ["docker", "compose", "container"])
        service_hits = _count_signals(text, ["redis", "postgres", "mysql", "elasticsearch", "qdrant", "milvus"])

        score = 0.65 * complexity_score + 0.35 * _clamp(form_score)
        score -= api_key_hits * 5.0
        score -= docker_hits * 3.0
        score -= service_hits * 3.0
        if summary.get("has_quick_start"):
            score += 5.0
        if summary.get("supports_one_command_run"):
            score += 5.0
        return _clamp(score)

    def _score_ecosystem_openness(self, repo: RepoInput) -> float:
        text = " ".join([repo.description, repo.readme_text, " ".join(repo.product_form)]).lower()
        summary = repo.readme_summary

        score = 20.0

        if repo.doc_completeness >= 5:
            score += 20.0
        elif repo.doc_completeness >= 4:
            score += 15.0
        elif repo.doc_completeness >= 3:
            score += 8.0

        if repo.readme_length >= 2000:
            score += 10.0
        elif repo.readme_length >= 500:
            score += 5.0

        if summary.get("has_api"):
            score += 20.0
        if summary.get("has_cli"):
            score += 10.0
        if summary.get("has_plugins"):
            score += 15.0
        if summary.get("has_sdk"):
            score += 15.0
        if summary.get("has_hooks"):
            score += 10.0
        if summary.get("has_examples"):
            score += 10.0

        score += min(20.0, 4.0 * _count_signals(text, ["custom", "extend", "plugin", "provider", "adapter", "license", "sdk", "api"]))
        return _clamp(score)


def load_repos(path: str | Path) -> list[RepoInput]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("items", data.get("repos", data.get("analysis", [])))
    if not isinstance(data, list):
        raise ValueError("Expected a list of repos or an object with items/repos.")
    return [RepoInput.from_dict(item) for item in data]


def save_scores(path: str | Path, payload: list[dict[str, Any]]) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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


def resolve_project_path(path: str | Path) -> str:
    p = Path(path)
    if p.is_absolute():
        return str(p)
    return str(Path(__file__).resolve().parent.parent / p)


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    config = load_config()
    input_path = resolve_project_path(argv[0]) if len(argv) >= 1 else resolve_project_path(config_path(config, "analysis", "data/analysis.json"))
    output_path = resolve_project_path(argv[1]) if len(argv) >= 2 else resolve_project_path(config_path(config, "scores", "data/scores.json"))
    scorer = Scorer(config.get("scoring_weights"))
    repos = load_repos(input_path)
    scored = scorer.score_many(repos)
    save_scores(output_path, scored)
    print(f"Saved {len(scored)} scored items to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
