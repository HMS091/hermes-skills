# Business & Company Research: Multi-Source Triangulation

Pattern for researching a company/service/product launch — extracting launch dates, growth data, business model, and verifying claims across sources.

## Context

Generic web searches for business research hit multiple blockers: DuckDuckGo full version returns CAPTCHA, Google returns redirects, target sites are behind Cloudflare or heavy JS rendering (Next.js, SPA). This pattern bypasses those layers systematically.

## Workflow

### Step 1: DuckDuckGo Lite — fastest search bypass

When `html.duckduckgo.com` returns CAPTCHA, use the **Lite** variant:

```bash
curl -sL "https://lite.duckduckgo.com/lite/?q=<search terms>"
```

DuckDuckGo Lite (`lite.duckduckgo.com/lite/`) returns simpler HTML that's less likely to trigger bot detection. Parse results by stripping HTML tags:

```bash
curl -sL "https://lite.duckduckgo.com/lite/?q=Saily+eSIM+launch+date+Surfshark" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  > /tmp/ddg.html
sed 's/<[^>]*>//g' /tmp/ddg.html | tr -s '\n' '\n' | grep -i 'saily\|launch\|2024' | head -40
```

DuckDuckGo Lite results include:
- Article titles and URLs
- Snippets with publication dates
- Multiple sources per query

### Step 2: Identify candidate sources from Lite results

Scan the Lite output for specific URLs to curl directly:
- **Press release sources**: Yahoo Finance, GlobeNewswire, PRNewswire, Manila Times (usually server-rendered, curlable)
- **Company official sites**: nordsecurity.com, saily.com (may have Cloudflare)
- **Tech media**: Gizmodo, TechCrunch (heavy JS, but meta tags are server-rendered)
- **Aggregators**: Grokipedia, travelesimexpert.com (lighter, easier to scrape)

### Step 3: Dive into each source — extract embedded JSON data

Many modern press release sites embed structured data in the HTML that's readable even when the visual page requires JavaScript:

**Yahoo Finance (Next.js app)** — structured data in `__NEXT_DATA__` script tag OR in JSON-LD:

```bash
curl -sL "https://finance.yahoo.com/news/browse-world-saily-esim-solution-130700231.html" \
  -H "User-Agent: Mozilla/5.0" > /tmp/article.html

# Extract JSON-LD schema (contains article metadata, dates, headline)
grep -oP '"@type":"NewsArticle"[^}]+}' /tmp/article.html | head -1

# Extract headline and date published from meta tags
grep -oP '(?<=<meta itemprop="datePublished" content=")[^"]+' /tmp/article.html
grep -oP '(?<=<meta name="description" content=")[^"]+' /tmp/article.html

# Extract __NEXT_DATA__ for full page JSON (contains all article body content)
grep -oP '__NEXT_DATA__[^>]*>\s*\{[^}]+(?:\{[^}]*\}[^}]*)*}' /tmp/article.html | head -1
```

**Nord Security site (Next.js SSG)** — `__NEXT_DATA__` embedded in page:

```bash
# The full press release content is in window.__NEXT_DATA__ JSON
grep -oP '"text":"[^"]{50,500}"' /tmp/nord_page.html | head -10
```

**Manila Times / GlobeNewswire** — meta attributes and HTML meta tags:

```bash
grep -oP '(?<=og:title" content=")[^"]+' /tmp/manila.html
grep -oP '(?<=<meta itemprop="description" content=")[^"]+' /tmp/manila.html
```

### Step 4: Multi-source triangulation

Cross-reference claims from different sources:

| Source Type | Reliability | Typical Data |
|-------------|-------------|--------------|
| Company press release (GlobeNewswire) | ✅ High (official) | Launch dates, product features, quotes |
| Company awards page (nordsecurity.com) | ✅ High (official) | Growth claims, user/billing targets |
| Tech media (Gizmodo, TechCrunch) | ✅ Medium-high | Independent review, feature coverage |
| Tech blogs / aggregators | ⚠️ Medium | May contain copy-paste errors |
| Wikipedia | ⚠️ Variable | May or may not mention the product |

**Look for contradictions** between the official press release and third-party claims. In this session's example, some blogs claimed Saily was "from Surfshark" but the official press release and company site clearly stated "from NordVPN/Nord Security" — Surfshark is a sibling brand under the same parent, not the creator.

### Step 5: Extract key data points

