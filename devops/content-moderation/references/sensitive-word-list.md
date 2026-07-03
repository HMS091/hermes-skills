# Sensitive Word List for L1 Quick Filter

This file provides the base sensitive word list for the L1 quick filter layer. Customize for your platform's risk profile.

## Usage

Place in `config/sensitive-words.php` in your Laravel app:

```php
<?php
return [
    'banned' => [
        // Exact-match banned words (block immediately)
    ],
    'flagged' => [
        // Words that require manual review (block temporarily)
    ],
    'political' => [
        // Chinese political sensitive terms (for GFW compliance)
    ],
];
```

## Category 1: Immediate Ban (Exact Match → Block)

### NSFW / Prohibited Content
```
child|children|minor|teen|underage
cp|loli|shota|jailbait
rape|incest|snuff
revenge porn|exposed|leaked|private|stolen
under 18|u18|未成年
```

### Drug / Weapons / Violence
```
buy drugs|sell drugs|cocaine|heroin|meth|fentanyl
weapon for sale|gun sale|ammo
kill|murder|assassinate
terrorism|bomb|explosive
```

### Spam / Platform Abuse
```
free onlyfans|free subscription bypass
hack|crack|stripe bypass
paypal hack|credit card hack
```

## Category 2: Flag for Review (Block → Manual Review)

### Borderline Sexual
```
sex|adult|nude|naked|xxx|porn|erotic
fetish|bdsm|kink|dominatrix
sugar daddy|sugar baby|escort
cam girl|cam show|live sex
custom video|custom content|private request
```

### Harassment / Hate Speech
```
die|kill yourself|suicide
racial slurs (n-word, etc.)
hate speech patterns
```

## Category 3: Chinese Political Sensitive Words (政治敏感词)

### Core banned terms (for GFW compliance / Chinese VPS)

> ⚠️ **Important**: This list is for platform safety compliance on Chinese VPS or for Chinese-language content moderation. The actual list evolves. These are patterns, not an exhaustive list.

```
// Leadership names — context-dependent
// Names of specific current national leaders (banned if used in negative context)

// Prohibited topics
falun|faliun|falungong|法轮
tibet independence|xizang independence
taiwan independence|台独
xinjiang|east turkistan
tiananmen|六四|64
democracy movement|freedom party
chinese communist party|ccp negative
human rights china
china political prisoner
velvet revolution|color revolution
hk independence|香港独立

// Chinese app/platform names that indicate spamming
wechat group|qq group invite  # If posted excessively
```

### Policy for Chinese Content

- **Hosted on Chinese VPS (Tencent Cloud/Alibaba)**: Must filter aggressively. Missing political content = hosting terminated.
- **Hosted on overseas VPS (Hetzner) serving US audience**: Less strict but still filter Chinese-language chat for political content if your platform has Chinese-speaking users.
- **For JustFans targeting US market**: Primary focus is NSFW/sexual content for Stripe/PayPal compliance. Political filtering is secondary.

## Category 4: URL / Link Blacklist

```
// Competitor platforms (users promoting rival sites)
onlyfans.com
fansly.com
patreon.com
（any competing creator platform）

// Phishing/scam links
bit.ly (shortened links without context)
// Any URL not from your own domain should be flagged
```

## Implementation Notes

### Hash-based Deduplication

Store SHA256 hash of each moderated file. If the exact same file is re-uploaded, apply the previous moderation decision instantly:

```php
// In ModerationJob
$hash = hash_file('sha256', $filePath);
$previous = Media::where('file_hash', $hash)
    ->whereNotNull('moderation_status')
    ->first();

if ($previous && $previous->moderation_status !== 'approved') {
    // Apply same decision
    $this->media->update([
        'moderation_status' => $previous->moderation_status,
        'moderation_reason' => $previous->moderation_reason,
        'moderation_data' => $previous->moderation_data,
    ]);
    return;
}
```

### False Positive Reduction

Use word-boundary matching:

```php
function wordBoundaryMatch(string $text, string $word): bool {
    return preg_match('/\b' . preg_quote($word, '/') . '\b/ui', $text) === 1;
}
```

### Wildcard / Fuzzy Matching

```php
function fuzzyMatch(string $text, string $pattern): bool {
    $regex = '';
    for ($i = 0; $i < mb_strlen($pattern); $i++) {
        $char = mb_substr($pattern, $i, 1);
        $regex .= preg_quote($char, '/') . '[^a-z0-9]{0,2}';
    }
    return preg_match("/{$regex}/ui", $text) === 1;
}
```

### Performance

- Keep the L1 word list in memory (Redis cache or PHP array).
- For 500 words, regex matching takes <1ms on modern hardware.
- For 5,000+ words, use Aho-Corasick trie algorithm for O(n) matching.
- Laravel's `Str::contains()` with array is O(n*m) — slow for large lists.

Recommended:
```php
// Install: composer require patrickschur/language-detection OR trie implementation
```

## Regular Maintenance

- Review false positives weekly from your moderation logs
- Add new patterns based on actual violations observed
- Update political sensitive word list quarterly (Chinese regulations change)
- Review competitor promotion patterns monthly
