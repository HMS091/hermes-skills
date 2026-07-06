# Platform Scam/Risk Investigation: Systematic Approach

## Purpose

When a user asks "is this platform legit?" or "investigate this website" — a systematic approach to assess whether an unknown online platform is a scam, fraud, or operates in a grey/black area. This is distinct from business research on legit companies — the target here is **verification of trustworthiness**, not feature comparison.

## When to Use

- User asks to "check out" an unknown website/platform
- User asks "有没有骗局" (is it a scam?)
- User provides a URL of an unfamiliar service
- The platform offers financial services (virtual cards, payments, lending, crypto)

## Data Sources & Collection Order

### Phase 1: Domain & Infrastructure Reconnaissance

Run these in parallel:

```bash
# 1. DNS records (via Google DNS API)
curl -sL "https://dns.google/resolve?name=<domain>&type=A"
curl -sL "https://dns.google/resolve?name=<domain>&type=NS"
# → IP addresses, nameservers

# 2. WHOIS (via web-based who.is — whois CLI often times out in Docker)
curl -sL "https://who.is/whois/<domain>" -A "Mozilla/5.0" --max-time 15
# → Registration date, registrar, registrant org, privacy status

# 3. Wayback Machine snapshot check
curl -sL "https://archive.org/wayback/available?url=<domain>"
# → Available snapshots, age of oldest snapshot

# 4. Direct curl to homepage (check if site is alive at all)
curl -sL --max-time 10 "https://<domain>" -A "Mozilla/5.0" | head -50
# → Is it Cloudflare? Is it a parking page? Does it load?
```

**Key data points from Phase 1:**

| Signal | What to Check | Interpretation |
|--------|---------------|----------------|
| **Domain age** | Creation date from WHOIS | <6 months = 🟠 huge red flag for financial platforms |
| **WHOIS privacy** | Registrant organization | "Domains By Proxy", "WhoisGuard", etc. = owner intentionally hidden |
| **Registrar** | WHOIS registrar field | GoDaddy + privacy = cheap throwaway setup |
| **Cloudflare** | HTTP headers / "Just a moment..." | Legit but also hides real server IP |
| **Nameservers** | Cloudflare NS | Expected for Cloudflare proxied sites |
| **Oldest snapshot** | Wayback Machine available URL | Site that's <1 year old + no Wayback history = 🟠 |
| **IP geolocation** | DNS A record IP | Cloudflare IPs are generic; if direct IP: where's the server? |

### Phase 2: Business Model & Contact Assessment

Once you can see the site (via Wayback Machine or direct curl):

1. **Extract text content** — What does the site claim to offer?
2. **Find contact info** — Email, phone, address, social media
3. **Check for registration info** — Company name, business license, ICP备案 (for China)

**Red flag checklist for contact/registration:**

| Finding | Risk Level | Explanation |
|---------|-----------|-------------|
| Contact email is **Gmail/Outlook/Yahoo** (not company domain) | 🔴 HIGH | Legitimate businesses use their own domain email |
| **Only Telegram/WhatsApp** for support | 🔴 HIGH | Telegram is unregulated, accounts can be deleted instantly |
| **No phone number** | 🟡 MEDIUM | Common for small online services but suspicious for financial |
| **No company name anywhere** | 🔴 HIGH | Every legitimate business has a legal entity name |
| **No physical address** | 🟡 MEDIUM | VPN-only businesses may not have public office |
| **No business license / ICP备案** (Chinese sites) | 🔴 HIGH | Required by law for Chinese financial services |
| **No privacy policy / terms of service** | 🔴 HIGH | Required for any site handling user data |
| Privacy policy has no legal entity name | 🟡 MEDIUM | Generic template, copy-pasted |

### Phase 3: Payment & Technical Assessment

1. **Check payment methods** — Do they take credit cards directly? Crypto only? Bank transfer?
2. **Check the tech stack** — What backend system are they using?
3. **Detection: White-label / Reskin Setup**

```bash
# Check for embedded JSON/JS that reveals the underlying platform
curl -sL --max-time 10 "https://<domain>" -A "Mozilla/5.0" | grep -oP 'src="[^"]*"' | head -20
curl -sL --max-time 10 "https://<domain>" -A "Mozilla/5.0" | grep -oP 'href="[^"]*"' | head -20
# → External script sources reveal the backend platform
```