Target fields for business research:
- **Launch date**: Look in multiple date metadata fields (`datePublished`, `dateModified`, `displayDate`, `publishDate`)
- **Growth claims**: "exceeded user registrations", "billing targets", "Global Recognition Award"
- **Pricing**: Look in article body for dollar amounts, plan types
- **Coverage**: "150+ countries", "200+ destinations"
- **Leadership**: CEO name, title (may have changed between press releases)
- **Funding/ownership**: "Created by the experts behind X", subsidiary of Y

### Step 6: Compile into structured report

Use a markdown table format grouping by:
1. Timeline (milestone → date → source)
2. Business overview (ownership, leadership, product specs)
3. Growth data (quote official sources, note any gaps)
4. Corrections (flag any common misconceptions found)
5. Source list

## Technique: Sibling Domain Bypass (for Cloudflare-blocked sister sites)

When a target domain is behind aggressive Cloudflare (managed challenge) that StealthyFetcher and the Hermes browser can't bypass, **navigate from a sibling domain** owned by the same company:

```mermaid
flowchart LR
    A[Target: saily.com] -->|Blocked by Cloudflare| X((❌))
    B[Parent: Surfshark B.V.] --> C[surfshark.com]
    C -->|Accessible ✅| D[Footer: "Other products > Saily"]
    D --> E[Product info, pricing, affiliate terms]
```

### Checklist for finding a sibling domain

1. **Identify the corporate owner**: Check WHOIS, about page, press releases, footer copyright
2. **Find other domains owned by the same entity**:
   - Footer "Other products" section on any accessible brand site
   - Wikipedia infobox "Parent company" → list of subsidiaries
   - Crunchbase subsidiaries/sibling relationships
3. **Try each sibling domain** — one may have weaker/no Cloudflare protection:
   - Parent company's main `.com` (often the most accessible)
   - Older/established brand domains
   - `.org`, `.io`, or other TLD variants
   - Blog/help subdomains (blog.xxx.com, help.xxx.com)
   - Partner/affiliate portals (xxx.com/affiliate, partner.xxx.com)
4. **Navigate via the accessible site's footers/links** to find the blocked domain's info:
   - Footer "Other products" links to sister sites (bidirectional)
   - Affiliate program pages often mention all companies' products
   - About/press pages list subsidiaries

### Real-world example

This technique was used to research Saily.com (eSIM + US phone number, owned by Surfshark B.V./Nord Security):

| Target | Status | Approach |
|---|---|---|
| `saily.com` | ❌ Cloudflare managed — StealthyFetcher loops, browser shows "Just a moment..." | Direct access impossible |
| `surfshark.com` | ✅ No Cloudflare — loaded instantly | Navigated normally |
| `surfshark.com/affiliate` | ✅ Loaded fully — showed 40% commission, 30-day cookie, $100 min | Found core data |
| `surfshark.com/affiliate-terms-and-conditions` | ✅ Full legal text — confirmed Saily NOT in listed affiliate products | Retrieved via curl |
| `surfshark.com/about-us` | ✅ 4,000万+ downloads, 500+ employees, $1.6B unicorn valuation | Key growth data |
| `surfshark.com/transparency-report` | ✅ 361K DMCA requests Q1 2026 | Operational scale signal |
| `surfshark.com/press` | ✅ FT 1000 fastest growing EU companies 2024/2025/2026 | Growth validation |

### Why it works

- Corporate parent sites (marketing, press, blog) are usually behind standard CDN caching or no Cloudflare at all
- New/niche brands (like Saily eSIM) get aggressive protection because they're newer and under active development
- The parent company's footer navigation links to all subsidiaries — you can browse the blocked sister company's product info without ever hitting its domain

### What to look for once inside a sibling site

- **Footer**: "Other products", "Our brands", "Sister companies" links
- **About / press page**: Subsidiary list with descriptions and launch dates
- **Affiliate terms**: Which products are listed in the affiliate program
- **Trust / transparency center**: Audit certifications, data handling, security standards (applicable to all subsidiaries)
- **Blog press releases**: Announcements about sister product launches

---

## Step 7: Browser-based corporate site reconnaissance (complement to curl)

Some corporate sites are Next.js/SPA apps where curl returns a shell and the real content requires JS rendering. In these cases, use the **browser tools** (browser_navigate, browser_snapshot, browser_console) as a complementary approach:

```javascript
// In browser_console — find hidden PDF/download links
Array.from(document.querySelectorAll('a'))
  .filter(a => a.textContent.trim() === 'Read more')
  .map(a => ({text: a.textContent.trim(), href: a.href, parentText: a.parentElement?.textContent?.trim()?.substring(0, 200)}))
```

