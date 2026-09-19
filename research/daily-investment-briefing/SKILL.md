---
name: daily-investment-briefing
description: Generate the daily Chinese investment briefing (NVDA/TSLA/gold) — parse collected quotes, supplement with financial news, write markdown briefing, refresh the HTML dashboard. Triggered by the daily cron job or any 每日投资简报 request.
---

# 每日投资简报 (Daily Investment Briefing)

Recurring pipeline (runs daily ~07:30 Beijing time as a cron job) that produces a Chinese-language
investment briefing for NVDA / TSLA / gold (XAU) and embeds it into a self-contained HTML dashboard.

## Pipeline

1. **Parse raw data** — the pre-run script writes `/opt/data/briefings/{collection_date}_raw.json`
   with `nvda`, `tsla`, `gold` (price/change/change_pct/volume), plus `collection_time`,
   `collection_date`, and news arrays (often empty / "No recent news" — do not rely on them).
2. **Supplement news** — order of preference:
   - `mcp__lightpanda__search` or browser search (may be unavailable; do NOT retry in a loop).
   - **Reliable fallback: Eastmoney search API** via `python3 /opt/data/scripts/fetch_news.py <keywords...>`.
     Returns fresh Chinese financial news, no proxy needed. See `references/eastmoney-news-api.md`.
     Keyword groups that worked: `英伟达` `特斯拉` `黄金` `美联储` `美元指数` `美伊谈判 原油`
     `特斯拉 机器人 Optimus` `英伟达 RTX` `黄金 美联储 降息`.
3. **Write the briefing** to `/opt/data/briefings/{collection_date}_briefing.md` using
   `templates/briefing_template.md` (keep the section structure: 行情概览 / 今日热点 / 技术面简析 /
   宏观环境 / 风险提示).
4. **Refresh dashboard**: `python3 /opt/data/scripts/generate_briefing_html.py` → writes
   `/opt/data/briefings/dashboard.html` (all briefings embedded, latest first).
5. **Verify**: `grep -c "{collection_date with /}" /opt/data/briefings/dashboard.html` (expect ≥2:
   card + modal data) and confirm the `.md` file exists with non-trivial size.

## Quality bar (user's standing requirements)

- 全中文、简洁务实; **结论先行** — judgment first, then reasons.
- 每个标的控制在 5-8 行; 有具体数据支撑 (prices, %, volumes, market-cap figures).
- **必须包含风险提示** ⚠️ — 不报喜不报忧. Always list: policy/Fed risk, valuation/positioning risk,
  geopolitical reversal risk, and data-quality caveats.
- **口径说明 (disclosure)**: when sources conflict or fail, state it explicitly in a footnote —
  never present estimated/reported values as authoritative.
- Cron final response = generation report: data table, key points per asset, output file paths,
  verification results.

## Reliable price-history source (for real MAs / 涨跌幅)

`GET https://api.nasdaq.com/api/quote/{SYM}/historical?assetclass=stocks&fromdate=2024-08-01&todate=YYYY-MM-DD&limit=600`
with headers `User-Agent: Mozilla/5.0` + `Accept: application/json` works **direct (no proxy)** and returns
`data.tradesTable.rows` (`date` MM/DD/YYYY, `close/high/low/open` with `$` and thousands separators,
`volume`). Use it to (a) verify the nasdaq.com snapshot actually equals a real session close and
(b) compute MA5/10/20/50/100/200, 52-week high/low, avg volume — far better than quoting stale levels.
Note: stooq.com CSV is JS-challenged/blocked; don't bother. Note the quote-snapshot `timestamp` field can
mislabel the session (e.g. shows "Sep 10" for the 9/11 close) — trust the historical API.

## Snapshot `change_pct` is AFTER-HOURS, not the day change (critical)

The raw-JSON quote snapshot (timestamp like `7:30 PM ET`) often arrives ~3.5h **after** the 4 PM close, so its
`price`/`change`/`change_pct` describe the **after-hours move measured FROM that day's close** — not the
session's gain/loss. Reading it as the day change inverts the story (a real -3.36% day showed as +0.62%).

