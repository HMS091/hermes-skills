---
name: cc-switch-config
description: "Configure and troubleshoot CC Switch proxy for third-party LLM providers with Codex CLI, Claude Code (CLI), and Claude Desktop (GUI)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [CC-Switch, Proxy, Codex, Claude-Code, Claude-Desktop, Cowork, Third-Party-Providers, DashScope, DeepSeek]
    related_skills: [codex, claude-code, hermes-agent]
---

# CC Switch Configuration & Troubleshooting

Configure and debug CC Switch local proxy for routing Codex CLI and Claude Code requests to third-party LLM providers (DashScope/Qianwen, DeepSeek, Kimi, etc.).

## When to use

- Setting up CC Switch to proxy Codex/Claude to third-party providers
- Debugging 401/404 errors from CC Switch proxy
- Configuring `wire_api` settings for provider compatibility
- Updating CC Switch database configs directly

## Architecture

CC Switch is a local proxy (default `127.0.0.1:15721`) that intercepts Codex/Claude CLI requests and forwards them to third-party LLM providers. It manages config in its SQLite database (`~/.cc-switch/cc-switch.db`). The CC Switch executable lives at `C:\Users\<user>\AppData\Local\Programs\CC Switch\cc-switch.exe` (scoop install) or under scoop's shim directory (`cc-switch` on PATH).

| Table | Purpose |
|-------|---------|
| `providers` | Source of truth — user-configured provider settings |
| `proxy_config` | **v3.18.0+** — Per-app proxy enable/disable flags. `enabled=0` means proxy won't start. |
| `proxy_live_backup` | Live config used by the running proxy (restored on startup). Must be cleared to force re-takeover. |
| `provider_endpoints` | Upstream API URLs per provider |

**Critical**: 
- In v3.18.0+, `proxy_config` table must have `enabled=1` and `proxy_enabled=1` for the proxy to listen. Default is `enabled=0`.
- `providers` and `proxy_live_backup` must be in sync when changing config, then CC Switch must be restarted.
- Clearing `proxy_live_backup` before restart forces CC Switch to re-read and re-takeover from the provider config.

## The `wire_api` Setting

Codex CLI uses OpenAI's API format. The `wire_api` setting in the provider config controls which endpoint Codex targets:

| Value | Endpoint | Compatible with |
|-------|----------|-----------------|
| `"responses"` | `/v1/responses` (WebSocket + HTTPS) | OpenAI only |
| `"chat"` | `/v1/chat/completions` | Most third-party providers (DashScope, DeepSeek, etc.) |

**Pitfall**: DashScope (Alibaba/Qianwen) does NOT support `/v1/responses`. If `wire_api = "responses"`, DashScope returns HTTP 404. Always use `"chat"` for third-party providers.

## Claude Desktop (GUI) Special Considerations

CC Switch handles Claude Desktop differently from Claude Code (CLI). The GUI app does not use a config file like `~/.codex/config.toml`; instead CC Switch uses the `deploymentMode: "3p"` flag and environment variables to redirect API calls.

### CRITICAL: Squirrel vs MSIX Installation

Claude Desktop can be installed in TWO ways, and CC Switch handles them differently:

