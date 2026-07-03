# Gold Price Data Sources — Verification Reference

**Last updated:** 2026-06-24

## Primary Sources (Reliable)

| Source | URL Pattern | Reliability | Notes |
|--------|-------------|-------------|-------|
| Kitco | `kitco.com/gold-price-today-usa/` | ★★★★★ | Industry standard, real-time spot |
| Bloomberg | `bloomberg.com/quote/XAUUSD:CUR` | ★★★★★ | Requires robust page scrape |
| Reuters | `reuters.com/markets/commodities/` | ★★★★☆ | Good for macro context |
| Investing.com | `investing.com/commodities/gold` | ★★★★☆ | Reliable, good DXY data too |

## Secondary Sources (Use with Caution)

| Source | Notes |
|--------|-------|
| **gold-api.com** | ⚠️ Known to occasionally return wrong instrument. In Jun 2026, reported $4,098/oz when spot was actually $2,948/oz. Always cross-check. |
| Yahoo Finance (GC=F) | Gold futures, not spot. May differ by $20-50 from spot price. Use `GC=F` symbol. |
| XE.com | Good for currency conversion, not primary gold source. |

## Price Ranges (Sanity Check)

When a gold price from any source looks suspicious, compare against these known ranges:

| Period | Typical Range | Notes |
|--------|---------------|-------|
| Early 2025 | $2,000 - $2,500 | Pre-rate-cut |
| Late 2025 | $2,500 - $2,800 | Rate cuts begin |
| Q1-Q2 2026 | $2,800 - $3,500 | Soft landing + central bank buying |
| Q2-Q3 2026 (current) | $3,500 - $4,200 | Weak USD (DXY~101), rate-cut expectations, geopolitical tensions, record CB buying |

**Updated 2026-06-26:** The $4,000+ level is the new reality, driven by DXY falling to ~101.5, persistent above-target inflation (~3.1% CPI), central bank buying on pace for 1,100+ tonnes in 2026, and multiple geopolitical flashpoints (Iran-Gulf, Ukraine-Russia, US-China trade escalation). A crisis scenario that pushed gold above $3,200 was originally treated as a tail risk; it became the baseline by mid-2026.

Any price outside $1,500-5,000 is almost certainly a data error, not a real price.

## Multi-Source Verification Pattern

When gold-api.com or any single source produces a suspicious price:

1. Delegate 2-3 parallel subagent research tasks, each hitting a different source
2. Cross-reference the returned prices
3. If 2+ sources agree, that's the correct price
4. In the briefing, note the discrepancy in a footnote

## Related Data

- **DXY (U.S. Dollar Index):** ~101.5 (Jun 26, 2026). Down from ~105 in early 2026. Inverse correlation with gold (~-0.7). Weak dollar is the #1 gold support factor.
- **Fed Rate Path:** CME FedWatch Tool is the gold standard for rate expectations. Fed funds rate at 5.25-5.50%, Q3 2026 cut expected. Real rates turning negative.
- **Central Bank Buying:** World Gold Council monthly data — major support factor. China +35t, India +12t, Poland +18t in Q2 2026 alone.
