# Gold Extreme Move Analysis

When gold moves $100+/oz in a single session (or ~3%+), it signals a significant shift in macro conditions. This reference documents extreme-move patterns and how to frame them in daily briefings.

## Normal vs Extreme Gold Moves

| Move Size | Classification | Frequency | Interpretation |
|-----------|---------------|-----------|----------------|
| ±$10-20 | Normal daily range | Daily | Routine volatility |
| ±$20-50 | Notable move | Weekly | Reaction to data/event |
| ±$50-100 | Large move | Monthly | Trend acceleration or reversal |
| **±$100+** | **Extreme** | **Rare** | **Macro regime shift / crisis** |

## What $100+ Gold Moves Typically Signal

### Upward spikes ($100+ gain, single session)

| Context | Most Likely Driver | Briefing Language |
|---------|-------------------|-------------------|
| Spike from below $4,000 to above $4,100 | Geopolitical escalation (Iran, Ukraine, Taiwan strait) | "地缘避险情绪急剧升温" |
| Spike during risk-off (equities also falling) | Flight to safety, systemic risk | "Risk-off全面开启，资金涌入黄金" |
| Spike alongside equities rallying (like this session: NVDA +2%, TSLA +2.5%, gold +3.3%) | Weakening USD + rate-cut expectations repricing | "降息预期重燃+美元走弱，多重因素共振引爆金价" |
| Spike with no obvious catalyst | Short squeeze / technical breakout above a key level | "技术性突破触发程序化买盘，空头被迫回补" |

### Downward spikes ($100+ loss, single session)

| Context | Most Likely Driver | Briefing Language |
|---------|-------------------|-------------------|
| Drop from above $4,100 to below $4,000 | Strong dollar / hawkish Fed surprise | "美元强势压制，降息预期骤降" |
| Drop on no news | Long liquidation / profit-taking after run-up | "连续上涨后多头获利了结" |

## Technical Analysis Adjustments for Extreme Moves

Standard technical indicators break down on $100+ days:

- **RSI**: Will jump to 70+ (overbought) instantly. Do NOT treat this as automatic "sell signal" — extreme moves can sustain above 70 for days in a trend. Flag it as "需警惕短期超买回调风险" but don't call a top.
- **Bollinger Bands**: A $100 move will blow through the upper band. The relevant question is whether price pulls back INTO the bands or the bands expand to accommodate.
- **Support/Resistance**: A $100 break resets the entire level structure. Previous resistance becomes new support. E.g., $4,100 was resistance, becomes support after the break.

## Example: This Session (2026-07-22)

Gold moved from $4,004.80 to $4,136.10 (+$131.30, +3.28%).

**Key observations for the briefing:**
1. **Multi-factor confluence needed to explain**: A $131 move is NEVER driven by one factor. Briefing should list 3-4 contributing drivers (weak USD, rate-cut expectations, geopolitics, technical breakout).
2. **Volume context was missing** (no gold volume in raw JSON) — note this as a data limitation.
3. **The spike scenario (gold + stocks both up) is rarer than a flight-to-safety spike** — equity-positive + gold-positive suggests a macro factor that benefits both (rate-cut expectations), not a risk-off event. This is the correct framing.
4. **Risk warning must be calibrated to move size**: A $131 spike creates much higher pullback risk than a normal day. Set the warning at "中高" severity.
5. **Support level resets**: After this move, the old resistance of $4,100 becomes the first support level, not the old $4,000 level.

## Briefing Template Fragment for Extreme Gold Moves

```markdown
### 🥇 黄金 ($4,136.10/oz，单日暴涨+$131.30)

1. **暴力突破！黄金单日飙升$131站上$4,136** — 这是今日最大亮点。金价从此前$4,005附近一夜间暴涨3.28%，以摧枯拉朽之势击穿$4,100关口。多头全面主导，$4,000的关键支撑已转化为牢固的底部。

2. **多重因素共振引爆金价** — $131的极端涨幅绝非单一原因所致：① 降息预期重新升温，美元指数承压下行；② 美伊地缘紧张局势持续升温，避险需求支撑；③ 技术面上金价回踩$4,000确认支撑后开启新一轮上攻。

3. **短期超买风险显著上升** — 单日3.28%的涨幅在黄金市场属于剧烈波动，RSI已逼近70超买区。$4,100成为新的关键支撑，$4,150-4,200为下一阻力区间。短期追高风险较大，建议等待回调至$4,080-4,100区间再考虑低吸。
```

## Data Source Considerations

- **gold-api.com returns 24/7 live prices** — unlike stock data, gold quotes are always current. When stock data is stale (weekend/after-hours), gold data may still be live. Note this divergence if it occurs.
- **Cross-verify gold via mid-day gold ETFs** (GLD, IAU) if available — spot gold at $4,136 should correspond to GLD around $444 (using ~$10.76 per GLD share ratio at ~$4,000 gold). If GLD data is available and doesn't match, flag a data discrepancy.
- **Gold $4,000+ prices were rare before 2025** — the existing sanity check range ($1,500-$5,000) is valid for the current macro environment.
