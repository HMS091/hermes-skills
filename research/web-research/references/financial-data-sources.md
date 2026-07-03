# Financial Market Data Sources

Commodity, forex, and macro-economic data sources discovered through financial market research sessions. All accessible via curl with no API key required.

## Commodity Prices

### Gold (XAU/USD) & Silver (XAG/USD)

**API**: `gold-api.com`
```
curl -s "https://api.gold-api.com/price/XAU"
curl -s "https://api.gold-api.com/price/XAG"
```
Response: `{"symbol":"XAU","price":4041.0,"currency":"USD","updatedAt":"2026-07-01T23:34:58Z"}`

- Free, no auth, no rate limit observed
- Updates every ~30 seconds
- Field `.price` is current spot price in USD

### Other Commodities

No verified free API found yet. For oil (WTI/Brent), try:
- Google News RSS with query "crude oil price 2026"
- MarketWatch quotes page scraping

## Dollar Index (DXY)

**Source**: MarketWatch DXY page
```
curl -sL "https://www.marketwatch.com/investing/index/dxy" \
  -H "User-Agent: Mozilla/5.0" | grep -oP '"price":\s*"?"?([0-9.]+)' | head -1
```
- Extract from JSON data embedded in HTML
- DXY ~101.41 as of July 2026

## Financial News — Google News RSS

Primary reliable source when DuckDuckGo/Google/Bing all block automated queries.

### Base URL format
```
https://news.google.com/rss/search?q=<URL_ENCODED_QUERY>&hl=en-US&gl=US&ceid=US:en
```

### Proven Query Templates

| Topic | Query | Notes |
|-------|-------|-------|
| Gold price | `gold+price+XAU+2026` | General gold headlines |
| Fed policy | `Federal+Reserve+rate+decision+2026+gold` | Rate decisions + gold impact |
| Dollar | `US+dollar+index+DXY+gold` | Dollar-gold relationship |
| Central bank buying | `central+bank+gold+reserves+buying+2026` | CB gold accumulation |
| Geopolitics | `Iran+Israel+US+geopolitical+gold+2026` | War/conflict impact on gold |
| Gold technicals | `gold+death+cross+technical+analysis+2026` | Chart patterns |
| Fed chair | `Kevin+Warsh+Fed+gold+2026` | Fed chair specific news |
| Inflation | `inflation+PCE+CPI+gold+price+2026` | Inflation data impact |

### Extraction
```bash
curl -sL "https://news.google.com/rss/search?q=gold+price+XAU+2026&hl=en-US&gl=US&ceid=US:en" \
  -H "User-Agent: Mozilla/5.0" | grep -oP '(?<=<title>)[^<]+' | head -15
```
- `<title>` tags contain "Headline - SourceName" format
- `<description>` contains HTML links but NOT full summaries — skip it
- The RSS XML is ~15-40KB, fast to download

## Financial News Sites — Extraction Notes

### CNBC
- Articles at `https://www.cnbc.com/YYYY/MM/DD/<slug>.html`
- Page content is JS-rendered — HTML download is ~560KB shell with no article body
- Meta description tag often contains article summary:
  ```
  grep -oP '"description":"([^"]+)"' /tmp/cnbc.html
  ```
- Best used for headlines from index/quotes pages (which are partially server-rendered)

### Reuters
- Articles at `https://www.reuters.com/markets/<section>/<slug>-YYYY-MM-DD/`
- Same JS-heavy limitation as CNBC
- JSON-LD `"description"` in the HTML head often has the article summary
- Interest rate section pages (`/markets/rates-bonds/`) have some server-rendered text

### MarketWatch
- DXY page: `https://www.marketwatch.com/investing/index/dxy`
- Gold articles reliably reachable
- Article texts sometimes server-rendered in paragraph tags

## Gold Market Context for July 2026

Key factors from latest session (captured 2026-07-01):

| Factor | Status | Source |
|--------|--------|--------|
| **Price** | ~$4,041 (XAU/USD) | gold-api.com |
| **DXY** | ~101.41 | MarketWatch |
| **Trend** | Q2 2026 = worst quarter in 13 years | CNBC headlines |
| **Key level** | Below $4,000 first time since Nov 2025 | Finance Magnates |
| **Death cross** | Forming, target ~$3,400 if confirmed | MarketWatch |
| **Fed chair** | Kevin Warsh (replaced Powell) | Multiple sources |
| **Fed stance** | Held rates steady, signaled potential hike | Reuters, CNBC |
| **Warsh comment** | "Inflation risks have eased" → boosted gold, helped dollar pare losses | Reuters |
| **Geopolitical** | US + Israel attacked Iran — biggest ME operation in 20+ years | Reuters |
| **Gold vs Iran war** | Paradoxically NOT rising on war; rate-hike fears from oil spike override safe haven | NY Post, CNBC |
| **Central banks** | 45% plan to increase gold holdings; 89% expect higher reserves | WGC survey via KITCO |
| **Institutions** | HSBC: sell-off nearing end; RBC: near key buying level | Exchange Rates Org UK |
| **Oil** | Surging on Hormuz disruption risk | ZeroHedge |

## Editable API List Pattern

When researching a new commodity or financial instrument:
1. Search Google News RSS with `"[commodity] + price + 2026"` for context
2. Try `api.gold-api.com/price/XAU` pattern — if a similar API exists for other metals, add it here
3. For forex pairs (EUR/USD, GBP/JPY), try exchangerate-api.com or MarketWatch queries
