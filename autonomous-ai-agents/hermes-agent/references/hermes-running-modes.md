# Hermes Agent Running Modes

This reference covers the three main ways to interact with Hermes Agent and when to use each.

## Quick Comparison

| Feature | CLI (`hermes`) | Dashboard (`hermes dashboard`) | Gateway (Telegram/Discord/etc) |
|---------|---------------|-------------------------------|-------------------------------|
| **Text select/copy** | ✅ Full mouse + keyboard | ❌ Usually not (TUI rendering) | ✅ Native app selection |
| **Rich formatting** | ✅ Terminal colors | ✅ Full color + layout | ❌ Plain text only |
| **Session persistence** | Auto-saved to disk | Auto-saved to disk | Persistent per chat |
| **Attach images** | Via `/image` command | Via Web UI upload | Native attachment support |
| **Background run** | No (blocking) | No (blocking) | Yes (always-on service) |
| **Multi-tasking** | `/bg` + tmux | No native | Yes (async per message) |
| **Slash commands** | Full set | Full set | Subset (no `/history`, `/copy`) |
| **Config changes** | Must restart | Must restart | `/restart` in-session |
| **Ideal for** | Active dev + debugging | Visual monitoring | Mobile / always-on |

## When to Use Each

### CLI Mode (`hermes` or `hermes chat`)

**Best for:**
- Active development and debugging
- Copy-pasting code from agent responses
- Quick one-shot queries (`hermes chat -q "..."`)
- Long interactive sessions where you need mouse selection
- When you're already SSH'd into the machine

**Start:**
```bash
hermes                          # interactive session
hermes chat -q "summarize this file"   # one-shot
```

**Common issue:** If Hermes is running in Dashboard, you can still SSH in separately and run `hermes` — they share the same config and don't conflict.

### Dashboard Mode (`hermes dashboard`)

**Best for:**
- When a browser-based view is more accessible
- Monitoring agent output from a remote machine
- Demos and presentations
- When SSH terminal access is limited

**Start:**
```bash
hermes dashboard                # default port
hermes dashboard --port 8080    # custom port
```

**Why text can't be selected:** Dashboard renders output through `ui-tui`, an Ink/React-based terminal emulator. The agent response is parsed into `<Md>` and `<Text>` components (see `messageLine.tsx` → `markdown.tsx`), then drawn as character cells by Ink's Xterm-compatible output renderer. It is **not native HTML/DOM text** — the browser sees a pixel canvas, not selectable text nodes. The `NoSelect` component explicitly prevents text selection on the gutter. Even without `NoSelect`, the underlying Ink + xterm.js rendering pipeline treats all text as rendered glyphs, not a DOM text layer.

**Text export workarounds:**
1. `/save /tmp/session.md` — dumps the full conversation to a file you can read with a regular text editor
2. Session store export:
```bash
hermes sessions list
hermes sessions export /tmp/out.jsonl
```
3. Run the CLI via SSH (`docker exec -it <container> hermes`) for a native terminal with full mouse selection support

**For developers who want to add copy functionality:** The rendering chain starts at `messageLine.tsx` → `Md` component in `markdown.tsx` → Ink output. A "copy message" button would need to be added as an Ink `<Box>` with `onClick`, wired to the browser's Clipboard API through the xterm.js addon layer. The message text is available as `msg.text` in `messageLine.tsx`.

### Gateway Mode (`hermes gateway run`)

**Best for:**
- Running Hermes as an always-on assistant
- Mobile access via Telegram/Discord/Signal/WhatsApp
- Integration into Slack for team use
- Scheduled cron jobs that deliver to chat platforms

**Start:**
```bash
hermes gateway run              # foreground
hermes gateway install          # as a systemd service
hermes gateway start            # start the service
```

**Common pitfalls:**
- Gateway logs at `~/.hermes/logs/gateway.log`
- Platform-specific setup (bot tokens, webhooks, intents) varies per platform
- `/restart` in-session reloads config without killing the process

## Switching Between Modes Mid-Workflow

These are independent processes and can run simultaneously:

```bash
# Session 1 (SSH terminal): CLI mode
hermes

# Session 2 (browser): Dashboard on port 9090
hermes dashboard --port 9090

# Background: Always-on Telegram gateway
hermes gateway start
```

They share the same session store (`~/.hermes/sessions/`) but each has its own process state. Config changes (`hermes config set`) apply to the next invocation of each mode individually.
