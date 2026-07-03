#!/opt/hermes/.venv/bin/python3
"""
GitHub Bounty 自动搜索 + 分析系统
用法: python3 search_gh_bounties.py

扫 GitHub 上带 bounty 标签的 Python/JS Issue → AI 分析 → 输出推荐清单
"""

import json, urllib.request, re, os, sys, time
from datetime import datetime

# ── Config ──────────────────────────────────────────────
TOKEN_FILE = "/opt/data/projects/online-earning/config/gh_token.env"
OUTPUT_DIR = "/opt/data/projects/online-earning/output"

def load_token():
    """从安全文件读取 token（不在代码中硬编码）"""
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ Token 文件不存在: {TOKEN_FILE}")
        sys.exit(1)
    with open(TOKEN_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("GH_TOKEN="):
                return line.split("=", 1)[1].strip()
    print("❌ Token 文件中未找到 GH_TOKEN= 行")
    sys.exit(1)

TOKEN = load_token()
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "auto-bot"
}

# ─── Token file locations (in order of preference) ───
# 1. /opt/data/.env_bot        (global, exported var style: export GH_BOT_TOKEN="ghp_...")
# 2. /opt/data/.env            (Hermes-wide env file)
# 3. $GH_BOT_TOKEN from env    (set by user or CI)

# ── Keywords ─────────────────────────────────────────────
TITLE_KWS = [
    "python", "crawl", "scrape", "scraping", "scraper",
    "automation", "auto", "script", "bot", "chatbot",
    "api", "data", "excel", "csv", "pdf", "ocr",
    "extract", "selenium", "llm", "gpt", "ai",
    "test", "etl", "parse", "parser", "report",
    "monitor", "dashboard", "migration",
    "webhook", "integration",
]

EASY_KWS = ["test", "unit test", "documentation", "doc", "readme", 
            "contributing", "typo", "fix typo", "lint", "format"]

# ── Helpers ──────────────────────────────────────────────
def gh_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return json.loads(urllib.request.urlopen(req, timeout=20).read())

def search_bounties(language="python", extra_q="", per_page=100, pages=3):
    """搜索带 bounty 标签的 Issue"""
    all_items = []
    for page in range(1, pages + 1):
        kw = f"+{extra_q}" if extra_q else ""
        lang = f"+language:{language}" if language else ""
        url = (f"https://api.github.com/search/issues"
               f"?q=is%3Aissue+is%3Aopen+label%3Abounty{lang}{kw}"
               f"&sort=created&order=desc"
               f"&per_page={per_page}&page={page}")
        try:
            data = gh_get(url)
            items = data.get("items", [])
            all_items.extend(items)
            print(f"   第{page}页: {len(items)} 条 (累计 {len(all_items)}，总数 {data.get('total_count','?')})")
            time.sleep(0.5)
        except Exception as e:
            print(f"   第{page}页失败: {e}")
    return all_items

def analyze(issue):
    title = issue.get("title", "")
    body = (issue.get("body") or "")[:2000]
    repo_url = issue.get("repository_url", "")
    repo_name = repo_url.split("/")[-1] if repo_url else "?"
    labels = [l.get("name", "") for l in issue.get("labels", [])]
    html_url = issue.get("html_url", "")
    all_text = f"{title} {body}".lower()

    # 难度
    difficulty = "medium"
    if any(kw in all_text for kw in EASY_KWS):
        difficulty = "easy"
    elif any(kw in all_text for kw in ["feature", "implement", "build", "complex", "hard", "architect", "refactor"]):
        difficulty = "hard"

    # 金额
    amount = 0
    amount_str = "未标注"
    for pat in [r'\$(\d[\d,]*)\s*(k|K)?\s*(bounty|grant|reward)', 
                r'(bounty|grant|reward)\s*(:|\sof)\s*\$?(\d[\d,]*)',
                r'\$\s*(\d[\d,]*)\s*(k|K)?']:
        m = re.search(pat, f"{title} {body}", re.IGNORECASE)
        if m:
            raw = m.group(0)
            amount_str = raw[:20]
            nums = re.findall(r'\d[\d,]*', raw)
            if nums:
                val = int(nums[0].replace(",", ""))
                if 'k' in raw.lower():
                    val *= 1000
                amount = val
            break

    # 标签
    tags = set()
    if any(kw in all_text for kw in ["python"]): tags.add("python")
    if any(kw in all_text for kw in ["test", "pytest", "unittest"]): tags.add("test")
    if any(kw in all_text for kw in ["doc", "documentation", "readme"]): tags.add("docs")
    if any(kw in all_text for kw in ["api", "rest", "endpoint"]): tags.add("api")
    if any(kw in all_text for kw in ["data", "csv", "json", "excel", "pandas"]): tags.add("data")
    if any(kw in all_text for kw in ["scrape", "crawl"]): tags.add("scraping")
    if any(kw in all_text for kw in ["automation", "script"]): tags.add("automation")

    return {
        "repo": repo_name,
        "title": title[:80],
        "url": html_url,
        "amount": amount,
        "amount_str": amount_str,
        "difficulty": difficulty,
        "tags": list(tags),
        "labels": [l for l in labels if l != "bounty"][:3],
        "created": (issue.get("created_at") or "")[:10],
        "body_preview": (body or "")[:300],
    }

# ── Main ─────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  🔍 GitHub Bounty 搜索 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    print("📄 搜索 Python Bounties...")
    py_items = search_bounties(language="python")
    print("\n📄 搜索 TypeScript Bounties...")
    ts_items = search_bounties(language="javascript", extra_q="+typescript")

    seen = set()
    results = []
    for item in py_items + ts_items:
        url = item.get("html_url", "")
        if url not in seen:
            seen.add(url)
            results.append(analyze(item))

    # 分组
    easy = sorted([i for i in results if i["difficulty"] == "easy"], key=lambda x: -x["amount"])
    medium = sorted([i for i in results if i["difficulty"] == "medium"], key=lambda x: -x["amount"])
    hard = sorted([i for i in results if i["difficulty"] == "hard"], key=lambda x: -x["amount"])

    print(f"\n{'='*60}")
    print(f"  🎯 共 {len(results)} 个可用 Bounty")
    print(f"{'='*60}")

    for section, items in [("🟢 简单 — 今天就能赚", easy),
                            ("🟡 中等 — 1-2天", medium),
                            ("🔴 困难", hard[:3])]:
        if not items: continue
        print(f"\n{section} ({len(items)}):")
        print(f"{'─'*60}")
        for i, item in enumerate(items[:8], 1):
            amt = f"${item['amount']:,}" if item['amount'] > 0 else f"💰 {item['amount_str']}"
            tags = " ".join(f"#{t}" for t in item['tags'][:3])
            print(f"  #{i} [{item['repo']}] {item['title'][:55]}")
            print(f"     {amt} | {item['difficulty']} | {tags}")
            print(f"     {item['url']}")

    ts = datetime.now().strftime('%Y%m%d_%H%M')
    path = f"{OUTPUT_DIR}/gh_bounties_{ts}.json"
    with open(path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📁 保存: {path}")

    # 🏆 最佳推荐
    best = [i for i in easy if i["amount"] > 0] or easy[:5] or medium[:5]
    print(f"\n{'='*60}")
    print(f"  🏆 最佳推荐")
    print(f"{'='*60}")
    for i, item in enumerate(best[:5], 1):
        amt = f"${item['amount']:,}" if item['amount'] > 0 else item['amount_str']
        print(f"  #{i} [{item['repo']}] {item['title'][:60]}")
        print(f"     {amt} | {item['url']}")

if __name__ == "__main__":
    main()
