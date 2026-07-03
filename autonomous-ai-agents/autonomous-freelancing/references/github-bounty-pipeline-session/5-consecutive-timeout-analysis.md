# 5 Consecutive Timeouts After Phase 3 "Final Fix" (2026-06-04 13:15)

## Timeline

| Time | Event | 
|------|-------|
| 12:28:59 | Last successful stats entry: script completed normally |
| 12:32 | First orphaned temp dir: `bounty_j2jl2r44` (empty — mkdtemp only) |
| 12:42 | Second orphaned temp dir: `bounty_wg1_pn5w` (empty) |
| 12:54 | Third orphaned temp dir: `bounty_pu5hixq3` (empty) |
| **12:57** | **Phase 3 fix applied** (MAX_CANDIDATES=1 + startup time check) |
| 13:03 | Fourth orphaned temp dir: `bounty_ggfn45j1` (empty) ← **Fix was insufficient** |
| 13:12 | Fifth orphaned temp dir: `bounty_8_e1_769` (empty) ← **Fix was insufficient** |
| 13:15 | This analysis session |
| **13:21-13:24** | **6th timeout — do_bounty.py PID 1967 captured alive** for `Rustchain/issues/6847`. First time an actual running subprocess (not just empty temp dir) observed after cron kill. 25+ total stale temp dirs accumulated. Stats file confirmed empty since 12:28:59 — 55-min gap with 0 records, proving `save_stats()` module-level bug. |

## Root Cause

The Phase 3 "final fix" at 12:57 applied:
1. `MAX_CANDIDATES_PER_TICK = 1` (was 2)
2. Startup time check before do_bounty.py starts (`if elapsed > CRON_TIMEOUT: break` at line 369)

But the startup time check doesn't account for subprocess duration:
```python
# Current (buggy): elapsed=60s → passes, but subprocess=240s → total=300s
if elapsed > CRON_TIMEOUT: break  # passes for 60 < 280
```

Should be:
```python
# Correct: elapsed=60s → 60+240=300 > 280 → blocked
if elapsed + SUBPROCESS_TIMEOUT > CRON_TIMEOUT: break
```

## Verification Script

Run this to check the current guard logic:
```bash
grep -n "elapsed > CRON_TIMEOUT" /opt/data/scripts/smart_bounty_search.py
# Should return line 369 with: `if elapsed > CRON_TIMEOUT:`
# This is the BUG — needs `elapsed + 240 > CRON_TIMEOUT`
```

## Additional Observations

- All 5 orphaned directories are EMPTY (0 bytes), meaning `tempfile.mkdtemp()` succeeded but `api_clone_repo()` in do_bounty.py never started writing files. This suggests the cron kill happens right at 300s, potentially during or right after the zipball download.
- Stats file stops at 12:28:59 — `save_stats()` at module level (line 480) never executes when script is killed.
- `api.github.com` is reachable (HTTP 200), `github.com:443` is unreachable (connection timeout) — confirmed.

## Recommended Fix (to be applied)

In `smart_bounty_search.py`, replace line 369:
```python
# Before (current):
if elapsed > CRON_TIMEOUT:
# After:
if elapsed + SUBPROCESS_TIMEOUT > CRON_TIMEOUT:
```

Also add a `SUBPROCESS_TIMEOUT` constant near line 364:
```python
CRON_TIMEOUT = 280
SUBPROCESS_TIMEOUT = 240  # match subprocess.run timeout
```
