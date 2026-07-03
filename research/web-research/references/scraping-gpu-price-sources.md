# GPU / Electronics Price Scraping Sources

Hong Kong and China real-time GPU price comparison.

## Hong Kong Sources

### DCFever.com (二手市集) — Curl-friendly
- **URL:** `https://www.dcfever.com/trading/search.php?keyword=RTX+3090`
- **Method:** `curl -sL` (no Cloudflare, no JS required)
- **Parse:** grep for `HK\$[0-9,]+` and card names in HTML meta tags
- **Listing:** Title tags contain card name + price inline, e.g. `ASUS TUF Gaming RTX 3090 24GB HK$7,000`
- **Notes:** ~100+ listings for popular cards. Also has "全新" (new) and "徵求" (wanted) categories.

### Price.com.hk (格價網) — Cloudflare protected
- **URL:** `https://www.price.com.hk/search.php?g=A&q=RTX+3090+24GB`
- **Method:** Requires browser with JS (Cloudflare Turnstile). Curl gets blocked by CF challenge.
- **Alternative:** Google cache / DuckDuckGo may have cached snippets from Price.com.hk

### BigGo Hong Kong (比價)
- **URL:** `https://biggo.hk/s/RTX%203090%20%E4%BA%8C%E6%89%8B/`
- **Method:** curl works, but pricing details are in JS-rendered components
- **Use:** Good as a search discovery tool (finds listings across DCFever, Carousell, JD)

### Carousell Hong Kong
- **URL:** `https://www.carousell.com.hk/rtx-3090/q/`
- **Method:** Requires JS rendering. Curl returns "Enable JavaScript" page.
- **Use:** Browser tool needed.

## China Sources

### Goofish (闲鱼) — JS-heavy SPA
- **URL:** `https://www.goofish.com/search?q=RTX+3090+24G`
- **Method:** Requires full browser (React SPA). Snapshot shows minimal content.
- **Use:** `browser_navigate` + `browser_vision` (screenshot + vision analysis for prices)
- **Alt:** Search DuckDuckGo for `闲鱼 RTX 3090 价格 2026年6月` to find recent articles about market price.

### Taobao (淘宝)
- **URL:** `https://www.taobao.com/list/product/二手3090.htm`
- **Method:** JS-heavy. Browser needed. Anti-bot aggressive.
- **Use:** Browser + vision for price overview.

### JD (京东)
- **URL:** `https://search.jd.com/Search?keyword=RTX%203090%2024G`
- **Method:** Browser needed. Anti-bot moderate.

### ZOL (中关村在线) — Price aggregation
- **URL:** `https://detail.zol.com.cn/vga/s8469/` (RTX 3090 category)
- **Method:** curl-friendly. Lists dealer prices.
- **Use:** Quick reference for commercial pricing across multiple vendors.

## Search Engine Fallback

When direct scraping fails:
```python
# DuckDuckGo HTML (no JS) for search with proxy
curl -sL "https://html.duckduckgo.com/html/?q=RTX+3090+二手+价格+2026" \
  -H "User-Agent: Mozilla/5.0"
```
Parse with regex: `class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</(?:a|div)`

## Currency Conversion
```bash
curl -s "https://api.exchangerate-api.com/v4/latest/HKD" | python3 -c "import json,sys;d=json.load(sys.stdin);print(f'1 HKD = {d[\"rates\"][\"CNY\"]:.4f} CNY')"
```
Current rate (as of 2026-06): ~1 HKD = 0.867 CNY

## Workflow for Price Comparison
1. Scrape DCFever HK with curl → extract all `HK$` prices
2. Search DuckDuckGo for recent (last 2 months) China market price articles
3. Browser → Goofish or Taobao for visual confirmation
4. Convert HK$ to CNY for comparison
5. Present side-by-side table

## Pitfalls
- **Dated articles:** Many "current price" articles are 2-4 months old. Always check publish date.
- **闲鱼价格波动大:** Can swing ¥1,000-2,000 in a month due to AI demand / mining cycles.
- **香港二手标价含水分:** DCFever listing prices are ask prices, not成交价. Negotiation typically -5-10%.
- **全新 vs 二手价差大:** Same card can be HK$6,500 (used) to HK$13,000+ (new old stock sealed box).
