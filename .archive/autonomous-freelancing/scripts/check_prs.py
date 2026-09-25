#!/opt/hermes/.venv/bin/python3
"""Check GitHub Bounty PR status — for cron usage. Alerts on merge/close/comments."""
import json, urllib.request, os, sys
from datetime import datetime

PRS = [
    {"repo": "tommycet/proofworks-genlayer", "pr": 35, "name": "CONTRIBUTING.md Bounty (proofworks-genlayer)"},
]

env_file = "/opt/data/.env_bot"
token = None
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if "GH_BOT_TOKEN" in line and "=" in line:
                raw = line.split("=", 1)[1].strip().strip('"').strip("'")
                token = raw.replace("export ", "")
                break

if not token:
    print("❌ No token found in /opt/data/.env_bot")
    sys.exit(1)

H = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "User-Agent": "auto-bot"}
changes = []

for item in PRS:
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{item['repo']}/pulls/{item['pr']}", headers=H)
        pr = json.loads(urllib.request.urlopen(req, timeout=15).read())
        merged = pr.get("merged", False)
        state = pr.get("state")
        comments = pr.get("comments", 0) + pr.get("review_comments", 0)

        if merged:
            changes.append(f"🎉 {item['name']} — MERGED! Payment pending.")
        elif state == "closed":
            changes.append(f"❌ {item['name']} — Closed (not merged)")
        if comments > 0:
            changes.append(f"💬 {item['name']} — {comments} comment(s)")
    except Exception as e:
        changes.append(f"⚠️ {item['name']} — Check failed: {e}")

if changes:
    for c in changes:
        print(c)
else:
    print("No changes — all PRs still pending")
