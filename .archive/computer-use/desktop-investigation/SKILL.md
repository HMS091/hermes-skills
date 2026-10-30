---
name: desktop-investigation
description: |-
  Investigate, diagnose, and configure unknown desktop applications
  using cua_driver MCP tools — inspect app type, config files,
  localization support, and settings UI. Covers Electron, UWP,
  and native Win32 applications on Windows.
version: 1.0.0
author: Hermes Agent
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [desktop, investigation, cua-driver, application-config, localization]
    category: computer-use
    related_skills: [computer-use, systematic-debugging]
---

# Desktop Investigation — cua_driver MCP Tools

## When to Use

Load this skill when the user asks you to:

- **Set an app to a different language** (e.g. "把 X 设置成中文")
- **Find and change a configuration option** in an app they don't know well
- **Investigate what an unknown application is** and what settings it has
- **Troubleshoot an app's behavior** by inspecting its configuration files
- **Discover how an app stores its preferences** (Electron vs native)

## Core Principle

The high-level `computer_use` tool is great for driving known UI, but for
**investigation** you need the lower-level `mcp__cua_driver__*` MCP tools.
These provide richer introspection: process lists, window trees with
element indices, web-page text extraction, and accessibility data that
the `computer_use` tool doesn't expose.

## Phase 1: Discovery — Find the App

### Find Running Processes and Windows

```python
# Best starting point — returns ALL processes + visible windows
get_accessibility_tree()

# The output has two sections:
# 1. Running processes (233+ entries on a typical desktop)
# 2. Visible windows (with pid, window_id, title, bounds)
```

**Key fields in the window table:**
- `pid` — process ID (for later get_window_state / click calls)
- `window_id` — HWND (required by many cua_driver MCP tools)
- `title` — window title (case-insensitive substring search)
- `x, y, width, height` — window bounds

Search the process list AND window list for your target app name.

### Alternative: list_apps + list_windows

```python
list_apps()       # Running + installed apps with kind (desktop/uwp)
list_windows(pid=...)   # All windows for a specific PID
```

`list_apps` returns `launch_path` which you can pass directly to
`launch_app(launch_path=...)` for UWP packaged apps.

## Phase 2: Categorize the App

### Find the Install Location

```bash
# Windows: use wmic (available in git-bash / MSYS)
wmic process where "processid=<PID>" get executablepath

# Typical paths:
#   C:\Users\<user>\AppData\Local\Programs\<App>\<App>.exe   (Electron)
#   C:\Program Files\<App>\<App>.exe                           (Native Win32)
#   shell:AppsFolder\...                                       (UWP Store app)
```

### Identify App Type

**Is it Electron?** Check for these files in the install directory:

```
chrome_100_percent.pak   ✓
chrome_200_percent.pak   ✓
locales/                  ✓  ← language packs (en-US.pak, zh-CN.pak, etc.)
resources/
  app.asar                ✓  ← the packed web UI
LICENSES.chromium.html    ✓
```

**Is it a UWP / Windows Store app?** It will have `kind: "uwp"` in
`list_apps` output and `aumid` (App User Model ID).

**Is it native Win32?** No Electron files, just an `.exe` + `.dll` files.

## Phase 3: Config Files — Find Language / Locale Settings

### Electron App Config Files

Electron apps store user config in `AppData/Roaming/<AppName>/`:

| File | Purpose |
|---|---|
| `argv.json` | Electron command-line args, **locale setting** |
| `Preferences` | Chromium-level preferences (Electron app shell) |
| `Local State` | Chromium encrypted local state |
| `languagepacks.json` | Installed VS Code-style language packs |
| `settings.json` | In `User/` subdirectory — user workspace settings |

**CHECK `argv.json` FIRST for locale:**

```bash
cat "C:\Users\<user>\AppData\Roaming\<AppName>\argv.json"
# → {"locale": "zh-cn"}  ✅ already set to Chinese
```

The locale in `argv.json` controls the **Electron shell** level — window
buttons (最小化/最大化/关闭) and native menus. It does NOT control the
web-level UI language.

**CHECK `locales/` for available languages:**

```bash
ls "C:\Users\<user>\AppData\Local\Programs\<AppName>\locales\"
# → zh-CN.pak  ✅ Chinese language pack exists
# → en-US.pak  ✅ English
```

### Native Win32 App Config Files

