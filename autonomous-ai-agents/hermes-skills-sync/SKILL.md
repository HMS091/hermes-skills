---
name: hermes-skills-sync
description: "Sync skills from Git; audit, dedupe, and prune the library."
version: 1.2.0
author: Hermes Agent
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [hermes, skills, sync, git, cron, setup]
    related_skills: [github, hermes-agent]
---

# Hermes Skills Sync

Synchronize a Hermes skills library from an external Git repository (e.g. a shared team skills repo on GitHub). This workflow makes the skills in that repo available to Hermes via `skills.external_dirs` and keeps them up-to-date with a cron job. The same skill owns library hygiene afterwards: duplicate detection, pruning unused vendor packs, and repairing the cross-references those removals break.

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

## Publishing: Proving the Push Landed, and Making It Portable

Two things the setup workflow never checks: whether the push actually reached the remote, and whether a cloning agent can *use* what it pulled. Both get asked the moment the user says "这样其他智能体也能用".

### Verify against the remote, not against a status file

```bash
cd /opt/data/skills
git status --porcelain | wc -l                    # expect 0 — a dirty tree means the commit step hasn't run
git rev-parse HEAD; git ls-remote origin HEAD     # SHAs must match exactly
git ls-tree -r origin/main --name-only | grep -i <skill>   # the file is in the pushed tree
```

Then confirm one file through the API, comparing **size**, not mere presence:

```bash
TOKEN=$(git remote get-url origin | sed 's#.*:\([^@]*\)@.*#\1#')
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/<owner>/<repo>/contents/<cat>/<skill>/SKILL.md" \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['size'],d['download_url'])"
wc -c <cat>/<skill>/SKILL.md                     # must equal the API size
```

**Never answer "is it synced?" from a status artifact.** A `manifests/sync-status.json` — or any hand-written `verified` line — drifts silently: it can read months stale while hourly syncs are green (false alarm), and a fresh-looking one proves nothing because no step regenerates it. Compare HEADs and file sizes; that is the only evidence. Also state the mechanism (job name, schedule, last status from `cronjob action='list'`) so the answer shows *why* it stays synced, not just that it is once.

### Portability — what "other agents can use it" actually requires

A skill whose body is a transcript of *this* box is not reusable when cloned. `/opt/data/<name>-venv`, `/usr/local/bin/<wrapper>`, `/opt/data/<name>-browsers` are local facts, not instructions; a cloning agent follows them literally and dies on `ModuleNotFoundError` or `No such file or directory`.

- Before claiming a skill is "available to other agents", grep its body: `grep -n '/opt/\|/usr/local/\|C:\\' SKILL.md`. Every hit is a portability debt — report it rather than hiding it.
- Keep the generalizable part (decision tree, pitfalls, prompt formats) machine-independent. Put local paths in the frontmatter `metadata.hermes` block, where they read as setup state instead of procedure.
- Add a short "cross-machine install" section naming the install command and the three or four paths a reader must edit on their own machine.
- Strip cron assumptions too: a cloned job with `deliver=all` resolves to no target on a machine with no connected platform — it runs, saves output, and notifies nobody. Set an explicit platform or say plainly that delivery is local-only.

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

0. **Scan the whole library first — don't eyeball it.** Token-set Jaccard over SKILL.md bodies finds the pairs you'd miss (nested dirs, umbrella-vs-leaf):

   ```python
   import glob, re, itertools
   D = "/opt/data/skills"
   docs = {}
   for p in glob.glob(D + "/**/SKILL.md", recursive=True):
       if "/.archive/" in p: continue
       t = open(p, encoding="utf-8", errors="replace").read()
       if t.startswith("---"):            # strip frontmatter so tags don't inflate overlap
           e = t.find("\n---", 3); t = t[e+4:] if e > 0 else t
       docs[p[len(D)+1:-9]] = set(re.findall(r"[a-z\u4e00-\u9fff]{4,}", t.lower()))
   for a, b in itertools.combinations(docs, 2):
       j = len(docs[a] & docs[b]) / len(docs[a] | docs[b])
       if j > 0.30: print(round(j, 2), a, b)
   ```

   Calibrate against the baseline: a large vendor pack (e.g. the 70-skill product-management drop) scores 0.33–0.38 for *unrelated* skills because they share one author's template. Only ~0.6+ means the same content; 1.00 means a literal copy.

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

**Before deleting, test for layering:** `grep -c '<other-skill-name>' A/SKILL.md B/SKILL.md` in both directions. Mutual references (advisor → executor → back) mean the pair is a *router + component* by design, not a duplicate — keep both. One-way or zero references plus a shared output artifact = real duplicate. Duplicates hide in three specific shapes:

