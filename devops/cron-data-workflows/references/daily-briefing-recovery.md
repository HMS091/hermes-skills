# Daily Briefing Pipeline — Recovery Case Study

**Date:** 2026-06-08  
**Context:** Cron job `daily-briefing` (ID: `994eb6fd48cb`) failed with "Script not found: /opt/data/scripts/daily_briefing.py"

## Job Configuration

```json
{
  "id": "994eb6fd48cb",
  "name": "daily-briefing",
  "script": "daily_briefing.py",           // ← This file does not exist
  "schedule": "30 23 * * *",               // 23:30 CST daily
  "deliver": "all",
  "no_agent": false,
  "skills": [],
  "repeat": { "completed": 3 },
  "last_status": "error",
  "last_error": "Script not found: /opt/data/scripts/daily_briefing.py"
}
```

## The Pipeline Architecture

```
[Scheduler 23:30 CST]
  │
  ├─ Script phase: daily_briefing.py (MISSING → error)
  │   └─ Expected to output: JSON with stocks/crypto/gold/NAS status
  │
  └─ Agent phase: receives prompt with {script_output}
      └─ Expected to:
          1. Parse raw JSON
          2. Web search for supplemental news
          3. Generate markdown briefing at /opt/data/briefings/{date}_briefing.md
          4. Run /opt/data/scripts/generate_briefing_html.py
```

## Raw Data Format

The data file at `/opt/data/briefings/2026-06-08_raw.json` uses this schema:

```json
{
  "date": "2026-06-08",
  "collection_time": "2026-06-08 08:01 CST",
  "stocks": {
    "nvda": { "symbol": "NVDA", "price": 205.1, "change": -13.56, "change_pct": -6.2, "volume": 219660072, "range_52w": "138.83-236.54" },
    "tsla": { "symbol": "TSLA", "price": 391.0, "change": -27.45, "change_pct": -6.56, "volume": 63422210, "range_52w": "273.21-498.83" }
  },
  "gold": { "symbol": "XAU/USD", "price": 4347.0, "unit": "USD/oz", "source": "gold-api.com" },
  "crypto": { "btc": { "price": 63185.88, "change_24h_pct": 3.81 }, "eth": ..., "sol": ..., ... },
  "nas_status": {
    "uptime": "9d14h",
    "load": [3.3, 2.58, 2.3],
    "disk_root": { "used_gb": 237, "total_gb": 890, "pct": 27 },
    "disk_data": { "used_gb": 286, "total_gb": 3500, "pct": 8 },
    "memory_gb": { "total": 15, "used": 9.5, "available": 6.0 },
    "swap_gb": { "total": 11, "used": 5.1 },
    "proxy_status": "DOWN"
  },
  "source": "nasdaq.com, gold-api.com, huobi.pro, google-news"
}
```

## Legacy Raw Data Format (June 6 and earlier)

An older format at the same path flattens the structure:

```json
{
  "nvda": { "symbol": "NVDA", "price": 205.1, "change": -13.56, "change_pct": -6.2, "volume": 219660072, "timestamp": "Jun 4, 2026", "source": "nasdaq.com" },
  "tsla": { ... },
  "gold": { "symbol": "XAU/USD", "price": 4330.0, "unit": "USD/oz", "source": "gold-api.com" },
  "nvda_news": [...],
  "tsla_news": [...],
  "gold_news": [...],
  "market_news": [...],
  "collection_time": "2026-06-06 17:33:05",
  "collection_date": "2026-06-06"
}
```

## Briefing Template

The desired template uses this structure (markdown):

```markdown
---
# 📋 每日投资简报 — {collection_date}

📡 数据采集时间: {collection_time}

## 📊 三大标的行情概览

| 标的 | 现价 | 涨跌 | 涨跌幅 |
|------|------|------|--------|
| **NVDA 英伟达** | $xxx.xx | +x.xx | +x.xx% |
| **TSLA 特斯拉** | $xxx.xx | +x.xx | +x.xx% |
| **XAU 黄金** | $x,xxx/盎司 | - | - |

## 🔥 今日热点
... (per-stock analysis, 5-8 lines each)

## 📈 技术面简析
... (key support/resistance levels)

## 🌐 宏观环境
... (macro factors affecting the market)

## ⚠️ 风险提示
... (downside risks, short-term concerns)
```

