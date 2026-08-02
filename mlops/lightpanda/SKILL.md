---
name: lightpanda
description: "Lightpanda headless browser (Zig, AI-focused) — use via Hermes MCP tools (mcp_lightpanda_*) for fast local bulk scraping / markdown dumps. When user asks to grab a page's content fast, batch-fetch many URLs, or dump a site to markdown/html without anti-bot concerns. NOT for anti-bot/login sites — use Scrapling/browser there."
version: "1.0.0"
triggers:
  - user asks for fast/bulk page fetching or markdown dump
  - user wants to grab many URLs quickly
  - mcp_lightpanda_* tools are available and target site has no heavy anti-bot
  - user mentions lightpanda
metadata:
  binary: /opt/lightpanda/lightpanda
---

# Lightpanda

Headless browser written from scratch in Zig, designed for AI agents. Local, fast (~9x
faster, ~16x less memory than headless Chrome), AGPL-3.0. Installed at `/opt/lightpanda/lightpanda`
(nightly build), integrated into Hermes via native MCP as `mcp_lightpanda_*` tools.

## Tool selection (scraping ladder)

1. **批量快爬 / 纯 dump** → Lightpanda (`mcp_lightpanda_*`)
2. **常规单页 / 需 CSS 解析** → Scrapling (load `scrapling` skill)
3. **反爬 / Cloudflare / 登录** → Scrapling StealthyFetcher or Hermes browser
   (Lightpanda has NO stealth — it will lose to Cloudflare)
4. **长任务批量** → Spider / cron

## Key MCP tools (31 registered)

`goto` (navigate+load), `markdown` (page→markdown), `html`, `links`, `extract` (structured
data), `evaluate` (JS), `click`, `fill`, `scroll`, `press`, `hover`, `waitForSelector`,
`getCookies`, `search`, `session_new`/`session_list` (isolated sessions), `tree`
(semantic DOM). Workflow: `goto` → `waitForSelector`/`waitForState` → `markdown`/`extract`.

## CLI fallback (if MCP not loaded)

```bash
# Dump page to markdown (⚠️ use --log-level info; --log-level error swallows the dump output)
/opt/lightpanda/lightpanda fetch --dump markdown --log-level info https://example.com

# CDP server for Puppeteer/Playwright: /opt/lightpanda/lightpanda serve --host 127.0.0.1 --port 9222
# MCP server standalone: /opt/lightpanda/lightpanda mcp  (stdio) | mcp --port 9223 (HTTP)
```

## Pitfalls

- **`--log-level error` hides dump output** — looks like a failed fetch. Use `--log-level info`.
- **No stealth/anti-bot** — Cloudflare/managed-challenge sites will fail; switch to Scrapling/browser.
- **CORS not implemented** (upstream issue #2015) — some sites' requests blocked by the browser itself.
- **Beta, may crash** — retry or fall back; don't debug config first.
- MCP tools appear only after Hermes restart (no hot-reload for MCP servers).

## Install / Hermes MCP integration record

Full install + config.yaml integration + pitfalls (`hermes config set` can't write arrays,
MCP SDK goes in Hermes' own venv at /opt/data/home/.local/share/uv/tools/hermes-agent/,
restart required) — see `web-research` skill → `references/lightpanda-browser-evaluation.md`.
