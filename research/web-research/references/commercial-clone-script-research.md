# Commercial Clone Script Research

Domain-specific knowledge for researching **white-label / clone script products** — ready-made SaaS-like platforms you buy and self-host.

## Key Market Differences vs. Open-Source Research

| Dimension | Open Source Repo | Commercial Clone Script |
|-----------|-----------------|------------------------|
| Price | Free | $699–$1,500+ one-time or $500+/mo subscription |
| Source code | Often partial/incomplete | Typically 100% included (may be encrypted on cheap plans) |
| License | Varies (MIT, GPL, none) | Proprietary EULA |
| Reviews | GitHub stars, forks, issues | SourceForge, G2, Sitejabber, Trustpilot |
| Demo | Clone & run | Usually a hosted live demo |
| Support | Community | Vendor provided (2-3mo free then paid) |
| Payment integration | Rarely included | Usually built-in (Stripe, PayPal, CCBill) |

## Search Strategy for Clone Scripts

### Phase 1: Find the Major Players

**Best sources (curl accessible):**
1. Comparison blog articles (e.g. xpertz.io, medium.com) — rank top products
2. SourceForge compare pages: `https://sourceforge.net/software/compare/<ProductA>-vs-<ProductB>/`
3. Product homepages: `fanso.io`, `adent.io`, `oyelabs.com`, `scrile.com`, `fansforx.com`

**Secondary sources (JS-rendered, hard to scrape):**
- G2.com — JS-heavy, reviews not accessible via curl
- Trustpilot — JS-rendered reviews
- Sitejabber — often empty for small vendors

**⚠️ CodeCanyon (Envato Market)** — A major PHP script marketplace that often has subscription/membership scripts at $20–$60 range, but NOT typically full OnlyFans clones. Access is blocked by Cloudflare's JS challenge from this Docker environment. See dedicated section below.

**Fallback:**
- Direct product page scraping (homepage, /pricing/, /features/) with curl
- DuckDuckGo HTML search for blog reviews (but increasingly blocked with CAPTCHA challenges)

### Phase 2: Extract Key Decision Factors

| Factor | What to Check |
|--------|---------------|
| **Pricing model** | One-time vs subscription vs revenue share |
| **Source code ownership** | Full source vs encrypted vs hosted only |
| **Payment gateways** | Stripe, PayPal, CCBill, Netbilling, crypto |
| **Deployment** | Self-hosted (PHP/Node/Python) vs cloud-hosted |
| **Web vs Mobile** | Responsive web + PWA vs native iOS/Android |
| **Live demo** | Is there a working demo to test? |
| **Review presence** | Any SourceForge/G2/Trustpilot rating? |

### Phase 3: Pricing Pattern Recognition

Typical pricing for OnlyFans-style clone scripts (2026):
| Tier | Price | What You Get |
|------|-------|-------------|
| Starter | $699–$950 | Encrypted/partial source, core features |
| Professional | $1,499–$2,500 | Full source code, all features |
| Enterprise | $5,000+ | Custom features, dedicated support |
| Subscription | $500/mo ($6k/yr) | Hosted solution, no source code ownership |

**Budget outlier**: FansForX offers full source at $499 — well below the typical starter tier. The tradeoff is older tech stack (Laravel 7.x, React 16.x).

**Rule of thumb:** If a "production-ready" repo on GitHub has <10 files and <100KB, it's likely a sales landing page, not actual source code. Check the file listing via GitHub API before investing time.

## Priced Discovery Technique: Meta-Description Mining

When product pages are JS-heavy but the homepage HTML loads, **the meta description tag often contains the pricing signal** directly. Vendors optimize meta descriptions for SEO and frequently embed their price:

```bash
curl -sL "https://fansforx.com/" -H "User-Agent: Mozilla/5.0" | \
  grep -oP 'content="[^\"]*\$\d+' | head -1
# Returns: content="...499$..."
```

