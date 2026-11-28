# Open-Source Tool Security Audit — Worked Example (NekokoLPA2, 2026-08)

Full audit of an eSIM LPA tool ("nekokolpa2" → GitHub `iebb/NekokoLPA2`, predecessor `iebb/NekokoLPA`). User asked: is it trustworthy, what do users say, is it safe to use an eSIM writer/manager? Reusable as a template for any open-source tool trust audit.

## What worked (command → insight)

| Step | Command | Insight gained |
|---|---|---|
| Find repo | `curl -s "https://api.github.com/search/repositories?q=nekokolpa"` | Found both v1 and v2 repos; user's name was a partial typo of "NekokoLPA2" |
| Repo metadata | `/repos/iebb/NekokoLPA2` + `.../releases?per_page=8` | 274★ v2 / 541★ v1, MIT license, release cadence (580 builds in 6 months = very active) |
| Author | `/users/iebb` | 2012-registered account (14yr old), Fukuoka Japan — not a throwaway |
| Contributors | `/repos/iebb/NekokoLPA2/contributors` | 1 main dev (53 commits) + 3 community contributors — solo-maintained flag |
| Issues+PRs in one call | `/repos/{o}/{r}/issues?state=all&per_page=50&sort=created&direction=desc` | PRs have `pull_request` key; labels/states show dev responsiveness; user-reported bugs + dev replies (e.g. #22 BLE timeout fixed 7/26, user confirmed 7/28) |
| Open-source date | `.../commits?until=2026-02-15T00:00:00Z` | v2 created 2026-01-14 but code only appeared ~1/26 — launched closed-source, opened later (confirmed by mineo.jp post: "ソースコードは公開されてない") |
| Store entity | `curl -s "https://itunes.apple.com/lookup?id=6757540723"` | sellerName = **KOSMONEKO OU** (legal entity, not the dev's handle) |
| Company lookup | DDG `<name> OÜ inforegister.ee` | Estonian e-Residency company: reg 16573324, legal rep Hongchuan Sun, owns lpa.ee+nekoko.ee; Sepapaja tn 6 addr = e-Residency hallmark; also makes esim.gg |
| Play rating | curl page (1MB) → regex `"ratingValue"\s*:\s*"?([\d.]+)"?` | 4.147 (~4.15★); data-safety + description are server-rendered ("我们不收集电话号码…" — dev explains Play auto-detects phone-number collection from a formatting feature) |
| App Store reviews | iTunes RSS customerreviews API | Only 1 rating → App Store volume tiny; report as "early-stage" signal |

## Code audit — checks that mattered

1. **Manifest permissions** (`android/app/src/main/AndroidManifest.xml`): INTERNET, BLUETOOTH*, location, notifications — all justified by BLE reader + OMAPI function. No overreach.
2. **Telemetry grep** `grep -rniE 'analytics|firebase|sentry|amplitude|mixpanel|posthog|telemetry' lib/`: ZERO third-party SDKs. Found self-hosted stats plugin instead (`lib/plugins/nekoko_stats_plugin.dart`).
3. **Endpoint classification** (`grep -rnoE 'https?://…'`): 12 endpoints → classified each: SM-DP+ direct (mobile), stats server (nlpa-data.nekoko.ee — project's own), update manifest (updates.lpa.ee), 3HK API (third-party, ICCID-prefixed only), cloudflare connectivity check, operator icons CDN, store links.
4. **Settings defaults** (`app_settings.dart`): `_enableNekokoStats = true` with `?? true` on load — **opt-out telemetry, default ON**. Report the default explicitly; user can disable.
5. **TLS override**: `badCertificateCallback = (cert, host, port) => true` in `smdp_client.dart` CustomHttpOverrides — accepts all certs globally. Real MITM weakness; mitigated by GSMA RSP protocol-layer signing, but must be reported.
6. **3HK enhancer** (`profile_enhancer_service.dart`): only fires for ICCID prefix `8985203` (3HK HK), sends ICCID to three.com.hk official API, cached, toggleable.
7. **Update manifest** `updates.lpa.ee/nlpa2.json`: verified it returns version metadata + SHA1 signature hashes pointing at GitHub Releases — NOT a payload.
8. **community.jks**: signing key + password committed — deliberate ("community" build flavor; store builds use private keys). Not a vuln; explains why re-signing an APK breaks eSIM (ARA-M whitelist binds to signature).

## Trust signals that carried the verdict

- Hardware vendors officially recommend it: 9esim.com software page ("NekokoLPA — the LPA we recommend"), eSTK.me founder defending it on X.
- Dual store presence (App Store + Play) + MIT license + active issue response.
- Community PRs merged (estk.me MAX slot-switch fix by external dev).
- No security complaints, no malware flags, no data-leak reports anywhere searched.

## Report structure that landed well (user: Chinese, tables, honest negatives)

结论先行 verdict → 它是什么 (table) → 可信度证据 (table) → 代码审查 (✅ clean table + ⚠️ findings w/ severity) → 用户反馈 (positive / negative / "未发现安全投诉") → 风险清单 (honest: single-maintainer, low review volume, write-risk) → 使用建议 (official channels only, turn off stats, test with cheap card) → 数据来源.

Key framing: separate "trustworthy" (open-source, auditable, vendor-endorsed) from "risk-free" (opt-out telemetry, TLS override, 3HK query) — give the user concrete settings to change after install.
