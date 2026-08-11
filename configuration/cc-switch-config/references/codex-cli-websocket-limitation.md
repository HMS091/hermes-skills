# Codex CLI WebSocket Hardcode (v0.145.0+)

## The Problem

Codex CLI v0.145.0+ uses the **Responses API exclusively** which communicates via WebSocket to
`wss://api.openai.com/v1/responses`. This WebSocket endpoint is **hardcoded** — Codex CLI
ignores `base_url`, `OPENAI_BASE_URL`, and every other proxy configuration setting.

## Evidence

```
ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket:
  HTTP error: 401 Unauthorized, url: wss://api.openai.com/v1/responses
```

This happens even when `~/.codex/config.toml` has:
```toml
base_url = "http://127.0.0.1:15721/v1"
wire_api = "chat"
```

## Root Cause

Codex CLI's WebSocket transport constructor takes the endpoint from a compiled-in constant,
not from the configuration file. The `base_url` and `wire_api` settings are only used for
the HTTPS fallback path (chat completions), which Codex never uses by default.

The CC Switch `experimental_bearer_token = "PROXY_MANAGED"` and modified `base_url` are
respected by **Codex Desktop (GUI)** but NOT by **Codex CLI**.

## `codex doctor` Output Snippet

```
Configuration:
  model: gpt-5.5 · openai
Connectivity:
  wire API: responses
  endpoint: wss://api.openai.com/v1/<redacted>
  handshake transport error: http 401 Unauthorized
```

## Workarounds

1. **Use Codex Desktop GUI** — CC Switch can proxy it successfully
2. **Use Claude Code** with CC Switch (env-var-based routing works differently)
3. **Use OpenCode** — open-source, provider-agnostic, supports custom endpoints
4. **Upgrade Codex Desktop** (not CLI) — newer versions may respect proxy config

## Relevant CC Switch Logs

When takeover is working:
```
[INFO] codex Live 配置已接管，代理地址: http://127.0.0.1:15721/v1
[INFO] 已同步 Codex Token 到数据库 (provider: 7b0a1112-...)
```

When proxy is forwarding HTTP (curl test):
```
[INFO] [Codex] >>> 请求目标: https://api.deepseek.com/v1/chat/completions (model=deepseek-v4-flash)
```