This works even when the /pricing/ page returns only 275 bytes (JS-only rendering).

## CodeCanyon (Envato Market) — Cloudflare Protected

CodeCanyon (`codecanyon.net`) is a major PHP script marketplace that can theoretically have subscription/membership scripts relevant to clone projects. However, in practice:

### Access Limitations

| Approach | Result | Detail |
|----------|--------|--------|
| Homepage (curl) | ✅ 200, 445KB | Loads but is JS-rendered React SPA — no extractable item data |
| Search page (all queries) | ❌ Cloudflare 403 | Any `/search/` URL triggers CF challenge. Even with session cookies from home page. |
| `popular_item/by_category?category=php-scripts` | ✅ 200, 487KB | Returns page content but JS-rendered — no item data in HTML |
| API endpoints (`api.envato.com/*`) | ❌ 401 | Requires API token (Envato developer account) |
| RSS feeds (`/feed/*`) | ❌ 404 | All feed endpoints return 404 |
| Internal XHR JSON endpoints | ❌ CF 403 | Any `/api/` or `format=json` URL pattern blocked |
| Bing/Google search for items | ❌ Empty | Search engines don't index individual CodeCanyon items well |
| **Wayback Machine (specific item page)** | ✅ **Works!** | Snapshot of the item's HTML page at a past date — bypasses Cloudflare entirely |

### Wayback Machine Strategy for CodeCanyon Item Pages

CodeCanyon item pages **can be accessed through the Wayback Machine** when the live site is Cloudflare-blocked:

**Step 1: Find snapshots**
```python
import requests
r = requests.get("https://web.archive.org/cdx/search/cdx?url=codecanyon.net/item/<item-slug>/<item-id>&output=json&limit=5",
                headers={"User-Agent": "Mozilla/5.0"})
data = r.json()  # Each row: [urlkey, timestamp, original, mimetype, statuscode, digest, length]
```
Returns a JSON array with available snapshots. Note: The CDX API may itself timeout from Docker — retry with shorter timeout or skip to Step 2.

**Step 2: Access a snapshot**
```
https://web.archive.org/web/{timestamp}/https://codecanyon.net/item/<item-slug>/<item-id>
```
Pick a timestamp where `statuscode` is `200` and page is large enough to contain the item details.

**Step 3: Extract key data from the archive**
From the archived HTML page, extract via regex or text processing:
- **Title**: `<title>` tag (reveals item name and "by author")
- **Price**: Search for `$XX.XX` patterns and contextual text (Regular/Extended License labels)
- **Version/Changelog**: Look for version numbers and changelog entries
- **Features**: Look for bullet-pointed feature lists and screenshot captions
- **Support terms**: Phrases like "6 months support", "Extend support to 12 months"
- **Tech stack**: "Backend powered by Laravel X", "Frontend powered by Bootstrap Y"
- **Demo URL**: Look for demo links (often `*.qdev.tech`, `*.demo.envato.com` etc.)
- **Admin credentials**: Phrases like "Credentials are pre-filled", "Admin features partially disabled"
- **Documentation**: Look for `/docs` path references

**Step 4: Cross-reference with live demo**
Once you have the item details from archive, test the live demo URL directly. Note that the tech stack found in archive may be outdated — the current version could be significantly upgraded (e.g., Laravel 6 → Laravel 10+, PHP 7 → PHP 8.2).

**Known limitation**: Wayback snapshots may be months or years old. Review/rating sections are usually JS-rendered and not captured. Changelog will stop at the snapshot date — don't assume the project was abandoned unless confirmed otherwise.

### CodeCanyon Item Deep-Eval Checklist

When evaluating a specific CodeCanyon PHP script item:

