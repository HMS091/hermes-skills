---
name: hermes-dashboard
description: "Architecture, rendering pipeline, and modification guide for the Hermes Dashboard Web UI (TUI/Ink). Know what renders where before writing code."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes-agent, dashboard, tui, ink, web-ui, architecture, rendering]
    related_skills: [debugging-hermes-tui-commands]
---

# Hermes Dashboard Architecture

## Overview

The Hermes Dashboard is **NOT a standard React SPA** rendered to the browser DOM. It is a **terminal-emulator-based TUI** that happens to run in a browser tab via xterm.js. This has profound implications for what you can and cannot do.

## When to Use

- You need to modify or add UI features to the Hermes Dashboard (buttons, click handlers, clipboard, etc.)
- You're trying to add browser-like interactivity and hitting walls
- You need to understand why something that's trivial in a web app is hard here
- You're debugging the rendering pipeline between Python backend and Ink frontend

## Rendering Pipeline

```
Browser Tab (xterm.js terminal emulator)
        ↑ ANSI escape sequences + mouse events
        ↓
    Node.js process (ui-tui/dist/entry.js)
  ┌─────────────────────────────────────────┐
  │  Ink (terminal React framework)          │
  │    → Renders React components to ANSI    │
  │    → No DOM, no HTML, no CSS             │
  │    → No navigator.clipboard              │
  │    → No document.createElement            │
  │    → No window or browser APIs           │
  └─────────────────────────────────────────┘
        ↑ WebSocket (JSON-RPC)
        ↓
  Python process (tui_gateway.entry)
        ↑ stdin/stdout (JSON-RPC)
        ↓
  Python process (slash_worker)
```

### Key Components

| Layer | Location | Language | Role |
|-------|----------|----------|------|
| Browser terminal | xterm.js in HTML | JS | Renders ANSI, captures keystrokes/mouse |
| Ink renderer | `ui-tui/packages/hermes-ink/` | TS | Converts React components to ANSI |
| TUI app | `ui-tui/src/` | TS/TSX | All UI components (messageLine, markdown, etc.) |
| Gateway client | `ui-tui/src/gatewayClient.ts` | TS | WebSocket ↔ Python bridge |
| Python gateway | `tui_gateway/entry.py` | Python | JSON-RPC server |
| Slash workers | `tui_gateway/slash_worker.py` | Python | Handle slash command execution |

## What This Means for Modifications

### ❌ Don't Try (won't work in Ink)
- `navigator.clipboard.writeText()` — no browser API access
- `<button onClick={...}>` — Ink's `Box onClick` is terminal-mouse based, absolutely positioned
- DOM manipulation — there is no DOM
- CSS styling — Ink uses ANSI escape codes (colors, bold, inverse)
- `<input>` / `<textarea>` — Ink has its own text input via `TextInput`

### ✅ What Works in Ink
- `<Text>` — styled text (color, bold, dim, italic, strikethrough, underline, inverse)
- `<Box>` — flexbox layout (flexDirection, padding, margin, width, border)
- `<Ansi>` — raw ANSI escape sequence passthrough
- `<Link>` — clickable URLs (rendered as hyperlinks, opens browser on click via `onHyperlinkClick`)
- `Box onClick` — terminal mouse click events (clicks are absolute-positioned, no DOM event bubbling)

### Real Copy/Paste Options

1. **OSC 52 clipboard escape sequence** (`\x1b]52;c;base64data\x07`):
   - Send from Python or Node.js to stdout
   - xterm.js in the browser receives it and writes to system clipboard
   - Works but requires coordination across 3 layers
   - See `references/osc52-clipboard.md`

2. **Pure-text mirror page** (recommended for copy-ability):
   - Run a separate lightweight Python HTTP server
   - Reads Hermes session files from disk
   - Renders as plain HTML divs — fully selectable and copyable
   - No dashboard modification needed
   - See `references/text-mirror-page.md`

## How to Modify Dashboard UI

### Build Process

```bash
cd /opt/hermes/ui-tui
npm run build   # esbuild → dist/entry.js
```

Build is fast (seconds). The dashboard runs `dist/entry.js` directly.

### Development Workflow

