---
name: content-moderation
description: "Build AI content moderation systems for user-generated content platforms (OnlyFans clones, social apps). Covers image/video NSFW detection, text sensitivity filtering, chat moderation, live stream frame analysis, and underage detection — with unsure→intercept→manual-review workflow and Laravel integration."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [content-moderation, nsfw-detection, safe-content, laravel, php, review-workflow, ai-moderation]
    related_skills: [web-research, business-project-evaluation, autonomous-freelancing]
---

# AI Content Moderation System

## Overview

Build a multi-layered AI content moderation system for user-generated content platforms (JustFans OnlyFans Clone, social apps, forums). Covers all content types with a **先拦截再人工** (intercept-first) policy when the AI is unsure.

**Target platform**: JustFans (Laravel PHP 8.2) on Linux VPS.

**Core principle**: Better to over-block and let manual review pass it, than to miss something that gets the platform shut down.

## When to Use

- Building an OnlyFans clone / subscription content platform that needs content safety
- Any platform where users upload images, videos, or send messages
- Platform needs to comply with US/EU content regulations (Stripe/PayPal require this)
- You need to filter Chinese political sensitive content AND Western NSFW content simultaneously
- Live streaming with real-time violation detection

## Architecture

```
User uploads content (image/video/text)
        │
        ▼
┌─────────────────────┐
│  Step 1: Quick Filter │  ← Local: sensitive word list, exact match
│  (~ms, no API cost)   │
└─────────┬───────────┘
          │ pass
          ▼
┌─────────────────────┐
│  Step 2: AI API     │  ← Sightengine / Azure / AWS Rekognition
│  (~1-3s, per-call $) │
└─────────┬───────────┘
          │ result
          ▼
    ┌─────┴─────┐
    │           │
  safe       suspect
    │           │
    ▼           ▼
  publish   ┌──────────────────┐
            │ Step 3: Queue    │  ← Teacher-in-the-loop (人工审核)
            │ for manual       │
            │ review           │
            └──────────────────┘
```

### Three Tiers

| Tier | Speed | Cost | Coverage | Used For |
|------|-------|------|----------|----------|
| **L1: Local Filter** | <10ms | Free | Broad, basic | Sensitive words, exact-match banned content |
| **L2: AI API** | 1-3s | $0.01-0.10/call | Images, text, video | Primary moderation decision |
| **L3: Manual Review** | 5-60min | Staff cost | Edge cases | AI unsure / appeal review |

## API Recommendations

### Primary Recommendation: Sightengine

| Feature | Sightengine | Azure Content Safety | AWS Rekognition |
|---------|-------------|---------------------|-----------------|
| **NSFW image** | ✅ Best-in-class | ✅ Good | ✅ Good |
| **NSFW video** | ✅ Frame-by-frame | ❌ Separate service | ✅ Per-frame |
| **Text moderation** | ✅ Also does text | ✅ Best for text | ❌ |
| **Political sensitivity** | ⚠️ Limited | ✅ Strong | ❌ |
| **Underage detection** | ✅ | ✅ | ✅ |
| **Chinese language** | ⚠️ Partial | ✅ Good CN support | ❌ |
| **Pricing (image)** | ~$0.01/call | ~$0.001-0.01 | ~$0.001 |
| **Free tier** | 4000 calls/mo | 5000 transactions/mo | 5000 images/mo |
| **API integration** | REST | REST + SDK | REST + SDK |

**Decision**: Use **Sightengine** as primary for image/video NSFW (best accuracy), pair with **Azure Content Safety** for text + Chinese political content.

### Sightengine Workflow Example

```php
// PHP integration for JustFans (Laravel)
$params = [
    'media' => [
        'url' => 'https://your-cdn.com/uploads/photo.jpg',
    ],
    'models' => [
        'nudity' => true,        // NSFW detection
        'weapon' => true,        // Weapons
        'offensive' => true,     // Hate symbols
        'text' => true,          // OCR text in image
        'selfie' => true,        // Age estimation
    ],
    'threshold_nudity_min' => 0.65,  // Sensitivity
];

$ch = curl_init('https://api.sightengine.com/1.0/check.json');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POSTFIELDS => $params,
    CURLOPT_USERPWD => "{$api_user}:{$api_secret}",
]);
$response = json_decode(curl_exec($ch), true);

// Decision logic
if ($response['status'] === 'success') {
    $nudity = $response['nudity']['raw'] ?? 0;
    $sexual_activity = $response['nudity']['sexual_activity'] ?? 0;
    
    if ($nudity > 0.85 || $sexual_activity > 0.7) {
        // BLOCK — explicit content
        $decision = 'blocked';
        $reason = 'explicit_nudity';
    } elseif ($nudity > 0.5 || $sexual_activity > 0.3) {
        // FLAG — unsure, send to manual review
        $decision = 'flagged';
        $reason = 'borderline';
        $confidence = max($nudity, $sexual_activity);
    } else {
        // ALLOW
        $decision = 'approved';
    }
}
```

