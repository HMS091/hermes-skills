# OSC 52 Clipboard Escape Sequence for Hermes TUI

## Overview

OSC 52 (Operating System Command 52) is an ANSI escape sequence that instructs the terminal emulator to write data to the system clipboard. Format:

```
\x1b]52;c;<base64-encoded-text>\x07
```

- `\x1b]` — OSC escape
- `52` — command number for clipboard
- `c` — clipboard selection (`c` = clipboard, `p` = primary/selection on X11)
- `<base64>` — base64-encoded UTF-8 text to copy
- `\x07` — ST (string terminator, BEL character)

## In xterm.js (Browser Dashboard)

The Hermes Dashboard renders via xterm.js in the browser. xterm.js **does** support OSC 52 — when it receives the sequence, it writes to `navigator.clipboard.writeText()`.

## Where to Send It

OSC 52 must be written to **stdout** of the process that xterm.js is connected to.

In the Dashboard architecture:
- The browser xterm.js is connected to the **TUI Node.js process** (`ui-tui/dist/entry.js`)
- Writing to `process.stdout` from the Ink app sends data through the terminal to xterm.js

## Implementation Sketch

### Option A: From Ink Component

```typescript
// In a TUI component (e.g., messageLine.tsx)
function copyToClipboard(text: string) {
  const b64 = Buffer.from(text).toString('base64')
  process.stdout.write(`\x1b]52;c;${b64}\x07`)
}
```

### Option B: From Python Gateway

The Python gateway could send OSC 52 via the TUI's stderr/stdout pipe, but stderr is shown in the logs panel, and stdout carries JSON-RPC. The cleanest path is through a dedicated RPC call:

1. Ink sends RPC `slash.exec` → Python copies text
2. Python writes OSC 52 to its own stderr → xterm.js receives it

**Problem**: Only stdout of the foreground process is piped to xterm.js. The Python gateway writes to its own stdout which the TUI reads as JSON-RPC lines. Writing raw OSC 52 there would corrupt the protocol.

### Option C: Ink layer RPC

1. Add an Ink handler that receives a "clipboard.set" event
2. In the handler, call `process.stdout.write('\x1b]52;c;...\x07')`
3. Python sends the event via WebSocket

This is the cleanest approach but requires modifying both the TUI and gateway.

## Prerequisites

- xterm.js must have `allowTransparency: false` (default) — if disabled, clipboard writes fail silently
- Browser permission for `navigator.clipboard` — must be triggered by a user gesture (click) in most browsers. An auto-copy on message receive may not work without user gesture.
- Some browsers (Firefox) require `clipboard-write` permission and user gesture

## Limitations

- One-shot only (can't stream to clipboard)
- Base64 encoding overhead (~33%)
- Browser clipboard permission may require user gesture
- Not all terminals/browsers support OSC 52
- Does NOT work from the Python side — must come from the TUI Node.js process's stdout
