# BscScan Cloudflare Bypass via curl

BscScan uses Cloudflare challenge pages that block headless browsers, but **curl requests with proper User-Agent headers regularly get through** and return the full HTML page. This makes curl a viable alternative when the browser tool is Cloudflare-blocked.

## Technique

```bash
curl -s --connect-timeout 10 "https://bscscan.com/token/0x8d65744527f55d0b2338350912d5c99a81ddf0e2" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml"
```

Note: no Accept-Encoding needed (curl decompresses automatically).

## Extractables from HTML

### Holders count
```python
import re
holders = re.findall(r'Holders[^<]*<[^>]*>([0-9,]+)', html)
```

### Token representation
```python
desc = re.findall(r'Token Rep[^:]*:\s*([^|]+)', html)
```

### Page title
```html
<title>BEP-20 Token | Address: 0x8d657445... | BscScan</title>
```

### Meta description (has timestamp + holders)
```html
<meta name="Description" content="Token Rep: Unknown | Holders: 616,059 | As at Jul-04-2026 04:15:40 PM (UTC)" />
```

### Source code
The HTML contains the full verified bytecode in a `verifiedbytecode2` attribute:
```python
code = re.search(r"verifiedbytecode2'>([a-f0-9]+)", html)
```

### Contract segments (opcodes view switch)
```python
contract_code = re.search(r'verifiedcontract\(\);">Switch to Opcodes View\nverifiedbytecode2'>(.+?)<', html, re.DOTALL)
```

## What does NOT work via curl

- **Price / Market Cap** — these are loaded dynamically via JavaScript
- **Token transfer history table** — JS-rendered
- **Interactive charts** — WebGL/JS
- **Analytics tabs** — JS-rendered

For price/volume data, fall back to LP reserve calculation (see `references/lp-price-calculation.md`).

## Environment notes

- Works from Docker containers with bridged network (IP on LAN subnet)
- Works from containers with DNS 8.8.8.8/1.1.1.1
- Fails from containers behind HTTP_PROXY that is unreachable
- If proxy env vars are set to a dead proxy: `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY` first
