# CNBC Quote Page — Embedded `window.__c_data` Extraction

When researching a publicly traded stock, the CNBC quote page embeds a massive JSON blob (`window.__c_data`) that contains structured financial data far richer than any RSS feed. This reference captures the extraction patterns discovered during NVIDIA (NVDA) research in July 2026.

## URL Pattern

```
https://www.cnbc.com/quotes/{TICKER}
```

Example: `https://www.cnbc.com/quotes/NVDA`

## What You Get

The page contains **all of the following** as structured JSON, server-rendered:

| Data Field | Location in ROOT_QUERY | Example Values (NVDA, 2026-07-17) |
|------------|----------------------|-----------------------------------|
| Stock price & change | Page-level `returnsData` | 5D: $210.96 → $202.81 (-3.86%), 1Y: $172.41 → $202.81 (+17.6%), YTD: $186.50 → $202.81 (+8.7%) |
| 52-week range | `getRangeData` → `.ranges[0]` | High: $236.54 (2026-05-14), Low: $164.07 (2025-09-05) |
| Market cap | `getTopPeers` → match by companyName | NVDA: $5.019T |
| Top peers | `getTopPeers` → `.topPeersList[]` | TSM $1.99T, AVGO $1.78T, MU $963B, SKHY $884B, AMD $816B, ASML $711B |
| Earnings (past + future) | `getEarningsData` → `.earnings.lstEarningsBean[]` | Q1 FY2027: EPS $1.87 actual vs $1.757 est (beat); Q2 FY2027 est: $2.085; Next earnings: 2026-08-26 |
| News headlines | grep `"headline":"..."` | Analyst calls, trade tracker moves, market commentary |

## Extraction Commands

### 1. Headlines (for recent stock-specific news)

```bash
curl -sL "https://www.cnbc.com/quotes/NVDA" -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" | grep -oP '"headline":"[^"]*"' | grep -v -E 'stocks|investing|markets|video|club|evening|quote' | head -15
```

### 2. Structured financial data

```bash
curl -sL "https://www.cnbc.com/quotes/NVDA" -H "User-Agent: Mozilla/5.0" -o /tmp/cnbc.html
python3 << 'PYEOF'
import re, json

with open('/tmp/cnbc.html') as f:
    text = f.read()

m = re.search(r'window\.__c_data\s*=\s*(\{.+?\});', text, re.DOTALL)
if not m:
    print("No __c_data found")
    exit(1)

data = json.loads(m.group(1))
root = data.get('ROOT_QUERY', {})

# 1. Price returns data — look for returnsData values
for key, val in root.items():
    if 'returnsData' in str(root):
        # returnsData is nested in the quote page data, not in ROOT_QUERY directly
        pass

# 2. 52-week range
for key, val in root.items():
    if 'getRangeData' in key:
        obj = val.get('ranges', [None])[0] if isinstance(val, dict) else None
        if obj:
            print(f"52W High: ${obj.get('high')} ({obj.get('highDate')})")
            print(f"52W Low: ${obj.get('low')} ({obj.get('lowDate')})")

# 3. Peers / market cap
for key, val in root.items():
    if 'getTopPeers' in key:
        peers = val.get('topPeersList', []) if isinstance(val, dict) else []
        for p in peers:
            mc = float(p.get('marketCap', 0)) / 1e6  # millify
            print(f"{p.get('symbol')}: ${p.get('last')} | ${mc:.2f}T | {p.get('change_pct')}%")

# 4. Earnings
for key, val in root.items():
    if 'getEarningsData' in key:
        earnings = val.get('earnings', {}).get('lstEarningsBean', []) if isinstance(val, dict) else []
        for e in earnings:
            if e.get('announcedDate'):
                print(f"EARN: {e['announcedDate']} | Actual EPS: {e.get('epsAdjActualValue')} vs Est: {e.get('epsEstimatedValue')} | Surprise: {e.get('surprise')}")
            else:
                print(f"EARN EST: EPS est {e.get('epsEstimatedValue')} | Next report: {e.get('nextEarningsDate')} | FY{e.get('fiscalYear')} Q{e.get('qtrId')}")

# 5. Stock price changes (embedded in page-level JSON, not ROOT_QUERY but in the main __c_data)
# Look for returnsData in the page-level __c_data JSON
for key in ['returnsData', 'getRangeData', 'getTopPeers', 'getEarningsData']:
    found = [k for k in root.keys() if key in k]
    if found:
        print(f"{key}: {len(found)} match(es)")

# Note: returnsData may be at the page-level __c_data, not inside ROOT_QUERY
# Check the top-level keys of data too
if 'returnsData' in data:
    for r in data['returnsData']:
        print(f"RETURN {r['type']}: ${r['closePrice']} ({r['closeDate']}) | {r.get('changePct', 'N/A')}%")
PYEOF
```