| Signal | Where to Check | What It Means |
|--------|---------------|---------------|
| Item ID | URL path | Lower IDs = older items, but not a quality signal |
| Author name | Page title | Multiple high-quality items from same author = good sign |
| Last update | Changelog or "Recently Updated" badge | Regular updates = active maintenance |
| Version | Changelog | Version numbers: v1.0.2 → current suggests recent major version |
| Laravel version | "Backend powered by" section | v6 (EOL), v7 (EOL), v8 (EOL), v9 (EOL), v10+ (supported) |
| License type | Regular vs Extended price | Regular = 1 end product, Extended = multiple sales/distribution |
| Support period | Pricing/support section | 6mo standard, extendable to 12mo |
| Payment gateways | Feature list | Stripe, PayPal, CCBill, crypto, YooMoney |
| Admin panel screenshots | Image filenames | `/admin_panel_dashboard.png`, `/admin_panel.png` confirm admin exists |
| Demo restrictions | "partially disabled" text | Demo may limit admin features or content posting |
| PWA support | Feature list | "PWA App included" = installable mobile app |
| Delivery method | Standard CodeCanyon | Downloadable zip via your Envato account |

**Verdict**: CodeCanyon is effectively unscrapable from this Docker environment. The site requires a full browser (agent-browser/Playwright) that can execute Cloudflare's JavaScript challenge.

### Practical Strategy

1. **Traditional browser method**: Use the `browser` tool with agent-browser (Chromium). Navigate to `https://codecanyon.net/search/onlyfans+clone` and interact with the rendered page.
2. **Setup prerequisite**: `cd /opt/hermes && npx agent-browser install` — this downloads Chromium. May take 5-10 minutes on slow proxy.
3. **If browser unavailable**: Provide the user with direct search URLs for self-verification and move on. CodeCanyon is unlikely to have full OnlyFans clones — it primarily sells smaller components (membership scripts, subscription plugins, video platforms) at $20–$60, not turnkey clone platforms.
4. **Known CodeCanyon categories to explore**: "PHP Scripts" → "Social Networking" or "Video Platforms" or "Membership Systems" — these may contain relevant building blocks but not a 1:1 OnlyFans replica.

### Technique: Wayback Machine CodeCanyon Comments & Reviews Analysis

CodeCanyon item **comments pages** at `/item/<slug>/<id>/comments` can be accessed via Wayback Machine snapshots, providing real buyer sentiment data that's otherwise Cloudflare-blocked.

#### Finding Snapshot Availability

```python
import requests
r = requests.get(
    "https://web.archive.org/cdx/search/cdx"
    "?url=codecanyon.net/item/<slug>/<id>/comments"
    "&output=json&limit=10",
    headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
data = r.json()
# Skip header row, iterate snapshots
for row in data[1:]:
    ts, status, size = row[1], row[4], row[6]
    print(f"{ts[:8]} HTTP {status} {size} bytes")
```

#### Accessing a Snapshot

Construct the URL: `https://web.archive.org/web/{timestamp}/https://codecanyon.net/item/<slug>/<id>/comments`

Pick the most recent snapshot with HTTP 200 and non-trivial size (>20KB = likely has comments).

#### Extracting Key Signals from Comments

Parse the archived HTML page (strip `<script>`, `<style>` tags, then remove HTML tags) and search for:

