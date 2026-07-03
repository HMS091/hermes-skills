# Freelancer API Notes (June 2026)

## API Token Location

API Tokens are NOT at:
- `developers.freelancer.com` (that's documentation only)
- `/users/api-tokens.php` (returns 404)
- `/settings/api-tokens` (returns 404 — old URL)

**Correct path:**
1. Log in at freelancer.com
2. Click avatar (top right) → **Settings**
3. Look for **API Tokens** in the left sidebar (may be under Integrations or Security)
4. Create new token

## Login Issue

Freelancer login page has **reCAPTCHA** — cannot be bypassed programmatically. User must log in manually. The Google social login button is enabled (unlike Facebook which is disabled).

## Public API (No Auth Required)

### Search Active Projects
```python
from scrapling.fetchers import Fetcher
resp = Fetcher.get("https://www.freelancer.com/api/projects/0.1/projects/active?limit=20")
data = resp.json()
projects = data["result"]["projects"]
total = data["result"]["total_count"]  # typically 6000+
```

### Response Structure
- `result.projects[]` — array of project objects
- `result.total_count` — total number of active projects (e.g. 6692)
- Each project has: id, title, type (fixed/hourly), budget (min/max), currency, bid_stats (bid_count, bid_avg), preview_description, submitdate, seo_url, jobs

### Real-World Price Data (Sample from 6692 active projects)

| Project | Budget | Type | Bids | Category |
|---------|:------:|:----:|:----:|:---------|
| Excel Name-Match Automation | $20-250 | Fixed | 1 | Data Analysis |
| Clean Malware from E-Commerce Site | $15-25/hr | Hourly | 63 | Security |
| CSR Compliance for Section 8 NGO | INR 600-1500 | Fixed | 2 | Legal |
| Podcast Listener Growth Strategy | $2-8/hr | Hourly | 5 | Marketing |
| Optimize Slow-Loading PDF File | $30-250 | Fixed | 74 | Acrobat |
| Digital Website (eCommerce) | $250-750 | Fixed | 221 | Web Dev |
| Tailored eSIM eCommerce Website | INR 600-1500 | Fixed | 26 | API |
| Roadside Assistance Mobile App | $750-1500 | Fixed | 179 | Flutter |
| Student Counseling Website | INR 5000-7000 | Fixed | 30 | Web Dev |

**Key observations:** Competition is fierce — a $750 app project has 179 bidders. Low-competition niches (1-5 bids) like niche data analysis or specialized automation are better targets.

## Bidding (Requires Auth + API Token)

- Endpoint: POST `/api/projects/0.1/bids/`
- Requires `Freelancer-API-Version` header
- Requires OAuth token or API key in `Authorization` header
- Body: `{ "project_id": int, "bid_amount": float, "description": "..." }`

## Payment Withdrawal Options

Based on platform documentation:

| Method | Speed | Fee Level | Notes |
|--------|:-----:|:---------:|-------|
| PayPal | Instant | High (4-5%) | Most common, easy setup |
| Wise (TransferWise) | 1-2 days | Low (0.5-1%) | Best FX rate, real mid-market rate |
| Payoneer | 1-3 days | Medium | Good for non-US freelancers |
| Bank Wire | 3-7 days | Varies | Old school, high bank fees |
| Skrill | Instant | Medium | Alternative to PayPal |
| Freelancer Debit Card | Instant | Low | US-only |
| **Crypto** | ❌ Not supported | — | No direct crypto withdrawal |
