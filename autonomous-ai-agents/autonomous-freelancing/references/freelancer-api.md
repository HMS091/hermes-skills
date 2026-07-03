# Freelancer API Notes (June 2026)

## API Token Location

API Tokens are NOT at:
- `developers.freelancer.com` (documentation only)
- `/users/api-tokens.php` (returns 404)
- `/settings/api-tokens` (returns 404 — old URL)

**Correct path:**
1. Log in at freelancer.com
2. Click avatar (top right) → **Settings**
3. Look for **API Tokens** in the left sidebar (may be under Integrations or Security)
4. Create new token

## Login Issue

Freelancer login page has **reCAPTCHA** — cannot be bypassed programmatically. User must log in manually. Google social login is available (Facebook disabled).

## Public API (No Auth Required)

### Search Active Projects
```python
from scrapling.fetchers import Fetcher
resp = Fetcher.get("https://www.freelancer.com/api/projects/0.1/projects/active?limit=20")
data = resp.json()
projects = data["result"]["projects"]
total = data["result"]["total_count"]
```

### Response Structure
- `result.projects[]` — array of project objects
- `result.total_count` — total number of active projects (typically 6000+)
- Each project has: id, title, type (fixed/hourly), budget (min/max), currency, bid_stats (bid_count, bid_avg), preview_description, submitdate, seo_url, jobs

### Real-World Price Data (from 6692 active projects)

| Project | Budget | Type | Bids |
|---------|:------:|:----:|:----:|
| Excel Name-Match Automation | $20-250 | Fixed | 1 |
| Clean Malware from E-Commerce Site | $15-25/hr | Hourly | 63 |
| Digital Website (eCommerce) | $250-750 | Fixed | 221 |
| Roadside Assistance Mobile App | $750-1500 | Fixed | 179 |

**Competition is fierce** — target low-bid-count niches.

## Bidding (Requires Auth + API Token)
- POST `/api/projects/0.1/bids/`
- Auth header required
- Body: `{ "project_id": int, "bid_amount": float, "description": "..." }`

## Payment Withdrawal Options

| Method | Speed | Fee | Crypto? |
|--------|:-----:|:---:|:-------:|
| **Wise** | 1-2 days | Low (0.5-1%) | ❌ |
| PayPal | Instant | High (4-5%) | ❌ |
| Payoneer | 1-3 days | Medium | ❌ |
| Bank Wire | 3-7 days | Varies | ❌ |
| Skrill | Instant | Medium | ❌ |

**Wise is recommended** — lowest fees, best exchange rate, supports transfer to Chinese bank cards.
