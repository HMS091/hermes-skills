---
name: hermes-skills-sync
description: "Sync Hermes skills from an external Git repository (GitHub/GitLab) via SSH, config.yaml external_dirs, and a cron job for periodic git pull."
version: 1.2.0
author: Hermes Agent
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [hermes, skills, sync, git, cron, setup]
    related_skills: [github-auth, hermes-agent]
---

# Hermes Skills Sync

Synchronize a Hermes skills library from an external Git repository (e.g. a shared team skills repo on GitHub). This workflow makes the skills in that repo available to Hermes via `skills.external_dirs` and keeps them up-to-date with a cron job.

## When to use

The user wants to make skills from a remote Git repo (their own, a teammate's, or an organization's) available in their local Hermes instance — e.g. "sync HMS091's skills", "clone the team skills repo".

## Prerequisites

- Git installed on the target machine
- (GitHub) SSH key access set up; the user must have push/read access to the repo
- Hermes installed and running

## Workflow

### 1. Generate SSH Key (if needed)

```bash
ssh-keygen -t ed25519 -C "<label>" -f ~/.ssh/<key_name> -N ""
cat ~/.ssh/<key_name>.pub
```

Print the public key and instruct the user to add it to the remote Git hosting service (GitHub: https://github.com/settings/ssh/new).

### 2. Configure SSH Client

```bash
mkdir -p ~/.ssh
cat >> ~/.ssh/config << 'EOF'
Host github.com
  HostName github.com
  IdentityFile ~/.ssh/<key_name>
  StrictHostKeyChecking accept-new
EOF
chmod 600 ~/.ssh/config ~/.ssh/<key_name>
```

### 3. Clone the Repo

Choose a location. On Windows, avoid `/opt/data/` (Linux path) — use:
- `C:\Users\<user>\AppData\Local\hermes\synced-skills` (Hermes data dir)
- `C:\Users\<user>\synced-skills` (user home)

```bash
cd <target_parent_dir>
git clone git@github.com:<user>/<repo>.git <dir_name>
```

### 4. Configure `skills.external_dirs`

Add the clone path to Hermes config so skills are discovered:

```bash
hermes config set skills.external_dirs "C:\path\to\synced-skills"
```

**Pitfall — `'[]'` looks empty but is a no-op string:** A fresh config ships `external_dirs: '[]'` — in YAML that is a *string*, not an empty array. Hermes treats any string as a single path entry (`agent/skill_utils.py` `get_external_skills_dirs()`: `if isinstance(raw_dirs, str): raw_dirs = [raw_dirs]`), expands `[]` against HERMES_HOME, and silently drops entries whose directory doesn't exist. Result: `hermes config get skills.external_dirs` prints `[]`, the config *looks* set, and nothing loads. A bare path string is the correct single-entry form.

**Write + verify:**
```bash
hermes config set skills.external_dirs "C:\path\to\synced-skills"
grep "external_dirs" $HERMES_HOME/config.yaml   # expect: external_dirs: C:\...\synced-skills (bare path)
hermes config get skills.external_dirs          # prints the path back
```

**Prove it actually loads — `hermes skills list` alone is misleading:** external skills appear with Source column `local` (not `external`); names are deduped with local-before-external precedence (`agent/skill_commands.py` `seen_names`); platform-incompatible skills are dropped (macOS-only `apple/*` never show on Windows). Absence from the list ≠ broken config. Run the skill's `scripts/verify-external-dirs.py <clone_path>` (prints external-only, platform-compatible skill names), then grep `hermes skills list` for a few of them.

### 5. Create a Sync Script

A bash script at `$HERMES_HOME/scripts/sync-<name>.sh`. **For a read-only mirror, do NOT `git pull`:** if the remote force-pushed (rewritten history) or a local commit deleted a file the remote later re-added, pull dies with a modify/delete conflict. Reset-based sync never conflicts and always matches remote exactly:

```bash
#!/bin/bash
REPO="<path_to_cloned_repo>"
cd "$REPO" || exit 1
git fetch origin >/dev/null 2>&1 || { echo "sync failed: git fetch error"; exit 1; }
if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
  git reset --hard origin/main >/dev/null 2>&1
  echo "skills updated: $(git log -1 --format='%h %s' origin/main)"
fi
```

**no_agent stdout contract (design the script around it):** with `no_agent=True` the cron delivers script stdout verbatim — non-empty stdout = message delivered, empty stdout = totally silent, non-zero exit = error alert. So: silent when up-to-date, one line when updated, `exit 1` on fetch failure. After a one-time force-push divergence, fix by hand: `git fetch origin && git reset --hard origin/main && git clean -fd`.

### 6. Create a Cron Job

Use the Hermes cron system with `no_agent=True` (no LLM overhead for a simple git pull).

**During a conversation (agent tool):** Use the `cronjob` tool:

| Parameter | Value |
|-----------|-------|
| action | create |
| name | "Sync \<Name\> Skills" |
| schedule | "every 1h" |
| script | "sync-\<name\>.sh" |
| no_agent | true |

The script path is relative to `$HERMES_HOME/scripts/`. Schedule accepts standard 5-field cron (`"0 5 * * 2"` = every Tuesday 05:00), not just `"every 1h"`. In CLI/TUI sessions `deliver` auto-becomes `local` (no live channel): output is saved to the job record, inspectable via `cronjob(action='list')` — with the update-only script above, local delivery is fine because silence is the default state.

**From CLI:** Use `hermes cron`:

```bash
hermes cron create "every 1h" \
  --no-agent \
  --script sync-<name>.sh \
  --name "Sync <Name> Skills"
```

**Pitfall — gateway required:** Cron jobs need the gateway to fire. Verify:

```bash
hermes cron status
```

If `✗ Gateway is not running`, install it:

```bash
hermes gateway install
```

On Windows this creates a Scheduled Task. On Linux, a systemd user service.

**Pitfall — interactive prompts:** `hermes gateway install` may ask (e.g. "Start now?" and "Auto-start on login?"). In practice, silently accepting defaults works — the prompts auto-advance with defaults on Windows. If a prompt hangs, use `pty=true` in the terminal call, or pipe `Y\\nY\\n`.

### 7. Reload Skills

Skills from `external_dirs` are auto-discovered at session start. They do NOT appear in the current session — the user must start a new session:

```
/reset
```

Or exit and relaunch Hermes.

> **Common gotcha:** The user may expect skills to be immediately available after syncing. Explicitly tell them to `/reset` (or start a new `hermes` session) for the skills to show up in the skills list.

## Post-Sync: Scanning & Categorizing the Library

After syncing, inventory the new skills to understand what's available.

### Batch Scan All Skills

Use Python to extract `name` and `description` from every SKILL.md frontmatter:

```python
from pathlib import Path
import re

skills_dir = Path("<cloned_repo_path>")
for f in sorted(skills_dir.rglob("SKILL.md")):
    text = f.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        continue
    yaml_text = m.group(1)
    name_m = re.search(r'^name:\s*(.+)$', yaml_text, re.MULTILINE)
    desc_m = re.search(r'^description:\s*(.+)$', yaml_text, re.MULTILINE)
    name = name_m.group(1).strip().strip('"').strip("'") if name_m else f.parent.name
    desc = desc_m.group(1).strip().strip('"').strip("'") if desc_m else ""
    print(f"[{f.parent.name}] {name} — {desc}")
```

Or via shell (git-bash):

```bash
find <repo> -name "SKILL.md" | while read f; do
  name=$(grep -m1 "^name:" "$f" | cut -d: -f2- | xargs)
  desc=$(grep -m1 "^description:" "$f" | cut -d: -f2- | xargs)
  dir=$(dirname "$f" | xargs basename)
  echo "[$dir] $name — $desc"
done
```

### Categorize by Directory

The repo's directory structure is the primary taxonomy:
- `creative/` → design, art, music skills
- `software-development/` → coding workflow skills
- `research/` → paper search, web research, crypto analysis
- `github/` → PR, issues, repo management
- `productivity/` → Notion, Airtable, Google Workspace, PDF
- etc.

Build a **task → skill** mapping table for the user so they know what to load for each job.

### Identity Duplicates

Two skills with similar names or descriptions in adjacent directories are the top candidates. For each suspicious pair:

1. **Read both SKILL.md files** — compare purpose, steps, tools used
2. **Check version** — higher version = more mature
3. **Check community adoption** — `hermes skills search <name>` for hub listing count
4. **Check upstream repo** — GitHub stars/forks of the origin repo via its API:

   ```python
   import urllib.request, json
   url = f"https://api.github.com/repos/{owner}/{repo}"
   d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Hermes"})).read())
   print(f"Stars: {d['stargazers_count']}, Forks: {d['forks_count']}, Watchers: {d['subscribers_count']}")
   ```

   Higher stars = more community validation. Higher forks = more derivative use and remixing.
5. **Check for conflicts** — do they disagree on:
   - Save location (`.hermes/plans/` vs `docs/plans/`)
   - Mode enforcement (planning only vs "go ahead and implement")
   - Interaction style (how to respond to `/command`)

Example — `plan` vs `writing-plans`:

| Criteria | `plan` | `writing-plans` |
|----------|--------|----------------|
| Version | 2.0.0 | 1.1.0 |
| Hub listings | 25 sources | 12 sources |
| Mode guardrail | ✅ "planning only, no code" | ❌ none |
| Save location | `.hermes/plans/` (Hermes-native) | `docs/plans/` + git commit |
| Result | **Keep** | **Delete** (fully covered + conflicts) |

**Pitfall — git config before commit:** When `git commit` fails with `Author identity unknown`, set local git config:
```bash
cd <repo>
git config user.email "yourname@users.noreply.github.com"
git config user.name "YourName"
```
Use `--global` only if this is the primary dev machine for this repo.

**Pitfall — git repo ownership:** If the skills are in a cloned repo you don't own (e.g. a colleague's repo), deleting files and pushing requires write access. Use `git rm`, `git commit`, `git push`. If you lack push access, use local-only skip-worktree instead: `git update-index --skip-worktree path/to/skill/SKILL.md`.

