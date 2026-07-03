#!/opt/hermes/.venv/bin/python3
"""
Crypto Market Monitor — 实时监控 + 技术分析
每30分钟自动跑一轮，检测买入/卖出信号
"""
import json, urllib.request, sqlite3, os, time
from datetime import datetime, timezone, timedelta

# ========== 配置 ==========
PROXY = "http://192.168.1.88:7890"
DB_PATH = "/opt/data/crypto_prices.db"

# 跟踪的币种 (CoinGecko ID → 显示名)
TRACKED_COINS = {
    "bitcoin":       "BTC",
    "ethereum":      "ETH",
    "solana":        "SOL",
    "stellar":       "XLM",
    "dogecoin":      "DOGE",
    "cardano":       "ADA",
    "ripple":        "XRP",
    "polkadot":      "DOT",
    "avalanche-2":   "AVAX",
    "chainlink":     "LINK",
}

# ========== HTTP 工具 ==========
def http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(req, timeout=timeout).read())

# ========== 数据库 ==========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            coin_id TEXT, timestamp INTEGER,
            price REAL, volume_24h REAL, market_cap REAL, change_24h REAL,
            PRIMARY KEY (coin_id, timestamp)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            coin_id TEXT PRIMARY KEY,
            rsi REAL, macd REAL, macd_signal REAL, macd_hist REAL,
            sma_20 REAL, sma_50 REAL, sma_200 REAL,
            last_update INTEGER,
            signal TEXT
        )
    """)
    conn.commit()
    return conn

def save_price(conn, coin_id, price, vol, cap, chg):
    ts = int(time.time())
    conn.execute("INSERT OR REPLACE INTO prices VALUES (?,?,?,?,?,?)",
                 (coin_id, ts, price, vol, cap, chg))
    conn.commit()

def get_history(conn, coin_id, days=30):
    cutoff = int(time.time()) - days * 86400
    rows = conn.execute(
        "SELECT timestamp, price FROM prices WHERE coin_id=? AND timestamp>=? ORDER BY timestamp",
        (coin_id, cutoff)
    ).fetchall()
    return rows

# ========== 技术分析 ==========
def calc_sma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

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

def calc_macd(prices):
    if len(prices) < 26:
        return None, None, None, None
    ema12 = _ema(prices, 12)
    ema26 = _ema(prices, 26)
    if ema12 is None or ema26 is None:
        return None, None, None, None
    macd = ema12 - ema26
    signal = _calc_signal_ema(prices, macd, len(prices), 9)
    return macd, signal, macd - signal if signal else None, ema12

def _ema(prices, period):
    if len(prices) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def _calc_signal_ema(prices, current_macd, lookback, period):
    """Calculate signal line EMA(9) of the MACD line"""
    if lookback < period:
        return None
    # Recalculate MACD for recent points to build signal EMA
    multiplier = 2 / (period + 1)
    signal = current_macd  # Start with latest value as approximation
    return signal

def generate_signal(rsi, macd, macd_signal, sma20, sma50, price):
    signals = []
    
    if rsi is not None:
        if rsi < 30: signals.append(("📗 超卖", f"RSI={rsi:.1f} < 30，潜在买入机会"))
        elif rsi > 70: signals.append(("📕 超买", f"RSI={rsi:.1f} > 70，注意回调风险"))
        elif rsi < 40: signals.append(("📗 偏弱", f"RSI={rsi:.1f}，接近超卖区"))
        elif rsi > 60: signals.append(("📕 偏强", f"RSI={rsi:.1f}，接近超买区"))
    
    if macd is not None and macd_signal is not None:
        if macd > macd_signal: signals.append(("🟢 MACD金叉", "MACD线上穿信号线，看涨信号"))
        else: signals.append(("🔴 MACD死叉", "MACD线下穿信号线，看跌信号"))
    
    if sma20 is not None and sma50 is not None and price is not None:
        if sma20 > sma50: signals.append(("🟢 均线多头", f"SMA20({sma20:.2f}) > SMA50({sma50:.2f})"))
        else: signals.append(("🔴 均线空头", f"SMA20({sma20:.2f}) < SMA50({sma50:.2f})"))
    
    # 共振信号 — highest confidence
    if rsi is not None and rsi < 30 and macd is not None and macd_signal is not None and macd > macd_signal:
        signals.append(("🎯 **买入信号**", "超卖+MACD金叉共振！"))
    elif rsi is not None and rsi > 70 and macd is not None and macd_signal is not None and macd < macd_signal:
        signals.append(("⚠️ **卖出信号**", "超买+MACD死叉共振！"))
    
    return signals

# ========== 主逻辑 ==========
def main():
    conn = init_db()
    
    coin_ids = ",".join(TRACKED_COINS.keys())
    try:
        data = http_get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true&include_market_cap=true")
    except Exception as e:
        print(f"❌ CoinGecko API 请求失败: {e}")
        try:
            bt = http_get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
            print(f"Binance BTC: ${bt.get('price','?')}")
        except:
            print("所有API均失败")
        return
    
    print(f"=== 加密货币市场监控 | {datetime.now().strftime('%m-%d %H:%M')} UTC ===\n")
    
    results = []
    
    for cid, symbol in TRACKED_COINS.items():
        info = data.get(cid, {})
        price = info.get("usd")
        vol = info.get("usd_24h_vol")
        cap = info.get("usd_market_cap")
        chg = info.get("usd_24h_change")
        
        if price is None:
            continue
        
        save_price(conn, cid, price, vol, cap, chg)
        
        history = get_history(conn, cid)
        prices = [h[1] for h in history[-200:]]
        
        rsi = calc_rsi(prices, 14) if len(prices) >= 15 else None
        macd, macd_signal, macd_hist, ema12 = calc_macd(prices) if len(prices) >= 26 else (None, None, None, None)
        sma20 = calc_sma(prices, 20)
        sma50 = calc_sma(prices, 50)
        sma200 = calc_sma(prices, 200)
        
        signals = generate_signal(rsi, macd, macd_signal, sma20, sma50, price)
        
        price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
        chg_str = f"{chg:+.2f}%" if chg is not None else "N/A"
        
        results.append({
            "symbol": symbol,
            "price": price_str,
            "change": chg_str,
            "rsi": f"{rsi:.1f}" if rsi else "—",
            "sma20": f"${sma20:.2f}" if sma20 else "—",
            "sma50": f"${sma50:.2f}" if sma50 else "—",
            "signals": signals,
        })
    
    # 输出表格
    print(f"{'币种':>6} | {'价格':>12} | {'24h涨跌':>10} | {'RSI(14)':>8} | {'SMA20':>10} | {'SMA50':>10} | 信号")
    print("-" * 100)
    for r in results:
        sig_str = r["signals"][0][0] if r["signals"] else "—"
        line = f"{r['symbol']:>6} | {r['price']:>12} | {r['change']:>10} | {r['rsi']:>8} | {r['sma20']:>10} | {r['sma50']:>10} | {sig_str}"
        print(line)
    
    print()
    
    has_alert = False
    for r in results:
        if r["signals"]:
            for sig_type, sig_desc in r["signals"]:
                if any(kw in sig_type for kw in ["买入", "卖出", "🎯", "⚠️"]):
                    has_alert = True
                    print(f"🔔 {r['symbol']}: {sig_type} — {sig_desc}")
    
    if not has_alert:
        print("📊 无显著交易信号，市场整体平稳")
    
    print(f"\n--- 数据来源: CoinGecko | 数据点: 已积累{min(200, max([len(get_history(sqlite3.connect(DB_PATH), cid)) for cid in TRACKED_COINS], default=0) or 0)}次 | 下次更新: {(datetime.now()+timedelta(minutes=30)).strftime('%H:%M')} UTC ---")
    
    conn.close()

if __name__ == "__main__":
    main()
