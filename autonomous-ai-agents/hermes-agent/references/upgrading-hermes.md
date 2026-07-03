# Upgrading Hermes Agent — Docker Environment Notes

## Environment Profile

This environment runs Hermes Agent inside a Docker container (Debian Trixie) on Synology DS918+ (Intel Celeron J3455). The install lives at `/opt/hermes/` with source code, but **there is no `.venv`** — PEP 668 enforcement removed the old virtualenv layout. All Python package management uses **`uv`**.

The source code at `/opt/hermes/` was cloned from GitHub but has **no .git directory** (was stripped for Docker layer size). The pyproject.toml version may be stale while the uv-installed version is newer.

## Upgrade Procedure

### Step 1: Check Current Version

```bash
# Installed version via uv
uv tool list 2>/dev/null | grep hermes-agent

# Or via pip show (fallback, may not work)
pip show hermes-agent 2>/dev/null | grep Version

# Source code version (may be stale)
cd /opt/hermes && grep "^version" pyproject.toml
```

### Step 2: Check Latest on PyPI

```bash
uv tool list 2>/dev/null | head -3
# Or directly query PyPI:
curl -s https://pypi.org/pypi/hermes-agent/json | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(f'Latest: {d[\"info\"][\"version\"]}')"
```

Note: `curl | python3` triggers Hermes security approval (pipe-to-interpreter HIGH alert). Approve it or use the `tool` parameter in cron jobs to avoid security prompts.

### Step 3: Upgrade with uv

```bash
uv tool install hermes-agent
```

This installs to `~/.local/share/uv/tools/hermes-agent/` and creates symlinks
in `~/.local/bin/`. If PATH does not include `~/.local/bin`, export it:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Do NOT use `pip` or `.venv/bin/pip`** — they don't exist in this environment.
The system Python 3.13 enforces PEP 668, and the old `.venv` layout was
removed during a previous migration. `uv` is the only working package manager.

### Step 4 (Optional): Sync Source Code with GitHub

The `/opt/hermes/` directory may not be a git repo. To sync:

```bash
cd /opt/hermes
git init
git remote add origin https://github.com/nousresearch/hermes-agent.git
git fetch --tags --depth=1 origin main
git checkout main  # or git checkout -f main
```

However, the GitHub repo has migrated from semantic version tags (v0.14.0) to **date-based tags** (v2026.5.29.2). The main branch pyproject.toml says `0.15.1` while the latest date tag is `v2026.5.29.2`.

After syncing, reinstall via `uv tool install hermes-agent` to match the new source.

## Full Upgrade Sequence (uv + Source Sync)

When upgrading to a specific git tag (preferred for source sync):

```bash
cd /opt/hermes
git init                                        # if no .git
git remote add origin https://github.com/nousresearch/hermes-agent.git
git fetch --tags --depth=1 origin main          # fetch tags + branch
git checkout --force v2026.5.29.2               # or latest date-based tag

# Reinstall matching version via uv
uv tool install hermes-agent

# Update Node.js dependencies
npm install

# Update Playwright browsers
npx playwright install --with-deps

# Verify
uv tool list 2>/dev/null | grep hermes-agent
grep "^version" pyproject.toml
```

Note: `git checkout main` gives v0.15.1; `git checkout v2026.5.29.2` gives v0.15.2. The date-based tags are the canonical releases now.

## Pitfalls

- **`.venv/bin/pip` does not exist**: The old virtualenv was removed. Do not try to create it — `uv` is the standard package manager in this environment. Running `python3 -m venv .venv` will fail due to PEP 668 restrictions on the system Python.
- **PATH must include `~/.local/bin`**: After `uv tool install`, the `hermes` binary is at `~/.local/share/uv/tools/hermes-agent/bin/hermes`, symlinked from `~/.local/bin/hermes`. If this directory is not in PATH, the new version won't be picked up.
- **Source version != installed version**: The pyproject.toml may show v0.14.0 while uv actually installed 0.17.0 (from PyPI). The uv-installed version is what matters at runtime.
- **No git repo**: The Docker build strips .git. To sync source, need `git init` first.
- **Tag scheme change**: Old v0.x.x tags no longer exist upstream. Upstream uses **date-based tags** like `v2026.5.29.2`. `git tag | sort -V` to list available tags. The latest stable tag may not be the most recent one alphabetically.
- **pip uninstall warning**: "Not uninstalling hermes-agent at /opt/hermes, outside environment /opt/hermes/.venv" — this is benign. The source directory has an editable install reference but the actual package goes into site-packages.
- **`from hermes_agent import __version__` fails**: After uv install, `hermes_agent` may not be a directly importable module even though the package is installed (depends on packaging scheme). Verify with `uv tool list` or `pip show` instead.
- **`hermes update` exists as a CLI command**: If the current version supports it, `hermes update` may be the easiest path — but it requires the old version's binary to be in PATH first.
- **npm install removes old packages**: Running `npm install` after a source upgrade will remove stale node_modules and rebuild the browser-tools. This is expected.
- **Playwright browser version mismatch**: After source upgrade, old Playwright browsers may be incompatible. Always run `npx playwright install --with-deps` to download matching Chromium/Firefox/WebKit versions. This downloads ~200+ MiB total.