**Always reverse-engineer and verify the true close:**

```
prev_close  = historical-API close of the PRIOR session (e.g. Fri 9/11)
true_close  = price - change            # exact, to the cent
verify      = prev_close * (1 + media-reported %/100)  # must equal true_close
```

Worked example (2026-09-14): NVDA snapshot `price 212.2597, change +1.2997` → true close **210.96**;
9/11 close 218.29 × (1 − 0.0336) = 210.96 ✓ (media: NVDA −3.36%). Same for TSLA: `359.7694 − 0.7994`
= 358.97 = 365.44 × (1 − 0.0177) ✓ (media: −1.77%). When the two agree to the cent, you have the real
session close with certainty. Report the **close** in the table, show the after-hours price in parentheses,
and put the correction in 口径说明 — never let the script's number stand as the day change.

Also note the historical API lags: right after a session it may still end at the previous day's row.
Use `fromdate=<month start>&todate=<today>` and take `rows[0]`; if it is the prior session, derive the
new close as above rather than reporting the stale row.

## Pitfalls

- **Weekend runs**: when the cron fires on a Beijing Sunday = US Saturday, there is NO new session; the
  snapshot repeats the prior briefing's close. Say so explicitly in 口径说明 rather than implying new data.
- **Gold API & Yahoo direct connections fail** *usually* (SSL `UNEXPECTED_EOF_WHILE_READING`) — but
  gold-api.com succeeds intermittently (2026-09-16 run returned a `XAU/USD` spot snapshot fine). Try it,
  then ALWAYS cross-check against media 现货/COMEX numbers (e.g. 东方财富《国际金融要情》gives 现货,
  COMEX 期金, 上金所 9999 and 黄金 T+D on one line) and disclose every 口径 used.
- **Proxy** `http://192.168.1.88:7890` exists, but proxy commands can trigger pending-approval in cron
  mode (no user to approve) — avoid depending on it; Eastmoney API works direct.
- **Snapshot vs close discrepancy**: the nasdaq.com quote snapshot (e.g. 7:30 PM ET) can differ sharply
  from the reported session close (e.g. +0.11% vs +2.90%). Present the collected numbers in the table
  AND note the reported close in analysis.
- **Gold has several conflicting 口径 on the same day** (gold-api spot snapshot, FX168 现货收盘, COMEX 期金
  which can move the OPPOSITE way). List all of them in the disclosure; never silently pick one.
- **News arrays in the raw JSON are usually empty** ("No recent news") — always do the web/API supplement.
- **Do not use `curl ... | python3 -c` for the Nasdaq historical API in cron mode**: the security scan
  classifies it as `tirith:curl_pipe_shell` and it hangs on `pending_approval` (no user to approve).
  Write a small script that uses `urllib.request` with the required headers instead. Also note file writes
  are restricted to `/opt/data` (`HERMES_WRITE_SAFE_ROOT`) — `/tmp/foo.py` is refused, so put throwaway
  helpers in `/opt/data/scripts/` and delete them afterwards.
- Check `/opt/data/scripts/` for existing helper scripts before building new fetch logic — the
  environment already ships `fetch_news.py`, `generate_briefing_html.py`, `net_probe.py`.

## Support files

- `generate_briefing_html.py` status cards: the snapshot `change/change_pct` made the dashboard's top cards
  read **after-hours** values as the day change (opposite sign vs the briefing). Fixed 2026-09-16: cards now
  show the derived close (`price - change`) as the headline value and label the move 盘后 explicitly. If you
  edit that generator, keep that convention — never print a bare `change_pct` from the raw JSON.
- `references/eastmoney-news-api.md` — Eastmoney search API mechanics + usage.
- `templates/briefing_template.md` — the markdown briefing template (copy + fill).

## Pitfall: the historical API can lag a full session

On the 2026-09-16 run the Nasdaq historical API still ended at 09/14 rows even though the 9/15 session was
closed and widely reported. Reverse-engineer the new close (`price - change`) and validate it against a media
headline's % move before reporting; do NOT report the stale row as "today".