1. Edit `ui-tui/src/components/*.tsx`
2. `cd /opt/hermes/ui-tui && npm run build`
3. Restart dashboard: `kill <pid_of_entry.js>` or restart the container
4. Refresh browser tab

### Key Files

| File | Purpose |
|------|---------|
| `src/entry.tsx` | Entry point, sets up GatewayClient + Ink render |
| `src/gatewayClient.ts` | WebSocket ↔ Python bridge |
| `src/app.tsx` | Main App component, session/subscription management |
| `src/components/messageLine.tsx` | Renders each chat message (user, assistant, tool) |
| `src/components/markdown.tsx` | Markdown → Ink rendering (tables, code, links, math) |
| `src/components/streamingAssistant.tsx` | Live streaming message rendering |
| `src/components/appChrome.tsx` | Dashboard chrome (header, footer, input bar) |
| `tui_gateway/server.py` | Python JSON-RPC server for slash commands |
| `tui_gateway/entry.py` | Python entry point for gateway process |

## Common Pitfalls

1. **Assuming Ink = React DOM.** Ink shares JSX syntax and component model with React but renders to ANSI text. The mental model must shift from "HTML page" to "terminal UI".

2. **Adding browser APIs that don't exist.** Always ask: "Does this API exist in Node.js? Does it exist without a DOM?" If not, it won't work in Ink.

3. **Forgetting the multi-layer coordination.** A feature that needs browser-side action (clipboard write, URL open, dialog) requires: Ink component → GatewayClient (WebSocket) → Python handler → stderr/stdout → xterm.js.

4. **Not rebuilding before testing.** The dashboard runs `dist/entry.js`, not the source. Always `npm run build` after source changes.

5. **Only testing one rendering path.** TUI detail rendering has at least two paths: live `StreamingAssistant`/`ToolTrail` and transcript/pending `MessageLine` rows. Changes that affect one may miss the other.

6. **User asks for copy/paste support in the Dashboard.** Do NOT try to add a copy button inside the Ink TUI — it requires multi-layer coordination (Ink → WebSocket → Python → OSC 52 → xterm.js) and is fragile. Instead, offer the **text-mirror-page** approach: a separate Python HTTP server that reads session files. Reference `references/text-mirror-page.md` for the full implementation. To make it persist across container restarts, set `HERMES_MIRROR=1` environment variable — the Docker entrypoint auto-starts it (`docker/entrypoint.sh` checks this env var and launches `session-mirror.py` on port 9120).

## Auto-Starting Sidecar Services

The Docker entrypoint (`docker/entrypoint.sh`) supports env-var-gated sidecar processes:

| Env var | Effect | Default |
|---------|--------|---------|
| `HERMES_MIRROR=1` | Start text-mirror HTTP server on port 9120 | off |
| `HERMES_MIRROR_PORT=9120` | Override mirror port | 9120 |
| `HERMES_DASHBOARD=1` | Start dashboard in background | off |

Pattern: add a `case` block to `docker/entrypoint.sh` that checks `${VAR_NAME:-}` and backgrounds the process with `stdbuf -oL -eL` + `sed -u 's/^/[tag] /'` prefixing so output is distinguishable in `docker logs`.

## Auth & Security Model

The Dashboard web server generates an **ephemeral session token** at startup
to protect all `/api/` routes. The token is a 43-char base64url string
(`secrets.token_urlsafe(32)`), stored only in process memory.

- **REST**: `X-Hermes-Session-Token` header or `Authorization: Bearer <token>`
- **WebSocket** (`/api/pty`): `?token=<session_token>` query param
- **Frontend**: Injected into `index.html` as `window.__HERMES_SESSION_TOKEN__`
- **Public (no token)**: `/api/status`, `/api/config/defaults`, and a few others

See `references/session-token-auth.md` for full details — token retrieval,
source code locations, and public endpoint list.

## Architecture Decision Records

- **Ink over React DOM**: Ink is a terminal-first React renderer. The dashboard runs in both real terminals (SSH) and browser xterm.js, so Ink unifies the rendering. The cost is no browser API access.
- **WebSocket bridge**: Python handles all business logic; Ink is purely a view layer. Events flow one direction (Python → Ink for display, Ink → Python via RPC for actions).
