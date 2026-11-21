# Dashboard `/chat` — the browser-embedded TUI

The dashboard does not re-implement chat. `/api/pty` spawns what `hermes --tui` would spawn through a PTY and
streams raw bytes both ways; `web/src/pages/ChatPage.tsx` renders them in an xterm.js terminal. Consequences
that matter during diagnosis:

- Session records still say `source/platform: tui`. Confirm the real client from the process tree
  (`scripts/surface_probe.py`), not from the session row.
- Ink markup bugs are shared with the terminal TUI; **everything about font size, cell grid, clipping and
  zoom is dashboard-only.**
- Resize travels as `\x1b[RESIZE:<cols>;<rows>]` and is applied server-side with `TIOCSWINSZ`.

## Font size is a hardcoded width table

`web/src/lib/terminal-appearance.ts`:

| host width | font px | line-height |
|---|---|---|
| <300 | 7 | 1.02 |
| <360 | 8 | 1.02 |
| <420 | 9 | 1.02 |
| <520 | 10 | 1.02 |
| <720 | 11 | 1.02 |
| <1024 | 12 | 1.02 |
| >=1024 | 14 | 1.15 |

There is no config knob for it (grep `DEFAULT_CONFIG` — nothing). The tier is re-evaluated on mount, on
`ResizeObserver` of `.hermes-chat-xterm-host`, on `window.resize` (60 ms debounce) and re-sent to the PTY
as a keepalive. `dashboard.theme` (e.g. `default-large`, 18 px base) styles the page chrome only; it does
not touch xterm.

## Why the right-hand columns can be invisible

`.hermes-chat-xterm-host` sits inside a wrapper with `overflow-hidden` (`p-2 sm:p-3`, rounded, dark).
The grid is `cols x cellWidth` derived from `fit()`; if the grid ends up wider than that box, the excess
is clipped with no scrollbar and no error — the transcript simply looks like it runs off the edge.

`FitAddon.proposeDimensions()` (checked in the shipped bundle) computes:

```
cols = floor((parentBox.width - parentPadding - overviewRulerWidth) / dimensions.css.cell.width)
rows = floor((parentBox.height - parentPadding) / dimensions.css.cell.height)
```

where `overviewRulerWidth` defaults to 14 px and the cell size comes from the **render service's cached
dimensions**, not from a live measurement. So any path that changes the font/cell size and then fits in the
same tick is a candidate: the grid can be computed with the previous cell width.

Two other ways to get the same symptom, both pixel-level and invisible to the server:

- browser zoom / trackpad pinch (layout box changes -> refit happens)
- visual-viewport pinch zoom (no layout change -> nothing refits; everything magnifies and the right edge
  falls outside the viewport)

## The refit hook (self-heal without touching the bundle)

`ChatPage` listens for `window`'s `resize` and funnels it into `syncTerminalMetrics()` -> `fit.fit()` ->
`\x1b[RESIZE:...]`. Dispatching a synthetic event therefore re-runs the app's own, already-correct path —
the safest possible lever from outside:

```js
function guard() {
  var host = document.querySelector('.hermes-chat-xterm-host');
  var screen = document.querySelector('.xterm-screen');
  if (!host || !screen) return;
  var cs = getComputedStyle(host);
  var box = host.getBoundingClientRect().width
          - (parseFloat(cs.paddingLeft) || 0)
          - (parseFloat(cs.paddingRight) || 0);
  if (box > 40 && screen.getBoundingClientRect().width > box + 2) {
    window.dispatchEvent(new Event('resize'));   // -> refit + RESIZE to the PTY
  }
}
```

Run it a few times after load (layout settles late: CSS transitions, webfont swap, PTY connect), then every
2 s, and once ~1.2 s after every Enter (the failure mode users describe as "after the first message").

Useful measurements to report next to it: `host.clientWidth`, `.xterm-screen` width,
`.xterm-char-measure-element` width (cell width), `.xterm-rows` computed `font-size`, `devicePixelRatio`,
`visualViewport.scale`, and `screenWidth - box` (overflow px). Post them somewhere the agent can read
(a tiny local HTTP sink; `navigator.sendBeacon` with a `text/plain` body avoids CORS preflight).

This is a **diagnostic harness**, not a proven fix: until the numbers come back, describe it to the user as
measurement + self-heal, never as "the bug is fixed".

## Shipping it without a rebuild

- `hermes_cli/web_server_dashboard.py::_serve_index` reads `WEB_DIST/index.html` **per request**, then injects
  the session token. Edit the file on disk and a plain page reload picks it up — no dashboard restart (a
  restart would kill the user's live session).
- `/assets` is a public `StaticFiles` mount with immutable caching: drop the payload at
  `web_dist/assets/<new-name>.js` and reference that exact name.
- `</head>` in the built `index.html` may have no leading whitespace (a `custom.css` link is glued to it) —
  match the bare tag, or the injector silently no-ops.
- Rollback = restore `index.html` from the `.bak` you took + delete the asset. Keep it as a script.