**Backend platform identification:**
Search the page source for script/src URLs pointing to a different domain. Common virtual card system backends:
- `sh5.live` — Chinese virtual card system (used by feiyangka.com)
- Various SaaS white-label card issuance platforms

If the site is just a **frontend reskin** of a known platform, the operator has minimal technical capability — they bought a template.

### Phase 4: User Review & Community Intelligence

1. **App Store search** — Is there an iOS app? What do reviews say?
2. **Search for complaints** — Try DuckDuckGo: `site:reddit.com <platform> scam|review`
3. **Check Telegram/Discord groups** — Many scam platforms have "official community" links on their site

### Phase 5: Red Flag Synthesis

**Critical: Distinguish "scam" from "grey market tool"**

| Classification | Definition | Example |
|---------------|-----------|---------|
| **🔴 Scam** | Takes money and disappears. Fake service. No delivery. | Ponzi, fake investment, payment without delivery |
| **🟠 Grey market tool** | Real service but used for illegal/questionable purposes | Anonymous virtual cards, unlicensed VPN, gambling tools |
| **🟡 Unprofessional but legit** | Real service, sloppy execution | Small legitimate business with Gmail contact |
| **✅ Legitimate** | Registered company, proper contact, KYC, licensing | Depay, OneKey, RedotPay, Wise |

## Worked Example: feiyangka.com (飞扬卡平台)

### Phase 1 Results

| Data Point | Finding | Signal |
|-----------|---------|--------|
| Domain created | 2024-08-08 (less than 2 years old) | 🟠 |
| WHOIS owner | Hidden via Domains By Proxy (GoDaddy) | 🔴 |
| Registrar | GoDaddy.com, LLC | 🟡 |
| DNS | Cloudflare (cheryl.ns.cloudflare.com) | Neutral |
| Wayback snapshot | One snapshot from 2024-09-06 | 🟡 (very few) |
| Server IP | Cloudflare proxied (hidden) | Neutral |

### Phase 2 Results

| Finding | Signal |
|---------|--------|
| Contact email: **feiyangcard@gmail.com** (Gmail) | 🔴 |
| Support: **Telegram @fyy8899** only | 🔴 |
| Official channel: Private Telegram invite link | 🔴 |
| No company name anywhere on site | 🔴 |
| No business license or ICP备案 | 🔴 |
| **Anonymous registration** (only email needed) — promoted as feature | 🔴 |
| **No credit check** — promoted as feature | 🔴 |
| **Referral/invite code system** (URL parameter `inNo=xxx`) | 🔴 |

### Phase 3 Results

| Finding | Signal |
|---------|--------|
| Backend: `sh5.live` — third-party card platform | 🟡 |
| PC entry: `/vc_web/main.html#/login` (SPA) | Neutral |
| H5 entry: `/vc_h5/#/?inNo=xxx` (mobile SPA) | Neutral |
| Referral codes hardcoded in landing page | 🔴 |

### Classification: 🔴 HIGH LIKELIHOOD SCAM / GREY MARKET TOOL

**Reasons:**
1. Anonymous-only registration + no KYC = designed for users who don't want to be identified
2. Promotes "no credit check" and "anonymity" as core selling points (legitimate card platforms never do this)
3. Only reachable via Gmail + Telegram (both fully anonymous)
4. Referral code system = MLM/pyramid-style growth
5. No company registration, no license, no physical address
6. Domain less than 2 years old
7. Real owner hidden behind WHOIS privacy

## Pitfalls

- **WHOIS CLI may time out** from Docker. Always fall back to `who.is` website (curl + grep extraction)
- **Cloudflare blocks most scrapers**. Use Wayback Machine for cached content when direct access fails
- **Referral codes can look like tracking params**. Distinguish: `inNo=xxx` is user-specific referral; `utm_source=xxx` is marketing tracking
- **A legitimate service CAN use Telegram + Gmail** for very small operations. But if it's a financial/payment service and they only have these = scam
- **Gmail as business email for a payment platform** is the single strongest red flag. Real payment/fintech companies always use their own domain
- **"Grey market" ≠ "scam"** — some platforms are genuinely useful but operate in regulatory grey areas. The user needs to understand the difference
- **Wayback Machine snapshots have 403 errors** for some sites even when they exist. Check `available` response first
- **Chinese virtual card platforms often use sh5.live as backend** — this is a known SaaS platform for card issuance. Finding sh5.live doesn't automatically mean scam, but combined with other red flags it's suspicious
