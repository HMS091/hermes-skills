---
name: hermes-ui-surface-triage
description: "Use when a Hermes UI bug needs surface triage first."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [debugging, hermes-agent, tui, dashboard, xterm, ui, layout]
    related_skills: [debugging-hermes-tui-commands, web-debugging, systematic-debugging]
---

# Hermes UI Surface Triage

## Overview

"The chat box is broken" reaches Hermes through at least four different renderers: the plain terminal TUI,
the dashboard's browser-embedded TUI (xterm.js over a PTY bridge), the desktop app, and messaging platforms.
The SAME words mean different bugs in each. Repro steps, source files, and even what "font size" can possibly
mean differ per surface — in a real terminal glyphs cannot be scaled, so "字变大了" is never a font-size change
there; in xterm.js it can only come from `fontSize` options, browser zoom, or a stale cell grid.

**Core principle: the session's `platform` label lies, the process tree does not.** A session served to a
browser still reports `platform: tui` because the dashboard runs the real TUI behind a PTY. Pin the surface
from processes before you read a single line of render code.

## When to Use

- User reports a visual/layout/legibility problem in Hermes ("text became huge", "right side cut off", "box looks wrong").
- A symptom is claimed to appear "after the first message", "after switching tabs", "only on my laptop".
- You need to know whether an Ink component, an xterm option, dashboard CSS, or data is at fault.

## Step 1 — Pin the surface

Run the probe (read-only, safe while the user is chatting):

```bash
python3 <skill_dir>/scripts/surface_probe.py
```

It prints every Hermes TUI/gateway/dashboard process with its parent, its tty, the **PTY grid the TUI believes
it has**, and the port the dashboard process listens on. Read it like this:

| What you see | Surface |
|---|---|
| `node .../ui-tui/dist/entry.js` whose **parent is the dashboard process** | browser dashboard, embedded xterm.js |
| same node process whose parent is a login shell / ssh session | real terminal, pure Ink |
| no node TUI at all | desktop app or messaging platform |

Cross-checks: `stty -F /dev/pts/N size` gives the client grid the TUI is laying out for
(`40 170` = 40 rows, 170 cols) — a wide grid plus a report of "text too big" points at pixel/zoom trouble,
not at transcript markup. Dashboard chrome preferences (e.g. `dashboard.theme` in `config.yaml`) tell you
whether the surrounding page is intentionally large; the terminal font is NOT driven by that theme.

## Step 2 — Reuse the prior diagnosis before re-deriving it

A recurring complaint is usually a recurrence, not a new bug:

```
session_search(query="<the symptom, in the user's own words>")
```

Past sessions often contain the mechanism already worked out, the reasoning that was wrong, and the
workaround that was handed out (which is therefore known NOT to be sufficient). Start from there; do not
re-run a whole investigation the user has already paid for once.

## Step 3 — Locate the actual renderer

| Surface | Source of truth | Constraint that bites |
|---|---|---|
| Terminal TUI | `ui-tui/src/components/*` (appLayout, messageLine, markdown, branding), rebuilt to `ui-tui/dist/entry.js` | terminals cannot scale glyphs; wrap/clip rules are cell-based |
| Dashboard `/chat` | `web/src/pages/ChatPage.tsx` + `web/src/lib/terminal-appearance.ts`, built to `hermes_cli/web_dist/` | the running UI is the **built bundle**, not the .tsx |
| Dashboard chrome | `web/src/**`, `web_dist/custom.css` | CSS overrides cannot change xterm cell metrics |

This install ships no `web/node_modules` and no npm toolchain: **editing `web/src/*.tsx` changes nothing at
runtime.** Only `web_dist/` artifacts are live, and `/opt/hermes` is not a git repo, so there is no history
to diff a regression against.

## Step 4 — Diagnose by category before reading code

- **Rendering (glyph level):** overlapping/text spilling out of cells, characters drawn bigger than their
  cells. Cause is a cell-metric mismatch (font-size option changed without a refit, or a CSS `font-size`
  override on `.xterm-rows`), never transcript content.
- **Layout (box level):** a pane clips content because an ancestor is `overflow-hidden` while its child is
  wider than it. In the dashboard the chat wrapper is `overflow-hidden` and the terminal grid is sized from
  `host.clientWidth`; a grid wider than the box = right-hand columns silently invisible, with no scrollbar.
- **Data/markup level:** missing rows, wrong text, wrong order — that is Ink/gateway territory
  (see `debugging-hermes-tui-commands`).

When the client is not reachable, **measure instead of guessing**: inject a temporary script that reports
`host width / grid width / cell width / fontSize / DPR / visualViewport.scale / overflowPx` and, when
`grid > host`, dispatches a `resize` event — the dashboard already listens for it and refits + re-sends the
PTY size. Recipe and code: `references/dashboard-chat-terminal.md`.

## Step 5 — Fix without collateral damage

- **Never restart the dashboard while you owe the user a reply.** Its PTY child IS the agent process
  serving the conversation; a restart kills the turn. Also expect node/gateway PIDs to change mid-session
  when the browser opens a new PTY — re-probe instead of reusing old PIDs.
- `web_dist/index.html` is read from disk on **every** request and `web_dist/assets/*` is served publicly:
  a new `<script>` takes effect on the user's next page load, no restart. Ship a NEW asset filename —
  hashed assets are cached immutably.
- `write_file` refuses paths outside `HERMES_WRITE_SAFE_ROOT` (default `/opt/data`): author in
  `/opt/data/cache/scratch`, then `cp` into place with `terminal`.
- Keep every artifact reversible: back up the original (`index.html.<something>.bak`) and leave a
  one-command rollback script next to it.
- `hermes update` overwrites `web_dist`: say so when you patch it, and offer a source-level fix if the
  user wants it permanent.

## Step 6 — Prove it, or say plainly that you could not

Verification that actually ran: asset returns 200 with the expected byte count, served `index.html` contains
the tag, telemetry sink accepts and persists a POST. Verification that did NOT happen (no screenshot, no
user confirmation) must be reported as such — never phrase an unconfirmed hypothesis as a fix.

## Pitfalls

- **Never `pkill -f` / `pgrep -f` a pattern that also appears in your own command line.** Piping a port
  number or process name into `pgrep -f` matches the shell running it, which SIGTERMs your own command
  mid-run (`exit_code -15`, no output). Kill a known PID, or find the owner by listening port via
  `/proc/net/tcp` socket inodes.
- Do not treat `platform: tui` as "the user is in a terminal" — see Overview.
- Do not "fix" a clipped terminal by adding a CSS `font-size` override on `.xterm-rows`: glyphs are painted
  into cells measured from xterm options, so the text overflows and overlaps instead. `web_dist/custom.css`
  carries this warning in its header for a reason.
- Do not burn the session trying to drive the dashboard from a local headless browser: `browser_exec`'s
  browser cannot reach `127.0.0.1` on the server, and a container renderer may crash on the heavy SPA. Go to
  server-side forensics + in-page telemetry instead.
- One `clarify` with the two discriminating options (which device; whole page vs only the chat pane) is
  cheaper than an hour of code archaeology — but this user dislikes being asked, so pair it with a
  self-service check they can run (Ctrl+0 then F5) and keep working while waiting.

## Reporting to this user

Chinese, conclusion first. Separate **facts pulled from the machine/process tree** from **hypotheses** in a
table, state which verification was impossible and why, then give a single next action for them
(usually: press F5 once). Name the rollback path. No process narration, no "great question".
