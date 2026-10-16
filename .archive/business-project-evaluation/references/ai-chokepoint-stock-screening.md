# AI Chokepoint Stock Screening — June 2026

## Methodology

Serenity's thesis: AI demand → datacenter buildout → GPU clusters → interconnect bottlenecks → upstream material/component chokepoints.

Systematic screening approach used:

1. Map AI supply chain layers (GPU → networking → optical → materials → test → power)
2. Identify small-cap ($0.5B-$10B) companies at each layer
3. Pull 2y monthly, 1y weekly, and 1d prices from Yahoo Finance chart API
4. Rank by: 1y% > 3m% > 1m% > distance from 52-week high
5. Flag: green (<40% 1y, <20% 3m), yellow (<80% 1y, <30% 3m), red (already ran)
6. Contextualize with recent news (earnings, analyst calls, insider transactions)

## Supply Chain Map & Screening Results

### Layer 1: Optical / Photonics (Serenity's Main Focus)

| Ticker | Price | 1y | 3m | From High | Verdict |
|--------|-------|-----|-----|-----------|---------|
| AXTI (InP substrates) | $106.70 | +458% | +172% | -?% | 🔴 10x from bottom, too late |
| POET (CPO/optical) | $15.38 | +295% | +125% | -?% | 🔴 +125%/3m, momentum play |
| LWLG (polymer photonic) | $12.29 | +85% | +120% | -?% | 🔴 Pre-revenue, speculative |
| LASR (nLIGHT) | $76.39 | +533% | +22% | -10% | 🔴 10x from bottom, CFO sold $3.9M |
| **IPGP** (IPG Photonics) | $121.62 | -5.9% | -4.1% | -21% | 🟡 Actually **down** 1y, fiber laser co |
| **VIAV** (Viavi) | $52.42 | +458% | +67% | -5% | 🔴 Optical testing, already ran |
| CIEN (Ciena) | $620.37 | +732% | +62% | -0% | 🔴 Optical networking, large cap |

### Layer 2: Test & Measurement

| Ticker | Price | 1y | 3m | From High | Verdict |
|--------|-------|-----|-----|-----------|---------|
| **AEHR** (Aehr Test) | $114.59 | +511% | +169% | -?% | 🔴 AI chip burn-in, +169%/3m |
| **FORM** (FormFactor) | $126.02 | +163% | +45% | -18% | 🟡 Probe cards, real chokepoint, already ran |
| **COHU** (Cohu) | $56.12 | +230% | +88% | -?% | 🔴 Test handlers, ran up |
| **KLIC** (Kulicke & Soffa) | $108.40 | +230% | +70% | -0% | 🔴 Assembly equipment, ran |

### Layer 3: Materials / Chemicals

| Ticker | Price | 1y | 3m | From High | Verdict |
|--------|-------|-----|-----|-----------|---------|
| **ENTG** (Entegris) | $140.33 | +50% | -1.4% | -?% | 🟡 Specialty chemicals, $21B too big |
| **MP** (MP Materials) | $68.55 | +82% | +35% | -15% | 🟡 Rare earths, mid cap, moderate run |

### Layer 4: Semiconductor Equipment

| Ticker | Price | 1y | 3m | From High | Verdict |
|--------|-------|-----|-----|-----------|---------|
| **PLAB** (Photronics) ⭐ | **$32.11** | **+76%** | **-12%** | **-40%** | 🟢 **BEST FIND. Photomasks, duopoly, CRASHED 35% on earnings miss** |
| UCTT (Ultra Clean) | $92.55 | +364% | +60% | -0% | 🔴 Gas delivery, ran huge |
| MTSI (M/A-COM) | $390.34 | +185% | +78% | -0% | 🔴 RF semi, ran |
| VECO (Veeco) | $60.46 | +207% | +97% | -0% | 🔴 Deposition equip, ran |
| ACMR (ACM Research) | $88.86 | +130% | +72% | -?% | 🔴 Wet processing, ran |

### Layer 5: Data Center Power & Infrastructure

