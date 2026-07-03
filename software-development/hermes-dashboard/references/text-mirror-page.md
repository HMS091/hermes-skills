# Text Mirror Page for Dashboard Copy/Paste

## When to Use

When a user wants to copy text from the Hermes Dashboard but the Ink/TUI rendering prevents text selection (no DOM, everything is ANSI-rendered in xterm.js).

**Do NOT try to hack copy buttons into the Ink UI** — it requires multi-layer coordination (Ink → WebSocket → Python → OSC 52 → xterm.js) and is fragile across rendering paths. The mirror page is simpler, zero-risk, and works perfectly.

## Approach

Run a separate lightweight Python HTTP server that reads Hermes session JSON files and serves them as plain HTML. No dashboard code is touched.

## Architecture

```
Browser Tab 1 (Dashboard, 9119)         Browser Tab 2 (Mirror, 9120)
  ┌──────────────┐                        ┌──────────────┐
  │ xterm.js TUI │                        │ Plain HTML    │
  │ (no copy)    │                        │ (full select) │
  └──────┬───────┘                        └──────┬───────┘
         │ WebSocket                              │ HTTP
         ▼                                        ▼
  Hermes TUI Node.js                      Python http.server
  (Ink → ANSI)                            (reads session .json files)
         │                                        │
         └──────────Both share filesystem─────────┘
```

## Session File Format

Important: Hermes stores session data as **`.json` files** (not `.jsonl`), one file per session, in `/opt/data/sessions/`. Each JSON file has:

```json
{
  "session_id": "20260528_070937_52ac60",
  "model": "...",
  "messages": [
    {"role": "user", "text": "..."},
    {"role": "assistant", "text": "...", "kind": "diff", "tools": [...]}
  ]
}
```

