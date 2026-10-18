---
name: windows-github-upgrade
description: Upgrade Windows portable software from GitHub releases — proxy detection, download, and safe replacement.
---

# Windows GitHub Software Upgrade

Upgrade portable Windows executables by downloading from GitHub Releases when the machine sits behind a proxy.

## Trigger

User asks to upgrade a Windows program from a GitHub release URL (e.g. `https://github.com/<owner>/<repo>/releases/tag/vX.Y.Z`).

See `references/cc-switch.md` for CC Switch-specific paths and asset naming patterns.

## Workflow

### 1. Check current version

```bash
ls -la "/c/Users/<user>/AppData/Local/Programs/<App Name>/"
```

### 2. Detect proxy

On Windows, the proxy may be set at the system level (not env vars). Check both:

```bash
# Method 1: Windows system proxy (most common with Clash/v2ray TUN mode)
powershell -Command "Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' | Select-Object ProxyEnable, ProxyServer, ProxyOverride"
```

If `ProxyEnable=1` and `ProxyServer` is set (e.g. `127.0.0.1:10808`), use that as the curl proxy: `-x "http://127.0.0.1:10808"`.

Also scan common localhost proxy ports as a fallback: `7890 7891 1080 10808 10809 8118 9090`.

**Try direct connection first.** The proxy may not be needed — GitHub may be reachable directly. Only fall back to proxy when direct `curl -s --connect-timeout 5 "https://github.com"` fails. The proxy can also go down mid-session; re-check direct connectivity before retrying.

### 3. Fetch release info via GitHub API

```bash
curl -s -x "http://127.0.0.1:<PORT>" \
  "https://api.github.com/repos/<owner>/<repo>/releases/tags/vX.Y.Z" | \
  python -c "import sys,json; d=json.load(sys.stdin); [print(a['name'],a['browser_download_url']) for a in d.get('assets',[])]"
```

### 4. Pick the right asset

Match architecture (`uname -m` or `powershell -Command "(Get-WmiObject Win32_Processor).AddressWidth"`):
- `x86_64` / `64` → Windows-Portable.zip (or Windows.msi)
- `arm64` → Windows-arm64-Portable.zip

### 5. Download

**Preferred path: Python `execute_code` (bypasses git-bash path issues).** When `curl` fails on Windows — especially with Chinese characters in paths, missing `/tmp`, or timeouts — switch to `execute_code`:

```python
import urllib.request, os

dest = r"C:\Users\<user>\<filename>.zip"
url = "https://github.com/<owner>/<repo>/releases/download/vX.Y.Z/<asset>.zip"
urllib.request.urlretrieve(url, dest)
print(f"Downloaded: {os.path.getsize(dest)} bytes")
```

**Curl fallback (when proxy is required and working):** GitHub release downloads redirect to `objects.githubusercontent.com`. Proxy CONNECT tunnels to this host often fail SSL handshake. **Always use `-k`**:

```bash
curl -L -k -x "http://127.0.0.1:<PORT>" \
  -o "/c/Users/<user>/<filename>.zip" \
  "https://github.com/<owner>/<repo>/releases/download/vX.Y.Z/<asset>.zip"
```

Without `-k`, expect: `curl: (35) schannel: failed to receive handshake, SSL/TLS connection failed`.

### 6. Inspect and install

**Preferred: Python `zipfile`** (same `execute_code` call, no shell path issues):

```python
import zipfile, os, shutil

target_dir = r"C:\Users\<user>\AppData\Local\Programs\<App Name>"
zip_path = r"C:\Users\<user>\<filename>.zip"

# Backup
exe_path = os.path.join(target_dir, "app.exe")
if os.path.exists(exe_path):
    shutil.copy2(exe_path, exe_path + ".bak")

# Extract
with zipfile.ZipFile(zip_path, 'r') as zf:
    zf.extractall(target_dir)

# Cleanup
os.remove(zip_path)
```

**Shell fallback** (only when terminal is healthy):

```bash
unzip -l "<zip>"                         # check contents
unzip -o "<zip>" -d "<target dir>"       # extract, overwriting
```

### 7. Safe replacement pattern

```bash
# Backup old executable
cp "<target>/app.exe" "<target>/app.exe.bak"
# Then unzip new version
```

### 8. Cleanup

```bash
rm -rf "/c/Users/<user>/AppData/Local/Temp/<app>-upgrade"
```

If "Device or resource busy", the temp dir is held by explorer; ignore — user can delete later.

## Pitfalls

- **`schannel SSL handshake failed` on GitHub download URLs**: Always add `-k` to curl when downloading through proxy. The redirect to `objects.githubusercontent.com` breaks CONNECT tunnel SSL.
- **Don't rely on env proxy vars**: Windows system proxy (Internet Settings registry key) is set separately and is the canonical source when TUN-mode proxies like Clash Verge are in use. Check it first.
- **Don't assume proxy port**: Common ports (7890, 10809) are not universal. Always read the registry value; the user's setup may use a non-standard port like 10808.
- **Stop running process before replacing**: `powershell -Command "Get-Process -Name '<name>' -ErrorAction SilentlyContinue | Stop-Process -Id ..."`
- **git-bash `curl` write failures on Windows**: Paths with Chinese characters or missing `/tmp` cause `curl: (23) client returned ERROR on write`. Use `execute_code` with `urllib.request.urlretrieve()` and `zipfile` instead — it bypasses all git-bash filesystem quirks.
- **Proxy can disappear mid-session**: If proxy was working earlier but fails later, try direct `curl` to GitHub before diagnosing the proxy — direct connectivity may have resumed.
