#!/opt/hermes/.venv/bin/python3
"""Smart Bounty Search — cron-ready. Searches, filters, and saves results."""
import json, urllib.request, time, re, os

TOKEN=***f os.path.exists("/opt/data/.env_bot"):
    with open("/opt/data/.env_bot") as f:
        for line in f:
            if "GH_BOT_TOKEN" in line and "=" in line:
                raw = line.split("=", 1)[1].strip().strip('"').strip("'")
                TOKEN=raw.re...port ", "")

H = {"Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json", "User-Agent": "auto-bot"}

def gh(url, data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, headers=H, data=body)
    if data: req.method = "POST"
    return json.loads(urllib.request.urlopen(req, timeout=20).read())

# Search multiple bounty-related labels
queries = [
    "bounty", "bounty+label:documentation", "bounty+label:good-first-issue",
    "bounty+label:bug", "bounty+label:test", "bounty+label:python",
    "bounty+label:automation",
]

seen, results = set(), []
for q in queries:
    try:
        data = gh(f"https://api.github.com/search/issues?q=is%3Aissue+is%3Aopen+{q}&sort=created&order=desc&per_page=50")
        for item in data.get("items", []):
            if item["html_url"] not in seen:
                seen.add(item["html_url"])
                results.append(item)
        time.sleep(0.5)
    except: pass

# Filter and rank
output, now = [], time.strftime("%Y%m%d_%H%M")
for item in results:
    title, body, url = item.get("title",""), (item.get("body") or "")[:500], item["html_url"]
    text = (title + " " + body).lower()
    amounts = re.findall(r'\$(\d[\d,]*)\s*(k|K)?', title + body[:200])
    max_amt = max((int(n.replace(",","")) * (1000 if k else 1) for n, k in amounts), default=0)
    is_token = any(k in text for k in ["rtc", "watt", "token reward", "bounty: 5 rtc", "bounty: 10 rtc"])
    if is_token and max_amt < 50: continue
    ai_ok = any(k in text for k in ["documentation", "doc", "readme", "test", "python", "script", "automation", "api", "fix", "bug"]) or max_amt >= 100
    if not ai_ok: continue
    output.append({"title": title[:80], "url": url, "amount": max_amt, "comments": item.get("comments",0), "created": item.get("created_at","")[:10]})

output.sort(key=lambda x: (-x["amount"], x["comments"]))
path = f"/opt/data/projects/online-earning/output/smart_bounties_{now}.json"
with open(path, "w") as f: json.dump(output, f, indent=2)

print(f"Found {len(output)} qualifying bounties")
for i, d in enumerate(output[:20], 1):
    a = f"${d['amount']:,}" if d['amount'] else "?"
    c = "LOW" if d['comments']<3 else "MED" if d['comments']<10 else "HIGH"
    print(f"{i:2}. [{a:>8}] [{c}] {d['title'][:60]}")
    print(f"    {d['url']}")
