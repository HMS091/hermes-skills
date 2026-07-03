# Session Mirror Page — Copy Text from TUI Dashboard

When the Hermes Dashboard (Web UI) renders the conversation via Ink TUI → xterm.js, text cannot be selected or copied with the mouse because the browser displays a terminal emulator, not DOM text.

The fix is a **sidecar mirror page**: a standalone Python HTTP server that reads session JSON files from disk and serves them as clean HTML that the user can select, copy, and paste from naturally.

## Architecture

```
Browser Tab 1 (Dashboard)     Browser Tab 2 (Mirror)
┌─────────────────────┐       ┌──────────────────────┐
│ Ink TUI via xterm.js │       │ Plain HTML <div>     │
│ ❌ 无法选中复制      │       │ ✅ 随便选随便复制    │
└────────┬────────────┘       └──────────┬───────────┘
         │ WebSocket                      │ HTTP
         ▼                                ▼
┌──────────────────────────────────────────────────────┐
│                  Hermes Agent Process                 │
│                                                       │
│  ┌─────────────────┐   ┌──────────────────────────┐  │
│  │ tui_gateway.entry│   │ session-mirror.py        │  │
│  │ (Python backend) │   │ (Python http.server)     │  │
│  └─────────────────┘   │ Port 9120                │  │
│                         │ Reads:                   │  │
│                         │ /opt/data/sessions/*.json│  │
│                         └──────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

## How to Use

1. Start the mirror server:
   ```bash
   python3 /opt/hermes/session-mirror.py &
   ```

2. Open in browser: `http://<nas-ip>:9120`

3. Keep both tabs open — Dashboard on the left to chat, Mirror on the right to copy.

## Features

- **Auto-refresh** every 3 seconds — new messages appear automatically
- **Per-message copy button** — hover over any message and click 📋
- **Select All + Copy** button in the header bar
- **Pure HTML rendering** — code blocks are styled as `<pre>` blocks, messages color-coded by role
- **Lightweight** — zero dependencies, Python stdlib only
- **Zero risk** — does not modify Dashboard code in any way

## Implementation Notes

- Session files live in `/opt/data/sessions/` as `session_<timestamp>_<hash>.json`
- Each file has `messages[]` with `role`, `text`, `kind` fields
- The mirror reads the most recently modified file and renders it
- Uses `http.server.HTTMTServer` (stdlib) — no Flask, no node_modules, no npm build
- Code blocks (```...```) are detected via simple fence parsing and rendered as styled `<div>` blocks

## When to Use This Pattern

This technique is applicable to any web-based terminal emulator that renders TUI output in the browser:
- Any Ink/React terminal app served via a WebSocket proxy
- Any tool where the browser shows a terminal rather than DOM elements
- The fix is always the same: read the data source (session files, logs, DB) and serve a plain HTML view

## Pitfalls

- The mirror is read-only — typing into it would break nothing but also wouldn't send messages to the agent
- Session files update on every assistant response — the 3-second refresh interval means there's a brief delay
- If the session file is very large (1000+ messages), rendering may be slow — the mirror reads the whole file each refresh
