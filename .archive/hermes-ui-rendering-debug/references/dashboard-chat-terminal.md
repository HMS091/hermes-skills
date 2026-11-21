# Dashboard chat terminal — internals

Depth for `hermes-ui-rendering-debug`, dashboard `/chat` case only.

## Transport

```
browser xterm.js  ──ws /api/pty?token=…──  hermes_cli/web_server_chat.py
   │                                              │ ptyprocess
   └── "\x1b[RESIZE:<cols>;<rows>]" frame ────────┴──> real `hermes --tui` (HERMES_TUI_INLINE=1,
                                                         HERMES_TUI_DASHBOARD=1, mouse off)
```

- RESIZE frames are intercepted server-side (`_RESIZE_RE`) and applied with `TIOCSWINSZ`; the TUI
  never sees them.
- The page sends RESIZE on socket open, on every xterm `onResize`, and again on a keepalive timer, so
  the PTY normally converges to the client grid. A stale `cols` therefore usually means the client's
  grid never changed — not that a frame was lost.
- `stty -F /dev/pts/<n> size` is the fastest read-back of what the server currently believes.

## Font tiers (`web/src/lib/terminal-appearance.ts`)

```
<300 → 7px   <360 → 8   <420 → 9   <520 → 10   <720 → 11   <1024 → 12   else → 14px
lineHeight: <1024 → 1.02, else 1.15
```

Input is `terminalTierWidthPx(host)` = the terminal host div's `clientWidth`, falling back to
`documentElement.clientWidth` / `visualViewport.width`. Tiers are applied at mount and re-applied in
`syncTerminalMetrics()` (ResizeObserver on the host + a 60 ms debounced window `resize` listener).
A tier change sets `term.options.fontSize/lineHeight` and then calls `fit.fit()` in the same tick.

## Clipping geometry

```
termWrap  (p-2 sm:p-3, rounded-lg, overflow-hidden)   ← anything wider is invisible, no scrollbar
 └ host   (.hermes-chat-xterm-host, flex-1)           ← what ResizeObserver measures / fit reads
    └ .xterm → .xterm-screen (width = cols × cellWidth)
```

- FitAddon reserves `overviewRuler.width || 14` px and reads `_renderService.dimensions.css.cell`
  (not a live measurement), so a fit issued before the renderer re-measures a new font keeps the old
  cell size.
- Browser probe: `grid = .xterm-screen.getBoundingClientRect().width` vs host `clientWidth`.
  `grid > box + 2` ⇒ clipping, not a PTY desync. `.xterm-char-measure-element` gives live cell width;
  `gridWidth / cellWidth` = columns.
- A safe external self-heal: `window.dispatchEvent(new Event('resize'))` re-enters the app's own
  `scheduleSyncTerminalMetrics` → refit → RESIZE. It touches nothing else, so it cannot corrupt state.

## Minified bundle facts (installed distro, no node_modules)

- Page chunk `hermes_cli/web_dist/assets/ChatPage-<hash>.js`; xterm chunk `xterm-<hash>.js`.
- `index.html` is read from disk on every request; `assets/*` are immutable-cached, so a rename is
  required to invalidate.
- The sync function survives minification as
  `i&&(h.options.fontSize=n,h.options.lineHeight=r);try{E.fit()}catch{return}` — the pattern a
  surgical patch would target (defer the fit one `requestAnimationFrame` after a font change).
- `custom.css` carries a standing warning not to font-size `.xterm-rows`; only xterm `options` may
  change cell metrics.

## Other surfaces in the same page

- `!narrow && !chatPanelCollapsed` renders a fixed `lg:w-60` side panel (model + sessions); `narrow`
  is `matchMedia("(max-width: 1023px)")` and `chatPanelCollapsed` is persisted in localStorage — both
  stable, so neither flips on the first message.
- Theme is a separate axis: `dashboard.theme` (default `default-large` = 18px base, spacious) scales
  the dashboard chrome only. Terminal font stays in px tiers, so the theme cannot cause a terminal
  font jump.
