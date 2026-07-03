# Web3 Earning Platforms Research (May 2026)

## Gitcoin — Public Goods Funding (Not Bounties)

### Critical Context: Gitcoin's Transformation

Gitcoin has **fully transitioned** from being a bounty/task marketplace (2017-2023) to a **public goods funding platform** (2024-present). The old explorer (explorer.gitcoin.co) is defunct. Gitcoin is now primarily a knowledge directory + grant coordination platform.

**Current Gitcoin.co structure:**
- `/campaigns/` — Active and past grant rounds (120+ campaigns)
- `/research/` — Deep dives into funding mechanisms
- `/apps/` — Funding platforms directory (120+ listings)
- `/mechanisms/` — Funding mechanism directory
- No `/bounties`, no `/explorer` — those pages are gone

### Gitcoin Grants 24 (GG24) — Detailed Breakdown

**Headline:** $1.8M distributed across 6 domains using plural funding mechanisms ($1.175M from Gitcoin, $632.5K from external partners).

#### Domain 1: Ethereum Developer Tooling & Infrastructure ($600K)
- **Deep Funding (Seer prediction markets):** $350K pool. Evaluated by 50 prediction market evaluators.
- **Quadratic Funding (via Giveth on Arbitrum):** $200K matching pool.
- **Results:** 55 projects funded from 1,028 unique donors, 2,361 total donations.
- **Direct community contributions:** $29,739
- **Notable:** Human Passport (604 donors), EthStaker ($765.79 per unique donor — highest match efficiency).
- **Matching cap:** $10K per project.

#### Domain 2: Privacy ($150K)
- QF matching pool. 7,427 QF votes cast.
- Raised 35.41 WETH total, ~$13K in community donations.
- Highest-funded project: dev3pack at 6.4368 WETH.

#### Domain 3: Interop Standards, Infrastructure & Analytics ($150K)
- **QF via Giveth on Celo:** $100K matching pool.
- **Results:** 23 projects funded, 328 unique donors, 681 donations.
- **Community contributions:** $6,918 direct.
- **Highlights:** Silvi (highest match $10,913), Superchain Eco (82 donors — broadest support), Hypercerts Foundation ($448.33 per donor — highest efficiency).
- **Observation:** Capital clustered around analytics/visibility tools. QF proved effective for standards work.

#### Domain 4: Public Goods R&D ($332.5K)
- **Public Goods Tooling Development Round:** $155K budget. 43 pre-applications, 12 projects proactively funded, $81.8K distributed, $60K in retroactive rewards, council-based allocation.
- **Bioregional Reforestation Round:** $100K matching pool across 9 bioregions (Nigeria, Kenya/Uganda, Cascadia, Mediterranean Coast, etc.)
- **Key partners:** CeloPG, Ethereum Foundation, Ma Earth, Climate Coordination Network ($35K), BioFi Project ($5K), GoodDollar ($4K in G$ tokens).

#### Domain 5: Targeted Development & Adoption ($450K)
- **Solutions Development Grants:** Up to $155K in milestone-based grants. 51 pre-applications, 22 full applications, 19 approved.
- **Grant range:** $2.5K–$20K per project. Spanned all 17 UN Sustainable Development Goals.
- **Localism Fund + Bioregional Reforestation** (additional pools within this domain).

#### Domain 6: InfoFi (Information Finance) ($125K)
- Information verification and data market mechanisms.

### Key Insights

| Metric | Value |
|:-------|:-----:|
| Total distributed | ~$1.8M |
| Gitcoin portion | $1.175M |
| External partner portion | $632.5K |
| QF matching pools (Giveth) | $300K (Dev Tooling + Interop) |
| QF direct donations | $36,657 (down from $95,278 in GG23) |
| Solutions Dev grants | 19 projects, $2.5K–$20K each |
| Public Goods Tooling | 12 projects, $81.8K distributed |
| Partner count | Multiple (CeloPG, EF, Climate, BioFi) |

**QF donation volume declined** ($36,657 vs $95,278 in GG23) due to narrower project scope (78 QF projects vs 235 in GG23), but the new domain allocator model successfully attracted external capital.

### How to Participate (AI-Compatible Paths)

1. **Write a grant proposal** for an open-source tool, infrastructure, or research project. AI can draft the full proposal. Target size: $2.5K-$20K.
2. **Participate in Deep Funding prediction markets** (evaluator role).
3. **Donate strategically** to projects you want to see funded ($1 minimum, QF amplifies impact).

### Key URLs
- Gitcoin home: `https://gitcoin.co/`
- GG24 campaign: `https://gitcoin.co/campaigns/gitcoin-grants-24-gg24`
- Explore projects (GG24): `https://grants.gitcoin.co/`

---

## Layer3 — Onchain Quest Platform

Layer3 (layer3.xyz) is a Web3-native quest/earn platform. Unlike traditional freelancing, tasks are predefined onchain interactions with automated reward distribution.

