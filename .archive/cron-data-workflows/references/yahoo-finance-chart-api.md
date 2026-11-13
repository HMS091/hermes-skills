# Yahoo Finance Chart API

A reliable, no-API-key data source for US stock and futures prices. Works without a proxy — direct connections succeed from most environments.

## Endpoints

Primary:
```
GET https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?range=5d&interval=1d
```

Fallback (use when query1 returns "Too Many Requests"):
```
GET https://query2.finance.yahoo.com/v8/finance/chart/{SYMBOL}?range=5d&interval=1d
```

Both `query1` and `query2` subdomains serve identical data. Rotate between them when rate-limited.

## Common Symbols

| Asset | Symbol | Notes |
|-------|--------|-------|
| NVIDIA | `NVDA` | Nasdaq |
| Tesla | `TSLA` | Nasdaq |
| Gold Futures | `GC%3DF` | URL-encoded `GC=F`, COMEX |
| S&P 500 ETF | `SPY` | SPDR S&P 500 |
| Nasdaq ETF | `QQQ` | Invesco QQQ |
| Bitcoin | `BTC-USD` | Crypto |

## Response Structure (key fields)

```json
{
  "chart": {
    "result": [{
      "meta": {
        "regularMarketPrice": 210.69,
        "chartPreviousClose": 204.87,
        "regularMarketVolume": 238264530,
        "fiftyTwoWeekHigh": 236.54,
        "fiftyTwoWeekLow": 142.03,
        "regularMarketDayHigh": 211.39,
        "regularMarketDayLow": 206.50,
        "regularMarketDayOpen": 207.33,
        "regularMarketTime": 1781812800,
        "exchangeName": "NMS",
        "instrumentType": "EQUITY",
        "currency": "USD"
      },
      "timestamp": [1781271000, 1781530200, 1781616600, ...],
      "indicators": {
        "quote": [{
          "open": [204.0, ...],     // May be absent for some ranges
          "high": [209.0, ...],
          "low": [203.0, ...],
          "close": [204.87, 210.69, ...],
          "volume": [180000000, 238264530, ...]
        }]
      }
    }]
  }
}
```

**Important:** The `timestamps` array indices align with the indicators arrays. Index 0 is the oldest day; index N-1 is the most recent trading day. `chartPreviousClose` in `meta` is the close before the first timestamp, not before the most recent one — use it to calculate today's change.

```python
m = meta
day0_close = indicators['quote'][0]['close'][0]     # First day's close
today_close = indicators['quote'][0]['close'][-1]    # Last day's close
prev_close = m['chartPreviousClose']                 # Close before Day 0
```

## Calculating Change/Change%

```python
price = meta['regularMarketPrice']
prev_close = meta['chartPreviousClose']
change = price - prev_close
change_pct = round((price - prev_close) / prev_close * 100, 2)
```

## Fetch Pattern (Security-Safe)

Environments with security scanners (curl-pipe-to-interpreter blocks) require a two-step pattern:

```python
from urllib.request import urlopen, Request

h = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
r = Request("https://query2.finance.yahoo.com/v8/finance/chart/NVDA?interval=1d&range=2d", headers=h)
d = json.loads(urlopen(r, timeout=10).read())
```

In shell, save to file first then process separately:

```bash
curl -s -o /tmp/nvda.json \
  "https://query2.finance.yahoo.com/v8/finance/chart/NVDA?interval=1d&range=2d"
python3 -c "import json; d=json.load(open('/tmp/nvda.json')); ..."
```

Never pipe curl output directly to a Python interpreter — security scanners flag this pattern.

## Rate Limits

Variable and IP-dependent. The `query1` subdomain may return "Too Many Requests" after as few as 3-5 requests within minutes. Rotate to `query2` when this happens — it typically has a separate rate counter. The `range=5d` parameter fetches more data per call and may help reduce request count. When both subdomains are blocked, wait 5-10 minutes or use the browser tool to navigate to `finance.yahoo.com/quote/{TICKER}/` and extract data via JavaScript DOM queries.

## 30-Day Historical Data (Technical Analysis)

For technical analysis (support/resistance levels, trend direction, RSI context), fetch 1 month of daily OHLCV data:

```bash
curl -s -o /tmp/nvda_1mo.json \
  "https://query1.finance.yahoo.com/v8/finance/chart/NVDA?range=1mo&interval=1d"
```

Parsing (Python, handles the nested quote structure):

