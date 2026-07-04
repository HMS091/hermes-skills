# Pro Token (PRO) — Updated Report (July 4, 2026)

Contract: `0x8d65744527f55d0b2338350912d5c99a81ddf0e2`
Chain: BSC (BNB Smart Chain)
Analyses: 2026-05-31 (initial), 2026-07-04 (corrected)

## ⚠️ Correction Notice

The May 31 analysis concluded this was "100% honeypot/蜜罐资金盘." This was **incorrect** due to a decimals calculation error (assumed 18 decimals; token uses 9). After correction, the token has $86M in real LP liquidity, verified renounced contract, and 616K holders.

## Corrected Findings

### On-Chain Data (via BSC RPC)

| Metric | Value |
|--------|-------|
| Name | (empty via RPC — "PRO Token" in bytecode) |
| Symbol | (empty via RPC — "Pro" in bytecode) |
| Decimals | 9 |
| Total Supply | 6,924,924 PRO |
| Contract Owner | ✅ Renounced (→ dead address) |
| Source Code | ✅ Verified on BscScan |

### LP Liquidity (PancakeSwap V2: PRO/USDT)

| Metric | Value |
|--------|-------|
| LP address | `0x63844bd4bfad910b1643713302a1cc1ed20d50c3` |
| PRO in LP | 715,423 PRO |
| USDT in LP | 43,149,860 USDT |
| Real price | ~$60.31/PRO |
| TVL | ~$86.3M |

### Holder Distribution (on-chain verified)

| Address | Balance | % | Note |
|---------|---------|---|------|
| `0xc002...8ee8` | 3,675,882 PRO | 53.08% | Contract wallet, nonce=2, 0 BNB |
| LP pool | 715,423 PRO | 10.33% | Legitimate liquidity |
| `0x...BCCC` (Ave.ai #2) | **0 PRO** | 0% | Ave.ai data bug — showed 578,990 PRO but on-chain is zero |

### Contract Features (from verified bytecode)

- Tax/fee mechanism on transfers
- Blacklist capability (owner renounced → frozen)
- Marketing wallet: `0xf9074b5c035c961443373f78a6344e5adc61d314`
- Liquidity wallet: `0x543302e9d9411e563ad8266ceef2a85b66050832`

## Risk Assessment

| Signal | Level | Detail |
|--------|-------|--------|
| Honeypot (balance faking) | 🟢 False positive | Corrected — decimals error |
| Contract renounced | 🟢 Positive | Owner → dead address |
| Source verified | 🟢 Positive | Verified on BscScan |
| LP liquidity | 🟢 $86M | Real USDT-PRO pair |
| Holder concentration | 🔴 53% | #1 holder can dump |
| Public team/social | 🔴 None | No website, Twitter, Telegram |
| CEX/mainstream listing | 🔴 None | Not on CoinGecko/CMC |
| DEX listing | 🟢 Yes | PancakeSwap V2 |

## Key Lessons

1. **Always check decimals before interpreting balanceOf()** — `eth_call` with `0x313ce567`
2. **Zero BNB on top holder ≠ abandoned** — may be a contract wallet
3. **Zero Transfer events ≠ fake balance** — tokens may be minted directly
4. **Ave.ai holder data can be wrong** — showed 578K for an address with 0 on-chain
5. **BscScan HTML scraping works via curl** (no Cloudflare on curl) even when browser is blocked