### 3. Quick summary (one-liner)

```bash
curl -sL "https://www.cnbc.com/quotes/NVDA" -H "User-Agent: Mozilla/5.0" -o /tmp/cnbc.html && python3 -c "
import re, json
with open('/tmp/cnbc.html') as f:
    t = f.read()
m = re.search(r'window\.__c_data\s*=\s*(\{.+?\});', t, re.DOTALL)
if m:
    d = json.loads(m.group(1))
    # Price data at top level
    if 'returnsData' in d:
        for r in d['returnsData']:
            print(f\"{r['type']}: \${r['closePrice']} ({r['closeDate']}) {r['changePct']}%\")
    # Peers
    for k,v in d.get('ROOT_QUERY',{}).items():
        if 'getTopPeers' in k and isinstance(v,dict):
            for p in v.get('topPeersList',[]):
                mc = float(p.get('marketCap',0))/1e6
                print(f\"{p['symbol']}: \${p['last']} | {mc:.2f}T | {p['change_pct']}%\")
"
```

## NVDA July 2026 Worked Example

From this session — the CNBC quote page returned:

**Price data:**
- 5D: $210.96 → $202.81 (-3.86%)
- 1MO: $210.69 → $202.81 (-3.74%)
- 3MO: $201.68 → $202.81 (+0.56%)
- 1Y: $172.41 → $202.81 (+17.63%)
- YTD: $186.50 → $202.81 (+8.75%)

**52-week:** High $236.54 (2026-05-14), Low $164.07 (2025-09-05)

**Peers (by market cap):**
- NVDA: $5.02T
- TSM: $1.99T
- AVGO: $1.78T
- MU: $963.6B
- SKHY: $884B
- AMD: $816.8B
- ASML: $711.2B

**Earnings:**
- FY2027 Q1 (announced 2026-05-20): Actual EPS $1.87 vs Estimated $1.757 — **BEAT**
- FY2027 Q2 (next: 2026-08-26): Estimated EPS $2.085
- FY2027 Q3: Estimated EPS $2.357
- FY2027 Q4: Estimated EPS $2.676

**News headlines recovered:**
- "Apple, Nvidia vie for title of world's most valuable company"
- "Here are Friday's biggest analyst calls: Nvidia, SpaceX, Netflix, Apple, Tesla, Alphabet, 3M, Moody's & more"
- "Market opportunities are hiding in plain sight with Nvidia, says GMO's Tom Hancock"
- "Early chip earnings reporters showing how high the bar really is"
- "Nvidia-backed Fireworks hits $17.5 billion valuation as companies pursue cheaper AI models"
- "Here are Thursday's biggest analyst calls: Nvidia, Apple, SpaceX, Blackrock, Cintas, Amazon, JPMorgan & more"
- "Nvidia unveils new AI model and expands Japan's physical AI ecosystem"
- "Here are Wednesday's biggest analyst calls: Nvidia, SpaceX, Tesla, Cava, AMD, Microsoft & more"
- "TSMC to invest additional $100 billion in Arizona after second-quarter profit soars 77%"
- "Trade Tracker: Kevin Simpson buys more Nvidia and Steve Weiss sells Caterpillar"

## Pitfalls

1. **Huge page size**: The CNBC quote page is 700K+ chars of CSS + JS + JSON. Always save to file first.
2. **`window.__c_data` vs `window.__NEXT_DATA__`**: CNBC uses their own `__c_data` variable, NOT Next.js `__NEXT_DATA__`. Don't confuse them.
3. **`returnsData` is at top level of `__c_data`**, NOT inside `ROOT_QUERY` — check the main object directly.
4. **Market cap is formatted as raw number** (e.g., 5019080.00000 for $5.02T) — divide by 1e6 for trillions.
5. **Headline noise**: CNBC headlines include many boilerplate category names. Always filter with `grep -v`.
6. **Earnings surprise field**: `"UP"` = beat, `"DOWN"` = miss, `"UNCH"` = future/not yet reported.
7. **CNBC blocks rapid requests** — add `--connect-timeout 15 --max-time 20` to curl.
8. **The embedded `window.__c_data` also includes** `feature_flags`, `pfl_data` (subscription features), and analytics scripts — these are noise, focus on `ROOT_QUERY`.