### Removing Skills from Upstream (When You Have Push Access)

When a duplicate or obsolete skill is identified, remove it from the remote repo so all synced clients pick up the deletion:

```bash
cd <cloned_repo>
git rm <path/to/duplicate-skill/SKILL.md>
# If git config hasn't been set yet:
git config user.email "yourname@users.noreply.github.com"
git config user.name "YourName"
git commit -m "remove <skill-name> (reason: e.g. duplicate, plan covers it)"
git push origin main
```

**Verify deletion propagated:**
```bash
cd <cloned_repo>
git push origin main 2>&1   # Should show the commit SHA pushed
ls <path/to/duplicate-skill/>  # Should show "No such file or directory"
```

**On the synced machine:** The next `git pull` (via cron) will remove the local copy automatically. No manual cleanup needed.

See `references/hms091-example.md` for a real deletion transcript (`writing-plans` removed, 297 lines deleted, commit `ff416f2`).

### Build a Quick-Reference Map

Save a concise task→skill mapping to memory (under 2200 chars) so future sessions know which skill to load without re-scanning. Group by task domain, not by directory name.

## Verification

```bash
# Script exists
test -f $HERMES_HOME/scripts/sync-<name>.sh

# Repo is a git repo
test -d <cloned_repo>/.git

# Config has the path
grep "external_dirs" $HERMES_HOME/config.yaml

# Cron job exists
hermes cron list | grep <job_name>

# Gateway is running (cron will fire)
hermes cron status | grep "Gateway is running"

# Skills are discoverable
find <cloned_repo> -name "SKILL.md" | wc -l

# External dir truly feeds discovery (not just config present) — run the skill's
# scripts/verify-external-dirs.py, then confirm a printed name shows in:
hermes skills list | grep <external-only skill name>

# Git remote is correct
cd <cloned_repo> && git remote -v

# Git fetch works (dry run)
cd <cloned_repo> && git fetch --dry-run
```

