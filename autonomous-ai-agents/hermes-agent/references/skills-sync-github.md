# 多设备技能同步（GitHub 方案）

## 概述

在多台运行 Hermes Agent 的设备之间同步技能库。本方案使用 **GitHub 私有仓库**作为中继，一台设备推送，其他设备拉取。使用 **HTTPS + Personal Access Token (PAT)** 认证，避免 SSH 被 GFW 封锁的问题。

## 架构

```
Device A (主设备)                    GitHub                    Device B (从设备)
/opt/data/skills/  ──HTTPS+token──▶  HMS091/hermes-skills  ──HTTPS+token──▶  /opt/data/synced-skills/
        │                                                                          │
  cron 每小时自动推送                                                        cron 每小时自动拉取
        │                                                                          │
        ▼                                                                          ▼
  无需额外配置                                                              skills.external_dirs:
                                                                              - /opt/data/synced-skills
```

## 前提条件

- GitHub Personal Access Token（`ghp_...` 或 `github_pat_...`）—— 保存在 `/opt/data/.env_bot` 中：
  ```bash
  export GH_BOT_TOKEN="ghp_你的token"
  ```
- Token 需要 **repo** 权限（私有仓库读写）

## 主设备设置（一次性）

### 1. 创建 GitHub 仓库

```bash
source /opt/data/.env_bot  # 加载 token
curl -sL -X POST "https://api.github.com/user/repos" \
  -H "Authorization: Bearer $GH_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"hermes-skills","private":true}'
```

### 2. 初始化本地 Git

```bash
cd /opt/data/skills

# .gitignore — 排除 Hermes 内部文件
cat > .gitignore << 'EOF'
.bundled_manifest
.curator_backups/
.curator_state
.hub/
.usage.json
.usage.json.lock
EOF

git init
git config --global user.email "hms091@users.noreply.github.com"
git config --global user.name "HMS091"
git config --global --add safe.directory /opt/data/skills
git add -A
git commit -m "初始技能库推送"
git branch -m master main
# HTTPS remote（token 嵌入URL，免交互推送）
source /opt/data/.env_bot
git remote add origin "https://HMS091:${GH_BOT_TOKEN}@github.com/HMS091/hermes-skills.git"
git push -u origin main
```

### 3. 设置自动推送（cron）

创建脚本 `/opt/data/scripts/skills-sync.sh`：

```bash
#!/bin/bash
# Auto-sync Hermes skills to GitHub (HTTPS + token)
# Runs every hour via cron

set -e

SKILLS_DIR="/opt/data/skills"
cd "$SKILLS_DIR"

# Load GitHub token
source /opt/data/.env_bot 2>/dev/null || {
    echo "Warning: /opt/data/.env_bot not found, try GH_TOKEN"
}

# Set up HTTPS credential for unattended push
if [ -n "$GH_BOT_TOKEN" ]; then
    git remote set-url origin "https://HMS091:${GH_BOT_TOKEN}@github.com/HMS091/hermes-skills.git"
fi

# Check if there are any changes
if ! git diff --quiet --exit-code || ! git diff --cached --quiet --exit-code; then
    git add -A
    git commit -m "auto-sync $(date '+%Y-%m-%d %H:%M')"
    # HTTPS push — no SSH/GFW issue
    git push origin main 2>&1 || echo "Push failed (may be transient)"
fi
```

```bash
chmod +x /opt/data/scripts/skills-sync.sh
```

通过 Hermes cronjob API 创建（每小时执行，no_agent 模式，纯脚本）：

```bash
# 使用 cronjob 工具创建
# action=create, schedule="0 * * * *", script="skills-sync.sh", no_agent=true, deliver=local
```

## 从设备设置

### 1. 克隆仓库

```bash
source /opt/data/.env_bot
git clone "https://HMS091:${GH_BOT_TOKEN}@github.com/HMS091/hermes-skills.git" /opt/data/synced-skills
```

### 2. 配置 Hermes 加载同步目录

编辑 `/opt/data/config.yaml`：

```yaml
skills:
  external_dirs:
    - /opt/data/synced-skills
```

### 3. 设置自动拉取

创建脚本 `/opt/data/scripts/skills-pull.sh`：

```bash
#!/bin/bash
cd /opt/data/synced-skills
source /opt/data/.env_bot
git pull "https://HMS091:${GH_BOT_TOKEN}@github.com/HMS091/hermes-skills.git" main 2>&1 || echo "Pull failed"
```

```bash
chmod +x /opt/data/scripts/skills-pull.sh
```

通过 Hermes cronjob API 创建：

```bash
# action=create, schedule="0 * * * *", script="skills-pull.sh", no_agent=true, deliver=local
```

### 4. 重启 Hermes 生效

## 验证

```bash
# 查看远程是否同步
cd /opt/data/skills && git ls-remote origin HEAD
# 确认远程和本地一致
cd /opt/data/skills && git log --oneline -1 && echo "---" && git ls-remote origin HEAD | cut -f1

# 从设备查看同步结果
ls /opt/data/synced-skills/
```

通过 GitHub API 验证：

```bash
source /opt/data/.env_bot
curl -s -H "Authorization: Bearer $GH_BOT_TOKEN" \
  "https://api.github.com/repos/HMS091/hermes-skills/commits?per_page=1" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['sha'][:10], d[0]['commit']['message'][:50])"
```

## Pitfalls

1. **Token 泄露：** Token 嵌入 git remote URL 后，会在 `.git/config` 中以明文存储。在同一设备上可以接受，但注意不要误分享 `.git/config` 文件。
2. **Token 过期：** GitHub PAT 有有效期。建议在 `.env_bot` 中标注过期日期，并设置 cron 定期检查。Token 过期后推送会返回 403。
3. **首次推送大仓库：** skills 目录可能包含数百个文件（案例 687 个文件），首次 push 需要耐心等待几分钟。HTTPS 比 SSH 略慢但更稳定。
4. **Hermes 内部文件：** `.bundled_manifest`、`.hub/`、`.curator_*`、`.usage.json` 等是 Hermes 运行时文件，不应入版本控制。务必配置 `.gitignore`。
5. **skills 目录权限：** `/opt/data/skills/` 可能由 `hermes` 用户拥有，但 git 操作以 `root` 运行。需要 `git config --global --add safe.directory /opt/data/skills` 解决 `dubious ownership` 错误。
6. **DNS 解析：** 中国网络下 GitHub API 的 DNS 可能被污染。如果 `api.github.com` 无法解析，尝试在脚本中使用 `--resolve` 或配置系统 DNS（如 `114.114.114.114`）。
