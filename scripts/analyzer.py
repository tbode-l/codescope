import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
CONFIG_FILE = "config.json"
SKIPPED_FILE = "data/skipped_repos.json"

DEFAULT_PATHS = {
    "known_competitors": "data/known_competitors.json",
    "analysis": "data/analysis.json",
}

# 垃圾仓库黑名单关键词（仅匹配仓库名和描述，不匹配 README 内容）
# 只匹配完全的垃圾仓库（机器人比赛、课程作业、教程、数据集、论文代码等）
SKIPPED_KEYWORDS = [
    "FTC", "robotics", "robot", "competition",
    "portfolio", "awesome list", "roadmap",
    "interview", "bootcamp", "course", "tutorial", "homework",
    "assignment", "cheatsheet", "whitepaper",
    "malware", "ransomware", "payload", "exploit",
    "crack", "hack", "pastebin", "keylogger",
    "basic programs", "hello world", "helloy",
    "dataset", "research dataset", "qa dataset", "question answering",
    "cvpr", "acl", "naacl", "emnlp", "neurips", "icml",
    "paper", "research paper", "arXiv",
    "chatbot", "simple chatbot", "sample chatbot",
    "game tool", "game mod", "hytale", "minecraft",
]

# 技术栈关键词：只匹配具体技术指标，而非泛泛提及
# 比如 "python" 会匹配 "python3", "python script", "python implementation" 但不够精准
# 改用安装命令和特定工具名组合
TECH_PATTERNS = {
    "python": [r"\bpip\s+install", r"\bpython3?\b", r"\.py\b", r"\bpypi\b"],
    "javascript": [r"\bnpm\s+(install|run|test)", r"\bnpx\b", r"\byarn\s+(add|install)", r"\bnode_modules\b"],
    "typescript": [r"\btypescript\b", r"\btsc\b", r"\.tsx?\b"],
    "go": [r"\bgo\s+(get|build|install|mod)\b", r"\bgolang\b", r"\.go\b"],
    "rust": [r"\bcargo\s+(install|build|run|test)\b", r"\brustc\b", r"\.rs\b"],
    "java": [r"\bmaven\b", r"\bgradle\b", r"\.jar\b", r"pom\.xml"],
    "c": [r"\bcmake\b", r"\bmakefile\b", r"\.c\b", r"\.h\b"],
    "ruby": [r"\bruby\b", r"\bgem\s+(install|build)", r"\bbundle\s+install\b", r"\.rb\b"],
    "shell": [r"\bbash\b", r"\bsh\b", r"\.sh\b", r"\bshell\s+script\b", r"\bsed\b", r"\bawk\b"],
}

# 产品形态：只匹配明确的自描述，而非 README 任何位置的泛词
PRODUCT_FORM_PATTERNS = {
    "cli": [r"\bcli\b", r"\bcommand.line\b", r"\bterminal\b"],
    "ide-plugin": [r"\bide\b", r"\bplugin\b", r"\bextension\b", r"\bvscode\s+extension\b"],
    "mcp-server": [r"\bmcp\b", r"\bmodel.context.protocol\b"],
}

INSTALL_COMPLEXITY_PATTERNS = [
    (r"\bpip\s+install\b", 1),
    (r"\bnpm\s+install\b", 1),
    (r"\bgo\s+get\b", 1),
    (r"\bcargo\s+install\b", 1),
    (r"\bbrew\s+install\b", 1),
    (r"\bgit\s+clone\b", 2),
    (r"\bdocker\b", 2),
    (r"\bcmake\b", 3),
    (r"\bmake\s+install\b", 3),
    (r"\bconfigure\b", 4),
    (r"\bmanual\b", 4),
]


def load_config():
    path = resolve_path(CONFIG_FILE)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def resolve_path(path):
    if os.path.isabs(path):
        return path
    return os.path.join(PROJECT_DIR, path)


def get_paths(config):
    configured = config.get("paths", {})
    paths = dict(DEFAULT_PATHS)
    paths.update({k: v for k, v in configured.items() if v})
    return paths


def load_known(known_file):
    path = resolve_path(known_file)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def read_readme(readme_path):
    full_path = readme_path if os.path.isabs(readme_path) else os.path.join(PROJECT_DIR, readme_path)
    if not os.path.exists(full_path):
        return ""
    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def detect_tech_stack(readme_text, github_language):
    text_lower = readme_text.lower()

    primary = github_language.lower() if github_language else ""
    if primary not in TECH_PATTERNS:
        return [primary] if primary else []

    result = [primary]

    candidates = []
    for tech, patterns in TECH_PATTERNS.items():
        if tech == primary:
            continue
        match_count = 0
        for p in patterns:
            if re.search(p, text_lower):
                match_count += 1
        if match_count >= 3:
            candidates.append((tech, match_count))

    candidates.sort(key=lambda x: x[1], reverse=True)
    if candidates:
        result.append(candidates[0][0])

    return result