## Non-Technical Users

If the user says "我不懂代码" (I don't understand code):
- Generate keys, clone, and configure everything yourself
- Only ask them to add the SSH public key to GitHub (step 1)
- Use clear step-by-step instructions in the user's language
- Do not ask them to run terminal commands — you run them

## Platform Notes

- **Windows:** Use MSYS paths (`/c/Users/...`) in terminal commands, native paths (`C:\\Users\\...`) in config.yaml. Cron via gateway installs as a Windows Scheduled Task.
- **macOS/Linux:** `/opt/data/` or `~/.hermes/synced-skills` both work. Cron via gateway installs as a systemd user service.

## SSH to NAS / Remote Hermes Pitfalls

When SSHing from this machine to a NAS running Hermes in Docker:

### fail2ban IP Ban
Rapid successive SSH attempts (e.g. 3+ failed auth in quick succession) will trigger Synology's built-in fail2ban and IP-ban the connecting host. Symptoms: `Connection reset by peer` on port 22 even though the port is open.

**Fix — have the NAS-side agent run:**
```bash
sudo fail2ban-client set sshd unbanip <windows_ip>
```

**Prevention — increase MaxStartups:**
```bash
sudo sed -i 's/^MaxStartups.*/MaxStartups 100:30:200/' /etc/ssh/sshd_config
sudo synoservicectl --restart sshd
```

### Docker Access
When Hermes runs in a Docker container on the NAS, `docker ps` may time out if the user (`tmm`) is not in the `docker` group. Use `sudo docker ps` or check `groups` output first. If Docker commands hang indefinitely, the Docker daemon may not be running or the socket is inaccessible.

### Command Batching
When working with SSH to a remote Hermes, **batch related commands into a single `ssh` call** instead of making multiple sequential SSH connections. Each connection can trigger rate limits, and the user gets frustrated by fragmented output. Use `&&` chaining, or better yet, use `ssh … "cmd1 && cmd2 && cmd3"`.

**Good (batched):**
```bash
ssh user@nas "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo 'key' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

**Bad (sequential — triggers rate limits + annoys user):**
```bash
ssh user@nas "mkdir -p ~/.ssh"
ssh user@nas "chmod 700 ~/.ssh"
ssh user@nas "echo 'key' >> ~/.ssh/authorized_keys"
```

## Reference

- `references/hms091-example.md` — Full transcript of a real HMS091 skills sync session on Windows (SSH key gen, clone, config, cron, gateway install). Use as a concrete template.
