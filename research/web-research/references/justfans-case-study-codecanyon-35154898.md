# JustFans Case Study — CodeCanyon Item 35154898

Reference case for evaluating a commercial OnlyFans clone via CodeCanyon.

## Item Profile

| Field | Value |
|-------|-------|
| CodeCanyon ID | 35154898 |
| Item URL | `https://codecanyon.net/item/justfans-premium-content-creators-saas-platform/35154898` |
| Author | ic0de |
| First Release | Dec 2021 (v1.0.2) |
| Current Tech (as verified) | Laravel (PHP 8.2) + Apache/2.4.6 (CentOS) |
| Demo URL | `https://justfans.qdev.tech` |
| Docs URL | `https://docs.qdev.tech/justfans` |
| Admin Path | `/admin` (403 with demo account) |
| Price (est.) | Regular License ~$35–$60 (CodeCanyon PHP script pricing) |

## Wayback Snapshots Found

| Date | Page | HTTP | Size |
|------|------|------|------|
| 2021-12-17 | Item page | 200 | 39KB |
| 2021-12-18 | Item page | 200 | ~40KB |
| 2022-02-03 | Comments page | 200 | ~40KB |
| 2023-02-03 | Comments page | 200 | 237KB (richest snapshot) |

## Buyer Comment Analysis (from 2023-02-03 snapshot)

### Volume
- **1,162 total comments** → very active item
- **46 reviews** → moderate review count

### Author Support Signals
- Author responded to virtually every comment (ic0de)
- Response time seemed fast (same-day replies in many cases)
- Author gave direct SQL fix when user locked themselves out of admin:
  ```sql
  UPDATE users SET role_id = 1 WHERE email = 'your@email.com';
  ```
- Demonstrated clear boundaries: "not really available for freelancing"

### Bug Reports Found
| Bug | Author Response |
|-----|----------------|
| Paid message price validation (can set price to impossible values) | "We've got that fixed and will be included in the next update" ✅ |
| Wasabi storage policy doc error | "Will update documentation accordingly in the next version" ✅ |
| Storage driver 500 error after misconfiguration | Provided quick guide link to reset to local storage ✅ |
| Registration "internal error" but still registers user | Asked for more details via DM |
| File permission issue on Apache http2 | Diagnosed as permissions issue, not script bug |
| License server connection failure during install | "Try again, if fails send DM" |

### Feature Requests Captured
| Request | Author Response |
|---------|----------------|
| Referral system | **Already added in latest version** ✅ |
| Show featured posts on login page (like OnlyFans) | Not addressed directly |
| Page builder for admin landing page | "Could be achieved with custom changes" |
| Discord integration | "Could be achieved with custom changes" |
| Disable comments on posts | Not addressed |
| Custom storage driver integration | Declined — not available for custom work |

### Buyer Satisfaction
- "Great work overall, Just finalizing and going live" — buyer taking to production
- "Great product" — simple positive
- "Yep, that was it. Thank you so much!" — support resolved

## Live Demo Evaluation (via curl login + i18n mining)

### Login Process
```python
# CSRF token extraction
import requests, re
s = requests.Session()
r = s.get("https://justfans.qdev.tech/login")
csrf = re.search(r'name=["\']_token["\'][^>]*value=["\']([^"\']+)["\']', r.text).group(1)
s.post("https://justfans.qdev.tech/login",
       data={"_token": csrf, "email": "good@gmail.com", "password": "123456badman"},
       allow_redirects=True)
# Redirects to /feed on success
```

### Confirmed Features (from i18n string extraction)

**Monetization:**
- Subscriptions (1/3/6/12 month bundles, promotional pricing)
- PPV (post unlock, paid messages)
- Tipping (post tips, chat tips)
- Referral system (invite others → get fee from their earnings)
- Platform commission (`:feeAmount% fee will be applied`)
- Digital store/e-commerce

**Payments:**
- Stripe (sandbox in demo) + Stripe Connect (direct to creator bank)
- PayPal
- Coinbase (crypto)
- YooMoney (Russian payment)
- Bank transfer (IBAN)
- Wallet deposit + withdrawal

**Creator Features:**
- Verification flow (must verify identity before posting)
- Tax info required before withdrawal
- Dashboard (total earned, subscriptions revenue, active subscribers, post count)
- Withdrawals manual (reviewed by admin, ~24h processing)
- Min withdrawal: $20, Max: $500
- Release forms (upload signed forms for people appearing in content)
- Welcome messages (auto-send on new subscriber)

**Content Features:**
- Posts with image/video/audio attachments
- Scheduled posts (release date + expire date)
- Pinned posts
- Blurred previews for locked content
- Watermark on images & videos
- Draft posts pending verification
- Stories (24h ephemeral)
- Bookmarks & user lists

**Engagement:**
- Live messenger (Pusher real-time)
- PPV messages (media locked behind payment)
- Live streaming (RTMP via OBS)
- Tips on posts
- Comments + reactions

**Admin Panel (confirmed via 403 probes):**
- `/admin` — main dashboard
- `/admin/users` — user management
- `/admin/posts` — post management
- `/admin/subscriptions` — subscription management
- `/admin/withdrawals` — withdrawal/payout management
- 90+ settings (from original description)

**PWA:** ✅ manifest.json present, mobile-first responsive design

### Demo Account Limitations
- good@gmail.com was a regular user (fan), not a creator or admin
- Could browse feed, view profiles, access /my/settings
- Could NOT: post content, view wallet, send messages, access creator dashboard
- Admin paths returned 403 (exists but blocked)

### Network vs Server Latency
| Site | Response Time | Verdict |
|------|--------------|---------|
| justfans.qdev.tech | 8.2s | |
| google.com | 9.6s | → **Network bottleneck** from Docker environment |
| github.com | 6.7s | |
| fansforx.com | 3.6s | |
**Conclusion**: Slowness is Docker environment's network, not the target server.

## Server Sizing Reference

For 300 users on this platform:

| Resource | Recommended | Notes |
|----------|-------------|-------|
| CPU | 2 cores | Laravel is CPU-moderate, not heavy at this scale |
| RAM | 4GB | Laravel + MySQL + PHP-FPM = ~2.5GB baseline |
| Storage | 80GB SSD + media volume | Media grows with uploads |
| Bandwidth | 30Mbps | ~3-5 concurrent video streams |
| Traffic | 1TB/month | Covers 300 users with moderate video |
| Cost | ¥50/月 (CN) / €4.5/月 (Hetzner) | |

## Key Takeaways
1. CodeCanyon items can be fully evaluated via Wayback Machine + live demo curl
2. i18n string extraction from the demo reveals ALL features — more reliable than vendor feature pages
3. 1,162 comments with active author response = healthy project
4. Admin path probing (403 vs 404) reveals admin module structure
5. Network latency must be measured independently of target site (compare with Google/GitHub)
