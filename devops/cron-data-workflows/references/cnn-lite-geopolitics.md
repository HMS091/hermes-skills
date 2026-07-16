# CNN Lite Geopolitics & Economy Extraction (Cron Job Source)

**Source:** `https://lite.cnn.com/` (also works for individual article URLs: `https://lite.cnn.com/2026/07/15/economy/...`)
**Reliability:** ★★★★★ — no Cloudflare, no CAPTCHA, clean accessibility tree
**Best for:** Geopolitical context, Fed/monetary policy, economic data (GDP, PPI, CPI), China trade data, and analyst commentary for daily briefings. Richer than headline-only sources — provides **full article text** with specific data points and analyst quotes.

## Two-Level Extraction Pattern

CNN Lite provides value at two depths: headline scanning (fast) and full article extraction (rich).

### Level 1: Front-Page Headline Scanning (30s)

Navigate to `https://lite.cnn.com/` and grep the snapshot for keywords:

```python
browser_navigate("https://lite.cnn.com/")
# Keywords: Iran, Middle East, oil, crude, strike, sanctions, Fed, Fed minutes,
# Federal Reserve, tariff, trade, NATO, China, tariffs, inflation, Ukraine, Russia,
# OPEC, semiconductor, chip, EV, electric, auto, economy, GDP, PPI, CPI
```

### Level 2: Full Article Extraction (60-90s per article)

This is the **real value** of CNN Lite — individual article pages serve **full-text content** with no paywall, no JS rendering, no Cloudflare. Each article gives you specific data points, analyst quotes, and expert commentary that directly feeds the briefing sections.

#### Step 1: Find article links

From the front page, extract article URLs by category:

```bash
# Extract all economy/business article links
curl -sL https://lite.cnn.com | grep -oP 'href="/2026/[^"]*(economy|business|tech)[^"]*"' | head -10
# → /2026/07/15/economy/fed-chairman-kevin-warsh-senate-testimony
# → /2026/07/15/economy/us-ppi-wholesale-inflation-june
# → /2026/07/14/business/china-q2-gdp-export-economy-intl-hnk
```

Or via browser snapshot, look for `link` elements with href paths containing `economy`, `business`, or `tech`. The pattern is: `/{year}/{month}/{day}/{category}/{slug}`.

#### Step 2: Click through or curl to get full text

```bash
# Browser: click the link
browser_click(ref="@e5")  # click the anchor

# OR curl (faster, no browser overhead):
curl -sL --connect-timeout 10 "https://lite.cnn.com/2026/07/15/economy/us-ppi-wholesale-inflation-june" \
  -H "User-Agent: Mozilla/5.0" | sed 's/<[^>]*>//g' | grep -v '^[[:space:]]*$'
```

#### Step 3: Extract content blocks

The full-text page has a recognizable structure. Strip HTML tags and extract:

| Section | What to Look For | Example from PPI article |
|---------|-----------------|--------------------------|
| **Title** | `<h1>` or the line after the date | "Wholesale inflation improved as energy prices fell last month" |
| **Byline** | "By [Author], CNN" | "By Elisabeth Buchwald, CNN" |
| **Lead** | First paragraph after byline | "Inflation at the wholesale level cooled last month..." |
| **Key Data** | Numbers with % signs or $ amounts | "PPI slowed at a 5.5% pace in June... 12% drop in gasoline... core PPI 4.6%" |
| **Analyst Quote** | "X, Y at Z, said in a note" | "Energy saved the day in June, but that might become ancient history if the Strait of Hormuz doesn't open soon" — David Russell, TradeStation |
| **Policy Context** | Fed chair/ policymaker quotes | "It's one data point... That is not my view" — Fed Chair Kevin Warsh |
| **Second-Order Impact** | What this means for other sectors | "semiconductor chip prices... jumped by 2.5% in one month. Apple recently announced 10% to 15% price hikes" |

### Content Type by Article Category

Different CNN Lite categories yield different briefing material:

| Category | What You Get | Briefing Section |
|----------|-------------|------------------|
| `/economy/` | PPI/CPI data with analyst quotes, Fed testimony transcripts, job market data, trade policy | macro环境 + 利率预期 |
| `/business/` | China GDP, oil markets, corporate earnings, supply chain disruptions, trade wars | macro环境 + all three assets |
| `/tech/` | AI regulation, cybersecurity, chip shortages, tech company news | 🖥️ 英伟达 + macro环境 |
| `/energy/` | Oil prices, renewable energy, EV transition context | macro环境 + 🚗 特斯拉 + 🥇 黄金 |
| `/politics/` | Fed appointments, tariffs, sanctions, regulatory policy | macro环境 |

