---
name: scrapling
description: "Web data extraction and crawling. When user asks to scrape/get/fetch/extract data from a website, use Scrapling FIRST. Hermes browser (navigate/click/snapshot) is ONLY for interactive tasks: login forms, CAPTCHA solving, visual confirmation, or sites needing manual click flows. Auto-select the right fetcher based on site difficulty."
version: "1.1.0"
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

Otherwise: Scrapling is faster, cheaper, and more reliable.

## Fetch Decision Tree

1. **Simple site** (blogs, docs, APIs) → `Fetcher.get()` / CLI `scrapling extract get`
2. **JS-heavy** (React/SPA, lazy-loaded) → `DynamicFetcher` / CLI `scrapling extract fetch`
3. **Has Cloudflare/anti-bot** → `StealthyFetcher` / CLI `scrapling extract stealthy-fetch --solve-cloudflare`
4. **Need multiple pages** → `Scrapling Spider`
5. **Not sure** -> start with `get`, if fails go `stealthy-fetch`

## PITFALL: Proxy env vars break curl-cffi

System has `http_proxy`/`https_proxy` set to 192.168.1.88:7890 (unreachable from here).
If Scrapling encounters `Failed to connect to 192.168.1.88 port 7890`, run:

```python
import os
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY','all_proxy','ALL_PROXY']:
    os.environ.pop(k, None)
```

The wrapper (`scrapling` CLI) and helper script handle this automatically.

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

```python
from hermes_tools import terminal

# Basic fetch
r = terminal('/opt/data/scripts/scrapling_helper.py fetch "https://example.com"')

# Stealthy with Cloudflare bypass
r = terminal('/opt/data/scripts/scrapling_helper.py stealthy "https://site.com" --css ".content"')

# Dynamic (JS rendering)
r = terminal('/opt/data/scripts/scrapling_helper.py dynamic "https://site.com" --output /tmp/page.md')

# Parse offline HTML
r = terminal('/opt/data/scripts/scrapling_helper.py parse /tmp/page.html --css "h1" --css ".price"')
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
