---
name: hermes-ui-rendering-debug
description: "Use when Hermes chat text is huge, clipped or misaligned."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, hermes-agent, tui, dashboard, xterm, layout, rendering]
    related_skills: [debugging-hermes-tui-commands, web-debugging, inspecting-hermes-desktop-dom, systematic-debugging]
---

# Debugging Hermes Chat Surface Rendering

Symptoms that bring you here: 「变成大字」, 「右边的字超出看不见」, overlapping/garbled rows, a chat pane
that is fine on load and breaks after the first message — in the terminal TUI, the dashboard `/chat`
tab, or the desktop app.

## Overview

Every Hermes chat surface renders through the same Ink app, but the transport differs and that
decides which layer a bug can live in:

| Surface | Renderer | Where the bug can be |
|---|---|---|
| `hermes --tui` in a terminal | Ink → terminal escapes | width math in `ui-tui/src` (a terminal wraps, so text cannot spill right) |
| dashboard `/chat` in a browser | Ink → PTY bridge → xterm.js | xterm font/grid sizing, PTY cols desync, browser zoom, CSS clipping |
| desktop app | Ink → its own terminal pane | same as dashboard, plus Electron CSS |

Translate the user's words into a layer before reading code: 「大字」= font/cell size changed;
「右边超出」= content wider than a clipping box; 「错位/重叠」= PTY cols ≠ client cols.

## When to Use

- The user says the chat box text became large, lost its right-hand characters, overlaps, or jumps
  size mid-session (any surface: `hermes --tui`, dashboard `/chat`, desktop app).
- A rendering bug appears only after the first message / after interacting, not on the first paint.
- You must tell which client a session is actually running in before changing UI code.
- You are about to "fix" the dashboard chat and need the deploy constraints of an installed Hermes.

Not for slash-command behaviour (see `debugging-hermes-tui-commands`) or generic CSS cascade
hunting in a plain web app (see `web-debugging`).

## Step 0 — identify the surface before theorising (never skip)

A dashboard-embedded session still reports `source=tui` in the state DB, so `source` alone is
useless. Walk the process tree instead:

```bash
ps -eo pid,ppid,tty,args | grep -E "dist/entry.js|tui_gateway.entry|dashboard" | grep -v grep
awk '{print $4}' /proc/<node-pid>/stat   # ppid → shell = local terminal; `hermes ... dashboard` = browser client
stty -F /dev/pts/<N> size               # "40 170" = rows cols the client negotiated — the key number
```

Confirm the client, its IP and the dashboard port:

- `grep "pty accepted" /opt/data/logs/gui.log | tail` → `peer=<lan-ip> mode=gated cred=ticket`.
- `grep ws_ticket_minted /opt/data/logs/dashboard-auth.log | tail` → who logged in, when.
- Port when `ss`/`netstat` are missing (common on NAS/minimal hosts): map the dashboard pid's socket
  inodes (`/proc/<pid>/fd`) onto LISTEN rows (`st=0A`) in `/proc/net/tcp{,6}`.
- Session record: `select id,source,title,cwd,started_at from sessions where id like '<sid>%'` in
  `/opt/data/state.db`.

## Step 1 — search session history before re-diagnosing

Recurring UI complaints usually already have a diagnosis on file. Search with the user's own words
first: `session_search("聊天框 大字 字体 超出")`. Re-deriving a mechanism that an earlier session had
already nailed down wasted an entire session once.

## Step 2 — get the numbers from the code, not from intuition

Dashboard specifics live in `web/src/pages/ChatPage.tsx` + `web/src/lib/terminal-appearance.ts`;
`references/dashboard-chat-terminal.md` holds the tier table, RESIZE protocol, clipping geometry and
the minified-bundle shape. The three rules that resolve most reports:

- Terminal font size is a **hardcoded width→px table** (7…14px), not a config knob. 14px is the
  ceiling, so a *further* enlargement cannot come from the tiers — test browser/page zoom instead.
- The terminal wrapper is `overflow-hidden`: a grid wider than its box is silently invisible on the
  right with no scrollbar. A pure PTY-cols desync cannot clip (terminals wrap), so clipping is a
  pixel-level cause: cells grew after the last fit, or the box shrank with no refit.
- "Fine on load, broken after the first message" points at a measurement that only settles after
  mount (webfont swap, CSS transition, breakpoint/sidebar, fit→tier jump) — instrument the
  transition; do not go re-reading the transcript renderer.

## Applying a fix on an installed (non-dev) Hermes

- **Never restart the dashboard to apply a change while replying through it.** The dashboard spawns
  the PTY that runs the current conversation; a restart kills the session and the reply is never
  delivered. Ship the change, then ask the user to reload.
- `web/node_modules` is normally absent in an installed distro → `npm run build` is unavailable and
  `ChatPage.tsx` edits are not deployable. The served artifact is `hermes_cli/web_dist/`.
- `web_dist/index.html` is read from disk **per request**: a `<script>`/`<link>` injection works on
  the next reload with no restart. `web_dist/assets/*` are hash-named and immutable-cached — rename
  the file to bust the browser cache.
- `hermes_cli/web_dist/custom.css` is the supported override point, but never set
  `.xterm-rows`/`.xterm` font-size or line-height there: CSS changes glyph size without changing the
  measured cell metrics, so text overlaps and spills out of the pane.
- Writes under `/opt/hermes` can be blocked by `HERMES_WRITE_SAFE_ROOT` (default `/opt/data`). Check
  the allowed root before promising a patch instead of discovering it at the last step.

## Verification

Client-side bugs need client-side evidence; "I changed the code" is not a fix report.

1. State the one action the user must take (a reload; a hard reload only if an asset changed).
2. Read a number back — negotiated `cols/rows` on the PTY after reload, or measurements the page posts
   back (host width, cell width, grid width, `visualViewport.scale`).
3. If you cannot read it back, say the fix is unverified and name the check that will confirm it.
   Never claim fixed from a code reading alone.

## Pitfalls

- Budget reproduction: at most a couple of calls proving you can render the user's URL. A private/LAN
  origin is reachable only from the user's machine — capture telemetry from *their* browser (a
  fire-and-forget POST to a local sink, or numbers echoed in the reply) instead of fighting for a
  local render of a page behind their session.
- Check the tier/zoom/clip triad before widening the search into the whole frontend.
- `custom.css` font-family overrides on `body, .app` are harmless inside the pane (xterm sets its own
  inline font) — do not blame them for wrong glyphs in the terminal.
- On a phone/tablet, treat focus-zoom as a candidate: iOS magnifies the visual viewport when a <16px
  input is focused, which enlarges everything and cuts the right edge while layout metrics (and thus
  ResizeObserver) never change — so no refit ever happens.
- The terminal's own glyph art (the ASCII banner) is a red herring: at ≥58 columns the full banner is
  drawn and looks like "big letters" in a scrolled-back transcript even when nothing is broken.
