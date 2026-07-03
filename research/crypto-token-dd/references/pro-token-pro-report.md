# Pro Token (PRO) — Investigative Report

Contract: `0x8d65744527f55d0b2338350912d5c99a81ddf0e2`
Chain: BSC (BNB Smart Chain)
Analyzed: 2026-05-31

## Red Flags Summary

| Flag | Detail |
|------|--------|
| No CoinGecko/CMC | Not listed on any major tracker |
| No DexScreener pairs | PancakeSwap V2 pool exists (`0x63844bd4bfad910b1643713302a1cc1ed20d50c3`) but DexScreener returned no data |
| No GoPlus security | Not on GoPlus token security API |
| BscScan Cloudflare | Page behind Cloudflare challenge |
| No social presence | No Twitter, Telegram, website found via DuckDuckGo |
| Price vs reality | OKX Web3 reported $60.46 / $234M mcap — but no active trading volume detected |

## Data Sources Used

1. **DuckDuckGo** → found token name "Pro Token (PRO)", BscScan link, OKX Web3 page
2. **OKX Web3** → `web3.okx.com/token/bsc/0x8d65744527f55d0b2338350912d5c99a81ddf0e2` → price $60.46, mcap $234.51M
3. **GeckoTerminal** → identified via DuckDuckGo, pool at `0x63844bd4bfad910b1643713302a1cc1ed20d50c3`
4. **CoinCarp/LiveCoinWatch/DexView** → secondary listings confirmed token exists on these platforms

## Notes

- User initially said "在币安连上的" (connected on Binance) — clarified this meant BSC chain, not Binance exchange listing
- Attempted: DexScreener (all variants), CoinGecko, GoPlus, Birdeye, Covalent — all returned empty/error
- DuckDuckGo was the only functional search engine
