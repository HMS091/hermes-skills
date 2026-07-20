---
name: business-project-evaluation
description: "Evaluate business project ideas OR stock/investment theses with a reality-checked framework. Covers business model analysis (service vs product), competition assessment, distribution strategy, and equity research (supply chain chokepoint analysis, influencer due diligence). For a solo developer with AI/automation capabilities."
version: 3.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [business, evaluation, market-research, competition-analysis, business-model, equity-research, stock-screening, solo-developer]
    related_skills: [autonomous-freelancing, web-research, crypto-token-dd]
---

# Business Project & Investment Evaluation

## Overview

A dual-purpose framework for evaluating (1) **business projects** as a solo developer with AI capabilities, and (2) **stock/investment theses** from influencers or thematic trends. Both share the same DNA: thesis → evidence → verification → risk assessment.

**Core insight (from user, June 2026):** Most AI-generated analysis is **overly optimistic** about competition and underestimates distribution difficulty. Always assume HIGH competition unless verified otherwise.

---

## Part 1: Business Project Evaluation

### Core Principles

#### 1. Competition is NEVER low — always assume HIGH

**If you think a market has low competition, you haven't looked hard enough.**

For AI customer service SaaS, for example:
- **Global players**: Intercom ($560M), Zendesk ($1.7B), HubSpot, Tidio ($40-60M), Crisp, ManyChat, LiveChat
- **AI-native players**: Forethought ($2k+/mo), Ada ($300+/mo), Ultimate.ai, Yellow.ai
- **Open source**: Chatwoot, Papercups — free, self-hosted
- **Vertical-specific**: Gorgias (ecommerce), Kustomer (retail), Glia (financial services)

Never say "competition is low" without verified data. Frame as: "the market has dominant players, but there may be an underserved segment."

#### 2. Distribution is harder than technology

**How will the first 10 customers be acquired?** If the answer involves "just post on Reddit/HN/Product Hunt" — that's not a plan.

B2B sales reality: 100 cold emails → 90 ignored → 8 rejections → 2 willing to talk.

#### 3. Service > Software for solo founders

| Model | Customer Reaction | Churn Risk |
|-------|------------------|------------|
| **SaaS** ("Buy my tool for $99/mo") | "Why not Intercom? Why not ChatGPT?" | High |
| **Managed service** ("I'll handle your customer service, you just get leads") | "Great, when can you start?" | Low (switching means losing operations) |

**Key question:** "Am I selling a tool the customer has to learn, or a result the customer just receives?"

#### 4. Pick the right customer segment

| Segment | Willingness to Pay | Best for |
|---------|-------------------|----------|
| Chinese-owned US contractors | **High ($200-500/mo)** | Language trust + high lead value ($3K-20K/lead) |
| Law firms | High ($200-500/mo) | $500-$5K/client value |
| Real estate | Medium ($100-300/mo) | High volume |
| Restaurants | Low ($30-80/mo) | Low CLV, skip |

#### 5. ⚠️ CRITICAL: Clarify the Actual Business Model First

**This is the most common analysis error.** User says "platform for X" — always verify what they actually mean:

| What they say | Could mean A | Or mean B |
|---------------|-------------|-----------|
| "上门按摩平台" | DTC marketplace (自建平台招技师) | Shop partnership (给店家做数字化+到家转介) |
| "电商平台" | Build a storefront (自营电商) | SaaS for sellers (帮卖家做店铺系统) |
| "家政平台" | Hire cleaners directly | Connect users with existing agencies |

**Ask before analyzing:**
- "Who is your customer? Consumer, shop/business, or corporate HR?"
- "Do you employ labor directly, or do existing businesses provide it?"
- "What does the shop/business get out of working with you?"
- "Revenue: transaction fee, subscription, referral commission, or ad?"

**Real example (July 2026):** User said "上门按摩平台". Analyzed DTC marketplace. User corrected: they wanted to help offline shops with free online booking + home service referral. **Two completely different models** — supply chain, competitors, legal risk profile all change.

#### 6. 🆕 B2B Service Business Evaluation (企业服务模式)

For businesses that sell a SERVICE to other businesses (not compete for end consumers).

**Key differences from B2C platform evaluation:**

