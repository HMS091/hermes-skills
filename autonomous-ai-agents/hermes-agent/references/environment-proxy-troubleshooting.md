# Environment & Proxy Troubleshooting (Hermes Agent in Docker/NAS)

## Network Proxy Recovery

When running inside a Docker container on a NAS (Synology DS918+) with an HTTP proxy:

### Symptoms
- `curl` returns `Connection refused` to proxy IP:port (192.168.1.88:7890)
- `apt-get update` hangs or fails to fetch indexes
- `pip install` fails with connection timeouts
- But direct access (`--noproxy '*'`) to public internet WORKS

### Root Cause
Stale proxy env vars in `/etc/environment` or `/etc/profile.d/proxy.sh` pointing to a proxy server that's no longer running or accepting connections.

### Quick Fix in Session
```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY
```

### Permanent Fix
```bash
# Check current state
cat /etc/environment | grep -i proxy

# Backup then edit
cp /etc/environment /etc/environment.bak.$(date +%Y%m%d)

# Option A: Remove ALL proxy lines (if proxy is permanently dead)
# Edit /etc/environment to delete http_proxy, https_proxy, HTTP_PROXY, HTTPS_PROXY lines

# Option B: Keep proxy config but add direct access fallback
# Just unset in current session when proxy is unreachable
```

### Restoration (when proxy comes back online)
```bash
cat > /etc/environment << 'EOF'
http_proxy=http://192.168.1.88:7890
https_proxy=http://192.168.1.88:7890
HTTP_PROXY=http://192.168.1.88:7890
HTTPS_PROXY=http://192.168.1.88:7890
NODE_PATH=/usr/local/lib/node_modules
NO_PROXY=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8
no_proxy=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/hermes/.venv/bin
EOF
```

### Testing Connectivity
```bash
# Test proxy
curl -s --max-time 5 -w "HTTP: %{http_code}\n" "http://192.168.1.88:7890" -o /dev/null
# 400 = proxy running, 000 = proxy dead or connection refused

# Test proxied access (requires valid proxy)
export http_proxy=http://192.168.1.88:7890
export https_proxy=http://192.168.1.88:7890
curl -s --max-time 8 -w "HTTP: %{http_code}\n" "https://www.google.com" -o /dev/null
# 200 = proxy working for Google, 000 = blocked

# Test direct access (no proxy)
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
curl -s --max-time 5 -w "HTTP: %{http_code}\n" "https://www.baidu.com" -o /dev/null
# 200 = direct internet works
curl -s --max-time 5 -w "HTTP: %{http_code}\n" "https://api.github.com" -o /dev/null
# 200 = GitHub accessible directly
```

## Playwright Proxy Configuration

Playwright's browser DOES NOT inherit the shell's proxy env vars reliably.

### Correct approach
Set proxy env vars in the SHELL before invoking the Python script:
```bash
export http_proxy=http://192.168.1.88:7890
export https_proxy=http://192.168.1.88:7890
/opt/hermes/.venv/bin/python3 << 'PYEOF'
# This script WILL inherit the parent shell's proxy env vars
from playwright.sync_api import sync_playwright
...
PYEOF
```

### Why `os.environ` inside Python doesn't work
```python
# This DOES NOT reliably propagate to Playwright's browser process:
os.environ['http_proxy'] = 'http://192.168.1.88:7890'
```

### Launch flags for certificate issues
Some sites (Gitcoin Explorer, etc.) have expired certificates:
```python
browser = p.chromium.launch(
    headless=True,
    args=['--ignore-certificate-errors', '--no-sandbox']
)
page = browser.new_page(ignore_https_errors=True)
```

### Checking if proxy is needed
```python
import os
# Check what proxy is actually set
proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY') or 'none'
print(f"Proxy: {proxy}")
```

## apt-get Hangs During Download

### Recovery
```bash
# 1. Find the stuck apt process
ps aux | grep apt

# 2. Kill it
kill -9 <PID>

# 3. Release dpkg locks (if present)
rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock

# 4. Fix broken state
dpkg --configure -a

# 5. If .deb files are already cached, install directly
ls /var/cache/apt/archives/chromium*.deb
dpkg -i /var/cache/apt/archives/chromium*.deb

# 6. Fix dependencies
apt-get install -f -y -qq

# 7. Verify installation
which chromium && chromium --version
```

## Bilibili API Access Patterns

### What works
```bash
# Search endpoint (no wbi signing needed)
curl -s "https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=<URL_ENC_KEYWORD>"

# Single video detail (no wbi signing needed)
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=<BVID>"
```

### What gets blocked
```bash
# Space API needs wbi signing -> -352
curl "https://api.bilibili.com/x/space/wbi/arc/search?mid=..."

# Python requests -> 412 on ANY endpoint
# Always use curl piped to python, not python's urllib/requests
```

### SPA page limitation
Bilibili space pages (space.bilibili.com/<UID>) are Vue SPA. `chromium --dump-dom` returns 150K+ of CSS/JS with no structured data.
Use API endpoints instead. When APIs fail, use Playwright to render search pages.
