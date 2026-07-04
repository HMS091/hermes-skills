# Bypassing Aggressive Cloudflare (Managed Challenge)

## The Problem

Scrapling's `StealthyFetcher` with `solve_cloudflare=True` cannot bypass Cloudflare's **managed challenge** (the most aggressive tier). The symptom is a looping log:

```
The turnstile version discovered is "managed"
Cloudflare page didn't disappear after 10s, continuing...
Looks like Cloudflare captcha is still present, solving again
```

This continues until timeout with no resolution.

## Real-world Example: Saily.com

**Target**: `go.saily.site` (redirects to `saily.com`) — Surfshark/Nord Security's eSIM + US phone number service.

**Failed approaches**:
1. `Fetcher.get()` → 403 (Cloudflare block)
2. `StealthyFetcher.fetch(solve_cloudflare=True)` → looped 6 times on "managed" challenge, timed out
3. Hermes browser → "Just a moment..." Cloudflare challenge, never resolved
4. Direct curl → 403 / connection reset

**Working approach — sibling domain**:
- `surfshark.com/affiliate` → loaded successfully (no Cloudflare or weaker protection)
- `surfshark.com/affiliate-terms-and-conditions` → also accessible, contained full affiliate program details
- This worked because Saily and Surfshark are both owned by Surfshark B.V. (Nord Security)

## Sibling Domain Discovery Process

1. Identify the corporate owner of the blocked site
2. Try owner's main marketing site (often less protected)
3. Try specific subpages: `/affiliate`, `/partner`, `/about`, `/blog`, `/help`
4. Check footer links for other products by same company
5. Example: saily.com footer listed "Surfshark VPN", surfshark.com footer listed "Saily" — bidirectional link

## Surfshark Affiliate Program Details (recovered via sibling domain)

| Field | Value |
|---|---|
| Commission | **40% revenue share** on new sales |
| Cookie duration | 30 days |
| Min payout | $100 |
| Networks | Tunes, Impact Radius, Avant, CJ, Appsflyer, Awin |
| Products listed | VPN, Antivirus, Search, Alert, Incogni, Alternative ID |
| **Saily listed?** | **No** (not in the affiliate program product list) |

The `go.saily.site` URL is just a 302 redirect to saily.com's homepage — not a referral tracking link.