| Aspect | Squirrel (legacy .exe) | MSIX (Windows Store / Claude Setup.exe) |
|--------|-------------------------|-------------------------------------------|
| Install path | `AppData\Local\AnthropicClaude\app-<ver>\` | `Program Files\WindowsApps\Claude_<ver>_x64__pzs8sxrjxfjjc\` |
| Config location | `AppData\Local\Claude\claude_desktop_config.json` | `AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json` |
| Env var inheritance | ✅ Inherits from launcher | ❌ Sandboxed — cannot read injected env vars |
| 3P configuration | Written by CC Switch via `deploymentMode: "3p"` in `Local\Claude\` | Same flag but at MSIX package path above |
| Verification | Check for `Update.exe` + `Squirrel-*.log` | Check `winget list` or `Get-AppxPackage *Claude*` |

**Detection**: Run `winget list --name Claude` to see the version. An MSIX install shows a package family name like `Claude_pzs8sxrjxfjjc`.

### How CC Switch Takeover Works for Claude Desktop

1. CC Switch writes `{"deploymentMode": "3p"}` to the correct `claude_desktop_config.json` (path depends on install type)
2. The `3p` (third-party) mode tells Claude Desktop to use a custom API endpoint and auth token instead of connecting to claude.ai
3. **For Squirrel installs**: CC Switch injects `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` env vars when launching Claude
4. **For MSIX installs**: Env vars are **ignored** (sandbox). The `3p` config must be populated in `Claude-3p/configLibrary/` under the MSIX package path. CC Switch does this via live takeover
5. The local proxy (port 15721) handles request forwarding

### Critical: Proxy Server Doesn't Auto-Start

The proxy server (port 15721) does NOT always start automatically when CC Switch launches, even with `enableLocalProxy: true` in `settings.json` and `enabled=1` in `proxy_config`. DB changes alone are not enough — you must toggle the routing service from the CC Switch GUI:

1. Open CC Switch window
2. Click **设置** (Settings) button (top-right, gear icon)
3. Click the **路由** (Routing) tab
4. Under **路由总开关** (Master Routing Switch), toggle the button to **运行中** (Running)
5. Also toggle **Claude** routing switch to enabled (appears below master switch when routing is active)
6. Verify: `netstat -ano | findstr 15721` shows LISTENING
7. Verify in logs: `[SRV-001] 代理服务器启动于 127.0.0.1:15721`

**Pitfall**: Relaunching CC Switch via `launch_app` or terminal does NOT trigger the proxy to auto-start. You must toggle it through the UI or it stays stopped even if `enableLocalProxy` is true.

### Key Config Files by Install Type

**Squirrel (legacy):**
| Path | Purpose |
|------|---------|
| `AppData\Local\Claude\claude_desktop_config.json` | `deploymentMode` flag (3p vs default) |
| `AppData\Roaming\Claude\claude_desktop_config.json` | User preferences (Cowork, web search) |
| `AppData\Roaming\Claude\logs\main.log` | App lifecycle logs |
| `AppData\Roaming\Claude\logs\claude.ai-web.log` | Web UI / API connection logs |

**MSIX (package):**
| Path | Purpose |
|------|---------|
| `AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json` | `deploymentMode` flag + user preferences |
| `AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\config.json` | General settings (locale, theme, version) |
| `AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\logs\custom3p-setup.log` | 3P mode startup logs |
| `AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local\Claude-3p\configLibrary\*.json` | 3P profile entries |

### Critical: `proxy_config.enabled` for Claude

The `proxy_config` table has a SEPARATE entry for `app_type='claude'`. If `enabled=0` (the v3.18.0+ default), CC Switch will NOT perform live takeover for Claude Desktop even though the proxy server itself is running. The proxy may still forward requests that reach port 15721 via other routes (system proxy), but the takeover (config injection) is skipped.

**Always check this first** when Claude Desktop shows issues:

```python
import sqlite3
conn = sqlite3.connect('C:/Users/<user>/.cc-switch/cc-switch.db')
rows = conn.execute('SELECT app_type, enabled, live_takeover_active FROM proxy_config').fetchall()
for r in rows:
    print(f'{r[0]}: enabled={r[1]}, takeover={r[2]}')
