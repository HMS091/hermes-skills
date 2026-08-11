# Squirrel Reinstall Workflow (MSIX → Squirrel Migration)

## When to Use

Claude Desktop was installed as an MSIX package (via `winget install` or the official `Claude Setup.exe` bootstrapper), **and** CC Switch cannot perform takeover because:
- MSIX AppContainer sandbox blocks environment variable injection
- Claude shows login page instead of 3P mode
- CC Switch logs show no `[Claude]` requests even though takeover was "completed"
- `winget list --name Claude` shows a version like `1.24012.9.0` (with `.0` suffix = MSIX)

**Solution**: Uninstall MSIX Claude, reinstall using Squirrel (EXE) mode.

## Step 1: Uninstall MSIX Claude

Remove the MSIX package:

```powershell
Get-AppxPackage -Name '*Claude*' | Remove-AppxPackage
```

Wait for completion, then clean up leftover data:

```bash
rm -rf "/c/Users/<user>/AppData/Local/Packages/Claude_*/"
```

Verify removal:
```bash
powershell "Get-AppxPackage -Name '*Claude*' | Select-Object Name"
# Should return nothing
```

## Step 2: Get the Squirrel Installer

### Method A: Bootstrapper + `--exe` flag (when network is stable)

Run the official bootstrapper with the `--exe` flag to force Squirrel install:

```bash
"Claude Setup.exe" --exe
```

This downloads a ~218MB Squirrel EXE from:
`https://downloads.claude.ai/releases/win32/x64/<version>/Claude-<hash>.exe`

### Method B: Manual download via aria2c (when network is flaky)

If CC Switch's proxy is on (port 15721), use it. If not, go directly (may need system proxy like Clash TUN):

```bash
cd /c/Users/<user>/Downloads
aria2c -x 4 -s 4 --retry-wait 10 --max-tries 50 \
  --connect-timeout 60 --timeout 300 --file-allocation=none \
  -o Claude-Squirrel-Setup.exe \
  "https://downloads.claude.ai/releases/win32/x64/1.24012.9/Claude-03c61d06f8e01a4db2273b9514e225f21d2ba62e.exe"
```

**Why aria2c over curl**: The 218MB download frequently fails with `schannel: server closed abruptly (missing close_notify)` through proxy. aria2c with 4 connections + auto-retry handles flaky connections much better than curl. If curl is the only option, use `-C -` for resume and `--retry 20 --retry-delay 10`.

The URL above is from the `--exe` run's log output: `Fetching latest version from https://api.anthropic.com/api/desktop/win32/x64/exe/latest` → `Squirrel setup URL: https://downloads.claude.ai/releases/win32/x64/<version>/Claude-<hash>.exe`. Extract the actual URL from the log.

### Squirrel vs MSIX Installer Size

| File | Size | Type |
|------|------|------|
| `Claude Setup.exe` | 6.7 MB | Bootstrapper (downloads the real installer) |
| `Claude-<hash>.exe` (with `--exe`) | ~218 MB | Standalone Squirrel installer |
| `Claude-<hash>.msix` (with `--msix`) | ~246 MB | MSIX package |

## Step 3: Run the Squirrel Installer

Run the downloaded Squirrel EXE directly:

```bash
"/c/Users/<user>/Downloads/Claude-Squirrel-Setup.exe"
```

The installer runs silently (UAC prompt appears on screen, no terminal output). Wait ~30 seconds for completion.

## Step 4: Verify Squirrel Installation

Check these indicators:

```bash
# 1. Squirrel directory structure
ls /c/Users/<user>/AppData/Local/AnthropicClaude/
# Should show: app-<version>/, claude.exe, Update.exe, packages/, Squirrel-*.log

# 2. Config directory exists
ls /c/Users/<user>/AppData/Local/Claude/claude_desktop_config.json

# 3. No MSIX package remaining
powershell "Get-AppxPackage -Name '*Claude*' | Select-Object Name"
# Should return nothing

# 4. Claude is running via CC Switch takeover
tail -5 ~/.cc-switch/logs/cc-switch.log
# Should show: [Claude] >>> 请求目标: https://api.deepseek.com/anthropic/v1/messages
```

## Step 5: Verify CC Switch Takeover

After Squirrel reinstall, CC Switch should automatically pick up Claude Desktop:

1. Check `deploymentMode: "3p"` is written:
   ```bash
   cat /c/Users/<user>/AppData/Local/Claude/claude_desktop_config.json
   ```

2. Check proxy server is running:
   ```bash
   netstat -ano | findstr 15721
   ```

3. Check Claude → proxy connection established:
   ```bash
   netstat -ano | findstr 15721 | findstr ESTABLISHED
   ```

4. Check CC Switch log for live takeover:
   ```bash
   tail -10 ~/.cc-switch/logs/cc-switch.log
   # Look for: [Claude] >>> 请求目标: https://api.deepseek.com/anthropic/v1/messages
   ```

## Pitfalls

- **Squirrel installer asks for UAC**: It elevates and shows a UAC prompt — the user must click "Yes". Without user interaction, the installer hangs waiting.
- **MSIX cleanup is critical**: If the MSIX package is not properly removed, Windows may launch the MSIX version instead of the Squirrel version when `claude` is invoked. Always verify with `Get-AppxPackage`.
- **CC Switch proxy must be running**: Before launching Claude after reinstall, ensure the proxy server is running (`netstat -ano | findstr 15721` shows LISTENING). If not, toggle routing on via CC Switch GUI.
- **Old Squirrel log confusion**: The `Squirrel-*.log` files in `AnthropicClaude\` contain Squirrel setup debug output, not app runtime logs.
