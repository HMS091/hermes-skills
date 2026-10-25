# Crypto Trading Repo Audit (Solana bots/CLI/terminals)

Extends the base procedure for trading bots and CLIs. The money-path greps that matter beyond section 2:

## Hidden monetization (the #1 attack in "free" bots)
- `grep platformFee|serviceFee|adminFee|devFee|donate|kickback` — free tools monetize by inserting a fee account into every swap. Zero hits = clean; every hit needs a per-line verdict.
- Read the tip-account registry file (e.g. `transactions/landing/tip-accounts.ts`): every address must belong to an OFFICIAL SWQoS provider (Jito, Nozomi, Helius Sender, ZeroSlot, bloXroute). An address that matches none of them = money flowing to the repo author. A public tip registry itself is a strong positive signal — cite it as evidence.

## Outbound inventory in Node/TS repos
- URL-regex extraction FAILS on template strings (`axios.post(\`https://x/${key}\`)`) — grep the call sites (`axios\.`, `fetch\(`) and read each provider file. Every target must be a user-configured endpoint from env; a hardcoded host is a finding.
- Grading nuance: a user-supplied key embedded in the URL path is the provider's API design (🟡 at most); a baked-in key constant is a backdoor.

## Wallet/key storage grading
- Plaintext keyfile with 0o600 perms in a home dir = normal for CLIs → 🟡, not 🔴. Verdict must split: fine for personal use, unacceptable for a platform — state the migration requirement (MPC infra like Turnkey) in the same breath.

## Supply chain for npm-published tools
- Verify the published package matches repo source (tarball vs git HEAD) before trusting install instructions; confirm deps are official ecosystem SDKs (`jito-ts`, `raydium-sdk`, `@meteora-ag/*`, `@orca-so/whirlpools`, `@triton-one/yellowstone-grpc`, `pumpdotfun-sdk`). An obfuscation/random-HTTP dep is a red flag.

## Landscape verdict (2026): no open-source platform engine exists
For memecoin trading terminals, the money sits in the business layer — limit-order matching, referral/rebate systems, RBAC, multi-user API, frontend — and NONE of that is open source anywhere. Every open repo is a single-trader bot/CLI, so "can I use this as the engine" must be answered in layers: execution/data layer yes, business layer must be self-built.

Usable as execution-layer base:
- `outsmartchad/onchain-dex-cli` (~580★, MIT, TypeScript): 18 DEX adapters + 12 SWQoS landing processors + Yellowstone gRPC/WebSocket event streams + LP manager. Best code base of the class; caveats: single author, alpha versioning, slow updates — fork and maintain.
- `mortdeus/solana-copy-sniper-mev-trading-bot` (~4.5k★, BSD-3): copy-trade/MEV/bundler features, but keyword-stuffed marketing README — audit before trusting.
- `chainstacklabs/pumpfun-bonkfun-bot` (~1k★, Apache-2.0): org-backed (Chainstack), actively maintained, narrow scope (pump.fun family only).
- `warp-id/solana-trading-bot` (2.3k★): stale since 2024 — skip.

Reuse pattern: fork the execution/data layers, self-build the business layer. "未发现后门" remains a sampling verdict — keep a human reviewer plus an audit firm before real money flows.