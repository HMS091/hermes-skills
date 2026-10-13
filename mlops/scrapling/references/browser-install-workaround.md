# Installing / repairing Scrapling's Chromium (behind the GFW)

The official Playwright CDN is unreachable from this network:
`cdn.playwright.dev`, `playwright.azureedge.net`, `playwright.download.prss.microsoft.com` all time out.
`npmmirror` mirrors the **same path layout**, so the normal installer works unchanged:

```bash
export PLAYWRIGHT_BROWSERS_PATH=/opt/data/scrapling-browsers
export PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright
export TMPDIR=/tmp
/opt/data/scrapling-venv/bin/python -m playwright install chromium chromium-headless-shell
```

One command, both architectures of artifact (step 1 of the script `bash /opt/data/scripts/scrapling_install_browsers.sh`).

## What the installer actually fetches

Playwright ≥1.60 no longer downloads `builds/chromium/<revision>` for linux-x64 — it downloads
**Chrome for Testing**:

| Browser | URL path | Directory it lands in |
|---|---|---|
| chromium | `builds/cft/<CFT version>/linux64/chrome-linux64.zip` | `<browsers>/chromium-<rev>/chrome-linux64/chrome` |
| chromium-headless-shell | `builds/cft/<CFT version>/linux64/chrome-headless-shell-linux64.zip` | `<browsers>/chromium_headless_shell-<rev>/chrome-headless-shell-linux64/chrome-headless-shell` |

(revision ⇄ CFT version come from `site-packages/playwright/driver/package/browsers.json`;
for revision 1223 it is Chrome for Testing 148.0.7778.96.)

Mirror hosts verified from this box:
- ✅ `https://cdn.npmmirror.com/binaries/playwright` — serves both `builds/cft/*` and (partial) `builds/chromium/*`
- ✅ `https://cdn.npmmirror.com/binaries/chrome-for-testing/<ver>/linux64/...` — CFT zips directly (no `/builds/cft/` prefix)
- ⚠️ `https://mirrors.huaweicloud.com/playwright/...` — serves `builds/chromium/*` but answers **HTML** for `builds/cft/*`, which makes the installer fail with `End of central directory record signature not found`
- ❌ `registry.npmmirror.com/-/binary/playwright/builds/chromium/1223/` only carries linux-**arm64** (x64 missing)

## Manual fallback (air-gapped / installer refuses)

1. Download `chrome-linux64.zip` (+ `chrome-headless-shell-linux64.zip`) from the CFT mirror above.
2. Extract into the expected directory and keep the zip's own top-level folder name:

```python
import zipfile, os
for zpath, dest in [('/tmp/chrome-linux64.zip', '/opt/data/scrapling-browsers/chromium-1223'),
                    ('/tmp/chrome-headless-shell-linux64.zip', '/opt/data/scrapling-browsers/chromium_headless_shell-1223')]:
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(dest)
        for info in z.infolist():                      # python's zipfile drops the exec bit
            mode = info.external_attr >> 16
            if mode:
                os.chmod(os.path.join(dest, info.filename), mode & 0o7777)
    open(os.path.join(dest, 'INSTALLATION_COMPLETE'), 'w').close()   # marker Playwright checks
```

Without the `INSTALLATION_COMPLETE` marker Playwright treats the directory as not installed and
tries to download again. `unzip` is **not installed** on this box — use python's zipfile.

## Verify

```bash
/opt/data/scrapling-browsers/chromium-1223/chrome-linux64/chrome --version   # -> Google Chrome for Testing 148.x
TMPDIR=/tmp /opt/data/scrapling-browsers/chromium-1223/chrome-linux64/chrome \
  --headless=new --no-sandbox --disable-dev-shm-usage --dump-dom "data:text/html,<h1>ok</h1>"
```

Then, end to end: `scrapling extract fetch "https://quotes.toscrape.com/js/" /tmp/out.txt` (1557 bytes = pass).
