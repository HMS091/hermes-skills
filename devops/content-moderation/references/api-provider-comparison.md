# Content Moderation API Provider Comparison

## Overview

Comparison of major AI content moderation APIs for the JustFans platform. Covers NSFW image/video, text moderation, political sensitivity, and age verification.

## Detailed Comparison

| Feature | Sightengine | Azure Content Safety | AWS Rekognition | Google Vision | OpenAI Moderation |
|---------|-------------|---------------------|----------------|---------------|-------------------|
| **NSFW Image** | ✅ Best (nudity + sexual activity breakdown) | ✅ Good | ✅ Good | ✅ Good | ⚠️ Text only |
| **NSFW Video** | ✅ Frame-by-frame | ❌ Partner product needed | ✅ Per-frame | ✅ Per-frame | ❌ |
| **Text Moderation** | ✅ Also does text | ✅ Best for text | ❌ | ❌ | ✅ Free with API |
| **Political Sensitivity** | ⚠️ Limited | ✅ Best (Chinese content) | ❌ | ❌ | ❌ |
| **Underage Detection** | ✅ Age 0-4/5-12/13-17/18+ | ✅ | ✅ | ✅ Age range | ❌ |
| **Chinese Language** | ⚠️ Partial | ✅ Full support | ❌ | ⚠️ | ❌ |
| **OCR in Images** | ✅ Text extraction | ❌ | ✅ | ✅ | ❌ |
| **Hate Symbols** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Weapons Detection** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Alcohol/Drugs** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Gore/Violence** | ✅ | ✅ | ✅ | ✅ | ✅ |

## Pricing (as of 2026)

### Sightengine
| Plan | Price | Calls/mo | Features |
|------|-------|----------|----------|
| Developer | Free | 4,000 | All models, watermark |
| Growth | $49/mo | 30,000 | All models, no watermark |
| Business | $149/mo | 150,000 | All models, priority support |
| Enterprise | Custom | Unlimited | SLA, dedicated |

**Pay-as-you-go**: ~$0.001-0.003 per image (volume pricing)
**Video pricing**: $0.02/min of video

### Azure Content Safety
| Tier | Price | Calls/mo | Features |
|------|-------|----------|----------|
| Free | $0 | 5,000 transactions | 1 transaction/sec |
| Standard | $0.001/call text, $0.001/image | Pay-as-you-go | 1000 req/min |

**Text moderation**: ~$0.001 per 1000 characters
**Image moderation**: ~$0.001 per image

### AWS Rekognition
| Feature | Price |
|---------|-------|
| Image moderation | $0.001 per image |
| Video moderation | $0.10 per minute |
| Free tier | 5,000 images/mo for 12 months |

### Google Cloud Vision
| Feature | Price |
|---------|-------|
| SafeSearch Detection | $1.50 per 1000 images (first 1000 free/mo) |

### OpenAI Moderation (Text Only)
| Feature | Price |
|---------|-------|
| Free | ✅ No cost with API usage |
| Coverage | Hate, harassment, self-harm, sexual, violence |

## Recommendation for JustFans

### Launch Phase (<$50/mo budget)
```
Primary: Sightengine Free (4,000 calls/mo)
Fallback: Azure Content Safety Free (5,000 calls/mo)
Text: OpenAIModeration (free)
Cost: ~$0/mo for first ~3,000 users
```

### Growth Phase ($50-150/mo budget)
```
Primary: Sightengine Growth ($49/mo, 30,000 calls)
Text: Azure Content Safety (pay-as-you-go)
Video: Sightengine video ($0.02/min)
Cost: ~$50-80/mo
```

### Scale Phase ($200+/mo budget)
```
Primary: Sightengine Business ($149/mo, 150,000 calls)
Text: Azure Content Safety
Video: AWS Rekognition (cheaper than Sightengine for video)
Cost: ~$150-200/mo
```

## Key Decision Factors

### If your platform has Chinese users or is hosted in China
**Azure Content Safety** is the only provider with strong Chinese political content moderation. Pair with Sightengine or AWS for NSFW.

### If your platform is US-only and has no political content concerns
**Sightengine** alone is sufficient. Best NSFW accuracy, reasonable pricing.

### If you need maximum accuracy for borderline content
Use **both Sightengine and Azure** in ensemble: if both flag it → auto-block. If only one flags it → manual review. This reduces false negatives at the cost of double API calls.

## API Integration

### Sightengine PHP SDK
```php
// No official PHP SDK, use cURL
$ch = curl_init('https://api.sightengine.com/1.0/check.json');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POSTFIELDS => [
        'media' => ['url' => $imageUrl],
        'models' => ['nudity' => true, 'weapon' => true, 'offensive' => true],
        'api_user' => $apiUser,
        'api_secret' => $apiSecret,
    ],
]);
```

### Azure Content Safety PHP
```php
use GuzzleHttp\Client;

$client = new Client();
$response = $client->post('https://{region}.api.cognitive.microsoft.com/contentmoderator/moderate/v1.0/ProcessImage/Evaluate', [
    'headers' => ['Ocp-Apim-Subscription-Key' => $key],
    'json' => ['DataRepresentation' => 'URL', 'Value' => $imageUrl],
]);
```

## NSFW Score Interpretation

Different APIs return different score ranges. This table normalizes them:

| Meaning | Sightengine `nudity.raw` | Azure `AdultScore` | AWS `Explicit` | Google `Adult` |
|---------|------------------------|-------------------|----------------|----------------|
| Safe (clothed) | 0-0.15 | 0-0.15 | NOT_EXPLICIT | VERY_UNLIKELY |
| Suggestive (bikini/swim) | 0.15-0.45 | 0.15-0.35 | — | UNLIKELY |
| Artistic nudity | 0.45-0.65 | 0.35-0.55 | — | POSSIBLE |
| Explicit (sexual) | 0.65-1.0 | 0.55-1.0 | EXPLICIT | LIKELY/VERY_LIKELY |

## Response Time Benchmarks

| Provider | P50 | P95 | Notes |
|----------|-----|-----|-------|
| Sightengine | 800ms | 2.5s | Fastest for single image |
| Azure Content Safety | 1.2s | 3.0s | |
| AWS Rekognition | 1.0s | 2.8s | |
| Google Vision | 900ms | 2.0s | |

## Fallback Strategy

When API is down or rate-limited:

```php
function moderateWithFallback(string $imageUrl): array
{
    // Try primary
    try {
        return SightengineService::check($imageUrl);
    } catch (Exception $e) {
        Log::warning('Sightengine failed, falling back to Azure', ['error' => $e->getMessage()]);
    }
    
    // Try fallback
    try {
        return AzureModerationService::check($imageUrl);
    } catch (Exception $e) {
        Log::error('All moderation APIs failed, auto-flagging', ['error' => $e->getMessage()]);
        return ['action' => 'flag', 'reason' => 'api_unavailable'];
    }
}
```

**Never auto-approve on API failure.** Always flag for manual review.