| Ticker | Price | 1y | 3m | From High | Verdict |
|--------|-------|-----|-----|-----------|---------|
| **CEG** (Constellation) ⭐ | **$267.24** | **-12%** | **-5%** | **-31%** | 🟢 **Nuclear for AI datacenters, DOWN 31% from high** |
| **VST** (Vistra) | **$153.80** | **-16%** | **+5%** | **-27%** | 🟢 **Power producer, DOWN 27% from high** |
| **SMR** (NuScale) | **$12.27** | **-67%** | **+7%** | **-76%** | 🟢 **Nuclear SMR, crashed 76%, high risk high reward** |
| POWL (Powell) | $299.73 | +414% | +74% | -3% | 🔴 Already ran |
| NVT (nVent) | $176.39 | +153% | +52% | -0% | 🔴 Electrical, ran |

### Layer 6: Data Center REITs

| Ticker | Price | 1y | 3m | Verdict |
|--------|-------|-----|-----|---------|
| **DLR** (Digital Realty) | $183.50 | +7% | +6% | 🟢 **Boring, barely moved, pays dividend, large cap** |

## PLAB Deep Dive (Best Undiscovered Find)

**Company:** Photronics, Inc. (NASDAQ: PLAB)
**Price:** $32.11 (from April high of $49.48 → down 35%)
**Market Cap:** ~$5B
**Business:** Photomasks — the stencils used in photolithography for ALL semiconductor manufacturing. Duopoly with DNP (Japan).

**Why it fits the chokepoint thesis:**
- Every chip needs photomasks, especially advanced AI chips (more layers = more masks)
- Only 2 global suppliers capable of leading-edge masks (PLAB + DNP)
- TSMC, Samsung, Intel ALL depend on mask supply

**Why it crashed:**
- May 29, 2026: Q2 earnings miss ("delayed semiconductor design releases")
- CEO flagged "supply strain and uncertainty"
- Stock dropped 37% in one week

**Risk/Reward:**
- Bull: cyclical miss in a secular growth market (AI chip demand is real, mask demand follows)
- Bear: chip cycle downturn, earnings continue deteriorating
- Wait signal: next quarter's guidance — if design delays were temporary, PLAB rebounds hard

## nLIGHT (LASR) — Warning Case Study

**Price:** $76.39 (from March 2025 low of $7.71 = 10x)
**Market Cap:** ~$3.5B

**The mistake in my initial analysis:** I calculated 3-month return as +22% and called it "hasn't run up." Correct calculation: **10x from bottom.** The "only +22% in 3 months" was because the stock had already 10x'd and was consolidating.

**Red flags identified:**
1. **CFO sold $3.9M on May 30** — insider selling at 10x is a strong "peak" signal
2. **Narrative shift detected** — headlines moving from "AI optical" to "directed energy" (needs new story)
3. **P/S ~18x with inconsistent profitability** — extreme valuation

**Lesson for future screenings:** Always check the full time range (2y), not just recent months. A stock can be consolidating near highs AFTER a 10x run, which looks "flat" but is actually fully priced.

## API Reference

### Yahoo Finance Chart API (works without auth)

```bash
# 1 year weekly data (gives 52 data points)
curl "https://query1.finance.yahoo.com/v8/finance/chart/TICKER?range=1y&interval=1wk"

# 2 year monthly data (gives 24 data points, good for long view)
curl "https://query1.finance.yahoo.com/v8/finance/chart/TICKER?range=2y&interval=1mo"

# Company info + news
curl "https://query1.finance.yahoo.com/v1/finance/search?q=TICKER&newsCount=10"
```

### Key Python extraction pattern

```python
data = json.load(raw)
result = data['chart']['result'][0]
meta = result['meta']
quotes = result['indicators']['adjclose'][0]['adjclose']
ts = result['timestamp']
current = meta.get('regularMarketPrice', quotes[-1])
```

Calculate: 1y perf (index -52 from end), 3m perf (index -13), 1m perf (index -5), 52-week high/low from quotes array.