### Platform Overview
- **Type:** Quest/earn platform (not freelancer marketplace)
- **Model:** Complete pre-defined tasks → earn rewards (tokens, points, NFTs)
- **Authentication:** Email + wallet (MetaMask, WalletConnect)
- **Payments:** Crypto-native (tokens/stablecoins)
- **Automation accessibility:** Web-based SPA (React/Next.js), accessible via Playwright

### Task Categories (Directly Observed)

| Category | Examples | Typical Reward | AI % |
|:---------|:---------|:-------------:|:----:|
| **Cross-chain bridging** | Bridge ETH to Arbitrum/Optimism/Base | $5-$50 | 100% |
| **DEX trading** | Swap on Uniswap, PancakeSwap, 1inch | $10-$100 | 100% |
| **Lending/borrowing** | Deposit to Aave, Compound, Morpho | $10-$80 | 100% |
| **Liquid staking** | Stake ETH via Lido, Rocket Pool | $20-$100 | 100% |
| **Restaking** | Deposit to EigenLayer, Symbiotic | $30-$150 | 100% |
| **Yield farming** | Provide liquidity, LP staking | $20-$200 | 100% |
| **NFT minting** | Mint from curated collections | $5-$30 | 90% |
| **NFT trading** | Buy/sell on Blur, OpenSea | $10-$50 | 90% |
| **Social tasks** | Follow Twitter, join Discord, retweet | $2-$20 | 50% |
| **Protocol testing** | Test new dApps, provide feedback | $50-$500 | 60% |
| **Content creation** | Write threads, make videos | $20-$200 | 80% |
| **Governance** | Vote in DAO proposals | $5-$50 | 100% |

### Reward Distribution
- **Immediate:** L3 points, protocol tokens, USDC
- **Delayed:** Airdrop eligibility, NFT badges (future claim)
- **Value per task:** Typically $2-$500+ USD equivalent

### AI Automation Potential

**Fully automatable (100%):** Bridge, swap, lend, stake, restake, farm, governance vote — all are standard EVM contract interactions that a script can execute.

**Partially automatable (50-90%):**
- NFT mint/trade — requires market awareness (which collection is hot)
- Social tasks — can automate follow/like/retweet but risk account flagging
- Content creation — AI generates text/video scripts; manual posting needed

**Low automation (<50%):**
- Protocol testing — requires understanding new UX, reporting bugs

### Anti-Detection Considerations

Layer3 has Sybil prevention measures:
- Wallet age requirements
- Transaction history analysis
- CAPTCHA on some tasks
- IP/proxy tracking

**Mitigation strategies:**
- Use aged wallets (3+ months, with prior transaction history)
- Space out task completion (not 50 tasks in 5 minutes)
- Vary gas price and timing patterns (avoid identical tx patterns)
- Use residential proxies
- Start with lower-value tasks to build wallet reputation

### Revenue Estimates

| Scenario | Tasks/Day | Avg Reward | Daily | Monthly |
|:---------|:--------:|:---------:|:-----:|:-------:|
| Conservative (paced, avoid detection) | 20-50 | $10 | $200-500 | $6K-15K |
| Moderate (optimized scripts) | 50-100 | $15 | $750-1.5K | $22K-45K |
| Aggressive (max throughput) | 100-200 | $20 | $2K-4K | $60K-120K |

**Note:** Real-world results are limited by gas costs, anti-detection measures, task availability, and token liquidity. Conservative estimates are realistic for a first attempt.

### Key URLs
- Home: `https://layer3.xyz/`
- Activations/Quests: `https://layer3.xyz/activations`
- Streaks: `https://layer3.xyz/streaks`

---

## Comparison: All Earning Pathways

| Dimension | Freelancer | CryptoTask | LaborX | Gitcoin Grant | Layer3 Quest |
|:----------|:---------:|:---------:|:-----:|:------------:|:-----------:|
| **Risk** | Medium | Low | Low | Medium | High (bot detection) |
| **Anonymity** | ⚠️ (PayPal) | ✅ Full | ✅ | ❌ | ✅ Wallet |
| **Single payout** | $50-$6K | $150-$18K/mo | $15-$4K | $2.5K-$20K | $2-$500 |
| **AI compatibility** | High | High | High | Medium | Very High |
| **Anti-detection** | Low | None | None | Low | High |
| **Setup time** | Day 1 | Day 1 | Day 1 | Weeks (rounds) | Day 1 |
| **First payout** | Days | Days | Hours | Weeks-Months | Minutes |
| **Platform fee** | 2.5-10% | Up to 3% | 0-10% | 0% (gas only) | Variable |
| **Best for** | Steady income | High-value Web3 | Quick gigs | Research/infra $ | Automated volume |

## Practical Recommendation

**Tier 1 (Start Here):** Layer3 for quick wins + Freelancer for steady income
**Tier 2 (Add When Ready):** CryptoTask for anonymous high-value + LaborX for crypto gigs
**Tier 3 (Long-term):** Gitcoin grants for big proposal-based funding (monthly rounds)