| Dimension | B2C Platform | B2B Service |
|-----------|-------------|-------------|
| Acquisition | Ad spend, app store, viral | **Direct sales/地推** — build relationships |
| Decision | Individual impulse | Multi-step: gatekeeper → budget → sign-off |
| Revenue/customer | ¥30-300/order | **¥3,000-200,000/year** |
| Churn reason | Found better app | **Budget cut or relationship change** |
| Contract | None (one-off) | **Monthly/quarterly/annual** |
| Legal risk (PRC) | 涉黄/劳动法穿透 (high) | **Low** — B2B, on client premises, supervised |
| Startup cost | ¥300,000+ (app + ops) | **¥20,000-50,000** (service first, tech later) |

**When evaluating a B2B service, ask:**
- [ ] Who is the decision maker? (HR? Admin? Union? CEO?)
- [ ] Sales cycle length? (1 week SMB, 3-6 months 国企)
- [ ] Contract size? (¥10K/yr vs ¥200K/yr)
- [ ] Can you start without tech? (微信 + Excel may be enough)
- [ ] **国企 vs 民企 decision:**
  - **民企/外企** → fast decision (1-2 weeks), fast payment (15-30 days), lower contract value (¥10-50K/yr). Start here.
  - **国企/央企** → slow cycle (3-6 months), tender required, slow payment (60-120 days), **high renewal rate**, higher value (¥50-200K/yr). Graduate to these.
  - Key contact at 国企: **工会主席** (union head) controls employee welfare budget

**Reference case study:** See `references/b2b-corporate-massage-analysis.md` — full analysis of B2B office massage service in Chengdu, including pricing models, channel strategy, competitive landscape, and 国企/央企 vs 民企 comparison.

### Evaluation Checklist

- [ ] List at least 5 competitors. If you can't, search harder.
- [ ] What is the pricing range? Can you compete on value or only price?
- [ ] Why would a customer switch? Specific answer required ("saves 5hrs/week" > "it's better").
- [ ] How will the first customer be acquired? Specific channel + outreach + offer required.
- [ ] Is this a product people BUY, or a product they TRY and forget?
- [ ] Realistic timeline to first paying customer? (Money in account, not product launch.)

---

## Part 2: Equity / Stock Thesis Evaluation

Trigger conditions: user asks to analyze an influencer's stock picks, a thematic investment thesis, or stocks mentioned in a specific sector/theme.

### Step 1: Understand the Thesis

