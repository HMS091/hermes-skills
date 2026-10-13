# Bypassing Aggressive Cloudflare (Managed Challenge)

> **Update 2026-10-13:** a managed challenge *can* be solved once the environment is right. With the
> matching Chromium build, `TMPDIR=/tmp` and a generous timeout, `StealthyFetcher(solve_cloudflare=True)`
> solved `https://www.scrapingcourse.com/cloudflare-challenge` (managed turnstile → then embedded) in
> ~2.5 min: status 200, text "You bypassed the Cloudflare challenge! :D". The earlier failure below was
> caused mainly by a **missing/broken browser build**, not by an impossible challenge. Always give
> `timeout=120000`+ so the solving loop has room, and retry the site before declaring it unbeatable.
> Hardest cases (interactive captcha, IP-reputation blocks, no residential proxy) still fail — the
> sibling-domain trick and the Hermes browser (Browserbase cloud IP) remain the fallbacks.

## The Problem

Scrapling's `StealthyFetcher` with `solve_cloudflare=True` can loop indefinitely on Cloudflare's **managed challenge** (the most aggressive tier). The symptom is a repeating log:

```
The turnstile version discovered is "managed"
Cloudflare page didn't disappear after 10s, continuing...
Looks like Cloudflare captcha is still present, solving again
```

This can continue until timeout with no resolution — that is the failure mode, not a guaranteed outcome.

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