```

To fix a disabled Claude entry:

```python
conn.execute('UPDATE proxy_config SET enabled=1, live_takeover_active=1 WHERE app_type=?', ('claude',))
conn.commit()
```

Then restart CC Switch for the change to take effect.

### MSIX Takeover Works Without Migration (Preferred Path)

MSIX-packaged Claude Desktop **can** work with CC Switch without switching to Squirrel. The key difference is that MSIX runs in an AppContainer sandbox and **ignores environment variables** from the launcher — so takeover relies entirely on the routing proxy layer.

**Requirements for MSIX takeover to work:**
1. `proxy_config.enabled=1` for `app_type='claude'` in the DB
2. `deploymentMode: "3p"` written to the MSIX config path (`Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`)
3. **Routing service must be toggled on via GUI** (Settings → 路由 → 路由总开关 → 运行中). This is the #1 missed step — the proxy does NOT auto-start even with correct DB configs on v3.18.0+.
4. Claude routing toggle enabled under the master routing switch

**Verification**: After setup, `netstat -ano | findstr 15721` shows an ESTABLISHED connection from a Claude PID, and CC Switch log shows `[Claude] >>> 请求目标: https://api.deepseek.com/anthropic/v1/messages`.

**When to migrate to Squirrel instead**: The MSIX path is preferred but fails if the routing service cannot be toggled on (e.g., headless/server with no GUI). In that case, see the migration workflow below.

### MSIX → Squirrel Migration (Fallback Path)

If MSIX takeover fails and routing-toggling is not possible, switch to Squirrel install:

1. **Uninstall MSIX**: `powershell "Get-AppxPackage -Name '*Claude*' | Remove-AppxPackage"`
2. **Clean up**: Delete `Packages\Claude_pzs8sxrjxfjjc\` directory  
3. **Get Squirrel installer**: Either run `Claude Setup.exe --exe` (downloads ~218MB Squirrel EXE) or download manually via aria2c
4. **Install**: Run the downloaded Squirrel EXE directly
5. **Verify**: Check `AnthropicClaude\Update.exe` exists → CC Switch takeover works

For the full step-by-step with commands, see [`references/squirrel-reinstall-workflow.md`](references/squirrel-reinstall-workflow.md).

**Pitfall**: The `Claude Setup.exe` bootstrapper auto-detects elevation and prefers MSIX install. Use `--exe` to explicitly force Squirrel mode. Without this flag, even running from Downloads may trigger MSIX install if UAC was accepted.

## Critical: Codex CLI vs Codex Desktop

**Codex Desktop (GUI app)** — CC Switch can proxy it successfully. The GUI app respects `base_url` and `experimental_bearer_token` injected by CC Switch.

**Codex CLI v0.145.0+** — **CANNOT be proxied through CC Switch's HTTP proxy.** It hardcodes WebSocket connections to `wss://api.openai.com/v1/responses`, completely ignoring:
- `base_url` in `~/.codex/config.toml`
- `wire_api` setting (`"chat"` is ignored)
- `OPENAI_BASE_URL` / `OPENAI_API_BASE` environment variables
- The CC Switch proxy port

**Diagnosis**: The error log shows `wss://api.openai.com/v1/responses` even when `base_url = "http://127.0.0.1:15721/v1"` is set. The WebSocket endpoint is baked into Codex CLI's binary.

**Workarounds**:
1. Use **Codex Desktop GUI** instead — CC Switch proxies it correctly
2. Use **Claude Code** with CC Switch (supports third-party via env vars)
3. Use **OpenCode** (open-source, provider-agnostic, supports custom endpoints)

## Common Failures & Fixes

### 1. 401 Unauthorized from OpenAI

**Symptom**: Codex connects directly to `wss://api.openai.com/v1/responses` instead of the local proxy, gets 401.

**Root cause**: CC Switch not running, or not properly intercepting Codex's config.

**Fix**:
1. Check CC Switch is running: `tasklist | findstr cc-switch` or `netstat -ano | findstr 15721`
2. If not running, launch from Start menu or `C:\Users\<user>\AppData\Local\Programs\CC Switch\cc-switch.exe`
3. Verify `~/.codex/config.toml` has `base_url = "http://127.0.0.1:15721/v1"`
4. Verify `~/.codex/auth.json` has the CC Switch proxy token

