---
name: crypto-trading
description: Real-time cryptocurrency market monitoring with technical analysis (RSI, MACD, SMA), signal generation, price tracking in SQLite, and automated trading strategy automation. Build, maintain, and iterate crypto monitoring and trading bots.
trigger: "User asks to: monitor crypto prices in real-time, set up trading alerts, build a trading bot, learn technical analysis, do quantitative crypto trading, or track specific coins."
tags: [crypto, trading, technical-analysis, market-monitoring, quantitative]
---

# Crypto Trading — Market Monitoring & Technical Analysis

End-to-end system for real-time crypto price monitoring, technical indicator calculation, buy/sell signal generation, and automated alerting.

## Architecture

```
cron (every 30min) → crypto_monitor.py → CoinGecko API → SQLite (price history)
                                         → Technical Analysis (RSI, MACD, SMA)
                                         → Signal Generation
                                         → Report to user
```

## First-Time Bootstrap (Critical!)

**Problem:** Fresh SQLite DB has 0 data points. RSI needs ≥15, MACD needs ≥26, SMA200 needs ≥200. Running the monitor on an empty DB shows all indicators as `—`.

**Solution:** Backfill 90 days of hourly price history before starting regular monitoring:

```python
# One-time bootstrap — run ONCE before enabling cron
for cid in COINS:
    url = f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart?vs_currency=usd&days=90"
    data = http_get(url)
    for ts_ms, price in data.get("prices", []):
        ts = int(ts_ms / 1000)
        conn.execute("INSERT OR REPLACE INTO prices (coin_id, timestamp, price) VALUES (?,?,?)",
                     (cid, ts, price))
    conn.commit()
    time.sleep(1.5)  # CoinGecko rate limit
```

After bootstrap: RSI available immediately, MACD available, SMA200 ready. The `/market_chart?days=90` endpoint returns hourly data (~2160 points per coin at 1-hour granularity).

**Verification after bootstrap:**
```sql
SELECT coin_id, COUNT(*) as points, 
       datetime(MIN(timestamp), 'unixepoch') as oldest,
       datetime(MAX(timestamp), 'unixepoch') as newest
FROM prices GROUP BY coin_id;
```

## Essential: Create Cron Job AFTER Bootstrap

After bootstrapping data, set up the recurring cron job. Without this, the monitor only runs once and never updates:

```bash
hermes cron create \
  --schedule "every 30m" \
  --script /opt/data/scripts/crypto_monitor.py \
  --prompt "分析以上币圈监控数据，如果有显著市场变动或交易信号，用中文以表格形式报告。如果市场平稳则静默。" \
  --name "Crypto Market Monitor"
```

> ⚠️ **Do not skip this step.** Bootstrapping alone gives one snapshot. The cron job is what keeps data fresh and generates ongoing reports.

## Setup

### Network (Docker / China environment)

CoinGecko and Binance APIs are BLOCKED without a proxy. Always use the configured proxy:

```python
PROXY = "http://192.168.1.88:7890"

def http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(req, timeout=timeout).read())
```

Test connectivity:
```bash
curl -s --proxy http://192.168.1.88:7890 --connect-timeout 8 "https://api.coingecko.com/api/v3/ping"
# Expected: {"gecko_says":"(V3) To the Moon!"}

curl -s --proxy http://192.168.1.88:7890 --connect-timeout 8 "https://api.binance.com/api/v3/ping"
# Expected: {}
```

### API Keys

CoinGecko public API (v3) requires NO API key for basic price/history endpoints. Rate limit: 10-30 calls/min on free tier.

Binance public API also requires no key for market data endpoints.

## Workflow

### 1. Initialize Price Database

```python
import sqlite3, time

conn = sqlite3.connect("/opt/data/crypto_prices.db")
conn.execute("""
    CREATE TABLE IF NOT EXISTS prices (
        coin_id TEXT, timestamp INTEGER,
        price REAL, volume_24h REAL, market_cap REAL, change_24h REAL,
        PRIMARY KEY (coin_id, timestamp)
    )
""")
```

### 2. Fetch Real-Time Prices

Use CoinGecko's `/simple/price` endpoint for bulk queries:

```python
coin_ids = "bitcoin,ethereum,solana,stellar"
url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true&include_market_cap=true"
data = http_get(url)
# Returns: {"bitcoin": {"usd": 62964, "usd_24h_vol": 3.2e10, ...}}
```

### 3. Technical Indicators

All indicators are calculated from the price history in SQLite.

