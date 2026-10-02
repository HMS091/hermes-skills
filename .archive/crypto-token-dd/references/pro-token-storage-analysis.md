# Pro Token (PRO) Storage Slot Analysis — "Renounced-but-Manipulated" Pattern

**Contract:** `0x8d65744527f55d0b2338350912d5c99a81ddf0e2`  
**Chain:** BSC (BEP-20)  
**Date:** 2026-07-04  
**Decimals:** 9 (non-standard — critical to verify before balanceOf interpretation)

## Constructor Bytecode Analysis (Initial State)

From the verified creation bytecode on BscScan:

```
constructor:
  owner = msg.sender                         // Deployer is owner
  slot_0xa (10) = 0x64 = 100                // Initial parameter
  slot_0xc (12) = 0x12c = 300               // Initial parameter
  slot_0xd (13) = msg.sender                // Liq wallet = deployer
  slot_0x6 (6)  = msg.sender                // Controller = deployer
```

## Current Storage (2026-07-04 via eth_getStorageAt)

| Slot | Initial | Current | Delta | Meaning |
|------|---------|---------|-------|---------|
| 0 | — | `0x00` | — | Generic |
| 1 | — | `0x00` | — | Generic |
| 2 | — | `0x189a5631072899` | — | Total supply |
| 3 | — | `0x50726f20546f6b656e...12` | — | name = "Pro Token" (len 12) |
| 4 | — | `0x50726f...06` | — | symbol = "Pro" (len 6) |
| **05** | deployer | **`0xdead`** | ✅ Renounced | Owner |
| **06** | deployer | **`0x96079ef9b7630a55608a3d4b90733ac56434a5ff`** | 🔴 Changed! | Controller transferred |
| 07 | — | `0xf9074b5c035c961443373f78a6344e5adc61d314` | — | Marketing wallet |
| 08 | — | `0x00` | — | — |
| 09 | — | `0x63844bd4bfad910b1643713302a1cc1ed20d50c3` | — | PancakeSwap V2 LP pair |
| **10** | **100** | **500** | 🔴 **5x increase!** | Parameter A (tax?) |
| 11 | — | `0x00` | — | — |
| **12** | **300** | **250** | 🟡 Changed | Parameter B (threshold?) |
| **13** | **deployer** | **`0x543302e9d9411e563ad8266ceef2a85b66050832`** | 🔴 Changed! | Liq wallet transferred |
| **14** | **0** | **1781982105** (2026-06-20) | 🔴 Active recently | Last config change timestamp |

## LP Token Analysis

**Pair:** `0x63844bd4bfad910b1643713302a1cc1ed20d50c3` (PRO/USDT on PancakeSwap V2)

| Metric | Value |
|--------|-------|
| LP total supply | 185,742,231,653 LP tokens |
| LP at dead address | 185,734,841,148 (99.996%) |
| Remaining LP | 7,390,505 (0.004%) — spread across many addresses |
| Pool USDT reserve | $43,132,758 |
| Pool PRO reserve | 715,763 PRO |
| Price (from LP) | ~$60.26/PRO |

**Conclusion:** LP is permanently locked — 99.996% burned. No one can withdraw. But also zero trading activity (0 Swap events in last 100K+ blocks across multiple RPC nodes).

## Blacklist Check

Tested via `eth_call` with `0x9b19251a` (isBlacklisted selector):

| Address | Blacklisted? |
|---------|:-----------:|
| Dead address `0x...dead` | 🟢 No |
| Controller `0x96079ef9...` | 🟢 No |
| Marketing wallet `0xf9074b5c...` | 🟢 No |
| **Liquidity wallet** `0x543302e9...` | 🔴 **Yes** |
| #1 holder `0xc0021e08...` | 🟢 No |
| LP pair `0x63844bd4...` | 🟢 No |

Mapping cannot be enumerated on-chain — total count of blacklisted addresses is unknown without indexed data.

## Top Holder (#1) Analysis

**Address:** `0xc0021e0849fadefb98761f40829009905dbd8ee8`

| Metric | Value |
|--------|-------|
| PRO balance | 3,675,725 PRO (53.08% of supply) |
| BNB balance | 0 BNB |
| USDT balance | 0 USDT |
| Total transactions (nonce) | **2** |
| Any sells? | **0 — never sold** |

## Owner Lock Analysis

```
eth_call(owner()) → 0x000000000000000000000000000000000000dead
transferOwnership() requires: msg.sender == owner()
```

- Only `0xdead` can call `transferOwnership()`
- `0xdead` private key = nonexistent
- **Owner permanently locked. Cannot be changed back.**

## The "Renounced-but-Manipulated" Pattern

```
Timeline:
  Deployment (by deployer A)
  → Controller transferred to address B (0x96079ef9...)
  → Address B changes tax (100→500), threshold (300→250), liq wallet
  → Last activity: 2026-06-20 (slot 14)
  → Owner renounced to 0xdead
  → Now: looks "safe" because owner is dead
  → BUT: tax was already hiked, liquidity wallet was already changed
```
