# Software / App Trust & Safety Vetting — full workflow

Worked example: NekokoLPA2 (eSIM LPA tool) full audit + EasyLPAC Windows binary verification (2026-08).

## Phase 1: GitHub repo triage

```bash
curl -s "https://api.github.com/repos/<owner>/<repo>"            # stars, license, created/pushed, archived, homepage, has_discussions
curl -s "https://api.github.com/repos/<owner>/<repo>/issues?state=all&per_page=50&sort=created&direction=desc"
curl -s "https://api.github.com/repos/<owner>/<repo>/releases?per_page=8"   # cadence: weekly = actively maintained
curl -s "https://api.github.com/users/<owner>"                   # account age (2012+ = old, established), followers, location, blog
curl -s "https://api.github.com/repos/<owner>/<repo>/contributors?per_page=15"  # 1-person vs community
curl -s "https://api.github.com/repos/<owner>/<repo>/commits?until=YYYY-MM-DD&per_page=10"  # open-source timeline check
```

Signals: license `NOASSERTION` = custom (often Infineon-derived or restricted); `MIT` = clean; repo created months before first public commit = launched closed, opened later (report this); contributor count + non-owner commits = real community.

**Pitfall**: unauthenticated GitHub API = 60 req/hr SHARED per egress IP — you WILL hit "API rate limit exceeded" mid-run. Wait ~20s and retry, or fall back to HTML pages / raw.githubusercontent.com READMEs.

## Phase 2: Source code audit

```bash
git clone --depth 1 https://github.com/<owner>/<repo> /tmp/xxx
```

Grep targets (use terminal `grep -r`, NOT search_files — ripgrep on cloned paths can silently return 0):

```bash
grep -rnoE 'https?://[a-zA-Z0-9._/-]+' lib/ src/ 2>/dev/null | sort -u   # classify EVERY endpoint
grep -rniE 'analytics|firebase|sentry|telemetry|tracking|amplitude|mixpanel|posthog' lib/ src/
grep -rniE '(api[_-]?key|secret|password|BEGIN RSA|BEGIN PRIVATE)' lib/ src/ | grep -viE 'keystore|key.properties|\.jks'
```

