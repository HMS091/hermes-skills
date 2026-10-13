---
name: scrapling
description: "Use when scraping/extracting structured data from a website. Scrapling first (HTTP → JS → stealth); Hermes browser only for interactive flows."
version: "2.0.0"
author: hermes-agent
license: MIT
triggers:
  - user says scrape, crawl, extract, fetch, get data from, collect, gather
  - user says "this site" plus data/info/content
  - user needs data from a URL
  - Hermes browser tool fails or returns empty
  - target site has Cloudflare or anti-bot
metadata:
  hermes:
    tags: [scraping, crawling, anti-bot, cloudflare, playwright]
    related_skills: [blocked-page-recovery, web-research, lightpanda]
  venv: /opt/data/scrapling-venv
  helper: /opt/data/scripts/scrapling_helper.py
  cli: /usr/local/bin/scrapling (wrapper; also /usr/local/bin/scrapling-mcp)
  browsers: /opt/data/scrapling-browsers (chromium 1243 = Chrome for Testing 153.0.8010.12)
  reinstall_browsers: bash /opt/data/scripts/scrapling_install_browsers.sh
  selftest: bash /opt/data/scripts/scrapling_selftest.sh [--with-cloudflare]
  healthcheck: /opt/data/scripts/scrapling_healthcheck.sh (cron 「Scrapling 健康检查」每日 00:30 UTC, deliver=all; 健康时静默, 只报故障与新版本)
---

# Scrapling

Web scraping toolkit, installed and **verified working** on this box (2026-10-13).
Installed at `/opt/data/scrapling-venv/`, CLI wrapper at `/usr/local/bin/scrapling`, browsers
(Chromium 1243 = Chrome for Testing 153.0.8010.12) at `/opt/data/scrapling-browsers`.
Tool versions: scrapling 0.4.15, playwright/patchright 1.63.0, curl-cffi 0.16.3, mcp 2.3.0.
Feature set: HTTP Fetcher (curl-cffi impersonation), DynamicFetcher (JS rendering),
StealthyFetcher (patchright + Cloudflare solving), Spider (full crawl), adaptive selectors, CLI, MCP.

Status: 0.4.15 = newest release on PyPI *and* GitHub (v0.4.15, 2026-08-23), so there is nothing
newer to upgrade to. What actually needed fixing was the environment (browsers missing, the
browser fetchers unable to launch, the helper writing empty files) — all fixed and re-tested.

## When to Use

- Any request to **get / scrape / extract / collect data from a URL or website** → this skill first.
- The target is **JS-rendered, rate-limited, or behind Cloudflare/anti-bot** → the stealth/dynamic fetchers.
- You need **many pages of one site** (crawl, product list, docs, feeds) → `Spider` or a loop with `Fetcher`.
- The Hermes browser tool returned empty/blocked content and you just need the data, not interaction.
- Do **not** use it for: logins, form submits, captcha popups, visual checks, or "what does this page look
  like" — that is the Hermes browser / Lightpanda path (see the comparison table below).

## Verified working commands (re-run these when in doubt)

```bash
# no browser: fastest, plain HTTP with browser impersonation
scrapling extract get "https://quotes.toscrape.com/" /tmp/out.md          # .md/.txt/.html = format
scrapling extract get --ai-targeted "https://site.com/article" /tmp/a.md  # main content only

# JS-rendered page (headless Chromium)
scrapling extract fetch "https://quotes.toscrape.com/js/" /tmp/out.txt

# anti-bot / Cloudflare challenge
scrapling extract stealthy-fetch --solve-cloudflare "https://www.scrapingcourse.com/cloudflare-challenge" /tmp/out.txt
# -> verified 200 + "You bypassed the Cloudflare challenge!"
```

Always call the CLI as `scrapling` (the `/usr/local/bin/scrapling` wrapper fixes proxy vars,
the browsers dir and TMPDIR). Calling `/opt/data/scrapling-venv/bin/scrapling` directly bypasses
those fixes and will fail on browser commands.

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

### Where Scrapling sits next to the other fetching tools (complementary, not competing)

