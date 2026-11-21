# Pump.fun / PumpSwap reference

Everything here was verified by decoding on-chain accounts and logs; treat offsets as current
layout, not a guarantee — re-decode before relying on a field that matters.

## Program IDs

| Program | ID | Use |
|---|---|---|
| pump.fun bonding curve | `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` | `CreateV2`, `SweepCreatorFee`, `DistributeCreatorFees*`, buy/sell on curve |
| PumpSwap AMM | `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA` | pool account owner, `CollectCoinCreatorFee`, `BuyExactQuoteIn`, `Deposit`/`Withdraw` |
| pump.fun fee sharing | `pfeeUx…` (prefix) | `CreateFeeSharingConfig`, `DistributeCreatorFees` |
| Streamflow | `strmRqUCoQUgGUan5YhzUZa6KqdzwX5L6FpUxfmKg5m` | vesting/token locks; `Create`, `ClaimFee` |
| Token-2022 | `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` | most new pump mints (metadata pointer, transfer fee) |
| SPL Token | `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA` | WSOL vaults, classic ATAs |

## PumpSwap pool account layout (301 bytes, `base64` decode)

| Offset | Field |
|---|---|
| 8 | bump (u8) |
| 9 | index (u16) |
| 11 | creator (pubkey) |
| 43 | base_mint |
| 75 | quote_mint (usually WSOL) |
| 107 | lp_mint |
| 139 | pool base token account |
| 171 | pool quote token account |
| 203 | lp_supply (u64) |
| 211 | **coin_creator** — the wallet that receives AMM creator fees |

Field detection trick: base58-slice 32 bytes at every offset and match against the mint/LP/vault
pubkeys you already know — that pins the layout without an IDL.

## Fee instructions seen in logs

`CollectCoinCreatorFee`, `CollectCreatorFeeV2`, `CollectCreatorFee`, `SweepCreatorFee`,
`TransferCreatorFeesToPump`, `DistributeCreatorFees`, `DistributeCreatorFeesV2`,
`DistributeFeeToHolders`, `CreateFeeSharingConfig`.

Read them from `meta.logMessages` lines containing `Instruction: `; the parsed-instruction JSON is
`null` for these Anchor programs, so logs are the only cheap classifier.

`CollectCoinCreatorFee` txs contain **no mint account** — the accounts are the creator, a WSOL fee
vault, the creator-vault PDA and the AMM program. So you cannot prove from the tx alone that the
collected fees came from one specific coin: state the total and say it may span every coin that
wallet launched.

## Fee economics (for the replicability math)

- Creator share lands around **0.3–0.35% of traded volume** on PumpSwap's high-fee tier. Verify per coin:
  `sum(positive SOL delta of fee-instruction txs) ÷ lifetime volume`.
- Total swap fee (LP + protocol + creator) is higher than the creator share, which is why
  wash-trading your own coin to farm creator fees loses money — say so when a user proposes it.

## Launch anatomy

1. `CreateV2` tx: payer = creator, dev buy in the same tx (typical 0.4 SOL → 1–1.5% of a 1B supply).
2. Curve fills at ~$40–70k MC → `Migrate` creates the PumpSwap pool; `pairCreatedAt` on DexScreener is migration time, not launch time.
3. Extra Meteora DLMM pools appear within hours (different `dexId`/`labels` on DexScreener) — their volume is **not** in the PumpSwap pool's GeckoTerminal OHLCV.

## Entity labels worth recognising in `knownAccounts`

`Pump Fun AMM`, `Pump Fun`, `LaunchLab`, `Streamflow Vault`, `Creator`. Everything else is unlabeled;
identify wallets from behaviour (tx cadence, round-trip sizes, ATA count), not from labels.

## API map

| Endpoint | Gives | Limits |
|---|---|---|
| `api.dexscreener.com/latest/dex/tokens/<mint>` | all pools, liquidity, 24h volume, `pairCreatedAt`, socials | no key; some pairs lack `liquidity` — use `.get` |
| `api.rugcheck.xyz/v1/tokens/<mint>/report` | topHolders + insider flags, insiderNetworks, knownAccounts, markets, totalHolders, creatorBalance | no key; a few hundred KB |
| `.../report/summary` | score, risks, LP locked % | no key |
| `api.geckoterminal.com/api/v2/networks/solana/pools/<pool>/ohlcv/{day,hour}` | OHLCV candles | no key; hour window ≈ last 200h; recent trades endpoint returns only ~300 |
| `api.coingecko.com/api/v3/coins/solana/market_chart` | dated SOL/USD for converting old fees | no key, rate-limited |
| `api.mainnet-beta.solana.com` | everything raw: getTransaction, getBlock, getProgramAccounts, getSignaturesForAddress | no key, ~3 concurrent max, 429s above that |

Not usable without keys / unreliable: Solscan, Birdeye, Helius, Moralis, SolanaFM (502s).
