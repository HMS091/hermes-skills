# Bounty Cron Job — Token Cost Analysis

> Generated: 2026-06-04 from actual measurement of `smart_bounty_search.py` + `check_bounty_prs.py`

## DeepSeek V4 Flash Pricing (confirmed via DeepSeek API docs)

| Item | Price |
|------|-------|
| 1M input tokens (cache hit) | **$0.0028** |
| 1M input tokens (cache miss) | **$0.14** |
| 1M output tokens | **$0.28** |

## Per-Run Token Breakdown

### Input: ~5100 tokens per cron tick
| Component | Est. tokens | Cacheable? |
|-----------|------------|------------|
| System prompt (base + memory + skills + user profile) | ~3500 | ✅ Yes (same every run) |
| Script stdout (bounty listings, ~4KB of CN+EN text) | ~1600 | ❌ No (changes each run) |

### Output: ~2 tokens (`[SILENT]`) — negligible

### One run: ~$0.000715 (no cache) — or ~$0.000234 (with cache hit on system prompt)

## Daily/Monthly Cost by Frequency

Values assume DeepSeek cache works for the fixed system prompt portion:

| Frequency | Runs/day | No cache (worst) | With cache (likely) |
|-----------|----------|-----------------|-------------------|
| every 5 min | 288/day | $10.20/月 | **$3.37/月** |
| every 2 min | 720/day | $15.45/月 | **$5.05/月** (current) |
| every 1 min | 1,440/day | $30.90/月 | **$10.10/月** |
| every 30 sec | 2,880/day | $61.80/月 | **$20.19/月** |

Includes both `smart_bounty_search.py` + `check_bounty_prs.py` (latter runs every 30min, adds ~$1/month).

## Key Insight: Marginal Cost of Tighter Frequency

- 2min → 1min: **doubles cost** ($5→$10/mo) but rarely catches new bounties faster because real competition hits within seconds-to-minutes, not minutes
- The current 2min setting ($5/mo) is the sweet spot — tight enough to catch fresh bounties within their first cycle, loose enough that cost doesn't dominate

## When to Rethink

- If switching to a more expensive model (e.g., DeepSeek V4 Pro at $0.435/M input instead of $0.14), cost approximately **3x**
- If moving from `[SILENT]` to full-report output (longer responses), output token cost becomes non-negligible
- If the script output grows significantly (more bounties found), the context token count goes up proportionally
