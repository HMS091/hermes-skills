#!/opt/hermes/.venv/bin/python3
"""
GitHub Bounty PR Creator — fork → write → PR pipeline

Usage:
  1. Set GH_BOT_TOKEN in /opt/data/.env_bot
  2. python3 create_bounty_pr.py

Requires: classic PAT (ghp_...) with `repo` scope
"""

import json, urllib.request, base64, os, sys

# ── Token loading ────────────────────────────────────────────
TOKEN = ""
env_file = "/opt/data/.env_bot"
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if "GH_BOT_TOKEN" in line and "=" in line:
                raw = line.split("=", 1)[1].strip().strip('"').strip("'")
                TOKEN = raw.replace("export ", "")
                break

H = {"Authorization": "Bearer " + TOKEN,
     "Accept": "application/vnd.github+json",
     "User-Agent": "auto-bot"}

def gh(url, data=None):
    """GitHub API call. POST if data, GET otherwise."""
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, headers={**H, **{"Content-Type": "application/json"}}, data=body)
    if data:
        req.method = "POST"
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

# ── Configuration ────────────────────────────────────────────
UPSTREAM = "tommycet/proofworks-genlayer"  # owner/repo to PR against
BRANCH = "feat/contributing-md"
FILE_PATH = "CONTRIBUTING.md"
FILE_CONTENT = """# Contributing to ProofWorks

...

## Running the tests

Run the full test suite with:
```
make test
```
"""

PR_TITLE = "docs: add CONTRIBUTING.md with three core sections"
PR_BODY = "Adds CONTRIBUTING.md with Setup, Running the tests (using `make test`), and Submitting a pull request."

# ── Step 1: Fork ─────────────────────────────────────────────
print("1. Forking upstream repo...")
fork = gh(f"https://api.github.com/repos/{UPSTREAM}/forks", {"name": UPSTREAM.split("/")[1]})
print(f"   Forked to: {fork.get('full_name', 'check url')}")

# ── Step 2: Get base SHA ─────────────────────────────────────
print("2. Getting base commit...")
base = gh(f"https://api.github.com/repos/{UPSTREAM}/git/refs/heads/main")
base_sha = base["object"]["sha"]

# ── Step 3: Create branch on fork ────────────────────────────
my_repo = fork["full_name"]
print("3. Creating branch...")
gh(f"https://api.github.com/repos/{my_repo}/git/refs",
   {"ref": f"refs/heads/{BRANCH}", "sha": base_sha})

# ── Step 4: Create blob → tree → commit ──────────────────────
print("4. Writing file...")
blob = gh(f"https://api.github.com/repos/{my_repo}/git/blobs",
          {"content": base64.b64encode(FILE_CONTENT.encode()).decode(), "encoding": "base64"})
tree = gh(f"https://api.github.com/repos/{my_repo}/git/trees/{base_sha}")
new_tree = gh(f"https://api.github.com/repos/{my_repo}/git/trees", {
    "base_tree": tree["sha"],
    "tree": [{"path": FILE_PATH, "mode": "100644", "type": "blob", "sha": blob["sha"]}]
})
commit = gh(f"https://api.github.com/repos/{my_repo}/git/commits", {
    "message": PR_TITLE,
    "tree": new_tree["sha"], "parents": [base_sha]
})
gh(f"https://api.github.com/repos/{my_repo}/git/refs/heads/{BRANCH}", {"sha": commit["sha"]})

# ── Step 5: Open PR ──────────────────────────────────────────
print("5. Opening PR...")
user = my_repo.split("/")[0]
pr = gh(f"https://api.github.com/repos/{UPSTREAM}/pulls", {
    "title": PR_TITLE, "body": PR_BODY,
    "head": f"{user}:{BRANCH}", "base": "main"
})
print(f"\n✅ PR created: {pr.get('html_url', '?')}")
