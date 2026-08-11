# Metered.ca TURN service research (2026-08)

**Verdict for Nextcloud Talk: NOT compatible — authentication-model mismatch.**

## Why it can't be used with Nextcloud
- Metered credentials are fixed **username/password** pairs. Fetch via:
  `GET https://<appname>.metered.live/api/v1/turn/credentials?apiKey=<key>` (optional `region` param).
  Response = standard ICE servers array: `urls`, `username`, `credential` (password). Dashboard: "Generate credential" / "Show ICE Servers Array" buttons.
- Nextcloud Talk only accepts TURN servers in **static-auth-secret** mode (coturn `use-auth-secret`): Nextcloud mints short-lived HMAC creds (username = unix timestamp, password = base64(hmac_sha1(secret, username))) and pushes them to clients. Talk's `turn_servers` schema has no username/password field.
- Net: Nextcloud cannot authenticate to Metered, and Metered would reject Nextcloud's HMAC creds. Metered fits custom WebRTC apps (their own SDKs), not Nextcloud Talk.

## Endpoints (valid for other WebRTC apps)
- STUN: `stun:stun.relay.metered.ca:80`
- TURN global: `turn:global.relay.metered.ca:80` (UDP/TCP), `:443` (UDP), `turns:global.relay.metered.ca:443` (TLS)
- Region pinning via `region` query param or region hostnames (asia, singapore, japan, …); global endpoint auto-routes to nearest of 100+ PoPs / 31+ regions; <30 ms claimed; no per-allocation throughput limit.
- Free tier ~25 GB/month (verify on pricing page — it changed before); paid plans above that.

## Docs map (for future lookups)
- Docs root: `https://www.metered.ca/docs/` — TURN Server Service sidebar: Overview / What is TURN / Creating TURN Credentials / TURN Server Regions / How to Create Expiring TURN Credentials / Custom Domain / TURN Projects / Turn Server API.
- Turn REST API pages: `/docs/turn-rest-api/get-credential`, `post-create-credential`, `delete-credential`, `get-current-usage`, `project/*`.
- No Nextcloud/Jitsi/Mattermost integration pages exist in the sitemap. `/llms.txt` returns 404 (`Cannot GET /llms.txt`). Some deep links 404 too (e.g. `/docs/turn-server-service/how-to-create-expiring-turn-credentials`) — use the sidebar links, they resolve.

## Real alternatives when self-hosted TURN is impossible
- Cloud VPS (Tencent/Aliyun lightweight ~¥30-50/mo) running coturn with the same `use-auth-secret` config — Nextcloud just points at the VPS public IP.
- Any provider that supports static-auth-secret / Nextcloud-compatible TURN REST credentials.
