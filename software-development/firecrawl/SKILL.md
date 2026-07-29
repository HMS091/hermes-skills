---
name: firecrawl
description: "Firecrawl web search + scrape — configure and use Firecrawl via Hermes built-in plugin. Self-hosted (Docker) or cloud API (FIRECRAWL_API_KEY)."
version: 1.0.0
author: Hermes Agent
tags: [firecrawl, web-scraping, search, crawl, hermes-plugin]
---

# Firecrawl — Hermes Integration

Firecrawl is a web scraping and search API. Hermes has it built-in as a **web search/extract provider plugin** (`plugins/web/firecrawl/`). No external skill installation needed — just enable it and set credentials.

## Prerequisites

- `firecrawl-py` Python package (Hermes optional dep)
- Either a **Firecrawl API key** (cloud) or a **self-hosted Firecrawl instance URL**
- Hermes TUI session (`/reset` after enabling)

## Installation

### 1. Install the Python SDK

```bash
uv pip install firecrawl-py
```

### 2. Configure credentials

Choose one:

**A) Cloud API (recommended for simplicity):**
```bash
export FIRECRAWL_API_KEY="fc-..."
```
Get a key at https://www.firecrawl.dev/ → Dashboard → API Keys. Free tier: 500 credits.

**B) Self-hosted (Docker):**
```bash
export FIRECRAWL_API_URL="http://localhost:3002"
```
Then start your local Firecrawl instance:
```bash
cd /opt/data/docker-services/firecrawl
docker compose -p firecrawl up -d
```

### 3. Enable in Hermes

The web-firecrawl plugin is built-in. After setting the env var:

```bash
# Verify it's detected
hermes tools list | grep firecrawl

# Reset session to pick up changes (in TUI session, run /reset)
```

## Usage

Once configured and after a `/reset`, Hermes will automatically use Firecrawl for:

- **`web_search(query)`** — search the web
- **`web_extract(url)`** — scrape/extract a page's content (markdown or HTML)

No manual config needed — the plugin auto-detects `FIRECRAWL_API_KEY` or `FIRECRAWL_API_URL`.

## Verification

```bash
# Quick test
python3 -c "
from firecrawl import Firecrawl
client = Firecrawl()
# Replace with your key if using self-hosted
print('Firecrawl SDK ready')
"
```

## Hermes Config

Firecrawl is the **default web backend** in Hermes. To explicitly set it:

```yaml
# ~/.hermes/config.yaml
web:
  backend: firecrawl          # shared fallback
  search_backend: firecrawl   # per-capability override
  extract_backend: firecrawl  # per-capability override
```

### Managed Gateway (Nous Subscribers)

If you subscribe to Nous Research, you can use the Tool Gateway:

```bash
export FIRECRAWL_GATEWAY_URL="..."
export TOOL_GATEWAY_DOMAIN="..."
```

Set `web.use_gateway: true` in config.yaml to prefer gateway over direct API.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: firecrawl` | Install: `uv pip install firecrawl-py` |
| `ValueError: Web tools not configured` | Set `FIRECRAWL_API_KEY` or `FIRECRAWL_API_URL` |
| Hermes doesn't show web_search tool | Run `/reset` (new session) after setting env vars |
| Docker not available (in container) | Use cloud `FIRECRAWL_API_KEY` instead of self-hosted |
| Rate limit / 429 errors | Upgrade Firecrawl plan or throttle requests |

## Important Notes

- Firecrawl is **NOT a Hermes skill** — it's a built-in **plugin** (`plugins/web/firecrawl/`).
- The package `firecrawl-py` is an **optional dependency** (not installed by default). Install it with `uv pip install hermes-agent[firecrawl]` or `uv pip install firecrawl-py`.
- After installing the package, the web-firecrawl provider is auto-detected by Hermes on next session start.
- In this Docker environment, Docker is NOT available in-container, so self-hosted mode requires a separate Docker host.