### 2. 404 from Upstream Provider

**Symptom**: CC Switch forwards to upstream but gets 404.

**Root cause**: `wire_api` is set to `"responses"` but the upstream doesn't support that endpoint.

**Fix**: Update `wire_api` to `"chat"` in both database tables (see "Updating Config" below).

### 3. Proxy Not Starting (port 15721 not listening)

**Symptom**: `netstat -ano | findstr 15721` shows no listener, though CC Switch process is running.

**Root cause (v3.18.0+)**: Two possible causes:
1. The `proxy_config` table has `enabled=0` for the app type (CC Switch v3.18.0 defaults all proxy entries to disabled)
2. The routing service was never toggled on via the GUI — `enableLocalProxy: true` and DB fixes alone are insufficient

**Fix step 1 — Check & enable DB**:
```python
import sqlite3, os
db = os.path.expanduser('~/.cc-switch/cc-switch.db')
conn = sqlite3.connect(db)
conn.execute("UPDATE proxy_config SET enabled=1, proxy_enabled=1 WHERE app_type='codex'")
conn.execute("UPDATE proxy_config SET enabled=1, proxy_enabled=1 WHERE app_type='claude'")
conn.execute("DELETE FROM proxy_live_backup")
conn.commit()
conn.close()
```

**Fix step 2 — Toggle routing via GUI (REQUIRED)**:
Even after fixing the DB, the proxy WILL NOT start without toggling through the UI:
1. Open CC Switch window
2. Click **设置** (gear icon, top-right)
3. Click **路由** tab
4. Toggle **路由总开关** to **运行中**
5. Toggle **Claude** routing to enabled
6. Verify: `netstat -ano | findstr 15721` shows LISTENING
7. Verify CC Switch log shows: `[SRV-001] 代理服务器启动于 127.0.0.1:15721`

**Fix step 3 — If GUI toggle is not possible**:
Kill and relaunch CC Switch, then immediately use computer_use to toggle the routing switch:
```
taskkill /F /IM "cc-switch.exe"
# Then launch via mcp launch_app, wait 5-8s, open settings, click 路由 tab, toggle routing on
```

**Old versions (pre-3.18)**: Check `~/.cc-switch/settings.json` for `"enableLocalProxy": true`.

### 4. CC Switch Overwrites `wire_api` to "responses"

**Symptom**: You set `wire_api = "chat"` in provider config, but after CC Switch takeover, `~/.codex/config.toml` shows `wire_api = "responses"`.

**Root cause**: CC Switch v3.18.0 hardcodes `wire_api = "responses"` for Codex during takeover, regardless of provider config string. The proxy translates WebSocket/Responses API calls to chat completions upstream.

**Impact**: Only affects Codex CLI (ignores proxy entirely). Codex Desktop respects the proxy despite this config value. No workaround to change it — CC Switch always overrides.

### 5. auth_mode "api_key" is Invalid

**Symptom**: `codex exec` fails with: `unknown variant \`api_key\`, expected one of \`apikey\`, \`chatgpt\`...`

**Root cause**: CC Switch writes `auth_mode: "api_key"` (underscore) to `~/.codex/auth.json`, but Codex CLI only accepts `"apikey"` (no underscore).

**Fix**: Edit `~/.codex/auth.json`: change `"api_key"` to `"apikey"`. CC Switch may overwrite on restart, so also fix the provider config in the DB.

### 6. Claude Desktop Empty UI / "Cowork Requires Reinstall"

**Symptom**: Claude Desktop launches but the window is blank/empty (UIA tree shows only title bar buttons). Or Claude shows "Cowork 需要通过现代安装程序安装 Claude Desktop" ("Cowork needs to be installed through the modern installer") despite Claude being properly installed via Squirrel.

