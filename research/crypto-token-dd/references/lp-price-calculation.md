# LP Price Calculation from Reserves

When DexScreener/CoinGecko show no data but a PancakeSwap V2 pair exists, you can calculate the real token price directly from the LP pool reserves via RPC.

## Technique

The PancakeSwap V2 pair contract stores token0 and token1 balances. You can query these via `balanceOf()` on each token contract, targeted at the pair address.

### Step 1: Find the pair address

```python
# PancakeSwap V2 Factory on BSC
factory = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"
# getPair(token0, token1) selector: 0xe6a43905
data = "0xe6a43905" + 
       "000000000000000000000000" + token0_addr[2:] + 
       "000000000000000000000000" + token1_addr[2:]
```

**Common BSC pairs:**
- WBNB: `0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c`
- USDT: `0x55d398326f99059ff775485246999027b3197955`
- BUSD: `0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56`

### Step 2: Get reserves

```python
pair_addr = "0x63844bd4bfad910b1643713302a1cc1ed20d50c3"

# PRO in LP via balanceOf
pro_data = "0x70a08231" + "000000000000000000000000" + pair_addr[2:]
pro_in_lp = int(eth_call(pro_contract, pro_data), 16)

# USDT in LP via balanceOf
usdt_data = "0x70a08231" + "000000000000000000000000" + pair_addr[2:]
usdt_in_lp = int(eth_call(usdt_contract, usdt_data), 16)

# Calculate price
pro_price = usdt_in_lp / 10**18 / (pro_in_lp / 10**9)  # USDT decimals=18, PRO decimals=9
```

### Step 3: Calculate total liquidity value

```python
total_liq = usdt_in_lp / 10**18 + (pro_in_lp / 10**9) * pro_price
# ≈ 2× the USDT side (for equal-weight LP)
```

## Real-world example: PRO Token

| Query | Result |
|-------|--------|
| PRO in LP (balanceOf, pair→PRO) | 715,423 PRO |
| USDT in LP (balanceOf, pair→USDT) | 43,149,860 USDT |
| Calculated price | $60.31/PRO |
| Total LP value | ~$86.3M |

## Pitfalls

- **token0 may not be the base you expect** — always check which token is token0 vs token1 via the pair contract itself (`0x0dfe1681` / `0xd21220a7`)
- **LP may be on a different DEX** — PancakeSwap V2 is default on BSC, but check for BabySwap, Biswap, etc.
- **Stale liquidity** — the reserves change every swap; this is a point-in-time snapshot
- **Single-sided LP** — if only one side has meaningful balance, the pool is drained