| Need | Use | Why |
|---|---|---|
| Static page / JSON / RSS / bulk text extraction | **Scrapling `Fetcher`** (curl-cffi impersonation) | fastest, no browser, TLS fingerprint looks like Chrome |
| JS-rendered page, one-off | **Scrapling `DynamicFetcher`** | renders JS, returns DOM + `markdown()` |
| Cloudflare / anti-bot wall | **Scrapling `StealthyFetcher --solve-cloudflare`** | patchright stealth + turnstile solving (verified) |
| Many pages of one site, structured crawl | **Scrapling `Spider`** | concurrency, resume, item export |
| Full local headless browser, interactive stepping (click/fill) | **Lightpanda MCP** (`mcp_lightpanda_*`) | real browser semantics, low memory |
| Login flows, CAPTCHA, visual check, cloud/anti-bot-as-a-service | **Hermes browser (`browser_exec`, Browserbase)** | cloud IP + human-in-the-loop |
| Chinese sites that 0-byte Scrapling/curl | **Hermes browser** or `cn.bing.com` via browser snapshot | see caveat below |

Rule of thumb: **extract data → Scrapling; interact with a page → browser/Lightpanda.**
Scrapling is the cheapest (no browser process) and the only one here that solves Cloudflare locally.

### ⚠️ EXCEPTION: Chinese websites (百度/36kr/知乎/163等) and Chinese search engines

Scrapling's `Fetcher.get()` **often returns 0 bytes** for Chinese websites due to aggressive anti-bot detection (anti-crawler, WAF, IP blocking). The same happens with plain `curl` and `urllib`. This is NOT a scrapling bug — Chinese sites run some of the most aggressive bot detection globally.

**When Scrapling Fetcher returns 0 bytes on a Chinese site:**
1. ❌ Do NOT debug Scrapling config (timeouts, headers, proxy) — the site is actively blocking you
2. ✅ **Immediately switch to Hermes browser** (browser_navigate + browser_snapshot) — the browser's accessibility tree bypasses most Chinese anti-bot systems
3. ✅ **Also try `delegate_task`** in parallel — the subagent's terminal session may have different network routing or can dedicate its own tools

**Confirmed working for Chinese search via browser:**
- `https://cn.bing.com/search?q=<query>&setlang=zh-Hans` — Bing China works well through browser snapshot. The accessibility tree renders search result titles, URLs, and descriptions as structured elements.
- Browser snapshot reveals Chinese search results as headings + links + paragraph descriptions, easily readable.

**Confirmed NOT working via Scrapling/curl (0 bytes):**
- Baidu search
- 36kr articles (SPA, JS-required)
- Zhihu pages
- 163.com articles

**Confirmed working via Scrapling Fetcher (non-Chinese):**
- Bing国际版 (www.bing.com, English)
- Google News RSS
- Most non-Chinese sites

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

StealthyFetcher with `solve_cloudflare=True` prints a loop while working:

```
The turnstile version discovered is "managed"
Cloudflare page didn't disappear after 10s, continuing...
Looks like Cloudflare captcha is still present, solving again
```

**Verified 2026-10-13:** with the matching browser build + `TMPDIR=/tmp` this loop *resolves* —
the `www.scrapingcourse.com/cloudflare-challenge` page (managed turnstile) returned 200 and the
page text "You bypassed the Cloudflare challenge! :D" after ~2.5 min. Give it
`--timeout 120000`+ (CLI: `--timeout 120000`), not the 30 s default, or it will time out mid-loop.
It still fails on the hardest CF configurations (interactive captcha, fingerprinting by IP
reputation) — there is no residential proxy available here. Fall back to the Hermes browser
(Browserbase cloud IP) in that case.

### Technique: Sibling domain bypass

When a site has aggressive Cloudflare, look for sibling/related domains from the same company that may have weaker protection:

- **Same company, different subdomain/product**: e.g. `surfshark.com` loaded fine while `saily.com` (also by Surfshark/Nord Security) was Cloudflare-blocked
- **Corporate parent > subsidiary**: try the parent company's marketing site, blog, or help center
- **Affiliate/partner portals**: `surfshark.com/affiliate` was accessible while `saily.com` was not
- **Web archives**: Wayback Machine (`web.archive.org`) may have cached versions without Cloudflare

## PITFALL: browser build missing / wrong dir (the #1 cause of browser-fetcher failure)

Symptom: `Executable doesn't exist at .../chromium-<rev>/chrome-linux64/chrome` plus the
"Looks like Playwright was just installed or updated" banner, from DynamicFetcher, StealthyFetcher,
the CLI `fetch`/`stealthy-fetch`, **or** `BrowserType.launch_persistent_context: Page crashed`.

