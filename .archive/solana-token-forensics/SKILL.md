---
name: solana-token-forensics
description: "Solana token forensics: insider, fees, holders."
platforms: [linux, macos, windows]
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [solana, crypto, onchain, memecoin, due-diligence]
    related_skills: [polymarket, daily-investment-briefing]
---

# Solana Token Forensics

## When to use

User drops a mint / pump.fun / DexScreener link and asks: is this real? 是不是老鼠仓/坐庄？谁赚了钱？能不能复制？Also for tracing who funded a wallet, verifying a "creator made $X" claim, and health-checking a token before buying.

Rule: **no claim without a tx, an account, or an API field behind it.** This user checks numbers and will catch invented ones. When a relationship is only asserted by the user (e.g. "this mint is the one in the video"), say so and analyse the chain independently.

## Step 0 — pin the token's real identity

```bash
M=<mint>
curl -s "https://api.dexscreener.com/latest/dex/tokens/$M" | jq '.pairs[] | {dexId,pairAddress,created:.pairCreatedAt,liq:.liquidity.usd,vol24:.volume.h24,mcap:.marketCap}'
curl -s "https://api.rugcheck.xyz/v1/tokens/$M/report/summary"
curl -s "https://api.rugcheck.xyz/v1/tokens/$M/report" -o rug.json   # topHolders, insiderNetworks, knownAccounts, markets
```

The full RugCheck report is the cheapest orientation available: `topHolders` (with `insider` flags and `knownAccounts` labels such as "Pump Fun AMM", "Streamflow Vault", "Creator"), `insiderNetworks` (4–7 wallet transfer clusters), `markets`, `totalHolders`, `creatorBalance`.

A mint **suffix proves nothing**: a `…pump` ending can be vanity-ground by anyone, and RugCheck's `launchpad` field can disagree with the actual DEX. Trust `markets[].marketType` and the pool account, not the name.

## Step 1 — price and volume history

```bash
curl -s "https://api.geckoterminal.com/api/v2/networks/solana/pools/<pool>/ohlcv/day?aggregate=1&limit=100&currency=usd"
curl -s "https://api.geckoterminal.com/api/v2/networks/solana/pools/<pool>/ohlcv/hour?aggregate=1&limit=200&currency=usd"   # last ~8 days only
```

Use it for launch MC, peak MC, drawdown, and **how many days carried real volume**. A chart that re-pumps toward the same MC several times over weeks, on sustained daily volume, is being maintained — not discovered once.

## Step 2 — holder census in ONE RPC call

Never page the mint's signature history to count holders: a live meme does ~50k tx/day, so reaching launch via `getSignaturesForAddress` takes hours. One `getProgramAccounts` with a dataSlice returns every holder with owner+amount:

```python
rpc("getProgramAccounts", ["TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb", {
    "encoding": "base64", "dataSlice": {"offset": 32, "length": 40},
    "filters": [{"memcmp": {"offset": 0, "bytes": MINT}}]}])
# d[0:32] = owner pubkey (base58 it), d[32:40] = amount u64, decimals from the mint
```

Filtering on `dataSize: 165` silently returns almost nothing for Token-2022 tokens — the bulk accounts are **170** bytes (extensions). Query with `memcmp` only, then group by `space`.

Report concentration honestly: top10 / top100 / top1000 share, dust-account count, and owners-per-ATA outliers (one owner holding 150–227 ATAs is a router/bot, not a whale).

## Step 3 — find the REAL creator and fee recipient

Aggregators' `creator` is often **not** the wallet that collects fees, and often not a human: serial launcher bots create dozens of coins an hour. Do not stop at the label.

1. Pull the labeled creator's signatures. If it creates/buys many different mints within minutes and round-trips 0.1–0.9 SOL, it is a launch/sniper bot, not the operator.
2. Find the actual creation from `CreateV2` on pump.fun program `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` (log line `Instruction: CreateV2`), dev buy usually in the same tx.
3. Confirm against the PumpSwap pool struct: `getAccountInfo(pool, base64)` (owner `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`) — `coin_creator` sits at byte offset **211**; base_mint 43, quote_mint 75, lp_mint 107, base vault 139, quote vault 171, lp_supply 203. Details in `references/pumpfun-pumpswap.md`.

## Step 4 — trace the money (what aggregators never show)

Scan **every** transaction of the creator/fee wallet, aggregating SOL and token deltas per direction:

```python
from solana_rpc import rpc, sigs, all_sigs, tx, sol_delta, token_delta, instruction_names  # scripts/solana_rpc.py
names = instruction_names(t)
```