Native apps may store config in:
- `AppData/Roaming/<AppName>/` — INI/XML/JSON config files
- `AppData/Local/<AppName>/` — machine-specific data
- Registry: `HKEY_CURRENT_USER\Software\<Vendor>\<AppName>\`
- Registry: `HKEY_LOCAL_MACHINE\Software\<Vendor>\<AppName>\`
- Settings files next to the executable

## Phase 4: Inspect the Settings UI

### Step 1 — Capture the window's UI tree

```python
get_window_state(pid=<PID>, window_id=<HWND>, max_elements=200)
```

Returns:
- **`tree_markdown`** — structured tree of all interactive elements
- **`elements`** — array with element_index, role, label, frame
- **`screenshot_file_path`** — screenshot of the window

Search for known settings categories:
```
Account, General, Appearance, Models, Language, Locale,
Customizations, Browser, App, Preferences, Settings
```

### Step 2 — Click through settings categories

```python
# Click settings sidebar items one at a time
click(element=N, delivery_mode="foreground", pid=PID, window_id=HWND)
capture_after=True  # to verify the click landed
```

### Step 3 — Read the content

For **native Win32 / WPF app elements** visible in the UIA tree:
→ The element labels and values are in `get_window_state` output directly.

For **Electron web content** (Chromium/Electron web views):
→ The UIA tree only shows the outer Document — actual content is invisible.
→ Use the page tool instead:

```python
page(action="get_text", pid=<PID>, window_id=<HWND>)
# Returns all visible text in the web view as plain text
```

## Phase 5: Electron/Chromium Window Limitations

| Issue | Cause | Workaround |
|---|---|---|
| Scroll returns `background_unavailable` | Electron windows (class `Chrome_WidgetWin_1`) don't accept background scroll | `delivery_mode: "foreground"` |
| Clicks don't land in background | Web content is rendered by Chromium's renderer, not native UI | Try element px first (x,y from screenshot), then escalate to foreground click |
| UIA tree shows only Document, no inner elements | Chromium web views don't expose DOM to UIA | Use `page(action="get_text")` or `page(action="query_dom")` |
| `execute_javascript` fails | Requires `--remote-debugging-port=N` flag on launch | Use `get_text` / `query_dom` for read-only; create bookmark bypass; ask user to relaunch with flag |
| Type text doesn't reach input fields | Chromium renderer ignores PostMessage WM_CHAR | Use `page(action="insert_text")` or `page(action="type_keystrokes")` |

### Foreground Escalation Rule

When background mode fails on an Electron/Chromium window:

```python
# 1. Try background first (default)
click(element=N, pid=PID, window_id=HWND)
# → {effect: "suspected_noop", escalation: {recommended: "foreground", ...}}

# 2. Escalate to foreground (this IS the right response to the signal)
click(element=N, delivery_mode="foreground", pid=PID, window_id=HWND)
```

**Never guess foreground preemptively.**
Let the driver's returned signal tell you when to escalate.
Different controls within the same Electron app may behave differently.

## Phase 6: Verdict — What to Tell the User

### Scenario A: Language is NOT available in app settings

If you checked all settings categories and found NO language/locale option:

1. The **Electron shell locale** is already set via `argv.json` (`"locale":"zh-cn"`)
   — window buttons show Chinese (最小化/最大化/关闭) ✅
2. The **web UI content** is only available in English — the app's developers
   haven't built Chinese translation into the web interface ❌
3. Tell the user the locale is configured but the app doesn't have Chinese
   localization for its web UI
4. Suggest providing feedback to the app team requesting Chinese support

### Scenario B: Language IS available — set it

1. Click the language dropdown/selector
2. Select "中文" / "简体中文" / "Chinese (Simplified)"
3. Confirm: the app should show the new language
4. If the app needs a restart, ask the user or restart the app via
   `kill_app` + `launch_app`

## Full Investigation Workflow (Cheat Sheet)

```
1. get_accessibility_tree()           → find pid + window_id + title
2. wmic process where ...             → find executable path
3. ls install_dir/                    → check for Electron files + locales/
4. cat argv.json                      → check locale setting
5. get_window_state(pid, window_id)   → inspect UI tree
6. Click through settings categories  → search for language option
7. page(action="get_text")            → read web content in Electron apps
8. Report findings to user
```

## Related Skills

- **`computer-use`** — High-level `computer_use` tool API (complementary;
  this skill covers the lower-level MCP tools for investigation)
- **`systematic-debugging`** — Root cause debugging for code issues
  (different class; use when investigating code bugs, not app config)