## Content Type Workflows

### 1. Image Moderation

**Path**: User uploads → upload handler → moderation job → result

**In Laravel (JustFans)**:
```php
// app/Jobs/ModerateImage.php
class ModerateImage implements ShouldQueue
{
    public function handle(): void
    {
        // 1. L1: Local filter (file hash blacklist)
        if ($this->isBlacklistedHash($this->media->file_hash)) {
            $this->media->update(['status' => 'blocked', 'reason' => 'blacklisted']);
            return;
        }
        
        // 2. L2: AI API (via Sightengine or job queue)
        $result = SightengineService::check($this->media->url);
        
        if ($result['action'] === 'block') {
            $this->media->update(['status' => 'blocked', 'reason' => $result['reason']]);
        } elseif ($result['action'] === 'flag') {
            $this->media->update(['status' => 'pending_review', 'ai_score' => $result['confidence']]);
            AdminNotification::dispatch('New flagged content', $this->media);
        } else {
            $this->media->update(['status' => 'active']);
        }
    }
}
```

**JustFans-specific integration points**:
- `app/Http/Controllers/MediaController.php` — upload handler
- `app/Models/Media.php` — add `status` and `moderation_data` columns
- `app/Jobs/` — queue jobs for async moderation
- `database/migrations/` — add moderation fields to media table

### 2. Video Moderation

**Strategy**: Extract key frames, moderate each frame

```php
// FFmpeg frame extraction
$cmd = "ffmpeg -i {$videoPath} -vf fps=1/5 -frames:v 20 /tmp/frames/frame_%03d.jpg";
exec($cmd);

// Moderate each frame
$frames = glob('/tmp/frames/*.jpg');
$violations = [];
foreach ($frames as $frame) {
    $result = SightengineService::check("file://{$frame}");
    if ($result['action'] !== 'allow') {
        $violations[] = $result;
    }
}

// Decision: if >30% frames flagged, block video
$violationRate = count($violations) / count($frames);
if ($violationRate > 0.3) {
    $this->media->update(['status' => 'blocked', 'reason' => 'video_nsfw']);
}
```

### 3. Text / Chat Moderation

**Two-layer approach**:

```php
// L1: Local sensitive word list (fast, free)
class TextFilter
{
    private array $patterns = [
        '/\b(specific+banned+terms)\b/i',
        // Custom Chinese political sensitive word list
        // Load from config/sensitive-words.php
    ];
    
    public function quickFilter(string $text): ?string
    {
        foreach ($this->patterns as $pattern) {
            if (preg_match($pattern, $text, $m)) {
                return 'matched: ' . $m[0];
            }
        }
        return null; // clean
    }
}

// L2: AI semantic analysis (Azure Content Safety)
class AITextModeration
{
    public function analyze(string $text): array
    {
        $response = Http::withHeaders([
            'Ocp-Apim-Subscription-Key' => config('azure.key'),
        ])->post('https://{region}.api.cognitive.microsoft.com/contentmoderator/moderate/v1.0/ProcessText/Screen', [
            'Text' => $text,
        ]);
        
        $result = $response->json();
        
        $categories = $result['Classification'] ?? [];
        $isAdult = ($categories['Category1']['Score'] ?? 0) > 0.5;
        $isRacy = ($categories['Category2']['Score'] ?? 0) > 0.5;
        $isOffensive = ($categories['Category3']['Score'] ?? 0) > 0.5;
        
        return [
            'action' => ($isAdult || ($isRacy && $isOffensive)) ? 'block' : 
                       ($isRacy || $isOffensive) ? 'flag' : 'allow',
            'scores' => $categories,
        ];
    }
}
```

**Chat moderation (real-time)**:
```php
// Event listener in Laravel
class MessageSending
{
    public function handle(MessageSending $event): void
    {
        $filter = new TextFilter();
        $hit = $filter->quickFilter($event->message->content);
        
        if ($hit) {
            $event->message->update(['status' => 'blocked', 'reason' => $hit]);
            $event->stopPropagation();
            return;
        }
        
        // Async AI check
        ModerateText::dispatch($event->message);
    }
}
```

