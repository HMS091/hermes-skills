# 第7次超时分析 (2026-06-04 13:34)

## Session Summary

Script timed out at 300s again — same root cause as the 5 previous consecutive timeouts (Pitfall 28). The user claimed the git network fix would stop timeouts, but the remaining bug is purely a **time budget calculation** issue, not a network/git problem.

## Evidence Collected

| Item | Value | Notes |
|------|-------|-------|
| Stale /tmp/bounty_* dirs | **27** | One per interrupted SIGKILL run |
| Orphan PID | **2241** | do_bounty.py for Scottcjn/Rustchain/issues/6847, alive 3+ min after parent died |
| Last stats entry | 2026-06-04T00:51:40 | ~13h gap confirms save_stats() module-level problem |
| Orphan status | S (sleeping) | Waiting on socket — likely DeepSeek API |

## What Was Done (code patches applied)

1. **Added `SUBPROCESS_TIMEOUT = 240`** constant at line 62 (next to CRON_TIMEOUT)
2. **Fixed line 370 guard check**: `if elapsed > CRON_TIMEOUT` → `if elapsed + SUBPROCESS_TIMEOUT > CRON_TIMEOUT`

## What Still Needs Fixing (was truncated by max_tool_calls)

1. **Line 418 second guard check** — Still `if elapsed > CRON_TIMEOUT` without subprocess budget. Same fix needed.
2. **Kill orphan PID 2241** — `kill 2241` then `rm -rf /tmp/bounty_*`
3. **Move save_stats() into main()** — Module level (line 480) means it never fires on SIGKILL. Must use `try/finally` inside `main()`.
4. **Add cleanup_stale_bounty_dirs()** at top of `main()` — pre-clean /tmp/bounty_* dirs older than 30 min before starting.

## Verify Before Next Run

```bash
# Line 370 fix
grep -n "elapsed + SUBPROCESS_TIMEOUT" /opt/data/scripts/smart_bounty_search.py
# Should show: 371:        if elapsed + SUBPROCESS_TIMEOUT > CRON_TIMEOUT:

# Line 418 still broken  
sed -n '416,420p' /opt/data/scripts/smart_bounty_search.py
# Should show elapsed > CRON_TIMEOUT (needs fixing)

# save_stats() still module level
tail -5 /opt/data/scripts/smart_bounty_search.py
# Should show save_stats() at line 480 (outside main)

# Stale dir count
find /tmp -name "bounty_*" -type d 2>/dev/null | wc -l
```

## Timeline

| Time | Event |
|------|-------|
| 12:28:59 | Last successful stats entry |
| 12:32-13:12 | 5 consecutive timeouts |
| 12:57 | "Final fix" (MAX_CANDIDATES=1 + startup check) applied, but guard used `elapsed > 280` not `elapsed + 240 > 280` |
| 13:34 | 7th timeout — this session |
| 13:34 | `SUBPROCESS_TIMEOUT=240` added + line 370 fixed |
