# App Store Review Analysis: Methodology & Worked Example

## Purpose

When a user asks "what do real users think of this app?", the goal is to extract **genuine user reviews** (not just aggregate ratings) from the App Store RSS API, classify them by sentiment, and identify recurring themes in complaints and praise.

## Workflow

### Step 1: Find the App Store track ID

```bash
# Search by app name + country
curl -sL "https://itunes.apple.com/search?term=APP+NAME&country=JP&entity=software&limit=5"
```

Key fields from response:
- `trackId` → the app ID for reviews API (NOT `artistId`)
- `bundleId` → reverse-domain identifier, reveals original brand name
- `trackName` → current app store listing name (may differ from brand)
- `averageUserRating` + `userRatingCount` → overall rating context
- `description` → full App Store listing text (business model, features, pricing)

### Step 2: Fetch the 50 most recent reviews

```bash
curl -sL "https://itunes.apple.com/jp/rss/customerreviews/page=1/id={trackId}/sortBy=mostRecent/json?l=en"
```

### Step 3: Parse and classify

Parse with python, skip the app entry itself (has `im:name` label = "iTunes Store"), then group by rating:
- **Good (4-5★)**: users who succeeded or were satisfied
- **Bad (1-2★)**: users who had problems, complaints
- **Mixed (3★)**: nuanced/neutral

### Step 4: Extract recurring themes

Scan bad reviews for repeated keywords/patterns (e.g., "审査"/"approval", "キャンセル"/"cancel fee", "サポート"/"support", "自動更新"/"auto-renew").

### Step 5: Write structured Chinese report

Format:
1. Overall distribution (good/bad/mixed counts)
2. Good reviews summary (with excerpts)
3. Bad reviews — each recurring theme as a section with example excerpts
4. Conclusion table for quick reference

## Pitfalls

- **Sort-by trap**: Only `sortBy=mostRecent` works; `mostHelpful` returns 0 entries
- **Page limit**: Only page=1 returns results; pages 2+ return empty arrays
- **50 review cap**: Regardless of total rating count (e.g., 11K ratings → still only 50 reviews via RSS)
- **Rebranding skew**: If the app recently rebranded or had a controversial update, the most recent 50 reviews can be 76% negative while the overall rating (3.86/5 from 11K reviews) is pulled up by older, more positive reviews. Always note this discrepancy.
- **Truncation**: Review content is ~600 chars max in the API response
- **No reviewer name**: `author.name` is empty — Apple anonymizes
- **Timezone**: Dates are US Pacific (`-07:00`), not local to the App Store country
- **Same bundleId keeps old reviews**: Even if the app rebrands (Dine→D³ with same `co.dinewith.Dine` bundleId), old reviews remain attached to the listing

## Worked Example: Dine/D³ (日本マッチングアプリ)

**Search query:**
```bash
curl -sL "https://itunes.apple.com/search?term=Dine&country=JP&entity=software&limit=5"
```

**Result:** trackId=964735828 (NOT artistId=964735827), bundleId=`co.dinewith.Dine`

**Business model from App Store description:**
- ¥2,900/month subscription
- Two services: matching app + shared seating lounge (相席ラウンジ)
- Works with Oriental Lounge and ag lounges in Tokyo, Osaka, Nagoya, Fukuoka, Sapporo
- Safety: mandatory ID verification, credit card for no-show prevention, 24/7 monitoring

**50 most recent reviews analysis:**
- 76% 1-2★, 12% 4-5★, 12% 3★
- Good: actually helped people get married, high-quality restaurant recommendations, decent user base in Tokyo
- Bad: recent "super downgrade" review system biased against men, unfair cancellation fees ($230+), terrible support, auto-renewal no-refund trap, gold-digger users, age filter broken, Tokyo-only effect
- Overall rating 3.86/5 from 11K ratings — misleadingly high due to legacy reviews

**Key business insight:** The mixed online+offline (matching app + physical lounge) model is unique and has no direct Chinese equivalent.
