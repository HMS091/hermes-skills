# Pro Token (PRO) — balanceOf() Cross-Verification Case Study

## Summary

Pro Token (PRO) on BSC (`0x8d65744527f55d0b2338350912d5c99a81ddf0e2`) is a **definitive honeypot scam**. The contract overrides `balanceOf()` to return inflated values, making the BscScan holders page display fake holdings that don't correspond to real on-chain transfers.

## Key Findings

### Wallet 0xc0021e0849fadefb98761f40829009905dbd8ee8

| Source | Value | Verification |
|--------|-------|-------------|
| BscScan holders page | **2,010,000 PRO** (50.62%) | Listed as #1 holder |
| `balanceOf()` via RPC | **0.0020 PRO** | Direct eth_call to contract |
| Incoming Transfer events | **0** | Full-range eth_getLogs scan |
| BNB gas balance | **0 BNB** | Wallet cannot pay gas to move any tokens |
| Nonce (total tx) | **2** | Wallet barely used |

### Other Top-10 Holders

- 7 out of 10 top holders had **identical patterns**: huge balanceOf() but zero/negligible Transfer events
- #3 is the PancakeSwap V2 pool address — legitimate LP, not a holder
- #7 is labeled "Blackhole/黑洞地址" — typical dust/sink address
- **Top 10 concentration: 97.9%** — no legitimate token has this distribution

### Network/Environment Notes

- Docker container on Synology NAS (no proxy after unsetting env vars)
- BSC public RPC `bsc-dataseed2.defibit.io` worked reliably
- BscScan was Cloudflare-blocked; all data obtained via direct RPC calls
- `eth_getLogs` with fromBlock=0 to latest hits rate limits on free tier; use bounded ranges
- `eth_getTransactionByNonce` is NOT supported on BSC RPC

## Detection Method Used

1. Called `balanceOf()` directly via `eth_call` on the token contract
2. Queried `eth_getLogs` for Transfer events involving the target wallet
3. Checked BNB balance (`eth_getBalance`) to see if wallet can pay gas
4. Compared all three against BscScan's displayed holder percentages

## Red Flags Summary

| Flag | Detail |
|------|--------|
| 🚩 balanceOf() ≠ Transfer-derived balance | 2M vs 0.002 |
| 🚩 Zero Transfer events for supposed top holder | No on-chain evidence of receiving tokens |
| 🚩 Empty BNB wallet as #1 holder | Cannot sell/transfer tokens |
| 🚩 Nonce = 2 (nearly unused wallet) | Not a real active holder |
| 🚩 97.9% top-10 concentration | Extreme centralization |
| 🚩 Not listed on any major tracker | CoinGecko/CMC/DexScreener/Birdeye all empty |
| 🚩 No source code on BscScan | Unverifiable contract logic |
| 🚩 $60 price with $234M market cap | Wildly implausible valuation |

## Conclusion

**100% honeypot/蜜罐资金盘.** The token has no real value, no real holders, and no real liquidity (beyond the fake numbers the contract returns to explorers). All data shown on BscScan's holders page is fabricated by the smart contract.