**Root cause (two overlapping issues)**:
1. `proxy_config.enabled=0` for `app_type='claude'` — CC Switch skips live takeover, so `deploymentMode: "3p"` may be missing or stale
2. The `ANTHROPIC_BASE_URL` env var points to `https://api.deepseek.com/anthropic` (the upstream), not `http://127.0.0.1:15721` (the local proxy). Without CC Switch interception, Claude connects directly to the upstream and the UI never renders properly if the upstream doesn't support Claude's web UI bundle

**Diagnostic steps**:
1. **Determine install type**: `winget list --name Claude` or check for `Update.exe` in `AnthropicClaude`
2. Check the correct `claude_desktop_config.json`:
   - Squirrel: `Local\Claude\claude_desktop_config.json`
   - MSIX: `Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`
   — does it have `"deploymentMode": "3p"`?
3. Check `proxy_config` in the DB — is `enabled=1` for `app_type='claude'`?
4. Check `settings.json` — is `enableLocalProxy: true`?
5. Check routing server status: `netstat -ano | findstr 15721` — is it LISTENING?
6. Check web log at `Roaming\Claude\logs\claude.ai-web.log` for `Failed to fetch` or `account_profile data is undefined` (indicates Claude is trying to reach claude.ai directly)
7. For MSIX: check `Packages\...\LocalCache\Roaming\Claude\logs\custom3p-setup.log` for `custom_3p_not_available` errors
8. Check main log at `Roaming\Claude\logs\main.log` for any startup errors
9. Check the Claude window via UIA (`get_window_state`) — if only title bar buttons appear, the web content is not rendering

**Fix**:
1. Enable Claude in proxy_config (see "Critical: proxy_config.enabled for Claude" above)
2. Toggle routing service ON via CC Switch GUI (Settings → 路由 → 路由总开关 → 运行中)
3. Kill all Claude processes: `taskkill /F /IM claude.exe`
4. Restart CC Switch: `taskkill /F /IM cc-switch.exe`, then relaunch from Start menu or `C:\Users\<user>\AppData\Local\Programs\CC Switch\cc-switch.exe`
5. Wait 5-10 seconds for CC Switch to initialize and perform takeover
6. Toggle routing service ON again (it may not survive restart — repeat step 2)
7. Launch Claude Desktop — it should start in 3p mode with proper env vars
8. Verify in CC Switch logs (`~/.cc-switch/logs/cc-switch.log`) that requests appear:
   `[Claude] >>> 请求目标: https://api.deepseek.com/anthropic/v1/messages`

**If the UI is still blank after takeover**:
- For Squirrel installs: Delete `Local\Claude\claude_desktop_config.json` and restart CC Switch — it will recreate it with proper 3p config
- For MSIX installs: Manually add `"deploymentMode": "3p"` to `Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`
- Verify `enableLocalProxy: true` in `~/.cc-switch/settings.json`
- Verify the provider's `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` are set correctly in the CC Switch database
- Check if Claude is showing a login screen (not blank) — this means 3p mode is NOT active and Claude is trying to connect to claude.ai normally

## Debugging Steps

1. **Check CC Switch is running**:
   ```bash
   tasklist | findstr cc-switch
   netstat -ano | findstr 15721
   ```

2. **Check logs**:
   ```bash
   tail -50 ~/.cc-switch/logs/cc-switch.log
   ```
   Look for `[FWD-003]` errors indicating upstream failures.

3. **Test proxy directly**:
   ```bash
   curl -X POST http://127.0.0.1:15721/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"qwen3.7-plus","messages":[{"role":"user","content":"hi"}]}'
   ```

4. **Test upstream directly** (bypass CC Switch):
   ```bash
   curl -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
     -H "Authorization: Bearer <api-key>" \
     -H "Content-Type: application/json" \
     -d '{"model":"qwen3.7-plus","messages":[{"role":"user","content":"hi"}]}'
   ```

