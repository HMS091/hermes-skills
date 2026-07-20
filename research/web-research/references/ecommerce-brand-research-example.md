# E-Commerce Brand Research Worked Example: BIOAQUA (泊泉雅)

## Context

User wanted to research whether they could sell BIOAQUA face masks overseas. They asked for: brand reputation, sales volume, pricing, number of sellers, social media presence, advertising. This reference documents the investigation workflow and findings.

## Brand Identity

| Field | Value |
|-------|-------|
| **Name** | BIOAQUA (also spelled "bioaoua" — domain name) |
| **Chinese name** | 泊泉雅 |
| **Domain** | bioaoua.com |
| **Site type** | WordPress + WooCommerce **B2B wholesale/OEM platform** |
| **SEO title** | "Bioaqua Skincare Products Wholesale OEM Manufacture" |
| **Actual nature** | Chinese factory selling OEM/ODM private label skincare, NOT a consumer brand |

## Platform-by-Platform Results

### Amazon US

- **Search term**: "bioaqua face mask" (Amazon autocorrects "bioaoua" → "bioaqua")
- **Results**: 80+ listings
- **Pricing**: All face masks at ¥108.24 CNY (~$15 USD), 4-8 packs
- **Ratings**: 2 to 89 ratings per product (extremely low)
- **"Bought in past month"**: None of the BIOAQUA products showed this badge
- **Best Seller badges**: 0 for BIOAQUA products (competitors like BIODANCE had them)
- **Seller count**: 1-2 offers per product, very few sellers
- **Sponsored ads**: BIOAQUA had NO sponsored ads; competitors ran heavy ad campaigns

### Brand Website (bioaoua.com)

- WordPress site with WooCommerce store
- Product categories include: face masks, serums, body scrubs, eye masks, lip masks, shampoo, body wash, concealer, creams
- Key strings: "Private Label", "Custom LOGO", "ODM OEM", "Factory price", "Wholesale"
- Contact method: WhatsApp (direct B2B chat)
- SEO optimized for wholesale/reseller search

### Cross-Platform Results

| Platform | Status | Finding |
|----------|--------|---------|
| **eBay** | ❌ Blocked | Error page |
| **AliExpress** | ❌ Timeout | No data |
| **TikTok** | ❌ No results | Zero brand presence |
| **Instagram** | ❌ Timeout | @bioaoua_official has no content |
| **YouTube** | ❌ No results | Zero reviews/unboxings |
| **Trustpilot** | ❌ No results | Zero customer reviews |
| **Walmart** | ❌ Blocked (CAPTCHA) | No detectable presence |
| **Reddit** | ❌ No mentions | Zero community discussion |

## Key Insights

1. **Brand ≠ consumer brand**: The official website reveals BIOAQUA is a factory/OEM supplier, not a brand with consumer marketing. Amazon listings are likely small resellers buying from this factory.

2. **Sales are near-zero**: No "bought in past month" badge, maximum 89 reviews per product (most 2-17), no Best Seller badges — these products have negligible sales velocity compared to competitors doing 100K+/month.

3. **No overseas marketing investment**: Zero social media presence + zero influencer reviews + zero sponsored Amazon ads = the brand has no overseas marketing strategy at all.

4. **Competitor landscape is brutal**: BIODANCE (43,542 ratings, 100K+/month), ZealSea (7,602 ratings, 6K+/month), FACETORY (217 ratings) — all heavily advertise on Amazon.

## Report Structure Used

1. 品牌概况 — Brand overview table
2. Amazon销售数据（核心）— Search results, ratings analysis, sales velocity, Best Seller count
3. 价格分析 — Product pricing table vs competitors
4. 销售渠道分布 — Platform-by-platform presence table
5. 社媒和广告投放情况 — Social media summary
6. 品牌定位真相 — Key insight: factory, not brand
7. 市场评估与风险 — Pros/cons/risks
8. 建议方向 — Options table with estimated investment levels

## Tools & Commands Used

```bash
# Brand website analysis
curl -sL --max-time 15 "https://bioaoua.com" | head -300

# Amazon search
browser_navigate(url="https://www.amazon.com/s?k=bioaoua+face+mask+sheet")

# Read cached browser snapshots for product details
read_file(path="/opt/data/cache/web/browser-snapshot-*.txt", offset=1, limit=500)

# Multi-platform cross-reference (each in parallel)
curl -sL "https://www.ebay.com/sch/i.html?_nkw=bioaoua"
curl -sL "https://www.walmart.com/search?q=bioaoua"
curl -sL "https://www.trustpilot.com/search?query=bioaoua"
curl -sL "https://www.youtube.com/results?search_query=bioaoua"
```

## Pitfalls Encountered (6 types)

1. **Amazon currency display**: Prices shown in CNY because delivery address = China. Divide by ~7.0 for USD estimate.
2. **Amazon autocorrect**: "bioaoua" → "bioaqua" — must click "Search instead for bioaoua" to verify exact spelling results.
3. **Browser timeout**: TikTok, Instagram, AliExpress all timed out → used curl instead or noted as unavailable.
4. **Competitor noise in search results**: Amazon intersperses sponsored competitor ads (BIODANCE, FACETORY, ZealSea) within BIOAQUA results. These are NOT the brand's products.
5. **B2B site misidentification**: The official site looks like a consumer brand at first glance but the SEO title and product page keywords reveal it's an OEM factory. Must read `<title>` and meta descriptions, not just the homepage hero image.
6. **False positive from product count**: 80+ results sounds like established brand presence, but zero "bought in past month" badges across all listings means actual sales are near-zero.
