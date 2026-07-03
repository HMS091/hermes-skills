# Multi-Day Trend Extraction from Sequential Briefing Data

When web research is unavailable (cron mode) and the pre-run script only provides one day's snapshot, you can still derive rich context by reading previous briefings and raw data files. This produces a more informed briefing than one that only reacts to a single day's numbers.

## Source Files

The pipeline stores files at `/opt/data/briefings/`:

| File Pattern | Contains | Use |
|---|---|---|
| `YYYY-MM-DD_raw.json` | Price, change %, volume, news headlines | Multi-day price tracking, trend calculation |
| `YYYY-MM-DD_briefing.md` | Previous day's analysis & risk warnings | Continuity, updating previous risk assessments |
| `dashboard.html` | All briefings embedded (rendered) | Quick browsing, but harder to parse programmatically |

## Trend Extraction Workflow

### Step 1: Identify the Lead-Up

Read the **previous 2-3** raw JSON files to establish the trajectory:

```bash
ls -lt /opt/data/briefings/*_raw.json | head -5
```

Extract for each asset:
- **Price direction**: Up, down, or range-bound over 3 days
- **Change magnitude**: Is the movement accelerating or decelerating?
- **Volume trend**: Increasing (conviction) or decreasing (exhaustion)?

### Step 2: Calculate Trend Vectors

From the JSON data, compute these across consecutive days:

| Asset | Day-2 | Day-1 | Today | Vector |
|---|---|---|---|---|
| NVDA | $195.33 | $199.49 | $197.43 | Spiked then pulled back (-1%) |
| TSLA | $408.84 | $415.95 | $423.37 | Steady recovery (+3.6%) |
| Gold | $4,017.80 | $4,012.20 | $4,038.30 | Bounced off $4,000 support |

### Step 3: Derive Analytical Insights

The multi-day view enables these claims that a single-day snapshot cannot:

| Single-Day Observation | Multi-Day Insight |
|---|---|
| "NVDA down 0.08% today" | "NVDA pulled back after yesterday's $195→$199 spike; still up $2 from 2 days ago" |
| "TSLA down 0.45%" | "TSLA up 3.6% over 3 days; today's dip is normal pullback from the rally" |
| "Gold at $4,038" | "Gold defended $4,000 for the 3rd straight day; $4,000 is confirmed support" |

### Step 4: Cross-Reference Previous Risk Warnings

Read the **previous day's briefing** to check which risks materialized and which didn't, then update:

```python
# Pseudo-logic for risk continuity
yesterday_risks = extract_risks(prev_briefing)
for risk in yesterday_risks:
    if risk.materialized:
        assess_impact(current_prices)
        add_follow_up(current_risk_list)
    else:
        reassess_relevance(risk, new_market_news)
        if still_relevant:  # Carry forward
            carry_to_today(risk, new_conditions)
```

**Example from real session:**

| Yesterday's Risk | Status Today | Action |
|---|---|---|
| "$200 level for NVDA" | PULLBACK: NVDA hit $199 then fell back | Level is still active, keep in today's analysis |
| "TSLA $400 support" | Price held at $408 and rallied | Risk downgraded, TSLA has recovered |
| "Gold super-buy RSI" | Price consolidated, RSI cooled to 62 | Risk reduced, gave space for further upside |

### Step 5: Weave Trend Data into Analysis

Use the multi-day context to write stronger opening statements:

- **Weak**: "NVDA closed at $197.43, down 0.08%."
- **Strong**: "NVDA pulled back from yesterday's $199 spike, settling at $197.43. The $195→$199→$197 sequence shows a stock oscillating around the $200 level without conviction—bulls can't hold above it, but bears can't push below $195 either."

- **Weak**: "TSLA closed at $423.37, down 0.45%."
- **Strong**: "TSLA rallied $14 in 2 days from $409 to $423; today's 0.45% dip is a normal breather after a 3.5% gain streak. The recovery from June 29's $408 low is intact."

- **Weak**: "Gold at $4,038.30."
- **Strong**: "Gold defended $4,000 for the third consecutive day. The sequence $4,018→$4,012→$4,038 shows $4,000 is now confirmed as strong support, not just a one-day breakout."

## When This Pattern is Most Useful

| Scenario | Value of Multi-Day Analysis |
|---|---|
| Regular trading day | Useful for context, but single-day is sufficient |
| **Monday morning after weekend** | **Critical** — last data is Friday close, needs 3-5 day trend |
| Holiday-shortened week | Helps bridge the gap in data frequency |
| After volatility event | Shows whether the move is continuing or reversing |
| When script data looks wrong | Historical comparison helps spot price anomalies |

## Limitations

- Only gives **one direction for gold** (no change_pct) — gold analysis relies on sequential price comparison only
- Volume data from Nasdaq API can be fractional; use `int(float(vol_str))` pattern for safe parsing
- Briefings before the script pipeline ran may use a different format — adapt extraction as needed
