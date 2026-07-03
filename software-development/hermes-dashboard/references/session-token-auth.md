# Hermes Dashboard Session Token & Auth

## Overview

The Hermes Dashboard web server (`hermes_cli/web_server.py`) generates an
**ephemeral session token** at startup (`_SESSION_TOKEN`) using
`secrets.token_urlsafe(32)` — a 43-character base64url string.

This token protects all REST API and WebSocket endpoints under `/api/`
(except a small public allowlist). It is **not persisted to disk** and is
**regenerated on every server restart**.

## Auth Mechanisms

| Transport | Auth Mechanism | Reason |
|-----------|---------------|--------|
| REST API | `X-Hermes-Session-Token` header **or** `Authorization: Bearer <token>` | Reverse proxies may already consume `Authorization` |
| WebSocket (`/api/pty`) | Query param `?token=<session_token>` | Browsers can't set custom headers on WS upgrade |

## How the Frontend Gets the Token

The SPA (served `index.html`) gets the token injected as a `<script>` tag:

```html
<script>window.__HERMES_SESSION_TOKEN__="<token>";window.__HERMES_DASHBOARD_EMBEDDED_CHAT__=true;window.__HERMES_BASE_PATH__="";</script>
```

This is injected in `mount_spa()` by replacing `</head>` with the script tag.

When `--skip-build` is used and `web/dist/` doesn't exist, the SPA is NOT
served, but the REST API and WebSocket endpoints still enforce the token.

## Retrieving the Token (from the running process)

Since the token is only in process memory, extraction requires one of:

1. **Read it from the SPA** — if `web/dist/index.html` exists, `curl http://127.0.0.1:9119/ | grep __HERMES_SESSION_TOKEN__`
2. **Read process memory** — `gdb -p <pid>` or `py-spy dump --pid <pid>`, then search for the token base64 string
3. **Restart the dashboard** and capture the new token (destroys existing session — use only as last resort)
4. **Call a public endpoint** — `/api/status` is public, but `/api/env/reveal` is token-gated

## Source Code Reference

- **Token generation & validation**: `hermes_cli/web_server.py` lines 82–148
- **Token injection into SPA**: `hermes_cli/web_server.py` lines 3512–3563
- **WebSocket token check**: `hermes_cli/web_server.py` lines 3126–3129
- **Public endpoint allowlist**: `_PUBLIC_API_PATHS` in `hermes_cli/web_server.py`

## Public Endpoints (no token required)

These endpoints are exempt from token auth:

```
/api/status
/api/config/defaults
/api/config/schema
/api/model/info
/api/dashboard/themes
/api/dashboard/plugins
/api/dashboard/plugins/rescan
```
