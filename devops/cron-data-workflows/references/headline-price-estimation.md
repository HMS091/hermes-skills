# Headline-Based Price Estimation (When ALL Price APIs Fail)

**Last updated:** 2026-07-07

## The Problem

In cron environments, three failure modes can combine to leave you with **zero** price data:

1. **Pre-run script's API fails** — Nasdaq/gold-api endpoints return errors
2. **Browser is unavailable** — Chromium times out, needs restart
3. **Subagents can't help** — `delegate_task` with `toolsets: ["web"]` returns empty results in cron mode

When this happens, you have no source for the actual price. But **news headlines often contain enough context to estimate the price range**, especially for heavily covered assets like gold, NVDA, and TSLA.

## The Technique: Infer Price from Headline Language

Google News RSS headlines from a per-ticker search frequently mention price levels, percentage moves, and key support/resistance levels. Parse these for price clues.

### Gold Price Estimation Example (2026-07-06)

The gold API failed. Google News RSS returned these clues:

| Headline | Price Clue | Implication |
|----------|-----------|-------------|
| "Gold Holds Above $4,000 Floor as FOMC Minutes Test $4,100 Fair Value" | $4,000 (floor), $4,100 (fair value) | Price is **between $4,000 and $4,100** |
| "Gold prices set for first weekly rise in a month" | No number, but confirms uptrend | Price is **rising from a low** |
| "Gold drops 30%... 2026 correction isn't the deepest yet" | 30% drop from highs | If high was ~$5,800, 30% off = ~$4,060 |
| "JPMorgan sees $4,500 gold price in fourth quarter" | $4,500 is *target* not current | Current price is **below $4,500** |
| "Gold Price Rises Rs 2,930 per 10 gram in India" | Local price rise confirms bullish momentum | Cross-reference: ~$4,080/oz (India gold typically at or near spot) |

**Result:** Price estimated at ~$4,080/oz (±~$50). This was verified as consistent when the CNBC and Fortune articles later showed prices in the $4,070-$4,090 range.

### NVDA Price Estimation

NVDA headlines tend to be very price-specific:
- "Nvidia Stock Is Nearly Flat for 2026" → price ~same as Jan 1 close
- "NVIDIA Stock Is Down 18% in 2026" → if Jan 1 was ~$237, 18% off = ~$194
- "Nvidia Stock Has Underperformed the Semiconductor Sector in 2026" → confirms weakness
- "If Jensen Huang Is Right, NVIDIA Stock Is a Steal at $200" → current price around $200

For NVDA, the pre-run JSON did provide a valid price ($195.28), so no estimation was needed.

### TSLA Price Estimation

TSLA headlines often mention delivery beats/misses:
- "Tesla stock sinks 7% despite strong deliveries report" → if price was ~$448, 7% off = ~$417
- "Tesla Q2 Deliveries Up 25%" → confirms the delivery beat
- "480K Deliveries Beat by 18%" → gives the actual delivery number

Again, the pre-run JSON provided a valid price, so estimation wasn't needed.

## When to Use This Technique

**Only use headline-based estimation when:**
1. The pre-run script's price API failed (no price, or clearly wrong price like volume-as-price)
2. The browser/Nasdaq curl/Yahoo API all fail as fallback
3. Google News RSS *does* return results (it's the most resilient source)

**When NOT to use it:**
- When you have any confirmed price source (Nasdaq API, Yahoo Finance, browser extraction)
- When the headline mentions a price but it's from days/weeks ago (check the `pubDate`)
- When the asset is obscure and headlines rarely mention price levels

## How to Format in the Briefing

When using estimated prices, always add a clear disclaimer:

```
> ⚠️ 黄金API采集失败，现价基于财经媒体综合估算
> （7/6 CNBC/Fortune报价约$4,080附近）
```

Or in English:
```
> ⚠️ Gold price API failed. Estimated ~$4,080/oz based on news headline analysis
> (CNBC/Fortune articles on Jul 6 reference $4,000-$4,100 range)
```

## Key Headline Keywords and Their Price Implications

| Keyword in Headline | Price Implication |
|--------------------|-------------------|
| "Holds Above $X,XXX" | Price is currently **above** $X,XXX (support) |
| "Tests $X,XXX" | Price is **near** $X,XXX |
| "Falls to $X,XXX" | Price dropped **to** $X,XXX |
| "Target of $X,XXX" | $X,XXX is an analyst **target**, not current price |
| "Down X% from highs" | Current price = high × (1 - X/100) |
| "Loses ___ status to ___" | Negative sentiment, but no specific price level |
| "Up X% in [timeframe]" | Use with a known reference price |
| "Price rises/falls $X" | Absolute move from an implied prior level |
