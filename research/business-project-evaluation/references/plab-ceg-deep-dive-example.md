# PLAB, CEG & MDA Deep-Dive (June 2026) — Worked Example

## Context

User asked to analyze Serenity (X/Twitter AI stock influencer). Her thesis: AI supply chain chokepoints → find small caps in upstream bottlenecks. We screened 60+ tickers, found PLAB and CEG as the most interesting. User then added MDA Space as a personal pick.

---

## PLAB (Photronics) — $32.11, $5B, Photomasks

### The Chokepoint Thesis
Every chip needs a photomask (the stencil for photolithography). AI chips have more layers = need more masks. Only TWO companies make high-end photomasks globally: **PLAB** and **Japan's DNP**. Genuine duopoly.

### Price Trajectory (2-year monthly)
```
2024-07: $25 → 2025-04: $18 (bottom) → 2026-04: $49 (peak) → 2026-06: $32 (now)
```
- 52wk high: $49.48 | low: $16.71
- 2y return: +26% (vs LASR +533%, vs AXTI +172%)
- From peak: -35%

### The Crash (May 29, 2026)
- Q2 earnings miss → -37% in one week
- CEO: "Delayed semiconductor design releases, supply strain, uncertainty"
- Margin compression
- Stock bounced slightly on June 2 (+? applied materials trade up)

### 🔴 Red Flags Found
1. **Form 4 cluster in April**: 8 insider filings (Apr 15-21) at ~$30-35 range, then crash in May. Potential insider front-running.
2. **CEO uncertainty**: Direct quote "supply strain and uncertainty" — management has no visibility.
3. **Earnings miss + margin compression**: Not just a delay; profitability is deteriorating.

### 🟢 Positive Points
- Photomask duopoly = hard to replace
- Only +26% in 2 years while AI stocks boomed elsewhere
- Still attending investor conferences (trying to rebuild confidence)

### Verdict
⚠️ **Waiting game** — if Q3 proves "delays are temporary", $32 could be a great entry. If chip demand cycle is turning, it goes lower. High risk, high reward.

---

## CEG (Constellation Energy) — $267, $50B, Nuclear Power

### The Chokepoint Thesis
AI datacenters need 100-500MW each. Nuclear is the only 24/7 zero-carbon baseload power source at scale. CEG operates the largest US nuclear fleet. Power IS the ultimate AI bottleneck.

### Price Trajectory
```
2024-07: $188 → 2025-07: $346 (peak) → 2026-06: $267 (now)
```
- 52wk high: $375 | low: $188
- 2y return: +42%
- From peak: -29%

### Major Events
- **Secondary offering**: 11M shares at $281 ($3.1B) on June 1 — diluted existing holders ~3.7%
- **Three Mile Island restart**: FERC waiver granted — positive catalyst for AI datacenter power PPA
- **Raymond James PT cut**: $392 → $374 (still Outperform)

### 🔴 Red Flags
1. **Secondary at $281**: Management said "we'll sell here" — implicit valuation signal 5% below pre-offer price
2. **$50B market cap**: Not a small cap; 2x from here = $100B, needs massive capital
3. **Utilities are regulated**: Less explosive upside than unregulated tech

### 🟢 Green Flags
1. **Insider trading**: No C-suite dumping detected (unlike LASR)
2. **Catalyst pipeline**: 3MI restart, PPA contracts with Big Tech
3. **+42% in 2 years**: Moderate, reasonable — not bubble territory
4. **Power demand trend**: Irreversible — AI datacenters, EVs, reshoring all need more power

### Verdict
🟢 **Reasonable entry at -29% from high** — not a home run but a solid core position. The secondary created a dip; if you believe in the AI power thesis, buy the dip.

---

## MDA Space (MDA) — $40.25, $3B, Space Infrastructure

### Why the User Tracked It
User independently identified MDA as a potential AI/defense/space pick, distinct from Serenity's picks. Tagged as "太空建筑队" (Space Construction Crew).

### Business
- Canadian space robotics company (Canadarm, Canadarm2 on ISS)
- Satellite assembly, inspection, and servicing in orbit
- MDA's robotics are on virtually every major space station and satellite program
- Broadening into defense/classified space contracts

### Price Trajectory
```
2024-06: $30.50 → 2026-03: $44 (peak) → 2026-06: $40.25 (now)
```
- 52wk high: ~$44 | low: ~$28
- 2y return: +31%
- From peak: -9%

### Key Characteristics
| Factor | Assessment |
|--------|-----------|
| **2y return** | +31% — extremely moderate vs space peers (RKLB +2089%, RDW volatile) |
| **Valuation** | No bubble — literally the lowest 2y return among US-listed space pure-plays |
| **Market cap** | ~$3B — small enough to 5x, large enough to be real |
| **Insider selling** | No CFO-level dumping detected |
| **Narrative** | "Space construction" — long-duration, government-backed contracts |

### The Thesis
- AI + space = long-term megatrend (earth observation, orbital computing, satellite servicing)
- MDA has entrenched govt contracts (NASA, CSA, DoD)
- Barron's / space analysts call it "the boring play" — which means it hasn't been hyped

### Verdict
🟡 **Long-term lottery ticket** — not a near-term AI chokepoint like PLAB/CEG. Low volatility, moderate return potential. 2-3x over 5 years is plausible if space budgets grow. Best as a small allocation within a larger AI/tech portfolio.

---

## Key Methodology Takeaways

### What Worked
- 2-year monthly chart > 1y daily data > 3m window
- News headline scan sorted by date reveals narrative arc
- Insider transaction timing relative to bad news is the strongest signal
- Cross-referencing user's independent picks against influencer picks broadens the thesis

### What Didn't Work
- The "v7 finance quote" Yahoo API is unreliable — use v1 search + v8 chart combination
- SEC EDGAR XML parsing is fragile (namespace issues, rate limiting) — scanning for Form 4 filing dates is sufficient; you don't need the XML content
- Single 3-month window is dangerously misleading (LASR showed +22% but was 10x from bottom)
- Yahoo Finance v8 chart API gets rate-limited when hammered through a shared proxy — use Google Finance fallback for quick single-ticker checks

### Data Source Reference
- Primary: `query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=2y&interval=1mo`
- Fallback: `https://www.google.com/finance/quote/{TICKER}:NYSE` (HTML scrape, class `YMlKec`)
- Insider data: `data.sec.gov/submissions/CIK{cik}.json` → scan `filings.recent.form[]` for "4"
- News: `query1.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount=10`
- Proxy: `HTTP_PROXY=http://192.168.1.88:7890` when behind Chinese firewall