### 4. Live Stream Moderation

**Strategy**: Periodic screenshot → moderate → take action

```php
// Cron job: every 30s per live stream
class ModerateLiveStream extends Command
{
    public function handle(): void
    {
        $streams = LiveStream::where('status', 'live')->get();
        
        foreach ($streams as $stream) {
            // 1. Capture screenshot via FFmpeg
            $screenshot = "/tmp/live/{$stream->id}_" . time() . ".jpg";
            exec("ffmpeg -i rtmp://{$stream->rtmp_url} -vframes 1 -s 640x480 {$screenshot} 2>/dev/null");
            
            // 2. Moderate the frame
            if (!file_exists($screenshot)) continue;
            $result = SightengineService::check("file://{$screenshot}");
            
            // 3. Take action
            if ($result['action'] === 'block') {
                $stream->violation_count++;
                
                if ($stream->violation_count >= 3) {
                    // Auto-terminate stream
                    exec("kill -9 {$stream->ffmpeg_pid}");
                    $stream->update(['status' => 'terminated', 'reason' => 'nsfw']);
                    $stream->user->ban(['reason' => 'live_nsfw']);
                } else {
                    // Send warning
                    $stream->update(['warning_sent' => true]);
                    // Notify admin for manual review
                    AdminNotification::dispatch("Live stream flagged: {$stream->id}");
                }
            }
        }
    }
}
```

## Laravel Integration — Database Schema

Add these migration fields to JustFans:

```php
// Add to media table
Schema::table('media', function (Blueprint $table) {
    $table->string('moderation_status', 20)->default('pending')
          ->comment('pending|queued|approved|flagged|blocked');
    $table->json('moderation_data')->nullable()
          ->comment('AI API response, scores, timestamps');
    $table->string('moderation_reason')->nullable();
    $table->timestamp('moderated_at')->nullable();
    $table->foreignId('moderated_by')->nullable()->constrained('users');
});

// Add to users table (for bans)
Schema::table('users', function (Blueprint $table) {
    $table->timestamp('banned_at')->nullable();
    $table->string('ban_reason')->nullable();
    $table->timestamp('ban_expires_at')->nullable();
});
```

## Admin Review Panel

JustFans already has an admin panel. Add a moderation queue page:

```php
// routes/admin.php
Route::get('/moderation/pending', [AdminModerationController::class, 'pending']);
Route::post('/moderation/{media}/approve', [AdminModerationController::class, 'approve']);
Route::post('/moderation/{media}/reject', [AdminModerationController::class, 'reject']);
Route::post('/moderation/{media}/ban-user', [AdminModerationController::class, 'banUser']);
```

**Admin UI features needed**:
1. Queue: shows flagged content sorted by AI confidence (lowest confidence = most uncertain = review first)
2. Preview: show the image/video alongside AI analysis breakdown
3. Actions: Approve / Reject / Ban User
4. Stats dashboard: flag rate, false positive rate, review backlog

## Decision Matrix

| Content Type | AI Score | Action | User Experience |
|-------------|----------|--------|-----------------|
| Image | Nudity < 0.3 | ✅ Pass | Visible immediately |
| Image | 0.3 ≤ Nudity < 0.65 | 🔍 Flag → Manual Review | "Under review" placeholder |
| Image | Nudity ≥ 0.65 | 🚫 Block + Ban | Content removed, user warned |
| Text | Offensive < 0.4 | ✅ Pass | Visible immediately |
| Text | 0.4 ≤ Offensive < 0.7 | 🔍 Flag → Manual Review | Hidden from public, visible to user |
| Text | Offensive ≥ 0.7 | 🚫 Block | Message not sent |
| Chat | Any L1 match | 🚫 Block | Message not sent |
| Live | 3+ violations in 5min | 🚫 Terminate + Ban | Stream cut, user banned |

## Confidence Tiers for "Unsure" Handling

```
AI Confidence  | Action
───────────────────────────────
> 0.85         | Auto-block (high confidence violation)
  0.65 - 0.85  | Block + flag for manual review (intercept first, then let admin confirm)
  0.40 - 0.65  | Flag for manual review, content hidden pending review
< 0.40         | Pass (confident it's clean)
```

**Key rule**: When AI confidence is between 0.40-0.85 for borderline content, **intercept first**. Content is hidden from public view until an admin reviews it. This prevents your platform being used to distribute borderline content even for the few seconds before review.