Derive the logical chain from the influencer/narrative. Example (Serenity's AI chokepoint thesis):

```
AI demand → datacenter buildout → GPU clusters need bandwidth →
optical interconnects bottleneck → upstream materials/components → find small caps
```

### Step 2: Map the Supply Chain

Identify companies at each layer of the chain:

| Layer | Companies | Status |
|-------|-----------|--------|
| Core GPU | NVDA, AMD | Obvious, huge caps |
| HBM Memory | MU, SK Hynix | Already priced in |
| Interconnect/Networking | AVGO, MRVL, CRDO | Mid-late cycle |
| **Optical/Photonics** | AXTI, POET, LWLG, LASR, IPGP | Serenity's focus — some already 10x'd |
| **Test/Measurement** | FORM, AEHR, COHU, KLIC | Real chokepoint, mostly ran |
| **Materials** | ENTG, PLAB, MP, VECO | Least discovered |
| **Power/Infrastructure** | CEG, VST, POWL, NVT | Nuclear and electrical for DCs |
| **Data Center REITs** | DLR, CONE | Boring, stable, barely moved |

### Step 3: Systematic Stock Screening

Use Yahoo Finance Chart API (no auth required) to screen across timeframes:

```bash
# Check 1y weekly, 2y monthly, and recent news
curl "https://query1.finance.yahoo.com/v8/finance/chart/TICKER?range=1y&interval=1wk"
curl "https://query1.finance.yahoo.com/v1/finance/search?q=TICKER&newsCount=10"
```

**Key metrics to extract from chart data:**
- Current price vs 52-week high/low (distance %)
- 1y, 3m, 1m performance (index offsets: -52, -13, -5 from end of quotes array)
- Volume pattern (20-day average vs recent)
- Market cap from quote search

**Classification rules:**
| Status | 1y Return | 3m Return | Action |
|--------|-----------|-----------|--------|
| 🟢 Undiscovered | <40% | <20% | Further research warranted |
| 🟡 Moderate | <80% | <30% | May have room, check catalyst |
| 🟠 Ran but not peaked | <150% | <50% | Wait for pullback |
| 🔴 Already priced | >150% | >50% | Skip — easy money made |

### Step 4: Verify Data Accuracy

**CRITICAL PITFALL (from user correction, June 2026):** A stock can show "only +22% in 3 months" while being 10x from its bottom — the 3-month window is misleading when the stock has already run and is consolidating.

**Always check:**
1. Full 2-year price chart (NOT just 1y-3m-1m windows)
2. Low-to-high percentage change (not just recent performance)
3. Insider transactions (CFO selling after 10x run = 🔴 strong signal)
4. Narrative shift ("story changing" from original thesis to something else)
5. News context (recent earnings, analyst upgrades/downgrades)

### Step 5: Influencer Due Diligence

See `references/financial-influencer-due-diligence.md` for full framework.

**Red flag checklist:**
- [ ] Can the claimed return be independently verified?
- [ ] Does the influencer disclose positions BEFORE or AFTER recommendations?
- [ ] Who benefits most: follower or influencer?
- [ ] Are losses disclosed alongside wins?
- [ ] Is the influencer selling a paid group/订阅?

**Key finding from Serenity case (June 2026):** Best use of an influencer is **learning their sector analysis**, not copying their trades. The real money was made by early followers; later followers buy into already-pumped stocks.

### Step 6: Deliver Layered Recommendations

| Category | Example | Recommendation |
|----------|---------|---------------|
| 🟢 Logic sound + not discovered | PLAB (photomasks, -35% from high) | Further research recommended |
| 🟡 Logic sound but moderately run | FORM (probe cards, +45% 3m) | Wait for pullback |
| 🔴 Logic sound but already 10x'd | LASR, AXTI (10x from bottom) | Do not chase |
| 🔴 Pure hype/penny | SMR ($12, -76% from peak) | Speculative only (bet-size = lose-it-all) |
| 🟢 Boring but real | DLR (data center REIT, +7% 1y) | Core holding for AI exposure |

### Known Viable Code Pattern

```python
import json, urllib.request
# Pull chart data
data = json.loads(urllib.request.urlopen(
    f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1y&interval=1wk"
).read())
result = data['chart']['result'][0]
quotes = result['indicators']['adjclose'][0]['adjclose']
ts = result['timestamp']
current = result['meta']['regularMarketPrice']
# Calculate performance
perf_1y = (quotes[-1] - quotes[0]) / quotes[0] * 100
perf_3m = (quotes[-1] - quotes[-13]) / quotes[-13] * 100  # ~13 weeks
high52 = max(quotes[-52:])
from_high = (current - high52) / high52 * 100
```

**Proxy tip:** If Yahoo Finance queries fail, try setting `HTTP_PROXY` and `HTTPS_PROXY` to the user's Clash proxy (typically `http://192.168.1.88:7890`).

**Fallback: Google Finance (when Yahoo is rate-limited):** When the proxy produces "Too Many Requests" on Yahoo Finance, use Google Finance's HTML endpoint as a lightweight price check:

```bash
curl -s "https://www.google.com/finance/quote/TICKER:NYSE" | grep -oP '"YMlKec">\$[\d,.]+<' | head -1
```

Python extraction:
```python
import re, urllib.request
html = urllib.request.urlopen(
    f"https://www.google.com/finance/quote/{ticker}:NYSE"
).read().decode()
m = re.search(r'"YMlKec">\$([\d,]+\.?\d*)<', html)
price = float(m.group(1).replace(',',''))
```

**Caveat:** Google Finance HTML is scraped (no API). The class name `YMlKec` may change. Use Yahoo Finance as primary source; Google Finance is a quick fallback for single-ticker price checks only, not historical data.

---

### Step 7: Company Deep-Dive — Insider & Financial Forensics

When a candidate passes screening, perform these checks before forming an opinion:

**A. Insider Transaction Check via SEC EDGAR**
- Get CIK: `https://www.sec.gov/files/company_tickers.json` → find ticker → format as 10-digit CIK
- Get filings: `https://data.sec.gov/submissions/CIK{cik}.json` (with `User-Agent` header)
- Look for Form 4 clusters before negative events (PLAB had 8 Form 4s in April, then May crash)
- CFO selling >$1M near 52wk high = 🔴 strong signal (LASR CFO sold $3.9M)

**B. Secondary Offering Detection**
- News containing "secondary offering", "underwritten", "registered direct"
- SEC form types S-3, 424B5
- The offering price = management's implicit fair-value signal
- Dilution = existing shareholders' stake shrinks
- CEG June 2026: 11M shares at $281 → 3.7% dilution, stock slumped

**C. News Catalyst Scan**
- Insider selling headlines → "sold", "divested", "disposed"
- CEO uncertainty quotes → PLAB CEO said "delays, supply strain, uncertainty" then stock -37%
- Earnings miss + margin compression + down guidance = triple red
- Analyst on back-to-back downgrades vs positive regulatory catalysts (CEG Three Mile Island restart)
- Check Yahoo Finance search: `?q=TICKER&newsCount=10` for recent headlines grouped by date

**D. The 2-Year Chart Reality Check**
Always pull 2-year monthly data — NOT just 1y/3m windows. A stock at "only +22% in 3 months" may actually be 10x from its 2025 bottom (LASR). The short window is misleading when the stock is consolidating after a massive run.

**E. Decision Matrix Template**
Present comparison table: chokepoint strength, market cap, % from 52wk high, insider signals, secondary offerings, 2y performance, CEO sentiment. Classify as: 🟢 Buy on weakness / ⚠️ Wait for catalyst / 🔴 Do not chase / 💀 Speculative only.

**F. Data Source Reference (for proxy-restricted environments)**
- Yahoo Finance v8 chart API (no auth): price history, volume, 52wk range
- Yahoo Finance v1 search API: company name, sector, CIK
- SEC EDGAR: filings, insider transactions — set User-Agent header required
- CoinGecko: XLM, stablecoin prices
- DexScreener: small-cap token prices
- Proxy: `HTTP_PROXY=http://192.168.1.88:7890` if APIs time out

---\n\n## Part 4: Physical DTC Product with Agent/Referral Distribution (实体DTC产品分销模式)\n\n### Trigger\n\nUser asks to evaluate selling a **physical product** (typically Chinese white-label/OEM goods) to overseas markets (primarily USA) through an **independent store + agent/referral distribution model** — such as \"推3反1\" (refer-3-get-1), team leader commissions (团长抽成), multi-level commissions, or subscription-with-referral models.\n\n### Core Framework\n\n#### 1. The Hidden Cost Trap: Shipping >> Product Cost\n\n**This is the single most important insight for cross-border physical DTC.** For lightweight products (masks, stickers, jewelry, small accessories):\n\n| Item | Example: 10 face masks | % of Total Cost |\n|------|----------------------|:--------------:|\n| Product (factory) | ¥2 ($0.28) | **4%** |\n| Packaging | ¥3-5 ($0.42-0.70) | **7%** |\n| **Shipping (China→USA, economy)** | **¥40-55 ($5.60-7.70)** | **75%+** |\n| Platform fee (Shopify 2.9%+$0.30) | ~$0.50 | **6%** |\n| **Total delivered cost** | **~$7-9** | **100%** |\n\n**The trap:** The factory price is so cheap it fools you into thinking you have massive margins. The shipping cost is the real price of the product. Not accounting for this leads to selling at a loss.\n\n**Shipping cost benchmark (China→USA, 2025-2026):**\n\n| Method | ~300g parcel (10 masks) | ~500g parcel | Transit |\n|:-------|:----------------------:|:------------:|:-------:|\n| 云途/YunExpress (economy) | ¥35-45 ($5-6) | ¥45-60 | 7-12 days |\n| 燕文/Yanwen (economy) | ¥30-50 ($4-7) | ¥40-65 | 7-15 days |\n| e邮宝/ePacket (standard) | ¥45-65 ($6-9) | ¥55-80 | 7-10 days |\n| 4PX/递四方 (economy) | ¥35-55 ($5-8) | ¥45-70 | 7-12 days |\n| 海运小包 (sea) | ¥15-25/kg | ¥8-12/kg | 25-40 days |\n| DHL/FedEx (express) | ¥80-120 ($11-17) | ¥100-150 | 3-7 days |\n\n**Key ratio:** For a face mask with factory cost ¥0.2/piece, shipping is ¥4-6/piece = **20-30x the product cost.**\n\n#### 2. US Retail Pricing Reference (Face Mask Market)\n\n| Tier | Brand Example | Per-Unit | Factory Cost (est.) | Retail-to-Factory Multiple |\n|:-----|:-------------|:-------:|:------------------:|:--------------------------:|\n| Budget bulk | ZealSea 7pk @ $7.50 | $1.07 | ¥2-4/7pcs | ~13-26x |\n| Low-mid | BIOAQUA 5pk @ $15 | $3.00 | ¥0.8/5pcs | ~18x |\n| Mid | BIODANCE 4pk @ $18 | $4.50 | ¥5.5/4pcs | ~24x |\n| Premium | Dr.Jart+ 5pk @ $25+ | $5.00+ | — | — |\n\n**Key insight:** Cheap factory price (¥0.2/piece) does NOT mean you can undercut competitors by 80%. Shipping cost is the same for all brands.\n\nThe cheap tier (ZealSea at $7.5) actually sells more volume (7,602 reviews) than the mid-tier (BIOAQUA at $15, max 89 reviews). Pricing too high for an unknown brand kills sales.\n\n#### 3. Agent/Referral Model Economics for Physical DTC\n\n**The \"推3返1\" (refer-3-get-1) model evaluation:**\n\n```\n核心公式：\n每单成本 = 出厂价 + 运费 + 包装\n毛利率 = (售价 - 每单成本) / 售价\n\n推荐3返1 + 代理佣金的完整账：\n总收入 = 4 × 售价 (客户+3个推荐人各买1单)\n总成本 = 4×每单成本 + 赠品成本(1份货+运费) + 3×佣金\n代理佣金通常占售价的15-30%\n净利润 = 总收入 - 总成本\n净利率 = 净利润 / 总收入\n```\n\n**Worked example — Economy mask (¥0.2/pc) sold at $12.99/10-pack:**\n```\nPer unit: cost $6.78, sell $12.99, gross margin 47.8%\n\n推3返1 cycle:\n  Revenue: 4 × $12.99 = $51.96\n  Total costs: $1.12(prod) + $24.00(ship) + $2.00(pack) \n               + $6.78(gift) + $7.79(commissions) = $41.69\n  Net profit: $10.27 | Net margin: 19.7% — thin but viable\n```\n\n**Worked example — Premium mask (¥1.375/pc) sold at $18.00/4-pack:**\n```\nPer unit: cost $6.26, sell $18.00, gross margin 65.2%\n\n推3返1 cycle:\n  Revenue: 4 × $18.00 = $72.00\n  Total costs: $3.04(prod) + $20.00(ship) + $2.00(pack)\n               + $6.26(gift) + $10.80(commissions) = $42.10\n  Net profit: $29.90 | Net margin: 41.5% — much better\n```\n\n**Critical finding:** Higher-cost products with higher retail prices produce better absolute margins for referral models, despite costing more to manufacture. Shipping is a smaller fraction of revenue.\n\n#### 4. Agent Commission Structure Design\n\n| Tier | Monthly Sales | Commission Rate | Team Override |\n|:-----|:-------------:|:--------------:|:--------------:|\n| 初级代理 | $0-500 | 15% | 0% |\n| 高级代理 | $500-2000 | 20% | 5% (团队) |\n| 团长 | $2000+ | 25% | 10% (团队) |\n\n**⚠️ FTC Compliance Warning:** \"推3返1\" + team override (团长抽成) is a multi-level compensation plan. US FTC aggressively prosecutes pyramid schemes. Legal MLM requirements: (a) sell genuine products with real demand, (b) primary compensation from product sales not recruitment, (c) 70% rule (70%+ inventory to real consumers), (d) money-back guarantee. Start with single-level affiliate (10-15% commission, no team override) before adding MLM layers. Pay a lawyer $500-1000.\n\n#### 5. Phase 1 → Phase 2 Strategy\n\n| Phase | Duration | Investment | Focus |\n|:------|:--------:|:----------:|:------|\n| **Phase 1: Validate** | Month 1-2 | <$500 | Shopify + stock 50-100 units + 5-10 trial agents + test shipping + answer: does logistics work? do customers reorder? can agents sell? what's real cost? |\n| **Phase 2: Scale** | Month 3-6 | $2000-5000 | Custom packaging + better shipping rates + 20-50 agents + social media |\n| **Phase 3: Brand** | Month 6-12 | $5000+ | Private label own brand + custom formula + full product line |\n\n**Phase 1 goal is NOT to make money — it's to answer 4 questions:**\n1. Does the logistics chain work? (China → US customer in <14 days)\n2. Will customers reorder? (Mask repurchase cycle = 3-4 weeks)\n3. Can agents actually sell? (Track real sales, not \"would they\")\n4. What's the real total cost? (Actual shipping + returns + lost packages)\n\n### Pitfalls\n\n- **Don't confuse low factory price with high margin** — shipping is the real cost driver for lightweight products\n- **Don't build an MLM plan before Phase 1** — you need real sales data first\n- **Don't underprice** — US consumers pay $1-4 per sheet mask. $12.99/10-pack is already value end.\n- **Don't ignore FDA compliance** — cosmetics imported to US need ingredient listing, may need facility registration\n- **Don't ignore returns** — skincare 5-15% return rate for allergies, return shipping $10-15 = you lose the whole margin\n- **Don't underestimate agent churn** — 80%+ dropout rate is normal\n- **Don't forget customs** — shipments under $800 duty-free (de minimis), over that faces 5-6% cosmetics tariff\n\n### Reference\n\n- `references/referral-economics-framework.md` — Full referral model economics, face mask factory pricing tiers (incl. real-time Alibaba data $0.03-$0.45/piece), cross-border shipping cost tables, worked examples for BIOAQUA (¥0.2/pc) vs BIODANCE (¥1.375/pc) vs ZealSea tier, Shopify reseller validation (thebioaqua.com, 128x markup)\n- `references/ecommerce-brand-research-example.md` — BIOAQUA (泊泉雅) brand research worked example (under web-research skill)\n\n---\n\n## Part 5 (was Part 3): Viral AI Monetization Claim Verification

### Trigger

User asks to verify a viral story/claim about someone making large money quickly with AI tools (OnlyFans AI girlfriend, $X in Y weeks, "passive income" with AI, etc.). These surface on Twitter/X, YouTube, Reddit, or AI newsletter spam.

### Step 1: Identify the Original Source

| Source Type | Credibility | Typical Motive |
|-------------|-------------|----------------|
| Twitter/X thread by anon account | 🟡 Low | AI tool marketing, follower growth |
| YouTube "I made $X with AI" video | 🟡 Low | Affiliate links, ad revenue, course sales |
| Reddit (r/passiveincome, r/Entrepreneur) | 🟡 Low | Attention test, referral farming |
| TechCrunch/Forbes/Forbes contributor post | 🟢 Medium | Often just rewrites the Twitter thread |
| Genuine interview with verifiable identity | 🟢 Higher | Rare |

**Pattern: most of these stories are monocausal** — one source, one tweet, no follow-up, no independent verification. If every article about it links back to the same single social media post, treat with maximum skepticism.

### Step 2: Check Platform Policy Compliance

The story often ignores whether the platform actually allows what's described:

| Platform | AI Policy | Implication |
|----------|-----------|-------------|
| OnlyFans | Bans AI-generated content impersonating real people; requires gov ID verification | AI "virtual girlfriend" can't legally operate an OF account |
| Patreon/Fanvue | More permissive but still requires real account holder | Possible but capped |
| Fiverr/Upwork | Prohibits AI-generated work sold as human-made | Accounts get banned, earnings forfeited |
| YouTube/TikTok monetization | Requires disclosure for AI-generated content | Limits reach and ad revenue |
| Subscription platforms (Substack, etc.) | Varies by payment processor (Stripe bans AI porn) | Payouts can be frozen |

**Key question:** Can the described activity actually survive platform enforcement for more than a month? If the answer requires violating ToS, the "4 weeks" timeline means it's about to get banned.

### Step 3: Reality-Check the Numbers

Use industry baselines to sanity-check claimed revenue:

| Platform / Activity | Industry Reality | Claim Red Flag Threshold |
|---------------------|-----------------|--------------------------|
| OnlyFans (new creator, zero following) | Top 1% = $5-15K/mo, after months of growth | >$20K in month 1 |
| YouTube (new channel) | $1-3 CPM, need 100K views/mo for $200 | Claims of $5K/mo in first month |
| Etsy (digital products, no audience) | Average $200-500/mo first 3 months | >$5K in first month |
| Affiliate marketing (no list) | 0.5-2% conversion, need 10K+ visitors | >$10K in first month |
| AI SaaS (solo founder, no launch) | $0-500 MRR first 3 months typical | >$10K MRR in first month |

**Rule of thumb:** If the claimed monthly revenue is >10x the industry baseline for a new entrant with no audience, the number is marketing, not reporting.

### Step 4: Separate Technical Feasibility from Financial Results

**"Could this be done?"** and **"Was this done at that scale?"** are two different questions.

- Technical feasibility: Evaluate the tool stack (e.g., Flux+LoRA for images, ElevenLabs for voice, Claude Code for automation) — yes, these tools exist and can do this.
- **Financial claim verification**: Much harder — requires auditable revenue, platform dashboard screenshots with metadata, tax records, or third-party verification.
- **The marketing trick**: Mix a true technical claim ("yes, you can generate consistent character images with Flux+LoRA") with an unverifiable financial claim ("and I made $43K in one month"). The true half carries credibility to the false half.

### Step 5: Classify the Claim

| Classification | Definition | Example |
|----------------|------------|---------|
| 🟢 **Verified** | Independent third-party evidence exists, numbers auditable | Extremely rare for viral stories |
| 🟡 **Plausible but unverified** | Technical route makes sense, numbers within baseline range | "Made $2K with AI art on Redbubble" |
| 🟠 **Technically feasible, numbers exaggerated** | Tech works, but claimed revenue is 5-10x industry baseline | Most "AI girlfriends" stories |
| 🔴 **Product Story (营销叙事)** | Tech is real but exists primarily to market the tools involved | Specific tools named prominently, no verifiable identity for the creator |
| 💀 **Scam** | Tech doesn't work or requires upfront payment for the "secret" | "Buy my course to learn the method" |

**Most viral AI monetization stories** fall into 🟠 or 🔴 — technically possible at small scale, but the blockbuster numbers are marketing tools to drive affiliate signups or course sales.

### Step 6: Provide Realistic Alternative

When the user wants to explore the idea after debunking, provide:

- Realistic first-month revenue (typically 1-10% of the claimed number)
- Actual tool costs (Flux LoRA training: ~$5-10, ElevenLabs: $5-22/mo, Claude Code: $20/mo)
- Hidden costs: time to iterate on LoRA training, content moderation, platform fees, payment processing
- Biggest risk specific to the claim (e.g., OnlyFans policy enforcement against AI content)
- Honest assessment: "This is a side project, not a business. Treat it as a learning experiment."

### Reference

- `references/viral-ai-claim-examples.md` — worked examples of specific viral claim analyses
- `references/product-opportunity-discovery.md` — Product category discovery framework: margin × frequency × virality matrix. Use when user asks "what products meet conditions X, Y, Z" rather than evaluating a named project. Includes: three-axis scoring system, high-unit-price vs high-frequency filtering, physical product hidden cost framework (shipping/returns/compliance/platform fees), China vs international marketplace comparison, user-profile fit filter, and industry baseline revenue data.
- `references/referral-economics-framework.md` — Referral-based business model evaluation: "推荐N返1" (refer-N-get-1-free) economics, profitability threshold calculator (minimum 60% gross margin), digital vs physical product cost comparison matrix, product-type suitability table, and best-fit referral incentive design patterns.

---

## The User's Litmus Test

When the user reviews your analysis, their corrections are signals:
- "This is too optimistic" → You failed the reality check → Go back to Step 2, look harder for competitors/problems
- "That stock is 10x from the bottom, not 'hasn't run'" → You missed the full timeframe → Always check 2y data
- "You always do X and I hate it" → This is a style/preference signal — save to memory AND embed in this skill

When the user corrects you about data accuracy, immediately:
1. Accept the correction — do not defend
2. Identify which specific metric/timeframe you missed
3. Update this skill with the corrected approach
4. Re-run the analysis with the corrected method

---

## References

- `references/smb-ai-cs-market-research.md` — AI customer service for US SMBs market data
- `references/financial-influencer-due-diligence.md` — Framework for evaluating stock influencers (Serenity case study)
- `references/ai-chokepoint-stock-screening.md` — Full AI supply chain stock screening results + API reference
- `references/plab-ceg-deep-dive-example.md` — Worked example of company deep-dive (PLAB: photomasks duopoly, CEG: AI nuclear power)
- `references/b2b-corporate-massage-analysis.md` — B2B corporate office massage market analysis: business model, pricing, 国企 vs 民企 channel strategy, Chengdu market data, startup requirements
