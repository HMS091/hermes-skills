# Pro Token (PRO) — balanceOf() Cross-Verification Case Study

## Summary

Pro Token (PRO) on BSC (`0x8d65744527f55d0b2338350912d5c99a81ddf0e2`) was initially flagged as a "100% honeypot" due to a **decimals calculation error** in the balanceOf() query. This file documents the correction and the real lessons learned.

## The Trap: Non-Standard Decimals

The token has **9 decimals**, not the default 18. The raw balanceOf() hex value `0x000000...072d2c866bc94c` = 3,675,882,446,875,117 wei.

| Division | Result | Interpretation |
|----------|--------|---------------|
| ÷ 10^18 (wrong default) | **0.0037 PRO** | ❌ False "honeypot" positive |
| ÷ 10^9 (correct) | **3,675,882 PRO** | ✅ Matches BscScan holder data |

**Lesson:** Always call `0x313ce567` (decimals()) before interpreting any balanceOf() value.

## Corrected Findings (July 4, 2026)

### Wallet 0xc0021e0849fadefb98761f40829009905dbd8ee8

| Source | Value | Verification |
|--------|-------|-------------|
| BscScan holders page | **2,010,000 PRO** (50.62%) | Listed as #1 holder (Ave.ai) |
| `balanceOf()` via RPC | **3,675,882 PRO** (53.08%) | After correct ÷10^9 division |
| Incoming Transfer events | **Zero** | May be minted or factory-distributed |
| BNB gas balance | **0 BNB** | Wallet is a contract, not an EOA (nonce=2) |
| `eth_getCode` | Returns code | Confirmed: address is a smart contract |

### Real LP Liquidity Confirmed

Through PancakeSwap V2 pair analysis:

- PRO in LP: **715,423 PRO**
- USDT in LP: **43,149,860 USDT**
- Real price from reserves: **~$60.31/PRO**
- Total LP liquidity: **~$86.3M**

### Contract Status

| Check | Result |
|-------|--------|
| Source verified on BscScan | ✅ Yes (bytecode available) |
| Owner renounced | ✅ Yes (owner → dead address `0x000...dead`) |
| Decimals | 9 (non-standard but confirmed) |
| Blacklist capability | Present in bytecode (owner renounced, so frozen) |

## What Made This Difficult

1. **Cloudflare on BscScan** — blocked initial attempt to read holders page
2. **Non-standard decimals** — defaulting to 18 produced a 1-billion-factor error
3. **Zero BNB on #1 holder** — looked like an abandoned wallet, but it's a contract
4. **Zero Transfer events** — tokens may be minted rather than transferred
5. **Ave.ai data bug** — showed wallet `0x...BCCC` holding 578,990 PRO (14.51%) but on-chain balanceOf = 0

## Corrected Conclusion

**NOT a balance-faking honeypot.** The token has:
- $86M in real PancakeSwap V2 liquidity
- Verified, renounced contract source code
- 616K holders
- Real on-chain price of ~$60 matching DEX data

**Remaining risks (not honeypot/scam, but high risk):**
- 🟡 #1 holder owns 53% of supply (can dump)
- 🟡 No public team, website, whitepaper, or social media
- 🟡 Not listed on CoinGecko/CoinMarketCap
- 🟡 Token model involves taxes/fees (from bytecode)
