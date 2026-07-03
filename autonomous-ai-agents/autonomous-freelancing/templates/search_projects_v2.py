#!/opt/hermes/.venv/bin/python3
"""
Freelancer 项目自动搜索 — 精准版 v2
只保留真正适合 AI 做的技术类项目

Usage:
    cd /opt/data/projects/online-earning
    /opt/hermes/.venv/bin/python3 scripts/search_projects_v2.py

Output:
    /opt/data/projects/online-earning/output/projects_YYYYMMDD_HHMM.json

For cron:
    0 */6 * * * cd /opt/data/projects/online-earning && /opt/hermes/.venv/bin/python3 scripts/search_projects_v2.py
"""
import json, re, time
from datetime import datetime
from urllib.request import Request, urlopen

BASE = "https://www.freelancer.com/api/projects/0.1/projects/active"

TECH_KWS = [
    "python", "web scraping", "crawl", "scraper", "selenium",
    "automation", "script", "data extraction", "data processing",
    "data mining", "data analysis", "data visualization",
    "api integration", "api development", "rest api",
    "chatbot", "bot development", "ai agent", "llm", "gpt",
    "machine learning", "deep learning", "nlp",
    "excel automation", "excel macro", "vba",
    "webhook", "automation script", "batch processing",
    "pdf extraction", "pdf to excel", "ocr",
    "database", "sql", "etl", "data migration",
    "web automation", "browser automation", "playwright",
    "testing automation", "test script", "qa automation",
    "report generation", "dashboard", "csv", "json parsing",
    "file conversion", "format conversion", "xml parsing",
]

TITLE_KWS = [
    "python", "crawl", "scrape", "scraping", "scraper",
    "automation", "auto", "script", "bot", "chatbot",
    "api", "data", "excel", "csv", "pdf", "ocr",
    "extract", "scrap", "selenium", "llm", "gpt", "ai",
    "test", "etl", "parse", "parser", "report",
    "monitor", "dashboard", "migration",
    "webhook", "integration",
]

EXCLUDE_TITLE = [
    "voice over", "模特", "model", "演员", "actor",
    "brand ambassador", "客服", "customer service",
    "sales", "销售", "recruitment", "招聘", "hr",
    "virtual assistant", "admin", "行政",
    "translation", "翻译", "content writing", "写手",
    "video", "edit", "剪辑", "design", "设计",
    "logo", "photoshop", "illustrator",
    "fashion", "clothing", "模特",
    "influencer", "marketing", "seo",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

def fetch(page=1, limit=50):
    url = f"{BASE}?page={page}&limit={limit}&sort=submitdate&order=desc"
    try:
        data = json.loads(urlopen(Request(url, headers=HEADERS), timeout=20).read())
        return data.get("result", {})
    except Exception as e:
        print(f"  Request failed: {e}")
        return {}

def is_good(proj):
    title = (proj.get("title") or "").lower().strip()
    desc = (proj.get("preview_description") or "").lower().strip()
    jobs = " ".join(j.get("name", "").lower() for j in (proj.get("jobs") or []))
    
    for kw in EXCLUDE_TITLE:
        if kw in title:
            return False
    
    non_tech_cats = ["recruitment", "brand management", "sales", "voice over",
                     "fashion modeling", "articles", "digital marketing",
                     "translation", "content writing", "seo"]
    if any(nt in jobs for nt in non_tech_cats):
        if not any(tk in jobs for tk in ["python", "api", "automation", "script", "data", "software"]):
            return False
    
    title_match = [kw for kw in TITLE_KWS if kw in title]
    desc_match = [kw for kw in TECH_KWS if kw in desc or kw in jobs]
    
    if not title_match and not desc_match:
        return False
    
    score = len(title_match) * 3 + len(desc_match)
    if score < 2:
        return False
    
    budget = proj.get("budget") or {}
    min_b = budget.get("minimum", 0)
    max_b = budget.get("maximum", 0)
    hourly = proj.get("hourly_project_info")
    
    budget_str = ""
    if hourly and max_b:
        hrs = hourly.get("commitment", {}).get("hours", "")
        budget_str = f"${max_b}/h" + (f"×{hrs}h/周" if hrs else "")
    elif min_b and max_b:
        budget_str = f"${int(min_b)}-${int(max_b)}"
    elif max_b:
        budget_str = f"${int(max_b)}"
    
    bids = proj.get("bid_stats", {}).get("bid_count", 0)
    
    all_kws = title_match + [d for d in desc_match if d not in title_match]
    unique_kws = list(dict.fromkeys(all_kws))
    
    return {
        "title": proj["title"],
        "url": f"https://www.freelancer.com/projects/{proj.get('seo_url', '')}",
        "budget": budget_str,
        "bids": bids,
        "type": proj.get("type", "fixed"),
        "time": datetime.fromtimestamp(proj.get("submitdate", 0)).strftime("%m-%d %H:%M"),
        "tags": unique_kws[:8],
        "desc": desc[:200],
    }

def main():
    print(f"\n{'='*60}")
    print(f"  Freelancer Project Search v2 | {datetime.now().strftime('%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    seen = set()
    results = []
    
    for page in range(1, 6):
        print(f"Page {page}...", end=" ")
        data = fetch(page)
        projects = data.get("projects", [])
        if not projects:
            print("no data")
            break
        for p in projects:
            pid = p.get("id")
            if pid and pid not in seen:
                seen.add(pid)
                good = is_good(p)
                if good:
                    results.append(good)
        print(f"matched: {len(results)} cumulative")
        time.sleep(1.5)
    
    results.sort(key=lambda x: (x["bids"] if x["bids"] is not None else 999))
    
    print(f"\n{'='*60}")
    print(f"  Matched {len(results)} projects")
    print(f"{'='*60}\n")
    
    if not results:
        print("No matches found.\n")
        return
    
    for i, r in enumerate(results[:20], 1):
        tag_str = " ".join(r["tags"])
        bid_str = f"{r['bids']} bids" if r['bids'] is not None else "new"
        print(f"{'─'*60}")
        print(f"  #{i} {r['title'][:70]}")
        print(f"    Budget: {r['budget'] or 'unlisted'} | {bid_str} | {r['type']} | {r['time']}")
        print(f"    Tags: {tag_str}")
        print(f"    URL: {r['url']}")
    
    if len(results) > 20:
        print(f"\n  ... {len(results)-20} more in saved file")
    
    path = f"/opt/data/projects/online-earning/output/projects_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {path}")

if __name__ == "__main__":
    main()
