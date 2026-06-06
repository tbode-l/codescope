import json
import os
import ssl
import sys
import urllib.request
import urllib.error
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CONFIG_FILE = "config.json"
KNOWN_FILE = "known_competitors.json"
RAW_DIR = "raw_data"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_QUERIES = [
    "code enhancement tool github stars:>30",
    "code analysis tool cli stars:>30",
    "static analysis code review tool stars:>30",
    "code quality improvement tool stars:>30",
    "code refactoring automated tool stars:>30",
]
DEFAULT_MAX_PER_QUERY = 30
DEFAULT_DOWNLOAD_LIMIT = 50

# GitHub description 关键词黑名单：排除与代码增强无关的仓库
IRRELEVANT_KEYWORDS = [
    "portfolio", "project list", "awesome list", "roadmap",
    "interview", "bootcamp", "course", "tutorial", "homework",
    "assignment", "cheatsheet", "whitepaper", "whitepaper",
    "FTC", "robotics", "robot", "competition",
    "malware", "ransomware", "payload", "exploit",
    "crack", "hack", "pastebin", "keylogger",
    "basic programs", "hello world", "helloy",
]


def _ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def load_config():
    path = os.path.join(BASE_DIR, CONFIG_FILE)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _api_get(url, token):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "codescope-tracker")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30, context=_ssl_context()) as resp:
        return json.loads(resp.read().decode())


def search_github(query, max_per_query, token):
    params = urllib.parse.urlencode(
        {"q": query, "per_page": max_per_query, "sort": "stars"}
    )
    url = f"https://api.github.com/search/repositories?{params}"
    return _api_get(url, token).get("items", [])


def load_known():
    path = os.path.join(BASE_DIR, KNOWN_FILE)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_known(data):
    path = os.path.join(BASE_DIR, KNOWN_FILE)
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def download_readme(owner, repo):
    readme_text = None
    last_error = None
    ctx = _ssl_context()
    for branch in ("main", "master"):
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "codescope-tracker")
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                readme_text = resp.read().decode()
                break
        except (urllib.error.HTTPError, urllib.error.URLError, ssl.SSLError, OSError) as e:
            last_error = e
            continue
    if readme_text is None:
        raise RuntimeError(f"{last_error}" if last_error else "无 README")

    raw_dir = os.path.join(BASE_DIR, RAW_DIR)
    os.makedirs(raw_dir, exist_ok=True)
    filename = f"{owner}_{repo}_README.md"
    filepath = os.path.join(raw_dir, filename)
    with open(filepath, "w", encoding="utf-8", errors="replace") as f:
        f.write(readme_text)
    return filepath


def is_relevant(repo):
    description = (repo.get("description") or "").lower()
    for kw in IRRELEVANT_KEYWORDS:
        if kw in description:
            return False
    topics = repo.get("topics", [])
    for kw in IRRELEVANT_KEYWORDS:
        for topic in topics:
            if kw in topic.lower():
                return False
    return True


def main():
    config = load_config()

    queries = config.get("search_queries", DEFAULT_QUERIES)
    max_per_query = config.get("max_per_query", DEFAULT_MAX_PER_QUERY)
    download_limit = config.get("total_download_limit", DEFAULT_DOWNLOAD_LIMIT)

    token = config.get("github_token", "") or os.getenv("GITHUB_TOKEN") or ""

    known = load_known()

    all_items = []
    for query in queries:
        try:
            items = search_github(query, max_per_query, token)
            print(f"[搜索] '{query}' -> {len(items)} 个结果", file=sys.stderr)
            all_items.extend(items)
        except Exception as e:
            print(f"[搜索失败] '{query}': {e}", file=sys.stderr)

    seen = set()
    unique = []
    filtered = 0
    for repo in all_items:
        name = repo["full_name"]
        if name in seen:
            continue
        seen.add(name)
        if not is_relevant(repo):
            filtered += 1
            continue
        unique.append(repo)

    if filtered > 0:
        print(f"[过滤] 排除 {filtered} 个不相关仓库", file=sys.stderr)

    unique.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)

    new_count = 0
    for repo in unique:
        if new_count >= download_limit:
            print(f"[达到上限] 已下载 {download_limit} 个，停止", file=sys.stderr)
            break

        full_name = repo["full_name"]
        if full_name in known:
            continue

        stars = repo.get("stargazers_count", 0)
        print(f"[发现] {full_name} ({stars} stars)", file=sys.stderr)

        owner, repo_name = full_name.split("/", 1)
        try:
            readme_path = download_readme(owner, repo_name)
        except Exception as e:
            print(f"[下载失败] {full_name}: {e}", file=sys.stderr)
            continue

        known[full_name] = {
            "status": "NEW",
            "stars": stars,
            "forks": repo.get("forks_count", 0),
            "open_issues": repo.get("open_issues_count", 0),
            "updated_at": repo.get("updated_at", ""),
            "language": repo.get("language", ""),
            "description": repo.get("description", ""),
            "readme_path": os.path.relpath(readme_path, BASE_DIR),
        }
        print(f"[已下载] -> {readme_path}", file=sys.stderr)
        new_count += 1

    save_known(known)
    total_known = len(known)
    print(f"[统计] 已追踪 {total_known} 个仓库，其中 NEW={new_count}", file=sys.stderr)
    print(new_count)


if __name__ == "__main__":
    main()