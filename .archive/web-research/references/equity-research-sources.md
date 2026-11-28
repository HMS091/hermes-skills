# Equity Research Sources — RSS & API Endpoints

RSS/API sources for stock and equity research that work from restricted environments (no browser needed).

## Seeking Alpha RSS Feeds

Universal format for any US-traded ticker:
```
https://seekingalpha.com/api/sa/combined/{TICKER}.xml
```

Returns ~30 most recent items per ticker. Each `<item>` contains:
- `<title>` — headline text
- `<pubDate>` — RFC 2822 date
- `<link>` — article URL (HTTP 403 on direct access without subscription)
- `<description>` — often empty or minimal

**Known working tickers**: NVDA, AMD, INTC, AAPL, MSFT, GOOGL, META, TSLA, AMZN

**Example usage:**
```python
import urllib.request, xml.etree.ElementTree as ET, ssl, html
ctx = ssl.create_default_context()
req = urllib.request.Request(
    'https://seekingalpha.com/api/sa/combined/NVDA.xml',
    headers={'User-Agent': 'Mozilla/5.0'}
)
resp = urllib.request.urlopen(req, timeout=15, context=ctx)
root = ET.fromstring(resp.read().decode('utf-8'))
for item in root.iter('item'):
    title = item.find('title')
    pubdate = item.find('pubDate')
    if title is not None and title.text:
        t = html.unescape(title.text)
        d = pubdate.text if pubdate is not None else ''
        print(f'{t[:120]} | {d}')
```

## CNBC RSS Feeds (Industry/Theme)

```
https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id={CATEGORY_ID}
```

| Category | ID | Content |
|----------|----|---------|
| Technology | `19854910` | Broader tech industry news (timed out less) |
| Semiconductors | `100006642` | May return empty — check before relying on it |
| US Markets | `100003114` | Market-level coverage |

CNBC RSS often contains semiconductor/chip sector news with Nvidia/AMD/Intel mentions — extract by filtering headlines client-side:
```python
keywords = ['nvidia', 'nvda', 'amd', 'intel', 'chip', 'semiconductor', 'ai', 'gpu']
matches = [t for t in all_titles if any(kw in t.lower() for kw in keywords)]
```

## Market Data Sources

### Trading Economics (Chinese-language stock data)
```
https://zh.tradingeconomics.com/{TICKER_LOWER}:us
```
Example: `https://zh.tradingeconomics.com/nvda:us`

HTML is garbled after StripTags (JS-heavy). Extract via regex:
```python
import re
prices = re.findall(r'([0-9]+\.[0-9]+)', text)
changes = re.findall(r'([0-9.]+%)', text)
```

Data accessible includes: current price, daily change, YTD change, PE ratio, market cap, Q3 analyst forecast.

### East Money (东方财富) — Chinese-language US stock quotes
```
https://quote.eastmoney.com/us/{TICKER}.html
```
Example: `https://quote.eastmoney.com/us/NVDA.html`

Page is JS-rendered. The initial HTML body after curl shows an empty shell with footer only. Use browser if available, or accept that detailed live data may not be extractable.

### Bing Search Snippets (from cn.bing.com)
Search URL: `https://cn.bing.com/search?q={TICKER}+{COMPANY}+消息+2026年7月`

When JavaScript is stripped, price snippets may appear in the raw HTML as plain text. Example extracted: `NVDA at $210.96, +4.03% daily, +27.92% yearly` from a `tradingeconomics.com` snippet in search results.

## What Does NOT Work

| Source | Reason |
|--------|--------|
| Google Search / Google News RSS | Times out from restricted networks |
| Yahoo Finance | Redirects mainland China to "service unavailable" page |
| MarketWatch RSS search | HTTP 401 (requires auth) |
| Finnhub API | Requires valid API key |
| Bing News API | Requires Azure subscription key |
| Investing.com | Cloudflare protected |
| Reuters.com | Times out (blocked) |

## Worked Example: NVDA July 2026

From this session — Seeking Alpha RSS returned these categories of news:

1. **New products/tech**: Nemotron 3 Ultra AI model, Vera Rubin AI platform (Samsung mass-producing HBM), Kyber AI rack delay refutation
2. **Analyst ratings**: BofA Buy reiteration ($compelling value), Citi weighing investor concerns, Wedbush bullish on Vera CPU, 22V Research buy signals at decade-low valuation
3. **Competitor moves**: AMD collaborating with 5C on AI campuses, Intel turnaround accelerating, SambaNova/Syntiant IPO/raising funds, domestic Chinese chip displacement
4. **AI demand signals**: $1.5T cloud capex maintaining AI cycle (BofA/Micron), Nscale $900M credit facility, Positron $750M raise at $5B valuation
5. **Earnings/sentiment**: Stock at cheapest valuation since pre-AI boom ($210.96, ~35x PE), bull/bear articles ("Market underestimates next phase" vs "It's about to get much worse")
