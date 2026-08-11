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

## Pitfalls

- **Gold API & Yahoo direct connections fail** in this environment (SSL `UNEXPECTED_EOF_WHILE_READING`).
  Fall back to media-reported spot/COMEX gold prices found via the Eastmoney news (e.g. 伦敦现货/COMEX
  期货 quotes appear in the daily roundup articles) and mark them as 媒体口径.
- **Proxy** `http://192.168.1.88:7890` exists, but proxy commands can trigger pending-approval in cron
  mode (no user to approve) — avoid depending on it; Eastmoney API works direct.
- **Snapshot vs close discrepancy**: the nasdaq.com quote snapshot (e.g. 7:30 PM ET) can differ sharply
  from the reported session close (e.g. +0.11% vs +2.90%). Present the collected numbers in the table
  AND note the reported close in analysis.
- **News arrays in the raw JSON are usually empty** ("No recent news") — always do the web/API supplement.
- Check `/opt/data/scripts/` for existing helper scripts before building new fetch logic — the
  environment already ships `fetch_news.py`, `generate_briefing_html.py`, `net_probe.py`.

## Support files

- `references/eastmoney-news-api.md` — Eastmoney search API mechanics + usage.
- `templates/briefing_template.md` — the markdown briefing template (copy + fill).
