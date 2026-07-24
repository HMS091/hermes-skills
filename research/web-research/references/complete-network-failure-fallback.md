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

Expected contents (stale dates but available):
- `YYYY-MM-DD_raw.json` — raw market data
- `YYYY-MM-DD_preview.txt` — plaintext preview
- `YYYY-MM-DD_briefing.md` — full AI-generated analysis
- `dashboard.html` — HTML index

### Step 2: Parse the latest raw JSON

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