## Browser-Based Price Extraction (2026-06-25 Case)

**When Yahoo Chart API also fails (rate-limited, blocked, or proxy issues), the browser tool is the most reliable fallback.**

**Problem (Jun 25-26 run):** Same volume-as-price parsing errors as Jun 23. Additionally, the Yahoo Chart API was inaccessible and subagent-based web research returned empty tool traces because cron jobs lack the `web_search` tool.

**Solution:** Use `browser_navigate` to load Yahoo Finance quote pages and extract prices from the accessibility tree.

**Winning workflow (proven Jun 25-26):**
1. `browser_navigate(url="https://finance.yahoo.com/quote/NVDA/")` → snapshot shows price, change, change%
2. Read the accessibility tree: `StaticText "195.74"` (price), `StaticText "-3.17"` (change), `StaticText "(-1.59%)"` (pct)
3. Detail list below provides: Previous Close, Open, Day's Range, Volume, 52-wk Range
4. Gold price is visible in the persistent index bar at the top of every Yahoo Finance page (no extra nav needed)
5. Repeat for TSLA, then construct the corrected `_raw.json` manually
6. Write the briefing and run `generate_briefing_html.py`

**Why subagents don't work in cron jobs:** `delegate_task` with `toolsets: ["web"]` runs but produces empty tool traces. The cron runtime doesn't expose `web_search`. Always use the main agent's browser tool for data extraction in cron jobs.

**Key lesson:** The browser accessibility tree is a reliable structured-data source — no JavaScript rendering needed, no API rate limits, no proxy config. Yahoo Finance and Google Finance both render clean static snapshots.

## Lessons Learned

1. **The `daily_briefing.py` script was configured but never created.** Cron jobs with `script` field need the file to physically exist at `/opt/data/scripts/` — the scheduler won't gracefully degrade if it's missing.
2. **Raw data can accumulate from other processes.** The `*_raw.json` files in briefings/ may be generated by a manual script, a different cron job, or a previous version of the pipeline. Always check what's available.
3. **The HTML dashboard generator is at `/opt/data/scripts/generate_briefing_html.py`** — it reads `*_raw.json` and `*_briefing.md` from the briefings directory and produces `dashboard.html`. It runs independently from the data-collection script.
4. **Web news fetching is unreliable from this environment** — Yahoo Finance rate-limits, gold-api.com needs an API key, Google News RSS may return empty results. The prompt-based news structure should be optional, not a hard blocker.

## Price Data Enrichment (2026-06-23 Case)

**Problem:** The pre-run data-collection script may produce prices with parsing errors. In the Jun 23 run, NVDA/TSLA prices were volume numbers (121M and 47M) erroneously parsed as prices, producing `invalid literal for int()` errors. Gold price ($4,192.20) was correct.

**Solution:** Always cross-check extracted price data against the Yahoo Finance Chart API as a fallback enrichment step before generating the briefing.

**Enrichment workflow:**

```
1. Try to parse {script_output} JSON
2. If NVDA/TSLA prices look suspicious (e.g., >$1000 or match volume ranges), fetch from Yahoo
3. Fetch via Python urllib (not curl-pipe):
   python3 -c "from urllib.request import urlopen, Request; import json;
   h = {'User-Agent': 'Mozilla/5.0'};
   r = Request('https://query2.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=1d&range=2d', headers=h);
   d = json.loads(urlopen(r, timeout=10).read())"
4. Extract: meta['regularMarketPrice'], meta['chartPreviousClose'], meta['fiftyTwoWeekHigh/Low']
5. Calculate change: price - prev_close
6. Valid ranges: NVDA ~$140-240, TSLA ~$280-500, gold use gold-api.com
```

**Key observations:**
- The script's `error` field in JSON (`"invalid literal for int() with base 10: '121921656.262064'")` is the raw value the parser tried to coerce — this is actually the volume, not the price
- `query2.finance.yahoo.com` works when `query1` returns "Too Many Requests"
- Always retrieve price data from Yahoo in a Python script block (`execute_code` or `python3 -c`) — direct `curl | python3` pipes are blocked by security scanners in this environment
