# GitHub Bounty Auto-Execution Pitfalls

## Issue 1: Fork API Returns a List (Not a Dict)

When POSTing to `/repos/{owner}/{repo}/forks`, GitHub returns **a list of fork objects**, not a single object. The naive code:

```python
fork = gh(f"https://api.github.com/repos/{owner}/{repo}/forks")
print(f"Fork: {fork.get('full_name', 'ok')}")
```

Crashes with `'list' object has no attribute 'get'` because `fork` is a list, not a dict.

**Fix:** The endpoint returns `[{...}]` — a list with one element (the newly created fork). Access it with `fork[0].get('full_name')`.

**Root cause:** The `gh()` function always calls `json.loads()` regardless of endpoint. The forks endpoint returns a list at the top level because it's a POST to a collection endpoint.

## Issue 2: Fine-Grained PATs Cannot Fork

Fine-grained personal access tokens issue:
```
403 Resource not accessible by personal access token
```
on fork creation. This is a GitHub platform limitation — fine-grained PATs support Contents, Pull Requests, and Issues, but NOT fork operations.

**Solution:** Use a **classic PAT** (`ghp_...`) with the `repo` scope. Classic tokens CAN fork repos.

## Issue 3: Cron Scripts Time Out on API Rate Limits

The `smart_bounty_search.py` script queries 7 different GitHub search endpoints sequentially with 0.3s sleep between each. Each endpoint returns up to 30 results (210 total raw results). For 136 unique results, the filter + loop + fork-attempt cycle can exceed 120 seconds.

**Causes:**
- GitHub unauthenticated rate limit: 60 req/hr. Authenticated: 5,000 req/hr
- Each `search/issues` call is 1 request
- The 0.3s sleep adds 2.1s between queries
- Fork attempts add additional API calls

**Fix:** 
- Remove per-query sleep (replace with one 1s delay after all queries)
- Reduce queries to the 3-4 most productive ones
- Set per-item processing timeout (skip slow repos)
- Wrap fork attempt in try/except with immediate skip on failure

## Issue 4: GitHub "Bounty" Labels Are Mostly Noise

Real-world scan (June 2, 2026): Of 136 unique issues tagged with "bounty":
- 100% had $0 reward attached
- Most were internal test repos, token bounties (MRWK, DOI, RT, WATT), or casual issue trackers
- Zero real USD/EUR bounties found

The "bounty" label on GitHub correlates with **open-source task tracking**, not monetary reward. Platforms like Gitcoin, Bounties Network, or external bounty boards are where real cash lives.

## Issue 5: Fork "Succeeds" for New Machine Accounts But Repo Doesn't Exist

A fork POST to `/repos/{owner}/{repo}/forks` can return `202 Accepted` (creating async) for a brand-new machine account (0 repos, created 24h ago), but the fork never actually materializes as a repo. Cloning the supposed fork URL `https://github.com/MACHINE_USER/repo.git` gives:

```
remote: Repository not found.
fatal: repository 'https://github.com/MACHINE_USER/repo.git/' not found
```

**Root cause:** GitHub's fork creation is asynchronous and may silently fail for accounts that:
- Were created very recently (< 48h)
- Have no existing repos
- Are using a new fine-grained PAT without full `repo` scope on the forked repo
- The fork returned 202 (queued) but the background job was rejected or not allowed

**Detection:** Before cloning, verify the fork exists:
```bash
curl -s -H "Authorization: Bearer $TOKEN" "https://api.github.com/repos/$MACHINE_USER/$REPO"
# If returns 404, the fork didn't materialize
```

**Workarounds (in priority order):**
1. **Use a Classic PAT** (`ghp_...`) with `repo` scope — classic tokens consistently succeed at forking even for new accounts
2. **Let the machine account mature** — create a dummy repo first, wait 48h before relying on fork API
3. **Direct-branch PR** (if the machine account has Write collaborator access) — push directly without forking
4. **Manual one-time fork** — user clicks "Fork" once per target repo, then the agent pushes to the existing fork

## Issue 6: GitHub API Calls Without Socket Timeout Hang Indefinitely

The `urllib.request.urlopen()` default has **no socket timeout**, so a single slow API call can hang the entire script for minutes. In a cron context where the job has a 120s outer timeout, even 2-3 slow calls will kill the process.

**Fix:** Always set global and per-call timeouts:
```python
import socket
socket.setdefaulttimeout(15)

def gh(url, data=None):
    ...
    return json.loads(urllib.request.urlopen(req, timeout=15).read())
```

Also reduce the sleep between API calls from 0.3s to 0.2s — GitHub's authenticated rate limit (5,000 req/hr) means you can send requests much faster without hitting the cap.