```python
import json
from datetime import datetime

d = json.load(open('/tmp/nvda_1mo.json'))
r = d['chart']['result'][0]
quotes = r['indicators']['quote'][0]
timestamps = r['timestamp']
closes = [c for c in quotes['close'] if c is not None]
opens = [o for o in quotes['open'] if o is not None]
highs = [h for h in quotes['high'] if h is not None]
lows = [l for l in quotes['low'] if l is not None]
volumes = [v for v in quotes['volume'] if v is not None]

for i in range(len(timestamps)):
    if i < len(closes) and closes[i] is not None:
        dt = datetime.utcfromtimestamp(timestamps[i]).strftime('%m/%d')
        print(f'{dt}: O={opens[i]:.2f} H={highs[i]:.2f} L={lows[i]:.2f} C={closes[i]:.2f} V={volumes[i]:,.0f}')
```

**Extracting key technical signals from 30-day data:**
- **Trend direction**: Compare first-5 closes vs last-5 closes. A string of lower highs/lower lows confirms downtrend.
- **Support levels**: Look for price levels that were tested 2+ times and bounced (local lows clustered within ~2%).
- **Resistance levels**: Recent highs that capped rallies.
- **Volume confirmation**: Heavy volume on down days vs light volume on up days reveals conviction.
- **Week-over-week change**: Compare last Friday's close to current Friday's close for weekly performance.
- **Relative strength**: Compare the stock's 30-day % change to the sector ETF (NVDA vs SMH/SOX, TSLA vs RIDE).

**Gold futures historical data:**
```bash
curl -s -o /tmp/gold_1mo.json \
  "https://query1.finance.yahoo.com/v8/finance/chart/GC%3DF?range=1mo&interval=1d"
```

## Pitfall: meta.previousClose May Be None

The `meta` object's `chartPreviousClose` or `previousClose` fields may be `null`/`None` for some symbols or time ranges. In this case, fall back to calculating the change manually from the indicator arrays:

```python
# If meta.previousClose is None, use the 2nd-to-last close
closes = r['indicators']['quote'][0]['close']
valid_closes = [c for c in closes if c is not None]
if len(valid_closes) >= 2:
    today_close = valid_closes[-1]
    prev_close = valid_closes[-2]
    change = today_close - prev_close
    change_pct = (today_close - prev_close) / prev_close * 100
elif len(valid_closes) == 1:
    # Only one data point -- compare against open
    opens_arr = r['indicators']['quote'][0]['open']
    today_open = [o for o in opens_arr if o is not None][-1]
    today_close = valid_closes[0]
    change = today_close - today_open
    change_pct = (today_close - today_open) / today_open * 100
```

This is especially common with `range=1mo` for certain symbols (GC=F gold futures, crypto pairs). Always check for None before using the meta fields.

## Pitfall: Gold Futures `chartPreviousClose` (1d vs 5d Discrepancy)

For gold futures (`GC=F` or `GC%3DF`), the `meta.chartPreviousClose` from a `range=1d` call may differ from the actual previous trading day's close visible in the 5d data. Observed discrepancy:

| Endpoint | `meta.chartPreviousClose` | Close array (previous day) |
|----------|--------------------------|---------------------------|
| `range=1d&interval=1d` | $4,157.40 | (no prior close in array) |
| `range=5d&interval=1d` | $4,068.30 | $4,155.10 (index -2) |

**Root cause:** The 1d endpoint's `chartPreviousClose` may be a settlement or official close price set by the COMEX exchange, while the actual last trading session's closing price (visible in the 5d close array) can differ by ~$2-40 for gold futures.

**Fix:** For gold futures, always calculate daily change from the 5d close array (comparing the last two closes) rather than from the 1d endpoint's `meta.chartPreviousClose`. Use this pattern:

```python
# Get gold data with 5d range
response = urlopen(Request("https://query1.finance.yahoo.com/v8/finance/chart/GC%3DF?range=5d&interval=1d", headers=h))
data = json.loads(response.read().decode())
r = data['chart']['result'][0]
quotes = r['indicators']['quote'][0]
closes = [c for c in quotes['close'] if c is not None]

# Use closes array for change, not meta.chartPreviousClose
today_close = closes[-1]
prev_close = closes[-2]  # Previous trading day's close from array
change = today_close - prev_close
change_pct = (today_close - prev_close) / prev_close * 100

# Meta fields for non-change data are still reliable:
fifty_two_high = r['meta'].get('fiftyTwoWeekHigh')
fifty_two_low = r['meta'].get('fiftyTwoWeekLow')
volume = r['meta'].get('regularMarketVolume')
```
