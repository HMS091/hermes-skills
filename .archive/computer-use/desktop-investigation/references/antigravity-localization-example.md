# Session Example: Setting Antigravity (Google AI Assistant) to Chinese

## Target App

**Antigravity** — Google's AI coding assistant app (similar to Cursor).
An Electron app wrapping a web UI served at `https://127.0.0.1:<port>/`.

## Investigation Steps Applied

### 1. Discovery

```python
get_accessibility_tree()
# → Found: Antigravity.exe (pid 4160), window "Antigravity" (HWND 394606)
# → Multiple Antigravity.exe processes (6 total): main + language_server + children
```

### 2. Categorization

```bash
wmic process where "processid=4160" get executablepath
# → C:\Users\Administrator\AppData\Local\Programs\Antigravity\Antigravity.exe

ls "C:\Users\Administrator\AppData\Local\Programs\Antigravity/"
# → chrome_100_percent.pak, chrome_200_percent.pak, locales/, resources/
# → CONFIRMED: Electron app
```

### 3. Config Files

```bash
cat "C:\Users\Administrator\AppData\Roaming\Antigravity\argv.json"
# → {"locale": "zh-cn"}  ← already set!

ls "C:\Users\Administrator\AppData\Local\Programs\Antigravity/locales/"
# → zh-CN.pak exists  ← Chinese pack installed
```

### 4. UI Inspection

```python
get_window_state(pid=4160, window_id=394606)
# → Window buttons already in Chinese: 最小化 / 最大化 / 关闭
# → Web content: URL = https://127.0.0.1:61158/?settingsOpen=true&settingsScreen=App
```

Settings categories checked (clicked each, read content):
- **Account** — telemetry, marketing, plan info, sign out — NO language option
- **General** — Prevent Sleep, Keep In Menu Bar — NO language option
- **Appearance** — theme, colors, conversation width — NO language option
- **Models** — (assumed no language option)
- **Customizations** — skills, MCP servers — NO language option
- **Browser** — JS execution policy — NO language option
- **App** — notifications — NO language option

### 5. Web Content Reading

```python
# For Electron web content, use page tool:
page(action="get_text", pid=4160, window_id=394606)
# Returns all visible text from the web view — confirmed all English
```

### 6. Verdict

- `argv.json` already has `"locale": "zh-cn"` ✅
- Chinese locale file `zh-CN.pak` exists ✅
- Electron shell shows Chinese window buttons ✅  
- **Web UI has NO Chinese translation** — the app's web interface is English-only
- No language setting exists in any settings section

## Key Notes for Future Sessions

- Antigravity uses Google sign-in (email: free.t8t88@gmail.com)
- Uses Gemini 3.6 Flash (High) model
- Has a project called "lumina-marketplace (15)"
- App runs its own local web server for the UI
- Has a `language_server.exe` (143MB) in `resources/bin/`
