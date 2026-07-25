# Complete TLS/Network Failure Fallback

## Scenario

All HTTPS connections fail with `SSL: UNEXPECTED_EOF_WHILE_READING`. Every API, search engine, and financial data source is unreachable. Even HTTP (port 80) connections silently drop. This is caused by a middlebox/firewall that intercepts and terminates TLS handshakes, or a broken SSL stack in the subagent environment.

## Diagnostic Commands

```bash
# 1. Check DNS resolution -- hijacked IPs signal DNS poisoning
python3 -c "
import socket
for host in ['www.google.com', 'finance.yahoo.com', 'api.nasdaq.com', 'api.gold-api.com']:
    ips = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
    print(f'{host} -> {ips[0][4][0]}')
"
# Healthy: Google -> 142.250.x.x, Yahoo -> 74.6.x.x
# Hijacked: Google -> 69.171.235.22 (Facebook/Meta range), Yahoo -> 180.222.116.x

# 2. Check known-good IPs for TCP reachability
# (use known-correct IPs, not DNS-resolved ones)
python3 -c "
import socket
for ip in ['142.250.80.4', '142.250.80.14', '216.58.192.14']:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex((ip, 443))
    print(f'TCP {ip}:443 -> {\"OPEN\" if result == 0 else \"CLOSED\"}')
    sock.close()
"

# 3. Check system time (wrong time breaks cert validation)
date

# 4. Check SSL cert store
ls -la /etc/ssl/certs/ca-certificates.crt
wc -l /etc/ssl/certs/ca-certificates.crt

# 5. Try openssl s_client to see where TLS handshake fails
echo "" | openssl s_client -connect 142.250.80.4:443 -tls1_2 2>&1 | grep -E "SSL handshake|CONNECTED|error"
# "SSL handshake has read 0 bytes and written 221 bytes" = ClientHello sent, no ServerHello
```

## Interpretation Matrix

| TCP Reachable? | TLS Handshake? | DNS Correct? | Likely Cause |
|----------------|---------------|--------------|-------------|
| Yes (port 443 open) | Fails (EOF) | Hijacked | Transparent proxy / MITM middlebox |
| Yes (port 443 open) | Fails (EOF) | Correct | Firewall dropping TLS handshake |
| No (port 443 closed) | N/A | Either | Outbound HTTPS blocked entirely |
| Yes | Works | Hijacked | DNS poisoning only (TLS still works through hijacked IP) |
| Yes (port 80) | N/A (HTTP) | Either | HTTP redirected/blocked by same middlebox |

## Local Data Recovery Workflow

### Step 1: Check briefing directory

```bash
ls -la /opt/data/briefings/
```

Expected contents:
- `YYYY-MM-DD_raw.json` — raw market data (may show errors if network was down)
- `YYYY-MM-DD_preview.txt` — plaintext preview
- `YYYY-MM-DD_briefing.md` — full AI-generated analysis with macro context (content may be stale but still useful)
- `dashboard.html` — HTML index

### Step 2: Parse the latest raw JSON for confirmed prices

```python
import json, os, glob

briefings_dir = "/opt/data/briefings"
raw_files = sorted(glob.glob(os.path.join(briefings_dir, "*_raw.json")))
if raw_files:
    latest = raw_files[-1]
    print(f"Latest raw data: {latest}")
    with open(latest) as f:
        data = json.load(f)
    
    # Extract confirmed data
    if "error" not in data.get("nvda", {}):
        nvda = data["nvda"]
        print(f'NVDA: ${nvda["price"]:.2f}, change: {nvda.get("change", "N/A")}, vol: {nvda.get("volume", "N/A")}')
    
    if "error" not in data.get("tsla", {}):
        tsla = data["tsla"]
        print(f'TSLA: ${tsla["price"]:.2f}, change: {tsla.get("change", "N/A")}')
    
    if "error" not in data.get("gold", {}):
        gold = data["gold"]
        print(f'XAU: ${gold["price"]:.2f}/oz')
    
    # If data has errors, check previous days
    if "error" in str(data.get("nvda", "")):
        print("Latest NVDA data failed. Checking previous days...")
        for f in raw_files[-5:-1]:
            with open(f) as fh:
                prev = json.load(fh)
                if "error" not in prev.get("nvda", {}):
                    print(f"  Found good data in {os.path.basename(f)}")
                    break
```

### Step 2b (Critical): Cross-reference briefing .md files for macro context

When raw JSON files show errors for MULTIPLE consecutive days (prolonged network outage), the `.md` briefing files are your richest source. They contain:
- **Price tables** in markdown (the last successful close embedded in prose, even when collection failed)
- **Multi-day trend narrative** with specific dates and directional analysis
- **Macro factor analysis** (geopolitics, Fed/DXY, central bank buying, earnings season)
- **Technical levels** (support/resistance, RSI, MACD)
- **Risk assessments** with probability levels

**Pattern**: Read 3-5 most recent briefing files in parallel to reconstruct the full picture:

