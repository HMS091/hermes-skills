---
name: scrapling
description: "Web data extraction and crawling. When user asks to scrape/get/fetch/extract data from a website, use Scrapling FIRST. Hermes browser (navigate/click/snapshot) is ONLY for interactive tasks: login forms, CAPTCHA solving, visual confirmation, or sites needing manual click flows. Auto-select the right fetcher based on site difficulty."
version: "1.3.0"
triggers:
  - user says scrape, crawl, extract, fetch, get data from, collect, gather
  - user says "this site" plus data/info/content
  - user needs data from a URL
  - Hermes browser tool fails or returns empty
  - target site has Cloudflare or anti-bot
metadata:
  venv: /opt/data/scrapling-venv
  helper: /opt/data/scripts/scrapling_helper.py
---

# Scrapling

Web scraping toolkit. Installed at `/opt/data/scrapling-venv/`. Full feature set: HTTP Fetcher, StealthyFetcher (Cloudflare bypass), DynamicFetcher (JS rendering), Spider (full crawl), CLI, MCP.

## AUTO-DECISION: Scrapling vs Hermes browser

When user asks to get data/site content:
→ **Scrapling FIRST**. Never default to browser tools for data extraction.

Only use Hermes browser (navigate/click/snapshot/vision) for:
- Login flows, filling forms, submitting
- CAPTCHA solving or interactive challenges
- Visual inspection ("what does this page look like?")
- Sites that require click-to-expand or manual navigation
- Checking if something rendered correctly
- **Sibling domain navigation** when target has aggressive Cloudflare (see sibling domain technique below)
- **Multi-page site traversal** through menus/links (navigate → click links on same domain)
- **Targeted data extraction** via browser_console JS when snapshots are truncated

Otherwise: Scrapling is faster, cheaper, and more reliable.

### Data extraction via browser_console

When `browser_snapshot` is truncated (>8000 chars) or doesn't show the content you need, use `browser_console` with JS expressions:

```javascript
// Get current page URL
window.location.href

// Find specific elements
document.querySelector('a[href*="terms"]')?.href

// Search page text for keywords
document.body.innerText.includes('Saily')

// Extract text around a keyword
const text = document.body.innerText;
const idx = text.indexOf('keyword');
text.substring(Math.max(0,idx-100), idx+500)

// Get all headings (page structure)
document.querySelectorAll('h2,h3,h4')
  .map(h => h.textContent.trim())

// List all link URLs matching criteria
const links = document.querySelectorAll('a');
[...links].filter(l => l.href.includes('impact')).map(l => l.href)

// Extract the body text after removing HTML tags
document.body.innerText
```

Combine with `browser_scroll` to reveal more content before extracting.

## Fetch Decision Tree

1. **Simple site** (blogs, docs, APIs) → `Fetcher.get()` / CLI `scrapling extract get`
2. **JS-heavy** (React/SPA, lazy-loaded) → `DynamicFetcher` / CLI `scrapling extract fetch`
3. **Has Cloudflare/anti-bot** → `StealthyFetcher` / CLI `scrapling extract stealthy-fetch --solve-cloudflare`
4. **Need multiple pages** → `Scrapling Spider`
5. **Not sure** -> start with `get`, if fails go `stealthy-fetch`

## PITFALL: Aggressive Cloudflare (managed challenge)

Some sites use Cloudflare's **managed challenge** (the most aggressive tier). StealthyFetcher with `solve_cloudflare=True` may loop 5+ times printing:

```
The turnstile version discovered is "managed"
Cloudflare page didn't disappear after 10s, continuing...
Looks like Cloudflare captcha is still present, solving again
```

This loop continues until timeout. **StealthyFetcher cannot bypass managed Cloudflare challenges** in this environment (no residential proxies, Chrome version may mismatch).

### Technique: Sibling domain bypass

When a site has aggressive Cloudflare, look for sibling/related domains from the same company that may have weaker protection:

- **Same company, different subdomain/product**: e.g. `surfshark.com` loaded fine while `saily.com` (also by Surfshark/Nord Security) was Cloudflare-blocked
- **Corporate parent > subsidiary**: try the parent company's marketing site, blog, or help center
- **Affiliate/partner portals**: `surfshark.com/affiliate` was accessible while `saily.com` was not
- **Web archives**: Wayback Machine (`web.archive.org`) may have cached versions without Cloudflare

### Chrome binary version mismatch