## Cron Jobs

```bash
# Run moderation queue (processes L1-passed, L2-queued items)
* * * * * cd /var/www/justfans && php artisan moderate:process-queue >> storage/logs/moderation.log

# Extract + moderate video frames (every 5 minutes)
*/5 * * * * cd /var/www/justfans && php artisan moderate:videos >> storage/logs/moderation.log

# Moderate active live streams (every 30 seconds)
* * * * * sleep 30 && cd /var/www/justfans && php artisan moderate:livestreams >> storage/logs/moderation.log

# Retry failed moderation jobs
0 */2 * * * cd /var/www/justfans && php artisan moderate:retry-failed >> storage/logs/moderation.log

# Clean up old moderation data (>30 days)
0 4 * * 0 cd /var/www/justfans && php artisan moderate:cleanup >> storage/logs/moderation.log
```

## API Cost Estimation

| Volume | Calls/month | Sightengine cost | Azure cost | Total |
|--------|------------|-----------------|------------|-------|
| Small (300 users) | ~3,000 images | ~$30 | ~$5 | ~$35/mo |
| Medium (3,000 users) | ~30,000 images | ~$250 | ~$30 | ~$280/mo |
| Large (30,000 users) | ~300,000 images | ~$2,000 | ~$300 | ~$2,300/mo |

**Cost optimization**:
- Sightengine: free 4,000 calls/mo covers small launch
- Use L1 quick filter to reject obviously safe content before hitting API
- Cache moderation results for identical file hashes
- Batch video frame checks (one API call per N frames)

## Pitfalls

1. **False negatives on AI-only moderation**: No AI is 100% accurate. Always have manual review for borderline cases. A single missed CSAI (child sexual abuse imagery) can get your hosting terminated and your merchant account closed.

2. **Stripe/PayPal account termination risk**: Payment processors have strict content policies. If prohibited content appears on your platform, they'll terminate your account permanently (blacklisted). This is non-negotiable — you must have automated moderation.

3. **Chinese Golden Shield (GFW) compliance**: If your platform is accessible from China or hosted on a Chinese VPS, you must filter political sensitive content. Different API providers have different Chinese content coverage — Azure is best for Chinese language, Sightengine is weakest.

4. **User bans require evidence**: Always store the moderation data (AI response JSON, screenshot) alongside the ban. Users will appeal, and you need to show evidence. Store in `moderation_data` JSON column.

5. **Don't block legitimate content**: Creators on OnlyFans-style platforms post artistic nudity that's not sexually explicit. Fine-tune your thresholds per content type. What's "artistic" vs "explicit" needs category-specific thresholds.

6. **Appeals process**: Users whose content was incorrectly blocked will churn. Build a simple appeal workflow: user can request review → pushes to admin queue as priority → admin reviews with original + AI results.

7. **API latency**: Sightengine API calls take 1-3 seconds. Don't block the upload HTTP request — use Laravel queues (Redis/DB) to process async. User uploads, gets "processing" status, email notification when moderated.

8. **API downtime**: If Sightengine is down, what happens? Have a fallback: if API call fails (timeout/error), auto-flag content for manual review. Don't auto-approve.

9. **Live stream screen capture quality**: FFmpeg screenshots from RTMP streams can be low quality, causing false negatives. Consider taking multiple frames and using the best-quality one.

10. **Video file size**: Large video files take time to FFmpeg-process. Set a max file size (JustFans default ~2GB) and handle the progress queue chunked.

## Verification Checklist

- [ ] Sightengine or Azure account created + API keys configured in `.env`
- [ ] Database migration added: `moderation_status`, `moderation_data`, `moderation_reason` columns
- [ ] L1 sensitive word list loaded into `config/sensitive-words.php`
- [ ] Image upload handler dispatches moderation job (async)
- [ ] Video upload handler dispatches frame-extraction + moderation job
- [ ] Chat/PM event listener intercepts and filters messages
- [ ] Admin moderation panel page added (pending queue + approve/reject/ban actions)
- [ ] Cron jobs registered: process-queue, videos, livestreams, retry-failed
- [ ] API cost calculated based on expected volume
- [ ] Fallback logic: if API down → auto-flag, don't auto-approve
- [ ] Ban evidence stored: moderation JSON saved alongside user ban record
- [ ] User appeal flow: blocked user can request manual re-review
- [ ] Live stream auto-terminate: 3+ violations in 5 min → cut + ban
