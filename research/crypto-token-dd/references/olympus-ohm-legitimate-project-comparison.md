# Olympus (OHM) — Legitimate Project Analysis Reference

## Session Context

Used as a counter-example to the Pro Token (PRO) honeypot during crypto token due diligence. OHM demonstrates what a real, legitimate, well-known DeFi project looks like through the same analysis tools (GoPlus, DexScreener, CoinGecko).

## Key Differentiators vs Scam Projects

| Signal | Olympus (OHM) — Legitimate | Pro Token (PRO) — Scam |
|--------|---------------------------|----------------------|
| CoinGecko rank | #149 listed | Not found |
| GoPlus honeypot | 0 (clean) | N/A (not on GoPlus) |
| Buy/sell tax | 0%/0% | Unknown/not verified |
| Open source | ✅ Verified | ❌ Unverified/blocked |
| Proxy contract | No (standard contract) | ✅ UUPS proxy (upgradable) |
| website/social | olympusdao.finance / @OlympusDAO | None found |
| Age | Multiple years | Unknown/recent |
| Creator balance | 0 (renounced) | Unknown |

## GoPlus Security Report (Full)

```json
{
  "is_honeypot": "0",
  "is_owner_change_balance": "0",
  "can_take_back_ownership": "0",
  "slippage_modifiable": "0",
  "is_proxy": "0",
  "hidden_owner": "0",
  "selfdestruct": "0",
  "trading_cooldown": "0",
  "transfer_pausable": "0",
  "cannot_sell_all": "0",
  "is_whitelisted": "0",
  "is_blacklisted": "0",
  "buy_tax": "0",
  "sell_tax": "0",
  "transfer_tax": "0",
  "is_open_source": "1",
  "is_mintable": "1",
  "trust_list": "1",
  "holder_count": "8380",
  "creator_balance": "0",
  "owner_balance": "0"
}
```

## Token Details

- **Name**: Olympus
- **Symbol**: OHM
- **Contract**: `0x64aa3364f17a4d01c6f1751fd97c2bd3d7e7f1d5`
- **Chain**: Ethereum (ETH)
- **Total Supply**: 19,724,012.99 OHM
- **Market Cap Rank**: #149
- **Categories**: DeFi, Rebase Tokens, Treasury-backed, Yield Farming, Governance

## Top Holders Analysis

| Rank | Address | % | Type | Notes |
|------|---------|---|------|-------|
| 1 | `0xb63cac384247597756545b500253ff8e607a8020` | 70.29% | Contract | Olympus Treasury |
| 2 | `0x245cc372c84b3645bf0ffe6538620b04a217988b` | 18.68% | Contract | LP Provider |
| 3 | `0xf65a665d650b5de224f46d729e2bd0885eea9da5` | 6.01% | Contract | - |
| 4-10 | Various | ~5% | Mixed | Includes UniV3 LP |

**Note on concentration**: 70% held by the protocol treasury is normal for OHM — it's a treasury-backed protocol where the treasury holds most tokens as backing. This is NOT the same as a scam's fake-concentration pattern because:
1. The treasury contract is open-source and audited
2. OHM is on CoinGecko with rank #149
3. The project has a real website, Twitter, and DAO governance
4. The treasury holdings are transparent and reported in protocol docs

## What Makes OHM Distinct from Scam Tokens

1. **Protocol-level minting**: `is_mintable: 1` exists but is part of the protocol's rebase mechanism (mint/burn for supply adjustments), not owner-abuse
2. **High concentration is by design**: Treasury-backed model requires the treasury to hold most of the supply
3. **No fake balanceOf()**: Actual balanceOf matches real Transfer events
4. **LP not locked but visible**: LP is held by known entities, not anonymous wallets
5. **Cross-chain presence**: Listed on Ethereum, Arbitrum, Optimism, Base, Solana, Berachain

## Usage in Due Diligence

When analyzing a token, compare against this profile. Red flags are:
- CoinGecko not listing a token that claims large market cap
- proxy contracts as top holders (proxies can be upgraded)
- balanceOf() that doesn't match Transfer events
- No website/social presence despite claiming millions in value
- Creator still holding tokens (OHM creator balance = 0)