#### RSI (Relative Strength Index)

```python
def calc_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    gains, losses = 0, 0
    for i in range(-period, 0):
        diff = prices[i+1] - prices[i]
        if diff > 0: gains += diff
        else: losses -= diff
    if losses == 0: return 100.0
    rs = (gains / period) / (losses / period)
    return 100 - (100 / (1 + rs))
```

- **RSI < 30**: Oversold — potential buy opportunity
- **RSI > 70**: Overbought — potential sell/reversal
- **RSI 30-50**: Weak/bearish zone
- **RSI 50-70**: Strong/bullish zone

#### SMA (Simple Moving Average)

```python
def calc_sma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period
```

- **SMA20 > SMA50**: Golden cross (bullish)
- **SMA20 < SMA50**: Death cross (bearish)
- Price above SMA20: Short-term bullish
- Price below SMA20: Short-term bearish

#### MACD (Moving Average Convergence Divergence)

```python
def calc_macd(prices):
    if len(prices) < 26: return None, None, None, None
    ema12 = _ema(prices, 12)
    ema26 = _ema(prices, 26)
    macd = ema12 - ema26
    signal = _ema_on_values(prices, macd, 9)
    return macd, signal, macd - signal, ema12
```

- **MACD > Signal line**: Golden cross (bullish)
- **MACD < Signal line**: Death cross (bearish)
- **Histogram rising**: Momentum increasing

### 4. Signal Generation Logic

Combine indicators for high-confidence signals:

| Signal | RSI | MACD | SMA20/50 | Confidence |
|--------|-----|------|----------|------------|
| Buy | < 30 | Cross up | Cross up | 🟢 HIGH |
| Buy | < 30 | — | — | 🟡 MEDIUM |
| Sell | > 70 | Cross down | Cross down | 🔴 HIGH |
| Sell | > 70 | — | — | 🟡 MEDIUM |
| Hold | 30-60 | — | — | ⚪ NEUTRAL |

Implementation pattern:

```python
def generate_signal(rsi, macd, macd_signal, sma20, sma50, price):
    signals = []
    
    if rsi is not None:
        if rsi < 30: signals.append(("📗 超卖", "RSI < 30，潜在买入机会"))
        elif rsi > 70: signals.append(("📕 超买", "RSI > 70，注意回调风险"))
    
    if macd is not None and macd_signal is not None:
        if macd > macd_signal: signals.append(("🟢 MACD金叉", "MACD线上穿信号线，看涨"))
        else: signals.append(("🔴 MACD死叉", "MACD线下穿信号线，看跌"))
    
    if sma20 is not None and sma50 is not None:
        if sma20 > sma50: signals.append(("🟢 均线多头", "SMA20 > SMA50"))
        else: signals.append(("🔴 均线空头", "SMA20 < SMA50"))
    
    # 共振信号 (highest confidence)
    if rsi < 30 and macd is not None and macd_signal is not None and macd > macd_signal:
        signals.append(("🎯 **买入信号**", "超卖+MACD金叉共振！"))
    elif rsi > 70 and macd is not None and macd_signal is not None and macd < macd_signal:
        signals.append(("⚠️ **卖出信号**", "超买+MACD死叉共振！"))
    
    return signals
```

### 5. Cron Job Setup

Set up periodic monitoring with a cron job:

```bash
# Run every 30 minutes (no_agent=True for silent watchdog pattern)
hermes cron create \
  --schedule "every 30m" \
  --script /opt/data/scripts/crypto_monitor.py \
  --name "Crypto Market Monitor" \
  --no-agent
```

Or with LLM analysis (agent sees the output and adds reasoning):

```bash
hermes cron create \
  --schedule "every 30m" \
  --script /opt/data/scripts/crypto_monitor.py \
  --prompt "分析以上币圈数据，如果有显著市场变动或交易信号，报告给我。如果市场平稳则静默。" \
  --name "Crypto 智能分析"
```

### 6. Data Accumulation

RSI needs **at least 15 data points** (14+1) to calculate.
MACD needs **26 data points** for full calculation.
SMA200 needs **200 data points**.

At 30-min intervals:
- RSI ready: ~7.5 hours
- MACD ready: ~13 hours  
- SMA200 ready: ~4.2 days

Fallback for sparse data: When history is insufficient, report "数据积累中" and show the data points count.

## Monitoring Report Format