Key parsing rules:
- Skip `kind: "trail"` messages that have no `text` (they're tool/reasoning status updates, not conversation)
- Skip `role: "system"` messages longer than ~50 chars (system prompts)
- Handle code fences (```) by wrapping in styled `<pre>` blocks
- Per-message copy buttons use `navigator.clipboard.writeText()`

## Implementation

Save as `/opt/hermes/session-mirror.py`:

```python
#!/usr/bin/env python3
"""
Hermes 会话镜像页面 — 纯文本可复制
访问: http://你的NASIP:9120
实时显示最新会话内容，鼠标可选中复制。
"""

import json
import os
import glob
import html
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

SESSIONS_DIR = "/opt/data/sessions"
PORT = 9120

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hermes 会话镜像</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", sans-serif;
    background: #f5f5f5;
    color: #333;
    line-height: 1.6;
    padding: 0;
  }}
  .header {{
    background: #1a1a2e;
    color: #fff;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .header h1 {{ font-size: 16px; font-weight: 600; }}
  .header .info {{ font-size: 12px; color: #aaa; }}
  .header .controls button {{
    background: #16213e;
    color: #fff;
    border: 1px solid #0f3460;
    padding: 6px 14px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    margin-left: 8px;
  }}
  .header .controls button:hover {{ background: #0f3460; }}
  .container {{ max-width: 860px; margin: 0 auto; padding: 16px; }}
  .msg {{
    margin-bottom: 12px;
    padding: 12px 16px;
    border-radius: 8px;
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 14px;
    position: relative;
  }}
  .msg.user {{ background: #e3f2fd; border-left: 3px solid #1976d2; }}
  .msg.assistant {{ background: #fff; border-left: 3px solid #388e3c; }}
  .msg.system {{ background: #fafafa; border-left: 3px solid #757575; color: #666; font-size: 13px; }}
  .msg.tool {{ background: #f3e5f5; border-left: 3px solid #7b1fa2; font-size: 13px; color: #555; }}
  .msg .label {{ font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; opacity: 0.7; }}
  .msg.user .label {{ color: #1976d2; }}
  .msg.assistant .label {{ color: #388e3c; }}
  .msg.system .label {{ color: #757575; }}
  .msg.tool .label {{ color: #7b1fa2; }}
  .empty {{ text-align: center; color: #999; padding: 60px 20px; }}
  .code-block {{ background: #1e1e1e; color: #d4d4d4; padding: 12px 16px; border-radius: 6px; font-family: "SF Mono", "Fira Code", "Consolas", monospace; font-size: 13px; overflow-x: auto; white-space: pre; margin: 8px 0; }}
  .refresh-bar {{ background: #eee; padding: 6px 20px; font-size: 12px; color: #888; display: flex; justify-content: space-between; }}
  a {{ color: #1976d2; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .msg .copy-btn {{
    position: absolute; top: 8px; right: 8px;
    background: transparent; border: 1px solid #ddd; border-radius: 4px;
    padding: 2px 8px; font-size: 11px; color: #999; cursor: pointer;
    opacity: 0; transition: opacity 0.2s;
  }}
  .msg:hover .copy-btn {{ opacity: 1; }}
  .msg .copy-btn:hover {{ background: #eee; color: #333; }}
  .msg .copy-btn.copied {{ background: #4caf50; color: #fff; border-color: #4caf50; }}
</style>
</head>
<body>
<div class="header">
  <div><h1>📋 Hermes 会话镜像</h1><div class="info">{session_info}</div></div>
  <div class="controls">
    <button onclick="selectAll()">全选复制</button>
    <button onclick="location.reload()">刷新</button>
  </div>
</div>
<div class="refresh-bar">
  <span>自动刷新中 ({interval}s)</span>
  <span id="countdown">{interval}s</span>
</div>
<div class="container" id="container">{content}</div>
<script>
function selectAll() {{
  const sel = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(document.getElementById('container'));
  sel.removeAllRanges(); sel.addRange(range);
  document.execCommand('copy');
  const btn = document.querySelector('.controls button:first-child');
  btn.textContent = '✓ 已复制';
  setTimeout(() => btn.textContent = '全选复制', 2000);
}}
document.querySelectorAll('.copy-btn').forEach(btn => {{
  btn.addEventListener('click', function() {{
    const text = this.getAttribute('data-text');
    navigator.clipboard.writeText(text).then(() => {{
      this.textContent = '✓'; this.classList.add('copied');
      setTimeout(() => {{ this.textContent = '📋'; this.classList.remove('copied'); }}, 1500);
    }});
  }});
}});
let remaining = {interval};
setInterval(() => {{
  remaining--;
  document.getElementById('countdown').textContent = remaining + 's';
  if (remaining <= 0) remaining = {interval};
}}, 1000);
</script>
</body></html>"""

def format_text(text: str) -> str:
    if not text:
        return "<em style='color:#999'>(空)</em>"
    escaped = html.escape(text)
    lines = escaped.split("\\n")
    result = []; in_code = False; code_lines = []; code_lang = ""
    for line in lines:
        if line.startswith("````"):
            if in_code:
                result.append(f'<div class="code-block">{"<br>".join(code_lines)}</div>')
                code_lines = []; in_code = False
            else:
                code_lang = line[4:].strip(); in_code = True
        elif line.startswith("```"):
            if in_code:
                result.append(f'<div class="code-block">{"<br>".join(code_lines)}</div>')
                code_lines = []; in_code = False
            else:
                code_lang = line[3:].strip(); in_code = True
        elif in_code:
            code_lines.append(line)
        else:
            result.append(line)
    if in_code and code_lines:
        result.append(f'<div class="code-block">{"<br>".join(code_lines)}</div>')
    return "<br>".join(result)

def load_session(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

def format_session_content(data: dict) -> str:
    msgs = data.get("messages", [])
    if not msgs:
        return '<div class="empty">📭 暂无消息</div>'
    parts = []
    for i, msg in enumerate(msgs):
        role = msg.get("role", "unknown")
        text = msg.get("text", "")
        kind = msg.get("kind", "")
        if kind == "trail" and not text: continue
        if not text and kind != "trail": continue
        if kind == "trail" and msg.get("tools") and not text: continue
        if role == "system" and len(text) > 50: continue
        label = {"user": "👤 你", "assistant": "🤖 Hermes", "system": "⚙️ 系统", "tool": "🔧 工具"}.get(role, role)
        if role == "assistant" and kind == "diff": label = "📝 差异"
        content_html = format_text(text)
        copy_text = html.escape(text or "")
        parts.append(f'<div class="msg {role}"><div class="label">{label}</div>{content_html}<button class="copy-btn" data-text="{copy_text}" title="复制本条">📋</button></div>')
    return "\\n".join(parts)

class MirrorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            files = sorted(glob.glob(os.path.join(SESSIONS_DIR, "session_*.json")), key=os.path.getmtime, reverse=True)
            data = load_session(files[0]) if files else None
            if data:
                session_info = f"会话: {data.get('session_id','?')[:12]} | {len(data.get('messages',[]))} 条消息 | 模型: {data.get('model','?')}"
                content = format_session_content(data)
            else:
                session_info = "暂无会话数据"
                content = '<div class="empty">📭 等待会话数据...</div>'
            html_out = HTML_TEMPLATE.format(session_info=html.escape(session_info), content=content, interval=3)
            self.wfile.write(html_out.encode("utf-8"))
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *args): pass

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), MirrorHandler)
    print(f"Mirror on http://0.0.0.0:{PORT}")
    server.serve_forever()
```

## How to Use

### Quick Start (manual)
```bash
python3 /opt/hermes/session-mirror.py &
```
Open `http://<nas-ip>:9120` in a browser tab.

### Auto-start (container restart proof)
Set environment variable `HERMES_MIRROR=1` on the Docker container. The entrypoint (`docker/entrypoint.sh`) auto-detects this and starts the mirror server in the background. Port override: `HERMES_MIRROR_PORT` (default 9120).

To disable: remove the env var or set to 0, restart container.

## Limitations

- 3-second auto-refresh (not real-time like the TUI) — enough for chat
- Only shows the latest session file (by modification time)
- Text only — no ANSI/color fidelity, just CSS-styled divs
- Works best with browser focus set to Dashboard tab while mirror tab sits beside it

## When Not to Use

- If the user just needs to copy the last response, use the `/save` or clipboard slash command
- If real-time exact ANSI rendering fidelity is required, this won't match the TUI
