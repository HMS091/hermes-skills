"""GitHub API helper — reads token from /opt/data/.env_bot, provides gh() function.

Usage:
    from github_api import gh, github_headers
    issue = gh("https://api.github.com/repos/owner/repo/issues/1")
    
    # Or use headers directly:
    H = github_headers()
    import urllib.request
    req = urllib.request.Request(url, headers=H)
"""
import json, urllib.request, os

ENV_FILE = "/opt/data/.env_bot"

def get_token():
    if not os.path.exists(ENV_FILE):
        return None
    with open(ENV_FILE) as f:
        for line in f:
            if "GH_BOT_TOKEN" in line and "=" in line:
                raw = line.split("=", 1)[1].strip().strip('"').strip("'")
                return raw.replace("export ", "")
    return None

def github_headers():
    token = get_token()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "auto-bot"
    }

def gh(url, data=None, method=None):
    """Make a GitHub API call. GET by default, POST if data provided, or specify method."""
    H = github_headers()
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, headers=dict(H, **{"Content-Type": "application/json"}), data=body)
    if method:
        req.method = method
    elif data:
        req.method = "POST"
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def search_issues(query, per_page=30, page=1):
    q = urllib.parse.quote(query)
    url = f"https://api.github.com/search/issues?q={q}&per_page={per_page}&page={page}&sort=created&order=desc"
    return gh(url)

if __name__ == "__main__":
    # Test
    t = get_token()
    print(f"Token found: {'yes' if t else 'no'} ({len(t) if t else 0} chars)")
    if t:
        u = gh("https://api.github.com/user")
        print(f"Authenticated as: {u.get('login')}")
