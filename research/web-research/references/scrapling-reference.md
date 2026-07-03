# Scrapling v0.4.9 Reference

Installed at: `/opt/data/scrapling-venv/`
CLI binary: `/opt/data/scrapling-venv/bin/scrapling`
Doc site: https://scrapling.readthedocs.io/en/latest/
Repo: https://github.com/D4Vinci/Scrapling (65.8k stars)

## Proxy Env Var Trap (⚠️ ALWAYS DO THIS)

```python
import os
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)
```

Or shell: `unset http_proxy https_proxy`

curl-cffi reads proxy env vars. The Clash proxy at 192.168.1.88:7890 is unreachable from this environment.

## Fetchers (Three Levels)

| Fetcher | Needs Browser? | Speed | Use Case |
|---------|:-------------:|:-----:|----------|
| `Fetcher` | ❌ No | 🚀 Fastest | Simple websites, APIs, blogs |
| `DynamicFetcher` | ✅ Playwright | 🐇 Medium | JS-heavy SPA, modern web apps |
| `StealthyFetcher` | ✅ Playwright | 🐇 Medium | Cloudflare, Turnstile, anti-bot |

**Currently only `Fetcher` works** — Playwright browsers couldn't be downloaded (no internet access from this environment).

## Basic Usage

```python
from scrapling.fetchers import Fetcher

# GET request
page = Fetcher.get('https://example.com')
print(page.status)  # int, not .status_code!

# POST request
page = Fetcher.post('https://example.com/api', data={'key': 'val'})

# With TLS impersonation
page = Fetcher.get('https://example.com', impersonate='chrome')
page = Fetcher.get('https://example.com', impersonate='firefox135')

# With session (persistent cookies)
from scrapling.fetchers import FetcherSession
with FetcherSession(impersonate='chrome') as session:
    page = session.get('https://example.com', stealthy_headers=True)
    page2 = session.get('https://example.com/page2')
```

## Parser (Selector Object)

The return value of Fetcher.get() IS a Selector. Call methods directly:

```python
# CSS selectors (supports Scrapy pseudo-elements)
page.css('.class')           # list of Selector objects
page.css('.class::text')     # extract text content
page.css('.class::text').get()      # first match (string)
page.css('.class::text').getall()   # all matches (list of strings)
page.css('.class').attrib['href']   # attribute of first match
page.css('.class')[0]        # first Selector by index

# XPath
page.xpath('//div[@class="quote"]')
page.xpath('//span[@class="text"]/text()').getall()

# BeautifulSoup-style find_all
page.find_all('div', class_='quote')
page.find_all(class_='text')
page.find_all(['div', 'span'], class_='quote')

# Text search
page.find_by_text('love')         # element containing text
page.find_by_text('love', tag='div')  # with tag filter

# Element navigation
first = page.css('.item')[0]
first.parent
first.next_sibling
first.previous_sibling

# Similarity (auto-relocate after site change)
first.find_similar()  # find elements similar to this one

# Below elements (spatial relationship on page)
first.below_elements()

# Parse raw HTML (without fetching)
from scrapling.parser import Selector
page = Selector("<html><body><p>Hello</p></body></html>")
page.css('p::text').get()  # 'Hello'
```

## Spider Framework

```python
from scrapling.spiders import Spider, Response

class MySpider(Spider):
    name = "my_spider"
    start_urls = ["https://example.com"]
    concurrent_requests = 10

    async def parse(self, response: Response):
        for item in response.css('.product'):
            yield {"title": item.css('h2::text').get()}
        # Follow pagination
        next_page = response.css('.next a')
        if next_page:
            yield response.follow(next_page[0].attrib['href'])

result = MySpider().start()
result.items.to_json("output.json")
result.items.to_jsonl("output.jsonl")
```

Key Spider options:
- `concurrent_requests` — parallelism (default varies)
- `crawldir="./crawl_data"` — pause/resume support (Ctrl+C grace)
- `robots_txt_obey=True` — respect robots.txt
- Multi-session: `configure_sessions(manager)` to add `FetcherSession` + `StealthySession` in one spider

## CLI Reference

```bash
# Output format by extension
unset http_proxy https_proxy
scrapling extract get "https://example.com" page.md     # Markdown
scrapling extract get "https://example.com" page.html   # Raw HTML
scrapling extract get "https://example.com" content.txt # Clean text

# With CSS selector
scrapling extract get "https://example.com" content.md --css-selector "article"

# POST with JSON
scrapling extract post "https://api.example.com" result.json -j '{"key":"val"}'

# With proxy (if available)
scrapling extract get "https://example.com" page.md --proxy "http://user:pass@host:port"

# TLS impersonation
scrapling extract get "https://example.com" page.md --impersonate "chrome"

# Stealthy fetch (needs browser)
scrapling extract fetch "https://example.com" content.md --network-idle
scrapling extract stealthy-fetch "https://nopecha.com/demo/cloudflare" data.txt --solve-cloudflare

# AI-targeted output (anti-prompt-injection + ad blocking)
scrapling extract get "https://example.com" content.md --ai-targeted
```

## Adaptive Scraping

```python
# First pass: save element fingerprints
products = page.css('.product', auto_save=True)

# Later, after site redesign (class names changed):
products = page.css('.product', adaptive=True)  # Finds them by similarity
```

This uses intelligent element similarity algorithms, not just DOM structure.

## MCP Server (AI Integration)

Scrapling has a built-in MCP server for AI tools (Claude, Cursor, etc.):

```bash
scrapling mcp
```

Configure in the AI tool's MCP settings to point to this server. The MCP server uses Scrapling internally to extract targeted content → pass minified data to AI → saves tokens.

## Performance Notes

- **Parsing**: 2.02ms for 5000 nested elements (≈12x faster than PyQuery, ≈784x faster than BS4+Lxml)
- **Element similarity**: 2.39ms (≈5x faster than AutoScraper)
- **Dependencies**: 68 packages installed, ~1.88s install time via `uv`
