# 实战案例：同步 HMS091 技能库

本会话的完整操作记录，作为 `hermes-skills-sync` 技能的参考用例。

## 环境

- OS: Windows 10 (git-bash)
- Hermes 桌面 GUI 版本
- 目标仓库: `git@github.com:HMS091/hermes-skills.git`

## 操作步骤

### 1. 生成 SSH Key

```bash
ssh-keygen -t ed25519 -C "HMS091-sync" -f ~/.ssh/hms091_sk -N ""
cat ~/.ssh/hms091_sk.pub
```

### 2. 用户操作（唯一需要用户参与的步骤）

让用户把公钥添加到 https://github.com/settings/ssh/new，Title 填设备名。

### 3. SSH 配置

```bash
mkdir -p ~/.ssh
cat > ~/.ssh/config << 'EOF'
Host github.com
  HostName github.com
  IdentityFile ~/.ssh/hms091_sk
  StrictHostKeyChecking accept-new
EOF
chmod 600 ~/.ssh/config ~/.ssh/hms091_sk
```

### 4. 克隆仓库

```bash
cd /c/Users/Administrator/AppData/Local/hermes
git clone git@github.com:HMS091/hermes-skills.git synced-skills
```

### 5. 配置 external_dirs

```bash
hermes config set skills.external_dirs \
  "C:\Users\Administrator\AppData\Local\hermes\synced-skills"
```

验证: `grep "external_dirs" /c/Users/Administrator/AppData/Local/hermes/config.yaml`

### 6. 创建同步脚本

写入 `C:\Users\Administrator\AppData\Local\hermes\scripts\sync-hms091-skills.sh`:

```bash
#!/bin/bash
cd /c/Users/Administrator/AppData/Local/hermes/synced-skills || exit 1
echo "=== $(date) ==="
echo "Pulling latest HMS091 skills..."
git pull 2>&1
echo "Done."
```

### 7. 创建 Cron 任务（用 cronjob 工具）

```
action: create
name: "Sync HMS091 Skills"
schedule: "every 1h"
script: "sync-hms091-skills.sh"
no_agent: true
```

### 8. 启动 Gateway（cron 需要）

```bash
hermes gateway install
```

**注意:** `hermes gateway install` 在 Windows 上会弹出两个交互提示（"Start now?" 和 "Auto-start on login?"），但默认值就是 Y，无需额外操作即可完成。安装后自动创建 Windows Scheduled Task。

### 9. 验证

```bash
hermes cron status
# → ✓ Gateway is running — cron jobs will fire automatically
```

## Post-Sync Analysis

### Batch Scan

All 102 skills were scanned via Python frontmatter extraction and categorized by directory:

```python
from pathlib import Path
import re
skills_dir = Path(r"C:\Users\Administrator\AppData\Local\hermes\synced-skills")
for f in sorted(skills_dir.rglob("SKILL.md")):
    text = f.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if m:
        yaml_text = m.group(1)
        name = re.search(r'^name:\s*(.+)$', yaml_text, re.MULTILINE)
        desc = re.search(r'^description:\s*(.+)$', yaml_text, re.MULTILINE)
        name_v = name.group(1).strip().strip('"') if name else f.parent.name
        desc_v = desc.group(1).strip().strip('"') if desc else ""
        print(f"[{f.parent.name}] {name_v} — {desc_v}")
```

Output: 102 skills across ~20 categories.

### Duplicate Found: `plan` vs `writing-plans`

Both in `software-development/`, both about writing implementation plans.

**Content comparison (by reading both SKILL.md side-by-side):**
- Plan content (bite-sized tasks, TDD, file paths, verification) → **identical**
- `plan` adds: Plan Mode enforcement ("no implementation"), interaction style for `/plan` command, `.hermes/plans/` path
- `writing-plans` adds: save to `docs/plans/` + git commit

**Community signals:**
| Criteria | plan | writing-plans |
|----------|------|---------------|
| Version | 2.0.0 | 1.1.0 |
| Skills Hub listings | 25 | 12 |
| Origin stars | 208k (nousresearch/hermes-agent) | 244k (obra/superpowers) |
| Forks | 37.8k | 21.6k |

**Conflict analysis:**
- `plan` says "only plan, no code" — `writing-plans` has no such guard → contradictory instructions
- `plan` saves to `.hermes/plans/` — `writing-plans` saves to `docs/plans/` + git commit → conflicting outputs
- Both define nearly identical task structure → double token cost with no benefit

**Resolution:** Delete `writing-plans`, keep `plan`.

### Deletion from Remote Repo

```bash
cd synced-skills
git rm software-development/writing-plans/SKILL.md
# Hit "Author identity unknown" — needed to set git config:
git config user.email "hms091@users.noreply.github.com"
git config user.name "HMS091"
git commit -m "remove duplicate writing-plans skill (plan covers it)"
git push origin main
```

**Gotcha:** `git commit` will fail on a fresh clone with `Author identity unknown`. Always set `user.email` and `user.name` before committing, even for a one-shot deletion.

Result: `ff416f2` pushed to `HMS091/hermes-skills.git`, 297 lines deleted, 101 skills remaining.

## Lessons

1. **Windows + `hermes config set`:** The value may be stored as JSON-string YAML — verify with `grep` after setting
2. **Gateway install on Windows:** Interactive prompts auto-default to Y — no pty needed
3. **Git config before commit:** Always set `user.email` + `user.name` before any commit on a non-configured clone
4. **GitHub SSH keys:** Name per-machine for clarity (e.g. `hms091_sk` with label `HMS091-sync`)
5. **Post-sync dedup:** Always scan + categorize + identify duplicates before telling the user "done"
6. **Deleting from owned repos:** `git rm → git config (if needed) → commit → push` is the full path; for repos you don't own, use `git update-index --skip-worktree`