- Fee income appears as `CollectCoinCreatorFee` / `CollectCreatorFeeV2` / `SweepCreatorFee` / `DistributeCreatorFees*`; sum only positive SOL deltas carrying those names.
- Then follow the **outflows**: profit usually leaves via a plain transfer to a treasury wallet, which forwards in chunks to 2-tx "hop" wallets that drain instantly. That hop chain is the layering pattern of a studio, not a retail seller.
- Check whether the dev actually sold: token delta ≈ 0 while a large bag is still held means the money came from fees, not from dumping. State which one it is — it flips the verdict.

## Step 5 — bundling test (were 20 wallets front-running?)

Two cheap tests; do not crawl mint history.

1. `getBlock(create_slot, {transactionDetails:"full", maxSupportedTransactionVersion:1})` for **1–3 blocks only**, keeping txs whose accountKeys contain the mint. A clean create block (dev buy + curve account only) rules out a same-block bundle.
2. Sample ATA first-receipt times: `getSignaturesForAddress(ata, {limit:1000})[-1].blockTime` is when that holder first received the token (ATAs carry few txs, so one call each). Bucket the sample by hours after create — a crowd arriving inside minutes is a bundle; a spread over days is real flow. Holders that all share one timestamp are an airdrop, not a community.

## Step 6 — hidden whales and market-making footprints

A fresh wallet with no visible SOL payment that suddenly holds a big bag = settlement/OTC transfer, i.e. someone hiding size. Observed patterns:

- `CreateGeneralAccount` / `CreateSmartAccountVault` + `ValidateExecutionV3` / `ApproveExecution` / `PostOptimisticExecution` / `VaultTransferSol` → a smart-account vault doing TWAP/DCA accumulation; the owner later sweeps the whole bag into a fresh address.
- Tokens moved into a Streamflow escrow (vault labeled "Streamflow Vault", program `strmRqUCoQUgGUan5YhzUZa6KqdzwX5L6FpUxfmKg5m`): the escrow's **first tx signer** is who locked it, and that timestamp tells you when. A 5% lock opened weeks after launch is market-making, not a launch commitment.

## Step 7 — verdict + replicability math

Answer three axes separately, each with its evidence:

| Axis | Evidence to cite |
|---|---|
| 老鼠仓 (insider front-run) | launch-block txs, dev allocation %, whether dev sold |
| 坐庄 (market-making) | TWAP accumulation, locks, repeated re-pumps, LP count, sustained volume |
| 自然炒作 (organic) | distinct holders, holder-acquisition spread, dust check (real wallets vs airdrop) |

Then cost the copycat claim in the user's terms:

- creator fee ≈ **0.3–0.35% of traded volume** on PumpSwap (verify: collected fees ÷ lifetime volume);
- invert it — "to earn $10k you need ≈$3M of volume" — and compare with what the case coin actually did;
- give base rates plainly (most launches earn $0–50 lifetime in fees) and separate **mechanism is copyable** from **outcome is not**;
- when the source is a video/course, check where the author's money actually comes from (description funnel) and say it.

## Pitfalls

- `getTransaction` fails with `Transaction version (1) is not supported` unless `maxSupportedTransactionVersion: 1`. Set it once in the helper, not per call.
- Public RPC `api.mainnet-beta.solana.com` 429s above ~3 concurrent requests. Use 2–3 threads with backoff, and never run two scans against it at once — ~700 txs take minutes, not seconds.
- `getBlock` with `transactionDetails:"full"` on a 1,200-tx block is heavy; 30 blocks can blow past 10 minutes. Restrict to the creation slot.
- `getSignaturesForAddress` returns newest-first with no reverse cursor — paginating to launch is a trap; use Steps 2 and 5 instead.
- A creator balance of 0 does not mean the dev sold; it means that wallet holds no tokens *now*. Check token delta across its history.
- Free indexers (SolanaFM and friends) come and go; public RPC + RugCheck + DexScreener + GeckoTerminal cover the whole job without API keys.
- Convert SOL to USD with a **dated** price (`coingecko /coins/solana/market_chart`), not today's — a fee total in SOL priced at today's rate misstates profit when the event was weeks ago.

## Output format (this user)

Chinese, conclusion first, then tables of real numbers, then risks. Structure that worked: 一句话结论 → 来源说的 vs 链上事实 → 钱被谁赚走（分层钱包表）→ 老鼠仓/坐庄逐项判定表 → 走势画像 → 能不能复制的算账 → 风险与建议. Shorten addresses to the first 8 chars in prose, keep full ones in code blocks, and separate explicitly what is verified / inferred / not checkable. No hedging padding.

## Files

- `scripts/solana_rpc.py` — tested RPC helpers (retry/backoff, v1 txs, SOL/token deltas, full signature paging).
- `references/pumpfun-pumpswap.md` — pool struct offsets, fee instruction names, entity labels, API map.
