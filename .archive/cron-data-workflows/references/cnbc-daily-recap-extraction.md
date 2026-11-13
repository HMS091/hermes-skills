# CNBC Daily Market Recap Extraction

The CNBC "stock market today live updates" article is a single-page goldmine for daily briefing macro context. It publishes daily after market close and contains everything needed for the briefing's macro/environment section.

## URL Pattern

```
https://www.cnbc.com/2026/07/16/stock-market-today-live-updates.html
```

The URL is date-anchored (`YYYY/MM/DD/slug`). Find the current one by navigating to `cnbc.com/markets/` or searching Google News for "stock market today live updates CNBC".

## Data Points Contained in a Single Article

| Data Point | Extraction Method | Example |
|-----------|-----------------|---------|
| S&P 500 close + daily change | `<p>` text containing "S&P 500" | "ended the day down 1.01% at 7,457.69" |
| Nasdaq close + daily change | `<p>` text containing "Nasdaq" | "lost 1.4% to finish at 25,520.24" |
| Dow close + daily change | `<p>` text containing "Dow Jones" | "shed 406.55 points, or 0.77%" |
| Weekly performance | `<p>` text containing "weekly" | "S&P 500 off 1.6%, Nasdaq slid 2.9%, Dow fell 0.9%" |
| Sector-level drivers | `<p>` text after index numbers | "chip stocks suffer", "semiconductor names" |
| Analyst quotes | Text in `"quoted"` strings | "We are seeing signs of fatigue..." — Edward Jones strategist |
| Geopolitical updates | `<p>` text mentioning countries | "Kuwait said Iran attacked a power plant", "US strikes against Iran" |
| Consumer sentiment | `<p>` text mentioning surveys | CNBC All-America Economic Survey results |
| Earnings highlights | `<p>` text near earnings mentions | "Travelers Companies rose over 8% after earnings" |
| Commodity impacts | `<p>` text mentioning oil/energy | "Oil elevated on Middle East tensions" |
| AI/tech specific | `<p>` text mentioning AI/chip | "Chinese open-source models rivaling leading offerings" |

## Extraction via curl

```bash
# Find the latest daily recap article URL first
curl -sL --max-time 12 "https://www.cnbc.com/markets/" \
  -H "User-Agent: Mozilla/5.0" 2>/dev/null | \
  grep -oP 'href="/2026/[^"]*stock-market-today[^"]*"' | head -1

# Then extract all paragraph text
url="https://www.cnbc.com/2026/07/16/stock-market-today-live-updates.html"
curl -sL --max-time 15 "$url" -H "User-Agent: Mozilla/5.0" 2>/dev/null | \
  grep -oP '(?<=<p>)[^<]{50,500}(?=</p>)'
```

## Extraction via browser (when curl fails)

```python
browser_navigate("https://www.cnbc.com/markets/")
# The markets landing page shows:
# - Major indices (SPX, DJIA, IXIC) from the top bar
# - Top market-moving headline with summary
# - Scrollable news list
# Gold, oil prices are typically in the commodities section
```

## Durable Analysis Frame

Financial analysis articles (from CNBC, Reuters, Investing.com) often contain **durable analytical frameworks** that remain relevant for weeks, not just the day they were published:

- **Fed rate probability**: "Markets pricing in X% chance of September rate hike" — the framework (FedWatch tool, inflation data dependency) persists even as the specific percentage changes
- **Analyst bull/bear thesis**: "Chinese open-source AI models rivaling leading offerings" — this structural analysis point remains relevant across multiple briefings
- **Central bank stance quotes**: "Hawkish turn among central banks" — framing persists until the next Fed meeting

**Technique**: When you find a dated article with an analytical framework still applicable, cite it with context: "7月初文章指出..." rather than pretending it's breaking news.

## Caution

- The daily recap URL changes every market day — the date is embedded in the URL path
- On weekends (Friday close data, Sunday briefing), the latest recap is from Friday. This is expected — the article covers the full Friday trading session
- CNBC may serve a Cloudflare JS challenge from some environments. Fall back to the RSS feed if curl returns 0 bytes
- The article's analyst quotes are from their specific timeframe — a quote from July 3 about "cautiously constructive" gold outlook may be stale by July 18 if there have been significant data releases since