## Issue 7: Fork API Returns List (Not Dict) — Comprehensive Handling

The old fix only checked `isinstance(fork_resp, list)`. A more robust approach handles all response shapes:

```python
fork_resp = gh(f"https://api.github.com/repos/{owner}/{repo_name}/forks", data={})
if isinstance(fork_resp, dict):
    fork_owner = fork_resp.get("owner", {}).get("login", my_login)
    fork_full = fork_resp.get("full_name", f"{fork_owner}/{repo_name}")
elif isinstance(fork_resp, list) and len(fork_resp) > 0:
    fork_owner = fork_resp[0].get("owner", {}).get("login", my_login)
    fork_full = fork_resp[0].get("full_name", f"{fork_owner}/{repo_name}")
else:
    fork_owner = my_login
    fork_full = f"{fork_owner}/{repo_name}"
```

## Issue 8: Silent AI Write Failure — File Never Created, Empty PR

The AI analysis step can claim to generate a file (e.g., `frontend_test_framework.md`) and report success, but the file is **never written to the filesystem**. All subsequent git operations are no-ops:

```
💡 AI 建议 1 个修改:
   ✅ create frontend_test_framework.md — Create a comprehensive design document
📤 Commit & Push...
🔄 创建 PR...
❌ GitHub API 错误 422: "No commits between upstream:master and fork:branch"
```

**Investigation** (confirmed live June 3, 2026 on limetext/lime #380):
- `find /tmp -name 'frontend_test_framework.md'` → nothing
- `git diff origin/master..origin/feature-branch` → empty (0 files, 0 lines)
- `git rev-list --count origin/master...origin/feature-branch` → `0 0`
- The branch on GitHub has **exactly the same content** as the fork's master — only `.github`, `LICENSE`, `README.md`
- Git reflog shows only `clone` and `fetch` — no commit or stash entries

**Root causes:**
- The AI-generated file content is held in memory but never passed to a `write()` call
- The write destination path may point outside the cloned repo directory
- The script's "write → commit → push" step is in a try/except that swallows the error
- The success message is printed optimistically before the write actually happens

**Fix — always extract and call write explicitly:**
```python
# DON'T trust AI to handle file I/O — extract content and write yourself
design_content = ai_result.generated_files[0].content  # or similar extraction
file_path = os.path.join(clone_dir, "docs", "frontend-test-framework.md")

# Write explicitly
os.makedirs(os.path.dirname(file_path), exist_ok=True)
with open(file_path, "w") as f:
    f.write(design_content)

# Verify
assert os.path.exists(file_path), f"File {file_path} not written"
assert os.path.getsize(file_path) > 0, f"File {file_path} is empty"

# Now git operations will work
subprocess.run(["git", "add", "."], cwd=clone_dir, check=True)
subprocess.run(["git", "commit", "-m", "Add frontend test framework design doc"], cwd=clone_dir, check=True)
```

## Issue 9: GitHub API Rate Limiting When Fetching Issue Comments

When investigating bounties, fetching issue comments via the GitHub API can hit rate limits if insufficient sleep is used between requests. The unauthenticated limit is 60 req/hr — fetching 5+ issues' worth of comments will exhaust it quickly.

**Fix:**
1. Always use authenticated requests (the bot token) for comment fetching
2. Authenticated limit: 5,000 req/hr — comfortable for scanning
3. If rate-limited, switch to reading the issue page via the browser instead

## Issue 10: Bountysource-Defunct Bounties (Dead Money Signal)

Bounties linked to Bountysource (defunct since ~2023) will never pay out. Detect by searching the issue body for `bountysource-plugin` HTML comments. Even if the price tag appears real ($40) and competition is low (7 comments), the platform is dead — do not waste time on these.

## Issue 11: Cron Script — `save_stats()` Runs After `main()` (Never Executed on Timeout)

In `smart_bounty_search.py`, the `save_stats()` call is at **module level on the last line of the file** (line 480), placed AFTER `if __name__ == "__main__": main()` (line 457-458). This means:

```python
# Execution order:
# 1. Lines 1-4:  imports
# 2. Lines 6-69: constants (fast)
# 3. Lines 71-245: function defs (fast)
# 4. Lines 247-458: main() def + the `if __name__ == "__main__": main()` call
#    → main() STARTS HERE. If cron kills it, Python never reaches line 460-480
# 5. Lines 460-480: save_stats() def + call — NEVER RUNS if main() times out
```

**First symptom:** The stats file has no entry for the current run, even though the script got far enough to spawn a subprocess (which takes ~60-240s). E.g., stats show last entry at 12:28:59, but the script ran at 13:06 and spawned `do_bounty.py` — the stats entry is missing because `main()` was killed before returning.

**Fix:** Move stats recording into a `try/finally` block inside `main()`, or call it as the very first action in `main()`:

```python
def main():
    import time
    _record_stats_start()  # ← call at top, before any long operations
    token = load_env()
    ...
    try:
        ...
    finally:
        _record_stats_end()  # ← always runs on normal exit or sys.exit()
```

Note: `try/finally` doesn't protect against `SIGKILL` (the cron's 300s timeout kill), but it does protect against Python crashes, `sys.exit()`, and `KeyboardInterrupt` — which covers the script's own 280s `CRON_TIMEOUT` exit path. The module-level placement protects against nothing.

