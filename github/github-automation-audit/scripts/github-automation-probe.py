#!/usr/bin/env python3
"""Read-only inventory of GitHub automation for the authenticated account.

Answers: which repos still have live Actions, what actually ran in a window,
what is still generating notifications, and how many PRs this account authored.
Changes nothing.

Usage:
    GH_TOKEN=ghp_xxx python3 github-automation-probe.py [DAYS] [LOGIN]
        DAYS   lookback window in days for runs / activity (default 60)
        LOGIN  account to search authored PRs for (default: authenticated user)

Token resolution: $GH_TOKEN -> $GITHUB_TOKEN -> contents of $GITHUB_TOKEN_FILE.
Stdlib only. Run this instead of hand-chaining curls: it re-reads the token and
is safe to re-run after a tool timeout.
"""
import collections
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 60


def token():
    for k in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(k):
            return os.environ[k].strip()
    path = os.environ.get("GITHUB_TOKEN_FILE")
    if path and os.path.exists(path):
        return open(path).read().strip()
    sys.exit("no token: set GH_TOKEN / GITHUB_TOKEN / GITHUB_TOKEN_FILE")


TOKEN = token()


def api(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Authorization": "token " + TOKEN,
            "Accept": "application/vnd.github+json",
            "User-Agent": "hermes-automation-audit",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"__error__": "%s %s" % (e.code, path)}
    except Exception as e:  # noqa: BLE001 - report and keep going
        return {"__error__": str(e)}


def paged(path):
    out, page = [], 1
    while page <= 20:
        sep = "&" if "?" in path else "?"
        d = api("%s%sper_page=100&page=%d" % (path, sep, page))
        if not isinstance(d, list) or not d:
            break
        out += d
        if len(d) < 100:
            break
        page += 1
    return out


def since(days):
    return (datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=days)).strftime("%Y-%m-%d")


repos = paged("/user/repos?affiliation=owner,collaborator,organization_member")
print("repos accessible: %d" % len(repos))

registered, ran = {}, {}
for r in repos:
    name = r["full_name"]
    wf = api("/repos/%s/actions/workflows" % name)
    if isinstance(wf, dict) and wf.get("workflows"):
        registered[name] = [(w["name"], w["state"]) for w in wf["workflows"]]
    runs = api("/repos/%s/actions/runs?created=%%3E%%3D%s" % (name, since(DAYS)))
    rr = runs.get("workflow_runs") if isinstance(runs, dict) else None
    if rr:
        ran[name] = collections.Counter(x["name"] for x in rr)

print("\n== repos with REGISTERED Actions workflows (Actions enabled) ==")
print("  none" if not registered else "")
for n, ws in registered.items():
    print("  %s: %d workflows" % (n, len(ws)))
    for nm, st in ws:
        print("     %-45s %s" % (nm[:45], st))

print("\n== repos that actually RAN workflows in the last %d days ==" % DAYS)
print("  none" if not ran else "")
for n, c in sorted(ran.items(), key=lambda x: -sum(x[1].values())):
    print("  %s (%d runs)" % (n, sum(c.values())))
    for nm, k in c.items():
        print("     %4dx %s" % (k, nm))

login = sys.argv[2] if len(sys.argv) > 2 else (api("/user") or {}).get("login")
if login:
    op = api("/search/issues?q=author:%s+type:pr+state:open&per_page=100" % login)
    items = op.get("items", []) if isinstance(op, dict) else []
    total = op.get("total_count") if isinstance(op, dict) else "?"
    print("\n== open PRs authored by %s: %s ==" % (login, total))
    for r, k in collections.Counter(
            i["repository_url"].split("/repos/")[-1] for i in items).most_common():
        print("  %3d  %s" % (k, r))
    for win in (7, 30):
        s = api("/search/issues?q=involves:%s+updated:%%3E%%3D%s&per_page=1"
                % (login, since(win)))
        tc = s.get("total_count") if isinstance(s, dict) else "?"
        print("  items involving %s updated in last %dd: %s" % (login, win, tc))

notifs = paged("/notifications?all=true")
print("\n== stored notifications: %d (proxy for email volume) ==" % len(notifs))
if notifs:
    print("  by reason:", dict(collections.Counter(n["reason"] for n in notifs)))
    for r, k in collections.Counter(
            n["repository"]["full_name"] for n in notifs).most_common(15):
        print("  %3d  %s" % (k, r))
    byday = collections.Counter(n["updated_at"][:10] for n in notifs)
    print("  by date:", dict(sorted(byday.items())))

print("\nNOTE: '0 runs' can mean never-enabled (forks) OR enabled-then-auto-disabled"
      " after long repo inactivity; run history is also truncated. Check commits too,"
      " and remember /commits defaults to the default branch.")
