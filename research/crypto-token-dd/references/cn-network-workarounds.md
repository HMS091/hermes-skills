# Chinese Network Workarounds for Token Analysis

When running from a Docker container in a Chinese network (Synology NAS, etc.):

## Core Problem

- Google is blocked
- Etherscan/BscScan use Cloudflare challenge (curl can't render JS)
- DexScreener/CoinGecko IP may be blocked by GFW
- Environment may have stale `HTTP_PROXY` env vars pointing to a proxy that's down

## Essential First Step

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY
```

## Source Reliability Matrix

| Source | Reliability in CN | Notes |
|--------|-------------------|-------|
| **DuckDuckGo HTML** | ★★★★★ | Always works, no JS needed |
| **OKX Web3** | ★★★★☆ | Works for BSC tokens, scrape for metadata |
| **GeckoTerminal** | ★★★☆☆ | Works if you have the pair address |
| **DexScreener** | ★★☆☆☆ | Often blocked (Connection refused) |
| **CoinGecko** | ★★☆☆☆ | ERC-20 only, often blocked |
| **GoPlus** | ★★☆☆☆ | Often blocked |
| **Etherscan/BscScan API** | ★☆☆☆☆ | Requires API key (V2) + may be blocked |
| **Etherscan/BscScan Web** | ★☆☆☆☆ | Cloudflare blocks curl |

## DuckDuckGo HTML Search — The Reliable One

```bash
curl -s "https://html.duckduckgo.com/html/?q=0x8d65744527f55d0b2338350912d5c99a81ddf0e2+BSC+token" \
  -H "User-Agent: Mozilla/5.0" | \
  grep -oP 'class="result__a" href="[^"]*">[^<]+</a>' | head -10
```

To extract result titles + URLs:
```bash
curl -s "https://html.duckduckgo.com/html/?q=<QUERY>" -H "User-Agent: Mozilla/5.0" | \
  grep -oP 'uddg=[^&"]+'  # extract encoded URLs
grep -oP '<a[^>]*class="result__a"[^>]*>[^<]+'  # extract titles
```

## OKX Web3 Data Extraction

OKX Web3 pages embed token info in `<title>` and `<meta name="description">` tags:

```bash
curl -s "https://web3.okx.com/token/bsc/<ADDRESS>" -H "User-Agent: Mozilla/5.0" | \
  grep -oP '(title|description)[^<]*' | head -5
```

Returns pattern like:
- `<title>Pro $60.46 (Pro Token) | Trading & Price Chart on BNB Chain | OKX Wallet</title>`
- `<meta description="... price is $60.46 with market cap of $234.51M ...">`

## Chain Determination via DuckDuckGo

Search the bare address — the results will reveal which chain explorer is linked:
- `bscscan.com` → BSC chain
- `etherscan.io` → Ethereum
- `polygonscan.com` → Polygon

## When All Mainstream APIs Fail

1. DuckDuckGo search for `<ADDRESS> BSC token` → find token name
2. OKX Web3 scrape with the address → get price + market cap
3. CoinCarp/LiveCoinWatch scrape with the token name → secondary verification
4. Note: data from these sources can't be independently verified — use as investigation leads, not confirmed facts
