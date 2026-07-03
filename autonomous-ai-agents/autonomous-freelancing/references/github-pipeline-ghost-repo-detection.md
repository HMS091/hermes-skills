# Ghost Repo / Dead Bounty Detection

## Problem
A repo can look active (stars, commits) while the maintainer never pays out. The Cognitive-OS $3k bounty had 31 comments, 11+ PRs submitted, and $0 paid out over 2+ weeks.

## Detection Signals

### 1. Payout Track Record (Most Revealing)
```python
# Check closed PRs — merged vs unmerged
terminal(f"curl -s 'https://api.github.com/repos/{owner}/{repo}/pulls?state=closed&per_page=10' -o /tmp/prs_closed.json")
# If 0 merged out of 5+ closed PRs → ghost repo
```

### 2. Fork/Star Ratio
```python
# If forks ≈ stars × 7 → bots forking each other
# Cognitive-OS: 56 stars, 381 forks → ratio 6.8 → 🔴
terminal(f"curl -s 'https://api.github.com/repos/{owner}/{repo}' -o /tmp/repo_info.json")
```

### 3. User Account Age
```python
# Accounts < 30 days old with 0 followers → high risk
terminal(f"curl -s 'https://api.github.com/users/{owner}' -o /tmp/user_info.json")
```

### 4. Bountysource Check
Bountysource platform has been defunct since 2023. Issue body containing `bountysource-plugin` = dead money.

### Validation Workflow
Before executing on any non-trusted bounty:
1. Check repo `pushed_at` — >90 days stale = skip
2. Check user `created_at` — <30 days + 0 followers = high risk
3. Check closed PR merge rate — 0 merged / 5+ closed = ghost
4. Check open PR count — 10+ open for same issue = extreme competition
5. Check fork/star ratio — forks > stars × 3 = suspicious
