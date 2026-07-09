---
name: business-project-evaluation
description: "Evaluate business project ideas OR stock/investment theses with a reality-checked framework. Covers business model analysis (service vs product), competition assessment, distribution strategy, and equity research (supply chain chokepoint analysis, influencer due diligence). For a solo developer with AI/automation capabilities."
version: 2.1.0
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
