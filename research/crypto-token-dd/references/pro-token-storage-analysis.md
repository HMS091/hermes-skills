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

## Key Findings

1. **Owner IS renounced** (`0xdead`) — but the contract was actively controlled until 2 weeks before.
2. **Controller was transferred** to a different address (`0x96079ef9...`) — the original deployer gave control to someone else.
3. **Parameter at slot 10 was increased 5x** (100→500) — likely a tax/fee change.
4. **Liquidity wallet was changed** to a different address.
5. **Timestamp at slot 14 = 2026-06-20** — someone modified the contract then, and renounced shortly after.

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

**Lesson:** "Renounced" is NOT "safe." The owner extracted maximum value first, then walked away.