def detect_product_form(text):
    text_lower = text.lower()
    found = []
    for form, patterns in PRODUCT_FORM_PATTERNS.items():
        for p in patterns:
            if re.search(p, text_lower):
                found.append(form)
                break
    return list(set(found))


def estimate_install_complexity(text):
    text_lower = text.lower()
    scores = []
    for pattern, score in INSTALL_COMPLEXITY_PATTERNS:
        if re.search(pattern, text_lower):
            scores.append(score)
    if not scores:
        return 3
    return min(scores)


def estimate_doc_completeness(text):
    score = 0
    if len(text) > 500:
        score += 1
    if len(text) > 2000:
        score += 1
    if re.search(r"\binstall\b|\binstallation\b", text.lower()):
        score += 1
    if re.search(r"\busage\b|\bexample\b|\bgetting started\b", text.lower()):
        score += 1
    if re.search(r"\blicense\b", text.lower()):
        score += 1
    return score


def save_known(known, known_file):
    path = resolve_path(known_file)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        json.dump(known, f, ensure_ascii=False, indent=2)


def load_skipped():
    path = resolve_path(SKIPPED_FILE)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_skipped(skipped):
    path = os.path.join(PROJECT_DIR, SKIPPED_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(skipped, f, ensure_ascii=False, indent=2)


def is_garbage_repo(repo_name, description, readme_text):
    """只匹配仓库名和描述，不匹配 README 内容（避免误判）"""
    text_lower = f"{repo_name.lower()} {description.lower()}"
    for kw in SKIPPED_KEYWORDS:
        kw_lower = kw.lower()
        # 两种匹配策略：
        # 1. 关键词本身是一个单词（比如 "FTC"、"robot"）：作为完整词匹配
        if " " not in kw_lower:
            # 检查是否作为完整词出现（前后是非字母/数字字符或边界）
            import re
            if re.search(r"\b" + re.escape(kw_lower) + r"\b", text_lower):
                return kw
        # 2. 关键词是短语（比如 "awesome list"、"hello world"）：作为子字符串匹配
        elif kw_lower in text_lower:
            return kw
    return None


def extract_features(known_file):
    known = load_known(known_file)
    if not known:
        print("[分析] 没有待分析的仓库", file=sys.stderr)
        return []

    skipped = load_skipped()
    results = []
    for repo_name, repo_info in known.items():
        if repo_info.get("status") != "NEW":
            continue

        readme_text = read_readme(repo_info.get("readme_path", ""))
        github_language = repo_info.get("language", "")
        description = repo_info.get("description", "")

        # 自动垃圾仓库检测，加入黑名单
        garbage_reason = is_garbage_repo(repo_name, description, readme_text)
        if garbage_reason:
            if repo_name not in skipped:
                skipped[repo_name] = {
                    "reason": f"检测到关键词：{garbage_reason}",
                    "skipped_at": "2026-06-06"
                }
                save_skipped(skipped)
                print(f"[黑名单] 自动加入 {repo_name}（原因：{garbage_reason}）", file=sys.stderr)
            else:
                print(f"[黑名单] 已存在 {repo_name}，跳过", file=sys.stderr)
            continue  # 不加入 analysis.json

        features = {
            "repo": repo_name,
            "stars": repo_info.get("stars", 0),
            "forks": repo_info.get("forks", 0),
            "open_issues": repo_info.get("open_issues", 0),
            "updated_at": repo_info.get("updated_at", ""),
            "language": github_language,
            "description": repo_info.get("description", ""),
            "tech_stack": detect_tech_stack(readme_text, github_language),
            "product_form": detect_product_form(readme_text),
            "install_complexity": estimate_install_complexity(readme_text),
            "doc_completeness": estimate_doc_completeness(readme_text),
            "readme_length": len(readme_text),
            "readme_path": repo_info.get("readme_path", ""),
        }
        results.append(features)
        print(
            f"[分析] {repo_name}: 语言={features['language']}, "
            f"技术栈={features['tech_stack']}, "
            f"形态={features['product_form']}, "
            f"安装复杂度={features['install_complexity']}",
            file=sys.stderr,
        )

    results.sort(key=lambda r: r["stars"], reverse=True)
    return results


def save_analysis(results, analysis_file):
    path = resolve_path(analysis_file)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main():
    config = load_config()
    paths = get_paths(config)

    results = extract_features(paths["known_competitors"])
    save_analysis(results, paths["analysis"])

    known = load_known(paths["known_competitors"])
    changed = 0
    for repo_name, repo_info in known.items():
        if repo_info.get("status") == "NEW":
            known[repo_name]["status"] = "ANALYZED"
            changed += 1
    if changed > 0:
        save_known(known, paths["known_competitors"])

    print(f"[分析完成] 共分析 {len(results)} 个仓库", file=sys.stderr)
    print(len(results))


if __name__ == "__main__":
    main()
