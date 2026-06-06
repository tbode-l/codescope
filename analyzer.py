import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWN_FILE = os.path.join(BASE_DIR, "known_competitors.json")
ANALYSIS_FILE = os.path.join(BASE_DIR, "analysis.json")

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


def load_known():
    if os.path.exists(KNOWN_FILE):
        with open(KNOWN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def read_readme(readme_path):
    full_path = os.path.join(BASE_DIR, readme_path)
    if not os.path.exists(full_path):
        return ""
    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def detect_tech_stack(readme_text, github_language):
    text_lower = readme_text.lower()
    found = []

    for tech, patterns in TECH_PATTERNS.items():
        match_count = 0
        for p in patterns:
            if re.search(p, text_lower):
                match_count += 1
        if match_count >= 2:
            found.append(tech)

    # 用 GitHub 标注的语言兜底
    if github_language and github_language.lower() in TECH_PATTERNS:
        gl = github_language.lower()
        if gl == "typescript":
            gl = "typescript"
        if gl not in found:
            found.append(gl)

    return found if found else ([github_language.lower()] if github_language else [])


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


def extract_features():
    known = load_known()
    if not known:
        print("[分析] 没有待分析的仓库", file=sys.stderr)
        return []

    results = []
    for repo_name, repo_info in known.items():
        if repo_info.get("status") != "NEW":
            continue

        readme_text = read_readme(repo_info.get("readme_path", ""))
        github_language = repo_info.get("language", "")

        features = {
            "repo": repo_name,
            "stars": repo_info.get("stars", 0),
            "language": github_language,
            "description": repo_info.get("description", ""),
            "tech_stack": detect_tech_stack(readme_text, github_language),
            "product_form": detect_product_form(readme_text),
            "install_complexity": estimate_install_complexity(readme_text),
            "doc_completeness": estimate_doc_completeness(readme_text),
            "readme_length": len(readme_text),
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


def save_analysis(results):
    with open(ANALYSIS_FILE, "w", encoding="utf-8", errors="replace") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main():
    results = extract_features()
    save_analysis(results)
    print(f"[分析完成] 共分析 {len(results)} 个仓库", file=sys.stderr)
    print(len(results))


if __name__ == "__main__":
    main()