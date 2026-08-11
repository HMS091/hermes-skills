# Claude Desktop Cowork / 3p Mode Diagnosis

Diagnose and fix Claude Desktop when it shows a login page, blank window, or "Cowork 需要通过现代安装程序安装 Claude Desktop" after CC Switch takeover.

## Quick Checklist

**Critical: Check the routing service first — the most common cause of failure is the proxy not being toggled on, not the DB config.**

- [ ] Is the proxy actually listening? `netstat -ano | findstr 15721` — if not LISTENING, the routing service is off
- [ ] Is the routing service toggled on? (Settings → 路由 → 路由总开关 → 运行中)
- [ ] Is Claude Desktop Squirrel or MSIX? Check `winget list --name Claude` and `C:\Users\<user>\AppData\Local\AnthropicClaude\`
- [ ] Does the correct `claude_desktop_config.json` have `"deploymentMode": "3p"`? (path depends on install type)
- [ ] Is `proxy_config.enabled=1` for `app_type='claude'` in CC Switch DB?
- [ ] Are requests appearing in CC Switch logs? Check `~/.cc-switch/logs/cc-switch.log` for `[Claude]`

## Two Fix Paths (MSIX vs Squirrel)

### Path A: MSIX Install (this session's approach)

MSIX-packaged Claude runs in an AppContainer sandbox — **environment variables injected by CC Switch are ignored**. The fix relies entirely on the routing proxy:

1. **Ensure routing is toggled on** (this is the #1 missed step):
   - Open CC Switch window
   - Click 设置 (gear icon, top-right)
   - Click 路由 tab
   - Toggle 路由总开关 to 运行中 (Running)
   - Toggle the Claude routing switch to enabled
   - Verify: `netstat -ano | findstr 15721` shows LISTENING
   - Verify log: `[SRV-001] 代理服务器启动于 127.0.0.1:15721`

2. **Write `deploymentMode: "3p"` to MSIX config path**:
   - Path: `Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`
   - Content: `{"deploymentMode": "3p"}`
   - *(CC Switch should do this automatically, but verify if Claude shows login page)*

3. **Kill and restart Claude**: `taskkill /F /IM claude.exe` then relaunch via Start menu or AUMID

4. **Verify**: CC Switch log shows `[Claude] >>> 请求目标: https://api.deepseek.com/anthropic/v1/messages`

### Path B: Squirrel Install (legacy CC Switch approach)

CC Switch injects `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN` etc. as environment variables. The Squirrel process inherits them.

1. Check `Local\Claude\claude_desktop_config.json` has `"deploymentMode": "3p"`
2. Ensure routing service is running (same as Path A step 1)
3. Kill and restart Claude: `taskkill /F /IM claude.exe` then relaunch
4. Verify: CC Switch log shows `[Claude]` requests

## Step-by-Step Diagnosis

### 1. Determine Install Type

```bash
# Check for Squirrel install
ls "C:\Users\<user>\AppData\Local\AnthropicClaude\"
# If this exists with Update.exe → Squirrel install

# Check for MSIX install  
winget list --name Claude
# Version with .0 suffix (1.24012.9.0) → MSIX
# Version without .0 (1.24012.9) → Squirrel

# Also check via PowerShell
powershell "Get-AppxPackage -Name '*Claude*' | Select-Object Name"
# If returns Claude_pzs8sxrjxfjjc → MSIX
```

### 2. Check the CC Switch Database

```python
import sqlite3, json, os
conn = sqlite3.connect(os.path.expanduser('~/.cc-switch/cc-switch.db'))
conn.row_factory = sqlite3.Row

rows = conn.execute('SELECT app_type, enabled, proxy_enabled, live_takeover_active FROM proxy_config').fetchall()
for r in rows:
    print(f'{r[0]}: enabled={r[1]}, proxy={r[2]}, takeover={r[3]}')

settings = json.load(open(os.path.expanduser('~/.cc-switch/settings.json')))
print(f"enableLocalProxy={settings.get('enableLocalProxy')}")
print(f"currentProviderClaudeDesktop={settings.get('currentProviderClaudeDesktop')}")
```