## Extractable Data Points (Real Examples from July 2026)

These are the **specific data points** you can extract from CNN Lite articles and use directly in the briefing:

### From PPI Articles
- Current PPI rate: 5.5% YoY (June), vs prior 6.0%
- Monthly change: -0.3% in June vs +0.6% in May
- Goods prices: -1.4% (largest fall in 4 years)
- Gasoline: -12% (accounted for 2/3 of index decline)
- Core PPI: 4.6% vs 4.9% prior
- Semiconductor chips: +2.5% in one month (driven by AI demand)
- Consumer impact: Apple 10-15% price hikes on products due to memory chip shortages
- Oil context: crude settled as high as $114/barrel in May (from China GDP article)

### From Fed Testimony Articles
- Fed Chair stance: "It's one data point" — dismisses single CPI/PPI improvement
- Political dynamics: Warren vs Warsh confrontation, Bowman blackout-period scandal
- Ethics questions: Warsh-Druckenmiller relationship, $100M divestiture demands
- Rate trajectory signal: Warsh says not "mission accomplished" — hawkish lean

### From China GDP Articles
- Q2 GDP: 4.3% vs 4.5% expected — first miss since COVID
- Exports: +27% in Q2 (semiconductors, computer parts, EVs)
- Retail sales: +1% YoY in June (weak consumption)
- Property investment: -18% in H1 2026
- Fixed asset investment: -5.7%
- Car exports: surpassed 1M/month for first time in June
- Trade surplus: $125.62B in June
- Oil imports: -41.3% YoY (near decade low)
- IMF: upgraded China 2026 forecast to 4.6% from 4.4%
- US-China: exports to US +26% in June after Trump Beijing visit

### From Iran/Geopolitics Articles
- Strait of Hormuz status: blocked/choked
- US-Iran military strikes resumed
- IMF warning: "renewed Middle East conflict looms large... extend commodity price volatility"

## Keywords-to-Section Mapping

| Keyword | Briefing Section |
|---------|-----------------|
| Iran, sanctions, oil, Middle East, Strait of Hormuz | 宏观环境 + 🥇 黄金 |
| Fed, Federal Reserve, inflation, rate, Warsh, Powell, Bowman | 宏观环境 |
| tariff, trade, USMCA, China, EU trade | 宏观环境 |
| NATO, defense, military | 宏观环境 |
| AI, semiconductor, chip, Nvidia/NVDA, GPU, data center | 🖥️ 英伟达 |
| EV, electric, Tesla, auto, tariff, battery | 🚗 特斯拉 |
| Apple, memory chip, price hike | 🖥️ 英伟达 (supply chain impact) |
| crude, oil price, gasoline, energy, barrel | 宏观环境 (cross-ref to gold) |
| GDP, PPI, CPI, jobs, unemployment, consumer | 宏观环境 |

## Pipeline Workflow for Daily Briefings

```
1. Navigate lite.cnn.com → scan for relevant headlines (30s)
2. Extract article URLs for economy/business/tech/energy (15s)
3. curl each article → get full text with data + quotes (3 × 30s = 90s parallel)
4. Map extracted data to briefing sections:
   - PPI numbers + analyst quotes → 宏观环境 section
   - Fed/political content → 宏观环境 (rate outlook + policy risk)
   - China GDP + trade data → 宏观环境 + 🚗 特斯拉 (EV exports)
   - AI chip price + memory shortage → 🖥️ 英伟达
   - Iran/oil → 🥇 黄金 + 宏观环境
5. Integrate data points into the template
```

## Advantages Over Other Sources

| Compared To | Why CNN Lite Wins |
|-------------|------------------|
| Google News RSS | Full article text (not just headlines); structured data with quotes |
| Yahoo Finance | No consent wall; no JS rendering; works from datacenter IPs |
| CNBC RSS | Economy content is richer (Fed transcripts, full PPI analysis) |
| MarketWatch | No Cloudflare; deeper economic analysis articles |
| Reuters | Same accessibility pattern; CNN Lite articles are more concise for quick extraction |

## Limitations

- Only shows ~50 most recent headlines on front page (not searchable)
- Article selection is CNN editorial — may miss some ticker-specific news (NVDA/TSLA specifically tend to be absent unless it's a major market-moving event)
- **CNN Lite lacks tech-company-specific coverage** — you won't find NVDA or TSLA earnings reports, analyst upgrades, or product launch articles here. Use Google News RSS or Seeking Alpha RSS for per-ticker news.
- No price/market data (purely news)
- US-centric news perspective (acceptable for US market-focused briefings)
- CNN Lite is primarily useful for **macro/economy/geopolitics** sections of the briefing, not for ticker-specific analysis