```
=== 加密货币市场监控 | MM-DD HH:MM UTC ===

币种     |         价格 |  24h涨跌 |  RSI(14) |      SMA20 |      SMA50 | 信号
-------------------------------------------------------------------------------
BTC      |   $62,964.00 |   -4.48% |     45.2 |  $65,100   |  $63,500   | 🟢 均线多头
ETH      |    $1,755.03 |   -4.02% |     38.7 |   $1,820   |   $1,790   | 🔴 均线空头
...

🔔 BTC: 🎯 **买入信号** — 超卖+MACD金叉共振！
📊 无显著交易信号，市场整体平稳

--- 数据来源: CoinGecko | 下次更新: HH:MM UTC ---
```

## Tracked Coins (Default Set)

| CoinGecko ID | Symbol | Notes |
|-------------|--------|-------|
| bitcoin | BTC | Main index |
| ethereum | ETH | Smart contract leader |
| solana | SOL | High-speed L1 |
| stellar | XLM | User's wallet chain |
| dogecoin | DOGE | Community meme |
| cardano | ADA | L1 |
| ripple | XRP | Payments |
| polkadot | DOT | L0 |
| avalanche-2 | AVAX | L1 subnets |
| chainlink | LINK | Oracle |

To add more: add entries to the `TRACKED_COINS` dict with CoinGecko ID → display symbol mapping.

## Extending

### Adding new indicators
- Bollinger Bands: SMA ± (stddev × 2)
- Volume-weighted average price (VWAP)
- Ichimoku Cloud
- Fibonacci retracement levels

### Adding exchange data
- Binance: `/api/v3/ticker/24hr?symbol=BTCUSDT` (free, no key)
- Add order book depth: `/api/v3/depth?symbol=BTCUSDT&limit=5`

### Adding alerts
- Price threshold alerts (BTC > $70k)
- % change alerts (24h > 10%)
- Signal-based alerts (RSI < 30)

## Pitfalls

- **Proxy REQUIRED**: CoinGecko and Binance APIs are inaccessible from China without proxy. Always use `http://192.168.1.88:7890`. Direct calls timeout with exit code 28.
- **Rate limiting**: CoinGecko free tier is ~10-30 req/min. The `/simple/price` bulk endpoint with comma-separated IDs counts as 1 call. Avoid per-coin individual requests.
- **Data freshness**: CoinGecko updates every 60-120 seconds. Don't poll more than once per minute.
- **Sparse history on first run**: All indicators return None until enough data accumulates. Report this clearly — don't leave the user wondering.
- **Binance ticker format**: Binance uses `BTCUSDT` not `BTC` as symbol. Only use for coins listed on Binance.
- **Market-wide dumps**: A 5-10% drop across all coins is a macro event, not a coin-specific signal. Note the broader context.
- **SQLite file locking**: If cron runs simultaneously, use timeout or WAL mode. Single-threaded cron avoids this.

## Signal Interpretation Gotchas

### "Overbought While Falling" Paradox

A coin can show **RSI > 70 (超买) while simultaneously having -15% 7-day returns**. This happens after a prolonged bull run that reversed recently:

- RSI looks back 14 periods (hours at 30-min intervals = ~7 hours, or hourly bars if using historical data)
- If a coin was $80 two days ago, crashed to $67 today, but had small intraday bounces in the last 14 hours — those micro-bounces inflate RSI
- **Interpretation:** RSI > 70 + 7d decline ≥ 10% = "dead cat bounce" pattern, not genuine bullish momentum
- **Action:** Strong sell signal regardless of RSI overbought reading

### XLM-style Deep Oversold Divergence

RSI < 15 (extreme oversold) while 30-day trend is **positive** (+20%+) is a bullish divergence:

- The coin is fundamentally stronger than peers
- The RSI reading is a short-term noise event (e.g., a failed breakout that got quickly bought)
- **This is NOT a sell signal** despite RSI < 30 — check the medium-term trend first
- Confirmation: look for 30-day return > 0 while peers are all negative

### Market-wide vs Coin-specific Signals

When **90%+ of tracked coins** show the same signal simultaneously (e.g., 9/10 coins "超买+死叉"), it's a **macro signal**, not 9 independent signals:

- Report it as a single market observation: "市场整体偏空，9/10币种出现卖出信号"
- Don't list 9 identical alerts — the user sees noise
- Flag the **outlier** coin (e.g., XLM at RSI=9.4 while everything else is oversold)

## Files

- `scripts/crypto_monitor.py` — Main monitoring script (re-runnable via cron)
- `references/coingecko-endpoints.md` — CoinGecko API reference (price, history, OHLC, trending endpoints)
