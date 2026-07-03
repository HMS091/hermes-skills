# Scrapling Full Installation Chain

**Library:** scrapling v0.4.8
**Installed:** June 1, 2026
**Environment:** Hermes Agent venv at `/opt/hermes/.venv/`
**Python:** 3.13 (from venv)

## Installation Command Chain

```bash
# Step 1: Install scrapling itself
/opt/hermes/.venv/bin/pip install scrapling

# Step 2: Install missing transitive deps (scrapling doesn't declare all of them)
# These MUST be installed in this order — each enables a deeper level of stealth:
/opt/hermes/.venv/bin/pip install curl_cffi          # TLS fingerprint engine (required for Fetcher)
/opt/hermes/.venv/bin/pip install browserforge        # Browser fingerprint generation (required for StealthyFetcher)
/opt/hermes/.venv/bin/pip install patchright          # Forked Playwright for stealth (required for StealthyFetcher)
/opt/hermes/.venv/bin/pip install msgspec             # Fast serialization (required after patchright)
```

**Note:** Try `pip install scrapling` first, then test. Only add the transitive deps if an import fails.

## Verification

```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher

# Basic HTTP
resp = Fetcher.get("https://httpbin.org/get")
print(resp.status)  # 200
print(resp.css("body"))  # Element list
print(resp.json())  # Dict from JSON response

# Stealth browser (Cloudflare bypass)
resp = StealthyFetcher.fetch("https://example.com", headless=True)
```

## API Notes

- Response objects ARE parsers: `.css()`, `.xpath()`, `.json()`, `.text` all available directly
- NOT `.status_code` — it's `.status`
- NOT `fetch()` on Fetcher — use `.get(url)`, `.post(url)`, etc.
- StealthyFetcher uses `.fetch()` not `.get()`

## Known Quirks (June 2026)

- `Fetcher.fetch()` does not exist as a static method. Use `Fetcher.get()`
- `StealthyFetcher.fetch()` takes `headless=True` param and supports Cloudflare Turnpstile bypass
- `browserforge` and `patchright` add ~50MB to the venv (playwright browser binaries)
- **`StealthyFetcher.fetch().text` returns 0 bytes** — there is a known bug where the `.text` property of StealthyFetcher responses is empty (0 chars). However, CSS selectors like `.css(".selector")` still work correctly and find elements. When using StealthyFetcher, prefer `.css()` for element extraction rather than `.text` for raw HTML.
- **`DynamicFetcher` timeout:** The default page load timeout is 30s. For slow pages (Freelancer, heavy JS sites), the first attempt may timeout. The library auto-retries once, which usually succeeds. Build in a small tolerance.
