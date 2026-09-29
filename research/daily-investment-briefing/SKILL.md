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

- **Identify the snapshot SHAPE before computing anything** (2026-09-27 run): the pre-run JSON can flip
  from the after-hours snapshot to the **official close** payload — `price 225.07 / change +0.49 / change_pct 0.22`
  with a `timestamp` that has **no clock time** (`"Sep 24, 2026"`). Here `price` IS the session close and
  `change` IS that session's move (225.07 = 9/25 close, 224.58 = 9/24 close → +0.49 ✓; TSLA 372.11 vs 377.94
  → −5.83 ✓). Rules: clock time in `timestamp` ⇒ after-hours, derive `price − change`; bare date ⇒ official
  close, use `price` as-is. The historical API **does catch up**: fetch it first and compare `rows[0]` — if
  `rows[0].close == price` and `rows[0-1].close == price − change`, no derivation/injection is needed and
  `ma_calc.py`'s `INJ` dict should stay empty. Never trust the `timestamp` date label (it read "Sep 24" for the
  Sep 25 close) — the historical API is the authority.
- **Weekend runs**: when the cron fires on a Beijing Sunday = US Saturday, there is NO new session; the
  snapshot repeats the prior briefing's close. Say so explicitly in 口径说明 rather than implying new data.
  Tell: on 2026-09-20 the snapshot `timestamp` reverted to "Sep 17, 2026" while `price 222.27 / change +2.93`
  were exactly the 9/18 close (and matched the previous day's briefing to the cent). Confirm by diffing the
  new briefing's numbers against the previous `*_briefing.md`; if identical, frame the piece as
  周末复盘 + 下周前瞻 (add 下周事件日历 and this week's 周涨跌幅) instead of a new session wrap.
- **Gold-api.com returns the same value all weekend** (2026-09-19 and 09-20 both 4,379.00) — a duplicate
  snapshot, not a flat market; label it as such when the w/wend run cites it.
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
  environment already ships `fetch_news.py`, `generate_briefing_html.py`, `net_probe.py`, and
  **`briefing_hist.py`** (created 2026-09-21: urllib-based Nasdaq historical fetch → prints last 8 rows
  plus MA5/10/20/50/100/200, 20-day avg volume, 2-year and 52-week high/low with dates, and the prior
  year-end close for YTD). Run `python3 /opt/data/scripts/briefing_hist.py` instead of rewriting it.
  It used to hard-code `todate="2026-09-22"` (which silently made the API look weeks stale) and now defaults
  to today; **if a helper prints rows that are older than the snapshot, check its `todate`/`INJ` before
  blaming the API**.
- **The historical API catches up fully when the session is old enough (2026-09-28 run):** `rows[0]` was
  `09/25 close 225.07` = exactly the snapshot `price`, and `rows[1] = 224.58 = price − change`. When that
  holds, **no derivation and no `INJ` injection is needed** — leave `INJ` empty in `ma_calc.py`, confirm by
  printing `rows[0]`, and compute MAs straight off the API. Only reach for `price − change` when the API
  still ends at the prior session.
- **Beijing-Monday-07:32 runs (US Sunday ~19:30 ET) have no new US session** — same "no new data" shape as
  the weekend, and NVDA/TSLA repeat the previous briefing's Friday close to the cent (diff the two `.md`s to
  confirm). **The difference from Sat/Sun: gold-api DOES return a genuine new-week quote** (2026-09-28:
  4,264.30 @ 23:30 UTC vs Friday's ~4,285.76, and it matched the 21世纪经济报道 6:35 print of 4,264.08
  −0.49% to the dollar). So frame Monday runs as **周一开盘前瞻**: gold/oil/futures are live, equities are
  not, and the payload is this week's calendar.
- **Best new-week intraday snapshot source:** the 07:0x–07:1x Eastmoney quick-news pair
  `一觉醒来，…` / `国际油价拉升，布油涨破…美元…` (source 21世纪经济报道) — one paragraph carries 截至北京时间 6:35 的
  WTI/布伦特 %+level、现货黄金 %+level、现货白银、美股三大指数期货涨跌、加密货币爆仓人数、CME 加息概率、伊朗/特朗普表态。
  Pair it with `一周前瞻` (stock.eastmoney.com, 07:17) = the week calendar + 瑞银/美银等机构对美光/耐克的最新修正。
  That two-article pair plus `国际金融要情 |（周X …）` covers a whole Monday briefing.
- **Crude-oil 口径 sanity check:** a Brent − WTI spread much wider than ~$6 is a flag, but *not* automatically
  an error — in the Hormuz-crisis regime the whole `国际金融要情` row legitimately prints Brent 105.30 vs
  WTI 93.31 (~$12, 2026-09-29). What actually proved the 2026-09-27 Brent 104.32 wrong was that it could not
  be reconciled with the next morning's Brent 98.84 (+1.4%). So: reconcile across two days/sources first, and
  when a single source is internally consistent, report it with a one-line caveat instead of "correcting" it.
- **A normal Tuesday-morning run (Beijing 07:3x = US 19:3x the prior day) DOES have a new US session.**
  Shape check: `timestamp` carries a clock time (`Sep 28, 2026 7:30 PM ET`) ⇒ after-hours snapshot ⇒ derive
  `price − change`. 2026-09-29 worked example: NVDA 229.68 − 0.82 = **228.86** matched media "+1.68%" to the
  cent; TSLA 358.38 − 0.93 = 357.45 but the official close was **357.36 (−14.75, −3.96%)** — the derivation
  can be a few cents off, so **always grep a US ticker-history page (`investing.com`/`stockanalysis.com`
  "Closed" line prints price + change + % together) and prefer the official close** in the table, keeping the
  derived number only as the cross-check.
- **`国际金融要情` can print a WRONG SIGN on the gold row** (2026-09-29: "现货黄金 4,123.70, +0.21%" on a day
  spot closed ~−3.8% and every other source, incl. COMEX futures, was down 3–4%). Treat a sign that
  contradicts the whole market as a benchmark mismatch in that table — do not average it in, say so in 口径说明,
  and take the day's spot from the news wires instead.
- **Best gold-close source for a big down day: `金价查询网` (huangjinjiage.cn)**, whose daily wrap prints the
  intraday high, the low, `创X月X日以来新低`, and a `截至 23:57 报 NNNN.NN（−Y%）` line — one fetch settles the
  spot close and the range. Pair it with the 05:4x–07:0x Eastmoney 快讯 ("现货黄金跌近4%，报4115.24美元/盎司") for
  a second confirmation.
- **US-side news for NVDA/TSLA is best found with plain English `web_search`** (worked well 2026-09-29:
  "NVIDIA Nvidia stock September 28 2026 close" surfaced the buyback story + price/volume; "Tesla stock
  September 28 2026" surfaced the JPMorgan PT cut and the exact close). Eastmoney covers the Chinese angles
  (宏观/黄金/日程); the English search covers company-level catalysts and the official closing print.
- **Week-ahead calendar source (Monday/Tuesday runs):** the Eastmoney/腾讯转载 of 见闻财经日历
  《下周重磅日程：美国非农与中国PMI…》 carries the whole week in one article (OpenAI DevDay, Trump AI
  meeting + America.gov, Micron earnings, Tesla Roadster/Cybercab, 非农 date, A-share holiday window).
  Don't rebuild the calendar from scratch — search `本周重磅日程 <month>日` and extract it.
- **`web_extract` on Eastmoney article URLs was 100% reliable this run (2026-09-28, 7/7 URLs)** — including
  `国际金融要情`, whose body the raw-urllib `em_article.py` path **cannot** see (the static HTML contains no
  `现货黄金`/`美元指数`; the body is injected). So try `web_extract` FIRST, batches of 3–5 URLs; keep
  `em_article.py` as the fallback it was designed to be.
- **Same-day Open-price conflicts are normal, never merge them:** 2026-09-28 财联社《早报》 quoted 现货黄金
  4,285.12 (+0.27%) while 21世纪经济报道 (6:35) quoted 4,264.08 (−0.49%) — a U-turn in sign. List both, and pick
  as headline whichever agrees with the collected gold-api value.
- **Helpers added 2026-09-25 (keep them, they save a full round trip every run):**
  `em_urls.py <keywords...>` prints `date | title | url` (fetch_news.py only prints truncated content and
  hides URLs — you need the URL to extract full text); `em_article.py <url> [chars] [offset]` fetches an
  Eastmoney article with urllib + crude tag strip (the reliable path when `web_extract` 403s/times out);
  `ma_calc.py` recomputes NVDA/TSLA MA5/10/20/50/100/200 **after injecting the derived closes the lagging
  Nasdaq API is still missing** (edit the `INJ` dict at the top with `price - change` before running;
  2026-09-29 shape: `INJ = {"NVDA": [("09/28/2026", 228.86)], "TSLA": [("09/28/2026", 357.36)]}`,
  `TODATE` = today, API still ended at 09/25 — the printed `newest rows` line confirms the injection was needed).
  `execute_code` is BLOCKED in cron mode — use `terminal` for all of this.
- **Cleanest gold-close 口径: the 06:3x 美股收盘 quick-news article.** It carries a one-line
  `伦敦金现跌X.XX%，报NNNN.NN美元/盎司；伦敦银现…` — an explicit % + level for spot, which
  `国际金融要情` does NOT give (that page lists 现货黄金/COMEX/上金所9999/黄金T+D/沪金主连 levels + 美元指数
  + every US Treasury tenor, but no spot % change). Search keyword `伦敦金现 收盘` lands on it directly.
  Also expect the RMB-priced gold legs (上金所/T+D/沪金主连) to fall **3–5x harder** than 伦敦金现 — report
  both, it signals domestic premium/speculative unwind rather than pure FX.
- Prefer **`web_extract` on Eastmoney article URLs** for the full text of the day's roundups: the search
  API truncates `content` to 150 chars. Two calls cover a whole briefing — `国际金融要情 |（周X YYYY.M.D）`
  (all indices + 现货/COMEX/上金所 gold + oil + yields + dollar in one page) and the day's 美股收盘 roundup.
  Find URLs by printing `r['url']` from `fetch_news.em_search()`. **The `国际金融要情` page is the single best
  source — it settles 现货金/COMEX/上金所/美元指数/10Y 收益率/三大指数 in one fetch; always extract it first.**
- **When `web_extract` fails** (keyless Parallel/Firecrawl backend times out or 403s — common), fetch the
  Eastmoney article directly with urllib + a crude tag strip; works every time, no proxy:

  ```python
  import urllib.request, re, html
  req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
  h = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'ignore')
  t = re.sub(r'<script.*?</script>', '', h, flags=re.S)
  t = re.sub(r'<[^>]+>', '\n', t); t = html.unescape(t); t = re.sub(r'\n\s*\n+', '\n', t)
  print(t[t.find('美伊'):t.find('美伊')+4200])   # anchor on a phrase near the body start
  ```
- **`web_search` is unreliable here too** — keyless Firecrawl returns 403 for roughly half the queries and
  `mcp__lightpanda__search` may be absent. Do NOT spend calls retrying; go straight to `fetch_news.py`
  (Eastmoney, always works) and treat `web_search` results as a bonus when they do return.
- Morning (Beijing 07:30) runs land ~3.5h after the US close, so the Nasdaq historical API frequently
  **still ends at the previous session**. That is expected, not a failure: derive the close as `price - change`
  and confirm against media % moves from the roundup articles (e.g. 2026-09-22 run: 227.38 / 375.21 derived,
  media +2.30% / +3.00% ✓).

## Support files

- `generate_briefing_html.py` status cards: the snapshot `change/change_pct` made the dashboard's top cards
  read **after-hours** values as the day change (opposite sign vs the briefing). Fixed 2026-09-16: cards now
  show the derived close (`price - change`) as the headline value and label the move 盘后 explicitly. If you
  edit that generator, keep that convention — never print a bare `change_pct` from the raw JSON.
- **The generator must branch on snapshot shape (fixed 2026-09-21).** Always printing `price - change` as
  "收盘" is only correct for the normal after-hours snapshot. The degenerate variant (see the `timestamp`
  pitfall) carries `price` = session close and `change` = that session's move, so the old code rendered the
  *prior* day's close as "收盘" (e.g. showed 219.34 for NVDA when the 9/18 close was 222.27), contradicting
  the briefing. `is_afterhours(d)` now tests the `timestamp` for a clock time (`\d{1,2}:\d{2}\s*(AM|PM)?`):
  with a time → headline `price - change`, sub-line labelled 盘后; without → headline `price`, sub-line
  labelled 当日. Keep both branches whenever you touch the cards, and diff the rendered card against the
  briefing's table before finishing.
- `references/eastmoney-news-api.md` — Eastmoney search API mechanics + usage.
- `templates/briefing_template.md` — the markdown briefing template (copy + fill).

## Pitfall: the historical API can lag a full session

On the 2026-09-16 run the Nasdaq historical API still ended at 09/14 rows even though the 9/15 session was
closed and widely reported. Reverse-engineer the new close (`price - change`) and validate it against a media
headline's % move before reporting; do NOT report the stale row as "today".