| Signal | What to Look For |
|--------|-----------------|
| **Total comment count** | "N comments found" — higher = more popular item |
| **Review count** | "Reviews (N)" on the page header |
| **Author responsiveness** | Author replies to each comment (look for author's name in replies) |
| **Bug reports** | "error", "bug", "issue", "problem", "500", "not working" |
| **Author bug fix commitment** | "will be included in next update", "got that fixed", "noted" |
| **Feature requests** | "add", "feature request", "wondering if", "possible to" |
| **Install/config issues** | "install", "error when I", "doesn't work", "permission" |
| **Buyer satisfaction signals** | "Great work", "Great product", "Thank you", "works fine" |
| **Author boundaries** | "not really available for freelancing", "could be achieved with custom changes" = will NOT do custom dev |
| **Support issue resolution** | Author giving direct SQL fixes: `UPDATE users SET role_id = 1 WHERE email =...` |
| **Version requests** | "latest update", "new version", "when will" |
| **Feature confirmation** | User asks if feature exists → author confirms or denies = best way to verify feature list |

#### Comment Frequency Pattern

If archived comments show:
- 1,000+ comments → Very popular item, active community
- 46+ reviews → Good review volume
- Author responds to every comment → Strong support reputation
- "Last Update" badge in snapshot → Verify the item was still receiving updates near the snapshot date

**Caveat**: Wayback snapshots capture pages at a point in time. Recent comments (from after the snapshot date) will be missing. The snapshot does NOT execute JS, so dynamically-loaded sections (real-time ratings, paginated older comments) won't appear. You get whatever was in the initial HTML response at that date.

### When to Skip CodeCanyon Entirely

If the user wants a **production-ready 1:1 OnlyFans replica** with all features (subscriptions, PPV, DMs, tipping, live streaming, admin dashboard), CodeCanyon is the wrong marketplace. Direct those users to dedicated clone script vendors (FansForX $499, Fanso $699–$1,499, OyeLabs $950+). Reserve CodeCanyon research for:
- Users on an extremely tight budget ($20–$100)
- Users who want building blocks to assemble, not a complete platform
- Specific plugin/module needs (e.g., just the Stripe subscription part)

Pricing comparison: CodeCanyon items $20–$60 vs dedicated clone scripts $499–$1,499. The price gap reflects complexity — CodeCanyon items are single-purpose scripts (500–2,000 lines), while clone platforms are 50,000+ line applications.

## Search Engine Blockade Pattern (All Major Engines Blocked)

In this Docker/NAS environment, all three major search engines can simultaneously block automated queries:

| Engine | Block Signal | Content Size | Action |
|--------|-------------|-------------|--------|
| DuckDuckGo HTML | CAPTCHA anomaly page | ~14KB, no `result__a` class | Retry with different UA, or abandon — CAPTCHA is usually a human challenge |
| Google | Returns ~91KB but JS-obfuscated, no real results | ~91KB | Abandon — anti-bot is aggressive |
| Bing | ~73KB but no extractable links or data | ~73KB | Abandon — may require JS rendering |

**When all three are blocked simultaneously**, shift strategy entirely:
1. **Skip search engines** — go directly to known vendor domains
2. **Use domain knowledge** — the major clone script vendors are well-known in the space
3. **Scrape product pages directly** with curl (many are PHP/Laravel e-commerce sites that return clean HTML)
4. **Fall back to GitHub API** for open-source baselines — this endpoint is consistently available from Docker

## Low-Cost Vendor Tier (India/Bangladesh/South Asia)

A distinct low-price tier exists from South Asian vendors, often $300–$500 cheaper than Western alternatives. Key differences:

| Factor | Low-Cost Tier ($499–$950) | Mid Tier ($1,499–$2,500) |
|--------|--------------------------|--------------------------|
| **Tech stack age** | Often Laravel 7.x or older, React 16.x | Modern Laravel 10+/React 18+ |
| **Source code** | Full source included | Full source included |
| **Support duration** | 1 year free | 2–3 months free |
| **Payment gateways** | Stripe + PayPal + crypto + CCBill | Stripe/PayPal |
| **Update frequency** | Quarterly patches | Monthly patches |
| **Review availability** | Sparse (SourceForge may list them) | Somewhat more reviews |

## Known Commercial Clone Script Vendors (OnlyFans Category)

Sorted by price low→high:

| Vendor | Product | Price | Model | Tech Stack | Notes |
|--------|---------|-------|-------|-----------|-------|
| **FansForX** | FansForX V6.0 | **$499** ⭐ | One-time | Laravel 7.30 + React 16.13 | Cheapest option; 100% source code; 1yr free support; Stripe/PayPal/crypto/CCBill payments; NFT/watermark/bulk upload features |
| **OyeLabs** | OnlyFans Clone v6.8 | **$950–$1,650** | One-time | PHP/Laravel | AI features; guaranteed 1-week launch; 2mo support |
| **Fanso.io** | Fanso | **$699–$1,499** | One-time | PHP/Laravel/MySQL | Starter=$699 encrypted source; Pro=$1,499 full source |
| **Adent.io** | xFans | **$1,499** | One-time | PHP | Lifetime license; full source; may need dev help for install |
| **Scrile.com** | Scrile Connect | **$500/mo** | Subscription | PHP/MySQL | $6,000/yr, NO source ownership ❌ |
| **Suffescom** | Custom | **$5,000+** | Custom | Laravel/Python | Enterprise only |

## Vendor Profile: FansForX ($499 — Budget Champion)

- **URL**: https://fansforx.com
- **Stack**: Laravel 7.30.4 (backend) + React 16.13 (frontend) — notably old versions
- **Pricing**: $499 one-time, includes 100% source code + 1 year free support. SourceForge listing exists.
- **Features**: Subscriptions, PPV messaging, tips, live streaming (Agora), audio/video calls, wallet/token system, ecommerce store, NFT minting, cryptocurrency payments, CCBill, watermarking, bulk media upload, stories, bookmarking, admin dashboard
- **Caveats**: Laravel 7.x reached end-of-life (security patches ended Feb 2022). React 16 is also legacy. If the user wants to modify and deploy, plan for a framework upgrade or accept the security risk on an isolated Docker network.
- **Hidden signals**: Has been updating features (changelog shows regular additions across multiple versions), which suggests active maintenance despite the old base framework.

## Chinese Marketplace Research (淘宝/闲鱼/拼多多)

Chinese e-commerce platforms can theoretically have clone scripts at very low prices ($50–$500), but they are **effectively inaccessible from this Docker environment**:

| Platform | Access Result | Reason |
|----------|--------------|--------|
| **Taobao (淘宝)** | ❌ Anti-bot captcha | Returns captcha challenge (`rgv587_flag`, `deny_h5.html`) or blank JS shell |
| **闲鱼 (Goofish)** | ❌ JS-rendered SPA | React-based single-page app, 100% client-side rendering |
| **拼多多 (PDD)** | ❌ JS-rendered | Requires full browser engine |
| **京东 (JD)** | ❌ Captcha/redirect | Redirects to verification page |
| **国内源码站** | ❌ Mostly dead/blocked | 5kym.com (403 forbidden), codesc.net (DNS fail), ymanz.com (now an unrelated blog) |

**What's likely on Chinese markets** (from domain knowledge):
Source code for subscription/video platforms is sold under terms like "付费视频系统源码" or "会员订阅网站源码" at ¥200–¥1,500 ($30–$200). However:
- No quality guarantee — often incomplete, stolen, or repackaged WordPress plugins
- No after-sales support ("售后" is unreliable on secondhand markets)
- Risk of malware/backdoors embedded in the code
- Usually old PHP versions or WordPress + paid membership plugin, not a full custom platform

**Practical approach**: If the user insists on checking Chinese markets, the only realistic way is manual browsing via the `browser` tool (agent-browser Chrome) — and even then anti-bot measures may block headless Chrome. Accept this limitation and present international alternatives.

**Recommendation framing**: Chinese markets are cheaper but carry high risk. Budget international options like FansForX ($499 with verified vendor, 1yr support, 100% source code) represent better risk-adjusted value for a deployable product.

## User Preferences (Price-Sensitive Solo Chinese Developer)

When the user is a solo Chinese developer (不懂代码,全靠AI做技术) looking to buy and customize a clone script:

- **Lead with cheapest viable option first** — present the lowest price point immediately with tradeoffs explicitly flagged
- **Price sensitivity is primary** — user will push back on anything over $1,000; the sweet spot is $500 or less
- **"货对版" (product matches description)** is critical — user needs certainty the code is real, complete, and functional
- **"售后" (after-sales support)** matters — budget vendors may promise but not deliver; check if support duration/scope is explicitly stated
- **Prefer one-time purchase over subscription** — user owns a NAS for self-hosting, monthly fees are a non-starter
- **Tech stack age is a secondary concern** — user can't independently verify framework modernity; focus on whether the code *works* and can be deployed
- **Provide clear price comparison table** — user makes decisions visually, not through paragraphs
- **Always end with an actionable recommendation** — don't list options without a clear stance on what to do next
- **Report in Chinese (中文)** with concise tables and bullet points
- **Be honest about limitations** — if you can't scrape a marketplace, say so and provide direct links for the user to self-verify rather than substituting stale data

## Server Sizing for Self-Hosted Clone Platforms

When a user plans to self-host a Laravel/PHP clone platform for ~300 users (+30 creators):

| Resource | Recommended | Monthly Cost (CN) |
|----------|------------|-------------------|
| CPU | 2 cores (Xeon/Epyc, not ARM) | Included |
| RAM | 4GB (Laravel + MySQL + PHP-FPM use ~2.5GB idle) | Included |
| Storage | 80GB SSD + external volume for media | Included |
| Bandwidth | 30Mbps peak | Included |
| Traffic | 1TB/month | Included |
| **Total** | **2C4G 80GB 30Mbps 1TB** | **≈¥50/月** |

**Traffic breakdown**: ~500GB-2TB/mo for 300 users depending on video frequency. 1TB is safe to start.

**Overage handling**: Most CN providers throttle to 10Mbps after quota (not cut off). Overseas: Hetzner €4.5/mo offers 20TB at 1Gbps.

**CN vs Overseas audience**: US-targeting → Hetzner €4.5/mo (lower latency for American users). China-targeting → Tencent/Aliyun (mainland access speed).

**Anti-recommendation**: $10/mo 1C1G VPS is insufficient — Laravel alone with MySQL needs 2GB+ minimum. Minimum viable: 2C2G but 2C4G recommended.

## Pitfalls
- **All-search-engines-blocked scenario**: When DuckDuckGo, Google, AND Bing all block simultaneously from Docker, abandon search and go directly to known product homepages. The major clone script vendors are well-known and don't need discovery.
- **"Production-ready" GitHub repos**: Many are just 9 files of config with a 21KB README but zero actual code. Always check GitHub API file count first.
- **Old Laravel versions**: Budget vendors often ship Laravel 7.x (EOL Feb 2022) or 8.x (EOL Nov 2022). No security patches. Acceptable for isolated Docker deployment, but risky if exposed to the internet.
- **Encrypted source code**: Cheap plans (Fanso Starter $699) often ship with encrypted/obfuscated PHP — you can't modify it. Only the Pro tier ($1,499) gives real source.
- **Subscription trap**: $500/mo × 12 = $6,000/year with no ownership. For self-hosting, one-time purchase is always cheaper after 3–4 months.
- **Hidden costs**: Payment gateway fees (high-risk: 5-10% + $50/mo), CDN for video streaming ($500+/mo at scale), content moderation ($5,000+/mo with AI tools).
- **Review scarcity**: Most clone script vendors have few reviews outside their own testimonials. Cross-reference on SourceForge, G2, and Reddit — but accept that for budget vendors, reviews may be nonexistent.
- **Live demo access**: Budget vendors often require contacting sales for a demo link. Be prepared to reach out or provide the vendor's contact info.
- **Chinese marketplace inaccessibility**: Do NOT keep retrying Chinese e-commerce sites with different curl flags — they all have the same JS/captcha protections. Once confirmed blocked, move on immediately and explain the limitation to the user with direct links for self-verification.
- **Do not substitute stale data**: When you can't scrape a marketplace, admit it clearly rather than fabricating or using old data. User prefers honesty + direct links over plausible-sounding numbers.