The installed Playwright/Patchright expects Chrome for Testing 148.x (chromium-1223), but the system has Chrome 149.x at `/opt/data/home/.agent-browser/browsers/chrome-149.0.7827.54/chrome`. Symlinking the newer Chrome to the expected path may let the browser launch but can cause Cloudflare bypass failures. To fix properly, install the exact expected version or update Patchright to match.

```bash
# Symlink workaround (launches but may fail Cloudflare):
target="/opt/hermes/.playwright/chromium-1223/chrome-linux64/chrome"
mkdir -p "$(dirname "$target")"
ln -sf /opt/data/home/.agent-browser/browsers/chrome-149.0.7827.54/chrome "$target"
```

## PITFALL: Proxy env vars break curl-cffi

System has `http_proxy`/`https_proxy` set to 192.168.1.88:7890 (unreachable from here).
If Scrapling encounters `Failed to connect to 192.168.1.88 port 7890`, run:

```python
import os
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY','all_proxy','ALL_PROXY']:
    os.environ.pop(k, None)
```

The wrapper (`scrapling` CLI) handles proxy env vars automatically.

## PITFALL: Helper script ModuleNotFoundError

Calling the helper script directly (`/opt/data/scripts/scrapling_helper.py`) uses system Python, NOT the venv. Result:

```
ModuleNotFoundError: No module named 'scrapling'
```

**Fix:** Always invoke the helper through the venv Python explicitly:
```bash
/opt/data/scrapling-venv/bin/python /opt/data/scripts/scrapling_helper.py fetch "https://example.com"
```

Or bypass the helper entirely — use direct Python (preferred for complex extractions).

## Installation Paths
- venv: `/opt/data/scrapling-venv/`
- Python: `/opt/data/scrapling-venv/bin/python`
- CLI: `/usr/local/bin/scrapling` (proxy-safe wrapper)
- Helper: `/opt/data/scripts/scrapling_helper.py`
- Browsers: chromiun-1223 chrome-headless-shell under Playwright driver dir
- Skill: scrapling in Hermes skill library

## Quick CLI Usage

```bash
scrapling extract get "https://example.com" page.md
scrapling extract stealthy-fetch "https://site.com" data.txt --solve-cloudflare
scrapling extract fetch "https://spa-site.com" content.md --network-idle
```

## Python Usage (via Hermes terminal)

❗ Always use `/opt/data/scrapling-venv/bin/python` — the helper script uses system Python and will fail with ModuleNotFoundError.

```python
from hermes_tools import terminal

# Basic fetch (use venv Python)
r = terminal('/opt/data/scrapling-venv/bin/python /opt/data/scripts/scrapling_helper.py fetch "https://example.com"')

# Stealthy with Cloudflare bypass
r = terminal('/opt/data/scrapling-venv/bin/python /opt/data/scripts/scrapling_helper.py stealthy "https://site.com" --css ".content"')

# Dynamic (JS rendering)
r = terminal('/opt/data/scrapling-venv/bin/python /opt/data/scripts/scrapling_helper.py dynamic "https://site.com" --output /tmp/page.md')

# Parse offline HTML
r = terminal('/opt/data/scrapling-venv/bin/python /opt/data/scripts/scrapling_helper.py parse /tmp/page.html --css "h1" --css ".price"')
```

## Python Usage (direct)

```python
import os, sys
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

sys.path.insert(0, '/opt/data/scrapling-venv/lib/python3.13/site-packages')
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher

# Basic - fastest
p = Fetcher.get('https://example.com', timeout=15)
title = p.css('title::text').get()

# Cloudflare bypass - uses headless Chrome
p = StealthyFetcher.fetch('https://protected.site.com', headless=True, solve_cloudflare=True, timeout=60000)

# JS rendering
p = DynamicFetcher.fetch('https://spa-site.com', headless=True, network_idle=True, timeout=45000)
```

## Spider Framework

```python
from scrapling.spiders import Spider

class MySpider(Spider):
    name = "demo"
    start_urls = ["https://example.com/"]
    concurrent_requests = 10

    async def parse(self, response):
        for item in response.css('.item'):
            yield {"title": item.css('h2::text').get()}

result = MySpider().start()
result.items.to_json("output.json")
```

## Adaptive Scraping

Scrapling can survive site redesigns:

```python
# First scrape: save element fingerprint
products = page.css('.product', auto_save=True)

# Later when site changes class names:
products = page.css('.product', adaptive=True)  # finds by content similarity
```