```javascript
// Find links containing keywords
Array.from(document.querySelectorAll('a'))
  .filter(a => a.textContent.toLowerCase().includes('impact') || a.textContent.toLowerCase().includes('full'))
  .map(a => ({text: a.textContent.trim(), href: a.href}))
```

```javascript
// Extract the current page URL
window.location.href
```

**Pages worth checking on corporate sites:**
- `/trust-center` or `/trust` — Security, technology, audits, and transparency tabs
- `/transparency-report` — Government data request volumes (not user counts, but operational scale signal)
- `/press` or `/media-center` — Awards, press releases, media assets
- `/blog` — Search for "impact report", "annual", "wrap-up", "year in review"
- `/about` or `/about-us` — Company overview (may be present in footer even if not in nav)
- PDFs at `/media/` — Annual wrap-ups and impact reports (e.g., `/media/Surfshark_Annual_Wrap-up_2025.pdf`)

**Browser-first navigation pattern for SPA sites:**
1. `browser_navigate(url)` — loads the page with JS execution
2. `browser_snapshot(full=true)` — get accessibility tree with all interactive elements
3. Click tabs/sections to reveal hidden content panels
4. `browser_console(expression="...")` — extract specific elements, links, or data from the rendered DOM
5. For PDF downloads, extract the URL from the console, then use `terminal()` with `curl` to download and `pymupdf` to parse

## Step 8: Download and parse corporate PDFs

Annual reports, wrap-ups, and impact reports are often published as PDFs. These can contain employee counts, server infrastructure data, and operational metrics (but rarely revenue for private companies):

```bash
# Download
curl -sL "https://company.com/media/Annual_Wrap-up_2025.pdf" -o /tmp/report.pdf

# Extract text (using pymupdf via uv in this environment)
uv run python3 -c "
import pymupdf
doc = pymupdf.open('/tmp/report.pdf')
for page in doc:
    print(f'--- Page {page.number + 1} ---')
    print(page.get_text())
"
```

**What to look for in annual wrap-up PDFs:**
- Employee headcount and demographics
- Server count / infrastructure scale
- YouTube or social media subscriber counts
- Partnership or grant numbers
- Any "users" references (usually vague like "growing user base")
- Revenue is almost never disclosed for private companies

## Pitfalls

- **Cloudflare on main domains**: saily.com, surfshark.com, hvmn.com all block curl. The press release subdomains (finance.yahoo.com, nordsecurity.com/press-area/) usually don't.
- **HTML-only extraction is messy**: Yahoo Finance page download is ~260KB of JS/infra code with the actual article embedded as JSON in a `<script>` tag. Search for `"headline"`, `"datePublished"`, `"text"` patterns inside the raw HTML.
- **Multiple date formats**: The same article may have `publishDate`, `displayDate`, `datePublished`, and `dateModified` — compare against the actual article headline for correctness.
- **No specific user/ARPU numbers**: Press releases rarely disclose specific user counts or revenue. "Exceeding targets" is the typical language. If you need hard numbers, look for external analyst reports or investor filings.
- **Private companies don't publish revenue or user numbers** — This is especially true for privacy-focused companies (VPNs, security tools) whose entire brand identity is around not tracking users. Dashboards, wrap-ups, and impact reports for these companies will contain employee counts, server counts, and ESG metrics but explicitly omit user counts and revenue. Don't expect to find them; plan research accordingly.
- **Annual wrap-up PDFs may not be downloadable from restricted environments** — PDF hosts sometimes block connections from cloud/Docker IP ranges. Try `curl` first; if it times out, try `browser_navigate` directly to the PDF URL; if both fail, note the limitation.
- **Verify CEO title changes**: Maknickas was "Head of Product Strategy" (March 2024) then "CEO of Saily" (September 2024) — titles change. Always check the date on the source.
- **DuckDuckGo Lite still can get blocked**: If Lite also returns CAPTCHA, try Google News RSS: `https://news.google.com/rss/search?q=<terms>&hl=en-US&gl=US&ceid=US:en`
- **Transparency reports ≠ business data**: A transparency report shows government data request volumes (DMCA, warrants, subpoenas), not user counts or revenue. High DMCA request volumes can indicate a large user base indirectly, but it's not a reliable proxy.
- **Browser click may not navigate on SPA sites** — In some cases, clicking a link on a SPA site via the browser tool reports success but the URL doesn't change. Always verify navigation with `browser_console(expression="window.location.href")` after clicking. If the URL didn't change, extract the href directly via console and navigate to it explicitly.