```python
import os, glob, re

briefings_dir = "/opt/data/briefings"
md_files = sorted(glob.glob(os.path.join(briefings_dir, "*_briefing.md")))
latest_mds = md_files[-5:]  # last 5 days

for f in latest_mds:
    with open(f) as fh:
        text = fh.read()
    
    date_match = re.search(r'— (\d{4}-\d{2}-\d{2})', text)
    date = date_match.group(1) if date_match else os.path.basename(f)
    
    # Extract price table (the markdown table near the top)
    price_table = re.search(r'\|\s*\*\*XAU.*?\*\*\s*\|\s*\$?([0-9,]+\.?\d*).*?\n', text, re.MULTILINE)
    if price_table:
        print(f"[{date}] Gold: ${price_table.group(1)}/oz")
    
    # Extract macro signals
    for kw in ['降息预期', 'DXY', '美元指数', '地缘', 'Fed', '央行购金', 'technical']:
        context_lines = [l.strip() for l in text.split('\n') if kw.lower() in l.lower()]
        if context_lines:
            print(f"  Macro: {context_lines[0][:150]}")
```

**Key insight from worked session (Jul 24-25, 2026):** When network has been dead for 3+ consecutive days:
1. The most recent successful raw JSON file is the last price anchor
2. The briefing .md files produced on subsequent days still reference that price in their analysis (the briefing script uses the last known data when collection fails)
3. Cross-day briefing comparison reveals the **trend direction** and **key drivers** even though today's live price is unknown
4. Example: briefings from Jul 22 (Tue close: $4,136), Jul 23 (Wed close: $4,121), Jul 24 (Fri: uses same $4,121) — the macro analysis on Jul 24 is still valuable because it discusses the multi-day context

**Always read both raw JSON and briefing MD files.** The JSON gives exact prices; the MD gives the macro narrative. Neither alone is sufficient.

### Step 3: Recover via session_search

When raw data files also have errors (same SSL failure), past session history contains the data:

```python
# Use session_search (Hermes agent tool) to find:
# session_search(query="daily-briefing NVDA TSLA gold", limit=3)
```

Past briefing sessions contain:
- Exact closing prices from the day's raw JSON
- AI-generated analysis with multi-day trends
- News headlines and macro context
- Technical analysis (support/resistance levels)

### Step 4: Build multi-day trend table

From raw JSON files spanning the past 5-7 days:

```python
import json, os, glob
from datetime import datetime

briefings_dir = "/opt/data/briefings"
rows = []
for f in sorted(glob.glob(os.path.join(briefings_dir, "*_raw.json"))):
    with open(f) as fh:
        data = json.load(fh)
    date = data.get("collection_date", "unknown")
    nvda = data.get("nvda", {})
    tsla = data.get("tsla", {})
    gold = data.get("gold", {})
    if "error" in str(nvda) or "error" in str(tsla) or "error" in str(gold):
        continue
    nvda_p = nvda.get("price", "N/A")
    tsla_p = tsla.get("price", "N/A")
    gold_p = gold.get("price", "N/A")
    if nvda_p != "N/A" and tsla_p != "N/A" and gold_p != "N/A":
        rows.append(f"| {date} | ${nvda_p:.2f} | ${tsla_p:.2f} | ${gold_p:.2f} |")

print("| Date | NVDA | TSLA | XAU |")
print("|------|------|------|-----|")
for r in rows[-7:]:  # last 7 days
    print(r)
```

### Step 5: Run the collection script (last resort)

Even if it fails, it updates the timestamp on the raw JSON files:

```bash
/opt/hermes/.venv/bin/python /opt/data/scripts/daily_briefing.py 2>&1
```

This also regenerates `dashboard.html`.

## Honest Reporting Template

When all data collection fails, use this pattern:

```
**Data Status: Collection Failed**

All HTTPS connections are blocked in this environment (SSL: UNEXPECTED_EOF_WHILE_READING).
No live data could be fetched for [today's date].

**Most Recent Confirmed Prices** (from [date], the last successful collection):
  - NVDA: $XXX.XX
  - TSLA: $XXX.XX
  - XAU:  $X,XXX.XX/oz

**Multi-Day Trend** (last 5-7 days of confirmed data):
| Date | NVDA | TSLA | XAU |
| ...  | ...  | ...  | ... |

**To complete this briefing**, manually fetch from:
  - NVDA: https://www.nasdaq.com/market-activity/stocks/nvda
  - TSLA: https://www.nasdaq.com/market-activity/stocks/tsla
  - XAU:  https://www.kitco.com/gold-price-today-usa/
```

## Worked Example (July 23, 2026 Session)

From the session that discovered this pattern:
- **Environment**: Docker subagent, Hermes, linux/amd64
- **DNS resolution**: Google -> 69.171.235.22 (hijacked), Yahoo -> 180.222.116.x (hijacked)
- **TCP reachability**: Known-good Google IPs (142.250.80.4) port 443 = OPEN
- **TLS handshake**: FAILS with "unexpected eof while reading" on all HTTPS
- **openssl s_client**: ClientHello sent (221 bytes), ServerHello never received
- **HTTP (port 80)**: Also silently drops connections
- **apt-get**: Debian repos unreachable (same TLS issue)
- **Package install (uv pip)**: PyPI unreachable
- **Hermes venv**: Python requests + certifi installed but same TLS failure
- **System time**: Correct (not a cert validity issue)
- **Data recovered from**: `/opt/data/briefings/2026-07-23_raw.json` (yesterday), plus 5-day trend from prior files
- **session_search**: Found prior cron sessions with NVDA $211.07, TSLA $358.31, XAU $4,121.20