5. **Check Codex config**:
   ```bash
   cat ~/.codex/config.toml | head -10
   ```
   `base_url` should be `http://127.0.0.1:15721/v1`.

6. **Check auth**:
   ```bash
   cat ~/.codex/auth.json
   ```
   Should have the CC Switch proxy token (not a real OpenAI key).

## Updating Config

### Update `wire_api` in CC Switch

Both tables must be updated, then restart CC Switch:

```python
import sqlite3, json, os

db_path = os.path.expanduser('~/.cc-switch/cc-switch.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

provider_id = '6bc4439a-69ad-494d-b00a-f8981c7ecef8'  # Replace with actual provider ID

# Update providers table
row = conn.execute('SELECT settings_config FROM providers WHERE id = ?', (provider_id,)).fetchone()
if row:
    config = json.loads(row['settings_config'])
    if 'config' in config:
        config['config'] = config['config'].replace('wire_api = "responses"', 'wire_api = "chat"')
        conn.execute('UPDATE providers SET settings_config = ? WHERE id = ?',
                    (json.dumps(config), provider_id))

# Update proxy_live_backup table
row = conn.execute('SELECT original_config FROM proxy_live_backup WHERE app_type = ?', ('codex',)).fetchone()
if row:
    config = json.loads(row['original_config'])
    if 'config' in config:
        config['config'] = config['config'].replace('wire_api = "responses"', 'wire_api = "chat"')
        conn.execute('UPDATE proxy_live_backup SET original_config = ? WHERE app_type = ?',
                    (json.dumps(config), 'codex'))

conn.commit()
conn.close()
```

Then restart CC Switch:
1. Kill the process: `taskkill /F /PID <pid>`
2. Relaunch from Start menu or `C:\Users\<user>\AppData\Local\Programs\CC Switch\cc-switch.exe`
3. Wait 5-10 seconds for the proxy to start
4. Verify: `netstat -ano | findstr 15721`

## Provider Compatibility Matrix

| Provider | `wire_api` | Upstream URL | auth_mode | Notes |
|----------|------------|--------------|-----------|-------|
| DashScope (Qianwen) | `"chat"` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `api_key` | Does NOT support `/v1/responses` |
| DeepSeek (Claude) | `"chat"` | `https://api.deepseek.com/anthropic` | env vars | Uses ANTHROPIC_AUTH_TOKEN for Claude |
| DeepSeek (Codex) | `"responses"` (overridden by CC Switch) | `https://api.deepseek.com` | `apikey` | Must use `apikey` not `api_key` in auth.json |
| Kimi | `"chat"` | Provider-specific | varies | Test with `"chat"` first |
| OpenAI | `"responses"` | `https://api.openai.com/v1` | `apikey` | Only OpenAI supports `/v1/responses` |

## Rules

1. **Always use `"chat"` for third-party providers** — DashScope and most others don't support OpenAI's Responses API
2. **Update both database tables** — `providers` and `proxy_live_backup` must be in sync
3. **Check `proxy_config` first on v3.18.0+** — Proxy won't start if `enabled=0` for the app type. Check `SELECT app_type, enabled FROM proxy_config` before anything else. **Claude Desktop** has its OWN entry (`app_type='claude'`) separate from Codex — both must be enabled.
4. **Restart CC Switch after config changes** — The proxy loads config into memory on startup
5. **Test the proxy directly with curl** — Isolates whether the issue is CC Switch or the upstream
6. **Check logs for `[FWD-003]` errors** — These indicate upstream failures with status codes
7. **Verify `base_url` in Codex config** — Must point to the CC Switch proxy, not directly to upstream
8. **Codex CLI cannot be proxied** — v0.145.0+ uses hardcoded WebSocket to OpenAI. Use Codex Desktop GUI instead.
9. **For Claude Desktop, check the UI via UIA** — An empty window (only title bar buttons) means the web content isn't loading. Always check `get_window_state` or take a screenshot to diagnose.