Checklist:
- **URLs**: update-check endpoint (curl it — should be version/signature JSON only), telemetry endpoint (who owns the domain? author's own server vs third party), SM-DP+ proxy (mobile apps should connect DIRECT to carrier, web builds may proxy for CORS), connectivity checks (cp.cloudflare.com/generate_204 is benign), operator-icon CDNs.
- **Telemetry data content**: what fields are sent? (device brand/model yes; IMEI/ICCID/phone/location = red flag). Is there a user-facing toggle? **Default-on vs off matters** — check `_prefs?.getBool('x') ?? true`.
- **Secrets**: hardcoded signing secrets that are public-by-design (upstream JS bundles ship them) are not leaks if commented as such.
- **Permissions** (AndroidManifest.xml): every permission must map to app purpose (BLUETOOTH_SCAN+LOCATION = BLE readers; POST_NOTIFICATIONS = reminders).
- **iOS**: NSAppTransportSecurity / NSAllowsArbitraryLoads exceptions.
- **In-repo signing key** (community.jks + storePassword "CommunityKey" in build.gradle.kts): intentional "community flavor" so user builds match official APK signature. NOT a vulnerability, but note that Play/App Store builds use private keys.
- **TLS**: `badCertificateCallback = (cert, host, port) => true` = accept-all-certs, a genuine weakness to report (MITM risk), even though eSIM protocol adds its own signing/encryption.
- **Update manifest**: `curl https://updates.example.com/app.json` — verify it's plain version + signature fingerprints + GitHub release URLs (not a payload).

## Phase 3: Store listings (identity + ratings)

```bash
# App Store — sellerName reveals the legal entity
curl -s "https://itunes.apple.com/lookup?id=<trackId>"
# Reviews (max 50, page=1 only, mostRecent works / mostHelpful returns 0)
curl -s "https://itunes.apple.com/jp/rss/customerreviews/page=1/id=<trackId>/sortBy=mostRecent/json?l=en"

# Google Play — MOBILE UA curl works; desktop/browser times out
curl -sL "https://play.google.com/store/apps/details?id=<pkg>&hl=zh_CN" \
  -H "User-Agent: Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Mobile Safari/537.36"
# parse: "ratingValue":"4.147..." and "reviewCount" from the ~1MB HTML
```

Cross-check bundleIds across the same seller → portfolio (NekokoLPA 1 + 2 both under KOSMONEKO OU). Play description often contains the developer's own data-safety disclaimers ("我们不收集电话号码…Google Play 会自动将其检测为收集电话号码").

## Phase 4: Company / author identity

DDG: `"<COMPANY> OU OR OÜ OR LTD"` → inforegister.ee (Estonia, shows reg code, owner name, owned domains), ariregister.rik.ee, digibaas.ee, dnb.com. `Sepapaja tn 6, Tallinn` = e-Residency virtual-address hub; small OÜ + Chinese/Japanese solo dev = typical indie e-Residency setup, verify but don't treat as scam signal. Owner's personal blog/GitHub age corroborates.

## Phase 5: Community feedback

- GitHub issues: bug categories (bluetooth, battery, slot-switching), dev response time (same-day vs silent), closed-with-fix rate, language mix (CN users present = Chinese community reach). Community PRs accepted = healthy.
- DDG: `"<tool>" reddit`, `"<tool>" telegram`, `<tool> 评价/吐槽/问题`, `site:xdaforums.com <tool>`.
- **Reddit is BLOCKED from datacenter IPs**: search.json returns HTML, RSS returns 403, old.reddit.com returns "File a ticket". Don't retry — pull snippets from DDG results instead.
- Hardware-vendor endorsement = strongest trust signal (e.g. 9eSIM official site: "NekokoLPA — the LPA we recommend"; eSTKme founder defending the tool publicly on X).
- Cloudflare-protected forums (forum.naixi.net etc.) return "Just a moment" to curl; browser daemon may be unavailable — accept DDG snippet-level evidence.

## Phase 6: Binary release verification

```bash
# 1. Official digest (no auth, but rate-limited)
curl -s "https://api.github.com/repos/<owner>/<repo>/releases/tags/<tag>"   # asset[].digest = "sha256:..."
# 2. Local hash
sha256sum <downloaded.zip>    # MUST equal official digest
# 3. Bundled engine vs upstream: download upstream official release, compare
sha256sum extracted/lpac.exe official/lpac.exe    # byte-identical = engine not swapped
```
- Python zipfile replaces missing `unzip`.
- **Authenticode** via Python struct (write as a file, don't inline): read PE header at `MZ+0x3C`, check `PE\0\0`, optional-header magic 0x20b=PE32+ (security dir at opt_off+112) / 0x10b=PE32 (+96); data dir index 4 = cert table; `cert_size > 0` = signed. **Unsigned is normal for solo open-source** → SmartScreen "unknown publisher" warning is expected, not malware evidence.
- `strings -n 6 <exe> | grep -iE 'https?://|token|secret'` — classify hits: Go stdlib error strings, Fyne/GUI framework strings, and for eSIM tools legit GSMA CI CRL endpoints (symauth.com, public.wisekey.com, crl.cnca.net, entrust, 111.204.x.x CN CI). No C2-looking endpoints = clean.
- Deliverable: hash-match table, file inventory, signature status, string-scan verdict, source labels.

## Report shape (this user)

结论先行 → 可信度证据表 → 代码审查(✅干净/⚠️披露分列) → 隐私数据流 → 用户反馈(正/负/未发现) → 诚实风险清单 → 使用建议. Chinese, tables + bullets. Every datapoint labeled with source + date. For "find me a more trustworthy alternative" follow-ups: produce a comparison table (platform / open-source / ratings / activity / verdict) and say plainly when the original tool is still the ceiling of trustworthiness.
