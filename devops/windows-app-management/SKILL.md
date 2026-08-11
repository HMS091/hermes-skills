---
name: windows-app-management
description: Install, uninstall, and clean up Windows desktop applications — especially Squirrel/MSIX-based apps behind problematic proxies. Covers complete removal, offline local-MSIX install, and aria2c download recovery.
---

# Windows App Management

Manage Windows desktop applications: complete uninstall (kill processes → uninstaller → cleanup registry/data/shortcuts), and offline install via pre-downloaded MSIX packages when the built-in downloader keeps failing.

## Trigger

- User asks to uninstall a Windows desktop app completely ("删干净")
- User asks to install/reinstall a Windows desktop app whose installer keeps failing mid-download (EOF, connection reset, SSL errors)
- User asks to clean up app data remnants after uninstall

## Workflow

### 1. Uninstall Squirrel/MSIX-based apps completely

#### 1a. Kill running processes first

```bash
taskkill /f /im <app>.exe
```

The app's own uninstaller (Squirrel `Update.exe`) acquires a mutex lock — it will fail with `"Couldn't acquire lock, is another instance running"` if the app is still running.

#### 1b. Run the app's own uninstaller

Squirrel-based apps (Claude Desktop, Discord, Slack, etc.) put an `Update.exe` in their install directory:

```bash
"C:\Users\<user>\AppData\Local\<AppName>\Update.exe" --uninstall -s
```

The `-s` flag runs silently.

Alternatively via winget:
```bash
winget uninstall "<Publisher.AppName>" --force
```

**Scope trap**: winget may fail with `"The package installed for user scope cannot be uninstalled when running with administrator privileges"`. When this happens, use the app's own `Update.exe --uninstall` approach instead — it handles user-scope uninstall correctly.

#### 1c. Clean up all remnants

```bash
# Local app data
rm -rf "/c/Users/<user>/AppData/Local/<AppName>"
rm -rf "/c/Users/<user>/AppData/Local/<AppName-extra-dirs>"

# Roaming data (user config, sessions, etc.)
rm -rf "/c/Users/<user>/AppData/Roaming/<AppName>"
rm -rf "/c/Users/<user>/AppData/Roaming/<AppName-extra-dirs>"

# Start Menu shortcut
rm -f "/c/Users/<user>/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/<AppName>.lnk"

# Registry (HKCU uninstall key)
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\<AppNameRegKey>" /f
```

#### 1d. Verify removal

```bash
winget list --name <AppName>    # should return nothing
tasklist | grep -i <app>        # should return nothing
```

### 2. Install Squirrel/MSIX apps from local file (bypass flaky download)

When the installer's built-in download keeps failing at ~10–20% with `unexpected EOF` / `server closed abruptly (missing close_notify)`, the MSIX download is being dropped by the network proxy. Solution: download the MSIX separately with a robust tool, then feed it to the installer.

#### 2a. Install aria2c

```bash
winget install aria2.aria2 --accept-package-agreements --accept-source-agreements
```

aria2c handles multi-connection downloads and retries far better than curl for flaky CDN connections.

#### 2b. Get the MSIX URL

Run the installer once and capture the MSIX URL from its log at `%TEMP%\ClaudeSetup.log`:

```
MSIX URL: https://downloads.claude.ai/releases/win32/x64/1.24012.9/Claude-<hash>.msix
```

Alternatively, the redirect API the installer hits:
```
MSIX URL: https://api.anthropic.com/api/desktop/win32/x64/msix/latest/redirect
```

#### 2c. Download MSIX with aria2c

**IMPORTANT**: If previous partial downloads exist (from curl etc.), delete them FIRST — mixing partial curl chunks with aria2c chunks corrupts the file and causes MSIX signature verification to fail.

```bash
rm -f "/c/Users/<user>/Downloads/<AppName>.msix"
```

```bash
cd /c/Users/<user>/Downloads
aria2c -x 4 -s 4 --retry-wait 10 --max-tries 50 --connect-timeout 60 --timeout 300 \
  --file-allocation=none --allow-overwrite=true -o <AppName>.msix \
  "<MSIX_URL>"
```

Key flags:
| Flag | Purpose |
|------|---------|
| `-x 4 -s 4` | 4 connections per file — speed vs reliability balance |
| `--retry-wait 10 --max-tries 50` | Aggressive retry for flaky connections |
| `--file-allocation=none` | Skip pre-allocation (saves startup time) |
| `--allow-overwrite=true` | Safe for re-downloads |

Wait for exit code 0 and `"Download complete"` in the output.

#### 2d. Install from local MSIX

```bash
"./<AppName> Setup.exe" -local-msix "C:\Users\<user>\Downloads\<AppName>.msix" -log-path "C:\Users\<user>\Downloads\<AppName>Install.log"
```

The installer will:
1. Verify the MSIX Authenticode signature (must match the bootstrapper)
2. Self-elevate (user sees UAC prompt — tell them to click "Yes")
3. Install via `AddPackage`
4. Launch the app automatically

Look for `"MSIX package installed successfully"` and `"=== <AppName> Setup completed successfully ==="` in the log.

#### 2e. Verify installation

```bash
winget list --name <AppName>    # should show version
ls -la "/c/Users/<user>/AppData/Local/<AppName>"  # install dir exists
tasklist | grep -i <app>        # process is running
```

### 3. Downloading through Clash/TUN proxy

When behind Clash in TUN mode:
- **Do NOT pass an explicit `-x` proxy** to curl/aria2c — TUN mode already routes all traffic transparently at the network level
- If you DO pass an explicit proxy (e.g. `-x http://127.0.0.1:10808`), you're double-proxying, which can cause `schannel: failed to receive handshake, SSL/TLS connection failed`
- Some CDN hosts (downloads.claude.ai) may still drop connections through TUN — aria2c's retry+multi-connection handles this
- For curl through Clash's HTTP proxy port (when not in TUN mode): check the registry key at `HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings` for `ProxyServer`
- Use `-k` (insecure) with curl through proxy if you get SSL handshake failures

## Pitfalls

- **MSIX signature verification failure after download**: If the MSIX fails with `"signature verification failed: MSIX signature is not valid (HRESULT: 0x800B0003)"`, the file is corrupted. Delete and re-download clean — do NOT resume from a partial curl download. aria2c properly reassembles chunks, but mixing curl partials + aria2c resume corrupts the file.
- **Squirrel uninstall lock**: `"Couldn't acquire lock, is another instance running"` — the app is still running. Kill it first with `taskkill /f /im <app>.exe`.
- **winget user-scope error**: `"The package installed for user scope cannot be uninstalled when running with administrator privileges"` — use the app's own `Update.exe --uninstall -s` instead.
- **UAC prompt during install**: The `-local-msix` path still triggers UAC elevation. The user needs to click "Yes" on the dialog.
- **Large file paths in curl**: curl on Windows (native binary) doesn't understand MSYS paths like `/c/Users/`. Use relative paths (change to download dir first) or Windows paths with `C:\` syntax.
- **Single connection vs multi-connection tradeoff**: Single connection (`-x 1`) is more reliable but much slower. Multi-connection (`-x 4`) is faster but more susceptible to partial corruption if mixed with other download tools. Always start clean.