| Shape | Example | Tell |
|---|---|---|
| Nested copy | `creative/comfyui/comfyui/` | Jaccard 1.00, inner dir has no scripts/tests |
| Umbrella that already consolidated the leaves | `software-development/github` says "consolidates six former skills", yet `github/github-{auth,issues,pr-workflow,…}` still exist | leaf refs+scripts are a subset of the umbrella's `references/` |
| Same topic, 4 rewrites | `nextcloud-talk-troubleshooting` vs `webrtc-turn-server` vs `coturn-turn-server` vs `webrtc-turn-troubleshooting` | all 4 answer "WiFi works, 4G fails"; keep the newest+largest+most-used, copy unique `references/*.md` into it first |

**Removal protocol (archive, never `rm`)**: `mv <skill> /opt/data/skills/.archive/_dedupe-<date>/<a__b>` + a `MERGED-INTO.txt` (reason + restore command). Dot-prefixed archives aren't scanned. Then, in the SAME pass, `grep -rn '<dead-skill-name>' /opt/data/skills --include='*.md'` and repoint every hit: `related_skills:` lists, "see the X skill" prose, `--skills "X"` in webhook/cron examples, and hardcoded `skills/<cat>/<skill>/scripts/...` paths (those break silently — the script moved with the umbrella). Finish with `hermes skills list | tail -2` (count drops by exactly the archived number, 0 disabled, no ambiguous-name errors) and `skill_view` on each survivor.

### Pruning a Whole Pack (vendor drop, 50+ unused skills)

When a vendor pack lands (e.g. a 77-skill PM methodology library) and every skill shows `use_count: 0`, dedupe is not the work — triage is. Rules:

1. **Keep a task-mapped core, not a topic-mapped sample.** For THIS user, keep the pack skills whose *artifact* they actually produce (market sizing, metric formulas, competitive snapshot, PRD, VoC mining, positioning) and archive the org/exec/career/process machinery (readiness advisors, EOL suites, stakeholder grids, workshops-by-dialogue). 8–10 survivors out of 77 is the right order of magnitude.
2. **Re-check what the survivors depend on before you stop.** `grep` each keeper for backticked sibling names; pack-wide infrastructure (an investigation protocol, a workshop pacing controller) is load-bearing even though it produces no artifact itself — pull those 1–2 back out of the archive or the keepers stall mid-run.
3. **Annotate every keeper in one line** right after its frontmatter: "siblings X/Y/Z are archived at `.archive/_<bucket>/`, pull one back with `mv` if needed; do not stall looking for them." Without it the model reads "hand off to skill Y", fails to load Y, and burns turns.
4. **Archive in one bucket per pass** (`.archive/_dedupe-<date>/`, `.archive/_pm-prune-<date>/`) with a per-skill `MERGED-INTO.txt` / `ARCHIVED.txt` holding the reason and the exact restore `mv`. Report the count delta and the index-token saving (name+description per entry, ~50 tokens each) — the user asks for the price of everything.

**Pitfall — an anchored `^related_skills:` regex silently edits nothing.** In every real SKILL.md the key is indented under `metadata.hermes:` (`    related_skills: [...]`), so `re.search(r'^related_skills:', t, re.M)` returns None, your "0 dangling removed" report is a lie, and the fix pass looks complete. Use the unanchored form `re.search(r'related_skills:\s*\[([^\]]*)\]', t)` and **assert a non-zero edit count** before believing a cleanup pass.

**Pitfall — never insert text by anchoring on `^# `.** Skill bodies embed templates in fenced blocks that start with `# ` (```` ```markdown # TAM/SAM/SOM Analysis ````), so the note lands inside the example the skill emits. Insert after the frontmatter's closing `---` instead, then assert the body's first line is the note.

Recipes (scan, archive, annotate, verify) live in `references/library-dedupe-and-prune.md`; run `scripts/skills_library_audit.py` for the one-command version (similar pairs + dangling `related_skills` + counts).

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

- `references/library-dedupe-and-prune.md` — Dedupe/prune recipes: Jaccard scoring and how to read it, the cross-reference test that separates layered skills from duplicates, archive+annotate+verify code, `related_skills` rewrite, seed-drift refresh rule, and the report shape this user expects.
- `scripts/skills_library_audit.py` — Read-only audit of the live library: counts, zero-use skills, similar pairs, dangling `related_skills`, live-vs-seed drift. Run it before any dedupe or prune pass.
- `references/hms091-example.md` — Full transcript of a real HMS091 skills sync session on Windows (SSH key gen, clone, config, cron, gateway install). Use as a concrete template.
