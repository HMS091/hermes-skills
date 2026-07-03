# Playwright Browser Install Workaround

When Playwright/Patchright browser download fails from `cdn.playwright.dev` (network drops, GFW issues):

## Step 1: Download with curl resume

```bash
# First attempt (might fail partway)
curl -L -C - --connect-timeout 15 --max-time 300 \
  -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  -o /tmp/chrome-headless-shell.zip \
  "https://cdn.playwright.dev/builds/cft/<REVISION>/linux64/chrome-headless-shell-linux64.zip"
```

The `-C -` flag auto-resumes partial downloads. Run it again if it fails - it will pick up where it left off.

## Step 2: Identify the right target directory

Playwright installs browsers under its driver package:
```
/opt/data/scrapling-venv/lib/python3.13/site-packages/playwright/driver/package/.local-browsers/
```

The directory name pattern is `{browser_name}-{revision}`, e.g. `chromium-1223`.

## Step 3: Extract with proper prefix stripping

The zip contains a `chrome-headless-shell-linux64/` prefix directory. Extract content directly into the Playwright target:

```python
import zipfile, os
zip_path = '/tmp/chrome-headless-shell.zip'
target = '/opt/data/scrapling-venv/lib/python3.13/site-packages/playwright/driver/package/.local-browsers/chromium-1223'

with zipfile.ZipFile(zip_path, 'r') as zf:
    for info in zf.infolist():
        if info.filename.startswith('chrome-headless-shell-linux64/'):
            rel_path = info.filename[len('chrome-headless-shell-linux64/'):]
            if not rel_path:
                continue
            dest = os.path.join(target, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if not info.filename.endswith('/'):
                with open(dest, 'wb') as f:
                    f.write(zf.read(info.filename))
                os.chmod(dest, 0o755)

chrome_bin = os.path.join(target, 'chrome-headless-shell')
if os.path.exists(chrome_bin):
    os.chmod(chrome_bin, 0o755)
```

## Alternative: Use `PLAYWRIGHT_CHROMIUM_EXECUTABLE`

If a Chrome/Chromium is already installed elsewhere, set:

```bash
export PLAYWRIGHT_CHROMIUM_EXECUTABLE=/path/to/chrome
```

## Verify browser works

```python
/opt/data/scrapling-venv/bin/python -c "
from scrapling.fetchers import StealthyFetcher
p = StealthyFetcher.fetch('https://httpbin.org/get', headless=True, timeout=30000)
print(f'Status: {p.status}')
"
```
