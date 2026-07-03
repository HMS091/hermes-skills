# CoinGecko API Endpoints Reference

## Base URL
`https://api.coingecko.com/api/v3`

## Authentication
Public API (v3) requires **no API key** for basic endpoints. Rate limit: ~30 calls/min on free tier.

## Price & Market Data

### Real-time Price (Bulk)
```
GET /simple/price
  ?ids=bitcoin,ethereum,solana,stellar
  &vs_currencies=usd
  &include_24hr_vol=true
  &include_24hr_change=true
  &include_market_cap=true
```
- **Returns:** `{"bitcoin":{"usd":62600,"usd_24h_vol":3.2e10,"usd_24h_change":-0.88,"usd_market_cap":1.2e12}}`
- **Counts as 1 rate-limit call** regardless of how many coin IDs

### Historical Price Chart
```
GET /coins/{id}/market_chart
  ?vs_currency=usd
  &days=1|7|14|30|90|180|365|max
```
- **`days=1`** → minute-level granularity (~1440 pts)
- **`days=7-30`** → hourly granularity
- **`days=90`** → hourly granularity (~2160 pts) — **best for bootstrap**
- **`days=max`** → daily granularity
- **Returns:** `{"prices":[[timestamp_ms, price], ...], "market_caps":[...], "total_volumes":[...]}`
- ⚠️ **Rate limit: each coin is a separate call** — add `time.sleep(1.5)` between coins

### OHLC Data
```
GET /coins/{id}/ohlc?vs_currency=usd&days=30
```
- Returns `[timestamp_ms, open, high, low, close]` candles
- Useful for candlestick charting but not needed for SMA/RSI/MACD

## Coin Info

### List All Coins
```
GET /coins/list
```
- Returns `[{id, symbol, name}, ...]` — all ~12k coins
- Use to find CoinGecko IDs (e.g., `avalanche-2` for AVAX)

### Coin Details
```
GET /coins/{id}?localization=false&tickers=false&community_data=false&developer_data=false
```
- Returns metadata, description, links, genesis date

## Categories & Trending

### Trending Coins
```
GET /search/trending
```
- Returns top 7 trending coins on CoinGecko
- Includes price data (24h change, etc.)

### Categories
```
GET /coins/categories
```
- Returns market data grouped by category (DeFi, L1, Meme, etc.)

## Proxy Requirements

In China/Docker environments, ALL requests must go through proxy:
```python
PROXY = "http://192.168.1.88:7890"
proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
opener = urllib.request.build_opener(proxy_handler)
```

**Test connectivity:**
```bash
curl -s --proxy http://192.168.1.88:7890 "https://api.coingecko.com/api/v3/ping"
# → {"gecko_says":"(V3) To the Moon!"}
```

## Important Notes

- **Data delay:** Spot prices are ~60-120 seconds delayed on free tier
- **Null handling:** Always check `data.get("usd") is not None` before using — some delisted coins return empty objects
- **Error format:** `{"error": "coin not found"}` or HTTP 429 (rate limit)
- **Alternative:** Binance public API (`api.binance.com/api/v3/ticker/price?symbol=BTCUSDT`) works with same proxy and has higher rate limits