### 3. Check Claude Logs

**Squirrel:**
```bash
tail -50 ~/AppData/Roaming/Claude/logs/main.log
tail -50 ~/AppData/Roaming/Claude/logs/claude.ai-web.log
```

**MSIX:**
```bash
# 3P mode startup log
cat "C:\Users\<user>\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\logs\custom3p-setup.log"
# Main lifecycle log
cat "C:\Users\<user>\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\logs\main.log"
```

**Key errors:**
- `Failed to fetch` / `account_profile data is undefined` → Claude connecting to claude.ai directly (3P mode not active)
- `custom_3p_not_available` → Claude IS in 3P mode but can't find the account/profile API (normal for 3P!)
- `Bootstrap request failed: 503 Service Unavailable` → Claude trying bootstrap endpoint (harmless in 3P)

### 4. Check the Claude Window

Claude Desktop is an Electron app. The UIA tree shows the web content in a Chromium Document pane, not as native controls.

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Only title bar buttons visible (window recently opened) | Web content still loading | Wait 20-30s, recheck |
| Cloude for Windows / Sign in page | 3P mode NOT active; Claude connecting to claude.ai | Write `"deploymentMode":"3p"` to correct config path |
| Full UI with model selector showing DeepSeek-V4-pro | ✅ Working correctly | — |
| Cowork requires modern installer | Squirrel install detected by CC Switch's desktop mode check | Ignore — normal for Squirrel installs |

### 5. CC Switch Logs

Check `~/.cc-switch/logs/cc-switch.log` for key entries:

```log
[SRV-001] 代理服务器启动于 127.0.0.1:15721          ← proxy running
[Claude] Live 配置已接管，代理地址: http://127.0.0.1:15721  ← takeover done
[Claude] >>> 请求目标: https://api.deepseek.com/anthropic/v1/messages (model=DeepSeek-V4-flash)  ← requests flowing
[FWD-003] Provider DeepSeek 请求失败: 上游 HTTP 404   ← upstream error
```

- Proxy running + takeover done but NO `[Claude]` requests → Claude is NOT using the proxy
- No `[SRV-001]` → routing service is off → toggle it on via GUI

## Common Fix Sequence (MSIX)

```
1. sqlite3: UPDATE proxy_config SET enabled=1 WHERE app_type='claude'
2. Delete proxy_live_backup
3. Kill CC Switch + relaunch
4. GUI: Settings → 路由 → toggle 路由总开关 ON
5. GUI: Settings → 路由 → toggle Claude routing ON
6. Verify: netstat shows 15721 LISTENING
7. Kill Claude + relaunch
8. Verify: CC Switch log shows [Claude] requests
```

## Critical: Routing Service Must Be Toggled On Manually

This is the #1 gotcha on CC Switch v3.18.0+. The proxy server (port 15721) does NOT auto-start even when:
- `settings.json` has `enableLocalProxy: true`
- `proxy_config` has `enabled=1` and `proxy_enabled=1`
- CC Switch log shows "正常启动模式：主窗口已显示"

The only way to start it is: **Settings → 路由 → toggle 路由总开关 to 运行中**.

This state does NOT persist across CC Switch restarts. Every time CC Switch relaunches, you must toggle routing on again (unless the previous toggle state was saved during a clean exit).

## Environment Variables (Squirrel only — MSIX ignores these)

```env
ANTHROPIC_AUTH_TOKEN=sk-<redacted>
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_MODEL=DeepSeek-V4-flash
ANTHROPIC_DEFAULT_HAIKU_MODEL=DeepSeek-V4-flash
ANTHROPIC_DEFAULT_SONNET_MODEL=DeepSeek-V4-pro[1M]
ANTHROPIC_DEFAULT_OPUS_MODEL=DeepSeek-V4-pro[1M]
```

Note: `ANTHROPIC_BASE_URL` points to the upstream DeepSeek API, not `127.0.0.1:15721`. CC Switch intercepts the request via its proxy routing layer.
