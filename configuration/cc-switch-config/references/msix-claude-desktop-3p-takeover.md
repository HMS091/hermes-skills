# MSIX Claude Desktop 3P Takeover Reference

## Background

When Claude Desktop is installed via the official `Claude Setup.exe` (which now distributes an MSIX package on Windows 10+), it runs inside an AppContainer sandbox. This fundamentally changes how CC Switch's takeover mechanism works.

## Key Differences from Squirrel Install

| Aspect | Squirrel | MSIX |
|--------|----------|------|
| Detection | `Update.exe` in `AnthropicClaude\` | `winget list Claude` shows version, `Get-AppxPackage *Claude*` shows family name |
| Config root | `AppData\Local\Claude\` | `AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\` |
| Env vars via launcher | ✅ Works | ❌ Sandbox ignores them |
| Proxy auto-start after launch | Sometimes | Requires GUI toggle (see below) |

## Config File Locations (MSIX)

```
Packages\Claude_pzs8sxrjxfjjc\LocalCache\
├── Roaming\Claude\
│   ├── claude_desktop_config.json    # deploymentMode + preferences
│   ├── config.json                   # locale, theme, version
│   └── logs\
│       ├── main.log                  # app lifecycle
│       ├── claude.ai-web.log         # web UI connections
│       └── custom3p-setup.log        # 3P mode startup errors
└── Local\
    └── Claude-3p\
        └── configLibrary\
            ├── _meta.json            # which profile is active
            └── <uuid>.json           # individual 3P profile entry
```

## CC Switch Database Commands

```sql
-- Check proxy config (enabled=1 is required)
SELECT app_type, enabled, proxy_enabled, live_takeover_active FROM proxy_config WHERE app_type='claude';

-- Enable Claude proxy takeover
UPDATE proxy_config SET enabled=1, live_takeover_active=1 WHERE app_type='claude';

-- Force fresh takeover
DELETE FROM proxy_live_backup;
```

## Proxy Not Starting Troubleshooting (v3.18.0+)

Even with `proxy_config.enabled=1` and `settings.json.enableLocalProxy=true`, the proxy server on port 15721 may NOT start. The CC Switch GUI has a separate on/off state for the routing service.

**Symptoms**:
- `netstat -ano | findstr 15721` → nothing
- CC Switch log shows `正常启动模式：主窗口已显示` but NO `[SRV-001] 代理服务器启动于 127.0.0.1:15721`
- Log continues without proxy entries for minutes

**Solution**: Toggle routing service on via GUI:
1. Open CC Switch window
2. Click gear icon (设置)
3. Click 路由 tab
4. Toggle 路由总开关 → 运行中
5. Toggle Claude routing switch to enabled
6. Verify log shows `[SRV-001] 代理服务器启动于 127.0.0.1:15721`

## 3P Mode Verification

When Claude Desktop starts in 3P mode with a properly configured proxy:
- The window shows "Claude for Windows" sign-in page (not blank)
- The file `custom3p-setup.log` shows `custom_3p_not_available` errors — these are NORMAL for 3P mode and indicate Claude is NOT trying to reach claude.ai
- The `claude_desktop_config.json` must contain `"deploymentMode": "3p"`
- The CC Switch log shows `[Claude] >>> 请求目标: ...` when requests flow through the proxy

If the window is blank (only title bar buttons visible via UIA), the web content isn't loading — check that:
1. `deploymentMode: "3p"` is set in the correct config file (MSIX path, not old Local\Claude path)
2. The routing service is actually running (port 15721 listening)
3. The provider (DeepSeek) is enabled and has valid credentials