## Issue 12: Pre-Subprocess Time Check Doesn't Account for Subprocess Duration

The script has an internal `CRON_TIMEOUT = 280` (line 364) — leaving 20s buffer before the cron's 300s limit. Before processing each candidate, it checks:

```python
elapsed = time.time() - start_time
if elapsed > CRON_TIMEOUT:   # line 369
    break
```

**The bug:** This check passes if `elapsed < 280`, but does NOT account for the upcoming `do_bounty.py` subprocess which can take up to **240 seconds** (its own timeout). 

**Worked example (from the June 4, 2026 13:06 run):**
- Search phase consumed ~120-210s (14 GitHub API queries × up to 15s each for slow responses)
- At 200s, `elapsed=200 < CRON_TIMEOUT=280` → check passes → proceed
- At ~203s, `do_bounty.py` starts with `timeout=240`
- At 300s, cron kills the parent process → `do_bounty.py` becomes orphan, still running
- Only 97s of the 240s subprocess got to execute before parent death
- Result: Failed bounty, orphaned subprocess, leaked `/tmp/bounty_*` directory

**Fix — account for subprocess budget at check time:**

```python
SUBPROCESS_TIMEOUT = 240
elapsed = time.time() - start_time
if elapsed + SUBPROCESS_TIMEOUT > CRON_TIMEOUT:
    print(f"   ⏰ 剩余时间 {CRON_TIMEOUT - elapsed:.0f}s 不足 {SUBPROCESS_TIMEOUT}s 子进程需求，等待下一轮")
    break
```

## Issue 13: Orphaned Subprocess + /tmp Directory Leak

When the cron kills `smart_bounty_search.py` (parent), the `subprocess.run()`-spawned `do_bounty.py` (child) becomes an orphan. The orphan continues running with no parent to collect its output or clean up its temp files. Key observations:

- **22 stale `/tmp/bounty_*` directories** accumulated as of June 4, 2026 — one per interrupted run
- **Orphan process example:** PID 1302 (`do_bounty.py` for Rustchain #6847), running 4min 46s after parent was killed, in `S` (sleeping) state with an open socket — likely waiting on DeepSeek API response
- The orphan's stdout/stderr pipes (fds 1, 2) are still connected to the dead parent's pipe objects, meaning no output is captured anywhere
- No mechanism to kill orphans on cron restart

**Fix — pre-cleanup at script start + orphan lifecycle awareness:**

```python
def cleanup_stale_bounty_dirs():
    """Clean /tmp/bounty_* dirs older than 30 min from prior interrupted runs."""
    import subprocess
    subprocess.run(["find", "/tmp", "-name", "bounty_*", "-type", "d", "-mmin", "+30", "-delete"],
                   capture_output=True, timeout=10)
```

Call `cleanup_stale_bounty_dirs()` at the top of `main()`. This won't kill running orphans but prevents `df` exhaustion from accumulating temp directories.

## Issue 14: The "Fixed" Script Still Times Out — Root Cause Pattern

This is a meta-issue. The `smart_bounty_search.py` v3 upgrade claimed to solve timeouts by:
1. Reducing `MAX_CANDIDATES_PER_TICK` from 2 to 1
2. Adding a time check before each candidate loop (line 368-373)
3. Cleaning `/tmp` residuals

But the time check (Issue 12) didn't account for subprocess duration, so the fix was incomplete. On the next cycle, when the search phase took long and a candidate was found, the script overran again.

**Pattern:** When diagnosing a timeout in a cron-spawned script with subprocesses, always check:
- Does the pre-subprocess time budget account for the subprocess's maximum runtime? (elapsed + sub_timeout < cron_timeout)
- Does the stats/save function run BEFORE the long operations, or only at module level after main() returns? (If the latter, kills are invisible in the stats.)
- Are orphan subprocesses cleaned up on script start? (temp dir leak + dangling process)
- Is the API timeout optimistic vs. the number of sequential API calls? (14 calls × 15s each = 210s worst case)

