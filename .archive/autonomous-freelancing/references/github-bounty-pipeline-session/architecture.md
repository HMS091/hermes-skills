# GitHub Bounty Hunter — Reference

## Current Script State (June 2026)

### smart_bounty_search.py (v3 — freshness-aware)
- Searches 8 different GitHub queries for bounty-labeled issues
- Returns 100-140 items per scan
- ⏰ **时效过滤**: 只保留创建 < 90天的 Issue（老Issue直接跳过）
- Filters crypto/token rewards out
- Rates each item by $ amount, AI-friendliness, competition level, creation date
- 🛡 **二次验证**: 自动执行前检查仓库 `pushed_at` < 90天
- **Auto-executes** vetted targets (≥$50 + AI-friendly + <10 comments + <90天 + 仓库活跃 + not done)
- Uses `subprocess.run([sys.executable, "do_bounty.py", url])` for execution
- History tracking via `.bounty_history.json`

### do_bounty.py (v2.2 — fixed fork logic + retry)
- Reads Issue title, body via GitHub REST API
- Forks the target repo via `POST /repos/{owner}/{repo}/forks` with `data={}` 
  - **Critically**: `data={}` in Python is falsy! The `gh_request()` helper uses `if data is not None` (NOT `if data`) to handle this properly
  - Waits 3 seconds, then uses `gh_request_retry()` (max 5 retries, 3s delay, only retries 404s) to verify fork exists
  - Fork reference is ephemeral — never stored/reused across runs
- Clones fork with token auth + **clean_env (无代理环境)** — defined BEFORE first git call
- Creates branch from `origin/{default_branch}` — no upstream remote needed
- Collects repo file tree + key files (README, setup.py, package.json, etc.)
- Calls DeepSeek Chat API with structured prompt to generate solution
- Expects JSON array output with file paths, actions, and content
- On parse failure: falls back to `.github/ISSUE_TEMPLATE.md` reference
- Commits, pushes (**clean_env**), creates PR via GitHub API
- Saves result to `.bounty_history.json`

### check_bounty_prs.py
- Monitors existing submitted PRs (currently proofworks-genlayer #35)
- Reports: state (open/closed), merged flag, comment count
- Notifies if merged, closed-without-merge, or new comments appear

## Common Tasks

### Manual trigger on a specific bounty
```bash
cd /opt/data/scripts
python3 do_bounty.py "https://github.com/owner/repo/issues/123"
```

### Force a scan (even if no good targets expected)
```bash
cd /opt/data/scripts
python3 smart_bounty_search.py
```

### Clear history to retry all bounties
```bash
echo '{}' > /opt/data/scripts/.bounty_history.json
```

### Update DeepSeek model
If DeepSeek changes model names (like `deepseek-chat` → `deepseek-v4-flash`), update the `DEEPSEEK_MODEL` constant in `do_bounty.py`.

## Environment Dependencies

| Dependency | Location |
|------------|----------|
| Python | `/opt/hermes/.venv/bin/python3` |
| GH Token | `/opt/data/.env_bot` (env var `GH_BOT_TOKEN`) |
| DeepSeek API Key | `/opt/data/.env` (env var `DEEPSEEK_API_KEY`) |
| History file | `/opt/data/scripts/.bounty_history.json` |
| Cron jobs | Managed via `cronjob` tool (auto-completed at session level) |

## DeepSeek Prompt Design for Code Generation

The system prompt in `do_bounty.py` is carefully structured:

1. **Role**: Professional software engineer
2. **Instruction**: Understand issue → analyze repo → generate working code
3. **Output format**: Strict JSON array with path/action/content/description
4. **Quality rules**: full files, not diffs; match existing code style; meaningful tests, not stubs; no unrelated changes
5. **Temperature**: 0.3 (deterministic enough for code generation)

The user prompt includes:
- Issue title + body (truncated to 2000 chars)
- Repo file tree (up to 100 files)
- Key file names (for reference reading)
- Explicit instruction on what to generate

## Freshness Filter Implementation

```python
NOW = datetime.now(timezone.utc)
MAX_AGE_DAYS = 90

def is_fresh(created_at_str):
    """Filter: only issues from last 90 days"""
    created = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    return (NOW - created).days <= MAX_AGE_DAYS

def check_repo_active(token, repo_full_name):
    """Secondary validation: repo must have recent activity"""
    repo = gh(token, f"https://api.github.com/repos/{repo_full_name}")
    pushed = datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00"))
    return (NOW - pushed).days <= MAX_AGE_DAYS
```

## Git Proxy Cleanup (Docker)

All git subprocess calls must use `clean_env` to prevent hanging:

```python
clean_env = {k: v for k, v in os.environ.items()
             if not k.lower().startswith('http_proxy')
             and not k.lower().startswith('https_proxy')}
subprocess.run(["git", "fetch", "origin"], env=clean_env, timeout=120)
subprocess.run(["git", "push", ...], env=clean_env, timeout=120)
subprocess.run(["git", "clone", ...], env=clean_env, timeout=120)
```

**Do NOT use upstream remote** — `git fetch upstream` on large repos (15k+ stars) hangs inside Docker with proxy issues. The fork was just created from upstream, so `origin/{default_branch}` already has the latest code.

## Fork API — Current Approach (v2.2+)

The old approach had two bugs:
1. `data={}` is falsy in Python → sent GET instead of POST → got a paginated fork list instead of creating a fork
2. `clean_env` used before definition → `NameError`

### Current simplified flow:

```python
# STEP 1: POST to create fork (empty JSON body)
# NOTE: data={} is falsy in Python! gh_request uses `if data is not None`
gh_request(token, f"https://api.github.com/repos/{owner}/{repo}/forks", data={})

# STEP 2: Wait for async creation
time.sleep(3)

# STEP 3: Verify fork exists with retry (only retries 404s)
fork_resp = gh_request_retry(token, f"https://api.github.com/repos/{my_login}/{repo_name}")
# gh_request_retry retries up to 5x with 3s delay, only on 404
```

### gh_request_retry helper

```python
def gh_request_retry(token, url, data=None, method=None, retries=5, delay=3):
    """带重试的 GitHub API 请求（用于 fork 等异步操作）"""
    for attempt in range(retries):
        try:
            return gh_request(token, url, data=data, method=method)
        except urllib.error.HTTPError as e:
            if e.code == 404 and attempt < retries - 1:
                print(f"   ⏳ 等待资源就绪 ({attempt+1}/{retries})...")
                time.sleep(delay)
                continue
            raise
    raise RuntimeError(f"重试 {retries} 次后仍然失败")
```

### Why no list-handling?

The old code tried to handle `POST /forks` returning a list (which only happens if the buggy GET was sent instead of POST). Since the `data={}` falsity bug is fixed, the POST always returns a single fork object. No more list handling needed.

### Key lesson (2026-06-03)

`data={}` in Python is falsy. `if data:` skips when you pass `data={}`. Always use `if data is not None` when `None` is the legitimate "no data" sentinel.

## Bountysource — Dead Platform

`bountysource.com` returns HTTP 000 (unreachable). Any issue with `bountysource-plugin` in its body is flagged. Skip it — the platform that held the bounty money is gone.
