# Weekly Package & Skill Update Pattern

Created: 2026-06-26
Source session: High-priority AI tool installation + weekly maintenance cron job setup

## Workflow

### 1. Choose Between Two Cron Modes

**A) LLM-driven agent mode** (default): Script collects data, agent formats/reports it.
Use `cronjob(action='create', prompt='...', script='update.sh')` — the agent receives `{script_output}` and produces a formatted report. Good when you want reasoning about results.

**B) Watchdog/no-agent mode** (`no_agent=True`): Script IS the entire job — its stdout is delivered verbatim with no LLM involved. Zero token cost. Use when the script itself produces the exact output the user should see (pure status report, version check, simple pass/fail).

```python
cronjob(
    action='create',
    name='hermes-self-update',
    schedule='0 8 * * 0',  # Weekly Sunday 8AM UTC
    script='hermes-self-update.sh',  # Relative to ~/.hermes/scripts/ — NOT absolute paths
    no_agent=True,          # ZERO tokens — script stdout delivered directly
    deliver='local',        # or 'all' for notification
)
```

**Key constraint:** `no_agent=True` jobs are pure bash/Python scripts. They run silently on empty stdout (nothing delivered). Non-zero exit / timeout triggers an error alert so a broken watchdog can't fail silently.

### 2. Hermes Agent Self-Update Script (Bash, no_agent=True)

```bash
#!/usr/bin/env bash
set -euo pipefail
export PATH="/opt/data/home/.local/bin:$PATH"  # uv tools live here

echo "========== Hermes 自动更新检查 =========="
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"

OLD_VER=$(uv tool list 2>/dev/null | grep -oP 'v\d+\.\d+\.\d+' | head -1)
echo "更新前版本: v${OLD_VER#v}"

UPDATE_OUTPUT=$(uv tool upgrade hermes-agent 2>&1) || {
    echo "❌ 更新失败 ($?): $UPDATE_OUTPUT"
    exit 1
}
echo "$UPDATE_OUTPUT"

if echo "$UPDATE_OUTPUT" | grep -qi "Updated"; then
    NEW_VER=$(uv tool list | grep -oP 'v\d+\.\d+\.\d+' | head -1)
    echo "✅ 升级成功！ v${OLD_VER#v} → v${NEW_VER#v}"
elif echo "$UPDATE_OUTPUT" | grep -qiE "Nothing to upgrade|up to date"; then
    echo "ℹ️  已是最新版本 (v${OLD_VER#v})"
fi
```

**Why `uv tool upgrade hermes-agent` instead of `hermes update`:**
- `hermes update` (CLI/TUI) is interactive — it prompts with a confirmation dialog and attempts to relaunch the session. This breaks in cron/scripted contexts.
- `uv tool upgrade hermes-agent` is fully non-interactive and works from any environment.
- The `hermes` binary path is typically `~/.local/share/uv/tools/hermes-agent/bin/hermes` — add `~/.local/bin` to PATH so shebangs resolve.

### 3. Save Script and Create Cron Job

```bash
# Script MUST go in ~/.hermes/scripts/ — absolute paths are rejected
cp /opt/data/scripts/hermes-self-update.sh ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/hermes-self-update.sh
```

### 3. Environment Detection Constraints

Before the script runs, check:
- **Python environment:** `pip list` may have `--break-system-packages` requirement (PEP 668). Prefer `uv tool list` / `uv tool upgrade` for tool-level packages instead of `pip install`.
- **Hermes install method:** Hermes is installed via `uv tool install hermes-agent`, not pip. The binaries live at `~/.local/share/uv/tools/hermes-agent/`. Add `~/.local/bin` to PATH.
- **PATH in cron:** Cron jobs inherit a minimal PATH. The script must explicitly set `export PATH="/opt/data/home/.local/bin:$PATH"` or the full uv bin path. Do NOT rely on interactive-shell PATH.
- **Network:** PyPI access may be slow through proxy; `uv tool upgrade` handles this automatically.

### 4. Common Issues

- **`hermes` not in PATH:** Use full path: `/opt/hermes/.venv/bin/hermes`
- **`pip index versions` not available:** Requires pip >= 23.1. Fallback: `pip install --dry-run` (slower)
- **`pip` may not be installed at all (PEP 668):** The system Python may be PEP 668 protected, meaning `pip` is not available at the system level. `pip show PKG` and `pip index versions PKG` silently return empty output with exit code 0 — they don't error, they just produce nothing. **Fix**: Check `pip` availability with `which pip || command -v pip` before using it. In Hermes environments, use `uv pip show PKG` from the project directory (e.g., `cd /opt/hermes && uv pip show PKG 2>/dev/null | grep "^Version:" | awk '{print $2}'`) or `uv tool list` for tool-level packages. See the `cron-data-workflows` SKILL.md pitfall section for more details.
- **`hermes skills check` grep may false-positive on Unicode borders:** The table output uses box-drawing characters (`┏`, `┃`, `┗`, `━`, `┓`) that can match loose grep patterns like `"update\|outdated\|new version"`. **Fix**: either parse `hermes skills check --json` output, run `hermes skills update` unconditionally (idempotent), or use more specific matching with `grep -c "up_to_date\|outdated"`.
- **Dry-run timeout:** `pip install --upgrade --dry-run` can take >60s on slow proxy networks. Default to `pip index versions` which is 3-5× faster.

## Files Created in this Session

| File | Purpose |
|------|---------|
| `/opt/data/scripts/weekly-update.sh` | Main update script |
| `~/.hermes/scripts/weekly-update.sh` | Copy for cron job resolution |
| Cron job `weekly-skill-update` (ID: 4d341306dd25) | Schedule: Monday 3AM UTC |