Two independent traps on this box:

1. **Wrong browsers dir.** A Hermes session exports `PLAYWRIGHT_BROWSERS_PATH=/opt/hermes/tools`
   (that is the Hermes browser tool's Chromium 1208). Scrapling's browsers live in
   `/opt/data/scrapling-browsers` (currently Chromium **1243**). The `/usr/local/bin/scrapling` wrapper
   and the helper script **force** the right path; direct `python -c` calls must set it themselves
   (`os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/opt/data/scrapling-browsers'`). Never write
   `${PLAYWRIGHT_BROWSERS_PATH:-/opt/data/scrapling-browsers}` or `.get(...) or default` — the session's
   value is already set (and wrong), so both silently keep the bad path and the browsers "disappear".
2. **Chromium crash from shared memory.** `/dev/shm` is only 64 MB and the Hermes scratch dir
   (`/opt/data/cache/scratch`) is not usable for Chrome's shm files (EACCES) — the page process
   crash-loops. Fix: `TMPDIR=/tmp` + launch flag `--disable-dev-shm-usage` (both bundle into the
   wrapper/helper; pass `extra_flags=['--disable-dev-shm-usage','--no-sandbox']` in raw Python).

Repair or reinstall the browsers (handles any future revision):

```bash
bash /opt/data/scripts/scrapling_install_browsers.sh
```

The **Playwright CDN is blocked here** (cdn.playwright.dev / playwright.azureedge.net time out) — the
script points `PLAYWRIGHT_DOWNLOAD_HOST` at `https://cdn.npmmirror.com/binaries/playwright`, which
mirrors the same `builds/cft/<chrome version>/<platform>/...` paths (verified for Chromium 1223 =
Chrome for Testing 148.0.7778.96 and Chromium 1243 = CFT 153.0.8010.12). huaweicloud mirrors
`builds/chromium/*` but serves HTML for `builds/cft/*`, so it is not a drop-in host.

`playwright install` also garbage-collects browser revisions it no longer knows about — the old
`chromium-1223` directory was removed automatically when playwright went to 1.63/1243. After any
playwright/patchright upgrade, re-run the installer script, then the self-test.

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

## PITFALL: `page.text` is empty (returns '')

In scrapling 0.4.x, `Response.text` is **empty** for normal HTML pages — `len(page.text) == 0` even
on a 200 response (verified on quotes.toscrape.com and example.com). Any code that does
`f.write(page.text)` writes an empty file. This is exactly what broke the v1 helper script.

Use instead:

```python
page.get_all_text()   # visible text of the page
page.html_content     # full HTML (str)
page.body             # raw bytes
page.markdown()       # markdown of the rendered DOM (method, not property)
page.css('title::text').get()
```

## PITFALL: scrapling MCP server needs mcp >= 2.0 (FIXED — mcp 2.3.0 installed)

`scrapling mcp` / `/usr/local/bin/scrapling-mcp` fails with
`ImportError: cannot import name 'MCPServer' from 'mcp.server'` when the venv has `mcp` 1.x
(the class only exists in mcp 2.x). Fixed on 2026-10-13 by installing the `ai` extra; verified with a
real stdio handshake (`initialize` + `tools/list` returns the scrapling tools).

If it ever regresses, upgrade inside the venv — never with system pip:

```bash
/opt/hermes/tools/uv-0.12.3-linux-x64/uv pip install --python /opt/data/scrapling-venv/bin/python \
  --default-index https://mirrors.aliyun.com/pypi/simple/ -U 'scrapling[fetchers,ai]'
```

`uv` is **not** on PATH here — the binary lives at `/opt/hermes/tools/uv-0.12.3-linux-x64/uv`, and the
venv has no pip (`python -m ensurepip` is the only fallback). Straight PyPI downloads from this network
crawl at ~250 KB/s; the Aliyun index (`--default-index https://mirrors.aliyun.com/pypi/simple/`) is
several times faster for the 100 MB+ playwright/patchright wheels.

MCP is still optional: the CLI + helper path needs no MCP server. Registering it with Hermes
(`hermes mcp add scrapling --command /usr/local/bin/scrapling-mcp --connect-timeout 60 --args`, then
restart) is the one step that needs the agent's config file, which it cannot edit itself.

Its 13 tools, for reference: `open_session`, `open_request_session`, `close_session`, `list_sessions`,
`make_request`, `bulk_get`, `fetch`, `bulk_fetch`, `stealthy_fetch`, `bulk_stealthy_fetch`,
`session_fetch`, `session_make_request`, `screenshot`.

## Installation Paths
- venv / Python: `/opt/data/scrapling-venv/bin/python`
- CLI: `/usr/local/bin/scrapling` (wrapper: unsets proxies, pins browsers dir + TMPDIR; source of truth
  is `/opt/data/scripts/scrapling_cli_wrapper.sh`, reinstall with `install -m 0755 <src> /usr/local/bin/scrapling`)
- MCP wrapper: `/usr/local/bin/scrapling-mcp`
- Browsers: `/opt/data/scrapling-browsers/{chromium-1243,chromium_headless_shell-1243}`
- Helper v2: `/opt/data/scripts/scrapling_helper.py` (v1 kept as `scrapling_helper.v1.py.bak`)
- Browser installer: `/opt/data/scripts/scrapling_install_browsers.sh`
- Self-test (6 checks, `--with-cloudflare` for the slow one): `bash /opt/data/scripts/scrapling_selftest.sh`
- Package baseline snapshot: `/opt/data/scripts/scrapling_venv_baseline_20261013.txt` (68 packages, pre-upgrade — use it to pin back if an upgrade regresses)

## Quick CLI Usage (preferred entry point)

```bash
scrapling extract get "https://example.com" /tmp/page.md              # .md / .txt / .html select the format
scrapling extract get -s ".price" "https://shop.com" /tmp/prices.txt   # CSS selector, repeatable
scrapling extract get --ai-targeted "https://news.site/x" /tmp/a.md   # main content only
scrapling extract fetch "https://spa-site.com" /tmp/content.md --network-idle --timeout 60000
scrapling extract stealthy-fetch --solve-cloudflare "https://cf-site.com" /tmp/data.txt --timeout 120000
scrapling shell                                                     # interactive console (needs IPython)
```

Browser commands: `--timeout` is **milliseconds** and the default 30 s is too short for
Cloudflare solving or heavy SPAs — pass 60000–120000.

## Python usage

Two options, both must pin the environment (browsers dir + TMPDIR) or the browser fetchers fail:

**A. Helper script v2** (handles the env, proxies and browser flags for you) — always the venv python:

```bash
/opt/data/scrapling-venv/bin/python /opt/data/scripts/scrapling_helper.py fetch    "https://example.com" -f markdown -o /tmp/page.md
/opt/data/scrapling-venv/bin/python /opt/data/scripts/scrapling_helper.py dynamic  "https://spa.com" -s ".item" -s ".price" -o /tmp/items.txt
/opt/data/scrapling-venv/bin/python /opt/data/scripts/scrapling_helper.py stealthy "https://cf-site.com" --solve-cloudflare -o /tmp/cf.txt
/opt/data/scrapling-venv/bin/python /opt/data/scripts/scrapling_helper.py parse    /tmp/page.html -s "h1" -s ".price" -o /tmp/out.json
```

Flags: `-s/--css` (repeatable), `-f/--format text|html|markdown`, `-o/--output`, `--timeout` (seconds),
`--solve-cloudflare` (stealthy only). Writes `# status=... url=...` to stderr so stdout stays clean.

**B. Direct Python** (for non-trivial logic; keeps working after the helper changes):

```python
import os
for k in ('http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY','all_proxy','ALL_PROXY'):
    os.environ.pop(k, None)
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/opt/data/scrapling-browsers'  # never leave this to the session env
os.environ['TMPDIR'] = '/tmp'

from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher

p = Fetcher.get('https://example.com', timeout=20)            # fast path, no browser
print(p.status, p.css('h1::text').get(), len(p.get_all_text()))

p = DynamicFetcher.fetch('https://spa.com', headless=True, network_idle=True, timeout=60000,
                         extra_flags=['--disable-dev-shm-usage', '--no-sandbox'])

p = StealthyFetcher.fetch('https://cf-site.com', headless=True, solve_cloudflare=True, timeout=120000,
                          extra_flags=['--disable-dev-shm-usage', '--no-sandbox'])
```

Run that snippet with `/opt/data/scrapling-venv/bin/python` (or `python -c`), **not** system python.



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
