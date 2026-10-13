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

set -uo pipefail

SKILLS_DIR="/opt/data/skills"
BRANCH="main"
cd "$SKILLS_DIR" || { echo "❌ 找不到 $SKILLS_DIR"; exit 1; }

# Load GitHub token
source /opt/data/.env_bot 2>/dev/null || {
    echo "Warning: /opt/data/.env_bot not found, try GH_TOKEN"
}

# Set up HTTPS credential for unattended push
if [ -n "$GH_BOT_TOKEN" ]; then
    git remote set-url origin "https://HMS091:${GH_BOT_TOKEN}@github.com/HMS091/hermes-skills.git"
fi

# 1. 有变更就提交（含**未跟踪**文件 —— 只 diff 已跟踪文件会漏掉新建的 skill）
changed=0
if ! git diff --quiet --exit-code \
   || ! git diff --cached --quiet --exit-code \
   || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    git add -A
    git commit -q -m "auto-sync $(date '+%Y-%m-%d %H:%M')" && changed=1
fi

# 2. 先拉远端（别的 Hermes 实例可能推过），再 rebase —— 少了这步 push 会永久 fetch first 失败
if ! git fetch -q origin "$BRANCH" 2>/dev/null; then
    echo "❌ skills 同步失败：git fetch 失败（GitHub 连不上 / token 失效）"; exit 1
fi
if ! git rebase "origin/$BRANCH" >/tmp/skills-sync-rebase.log 2>&1; then
    git rebase --abort 2>/dev/null
    echo "❌ skills 同步失败：rebase 冲突，已回滚，本地改动未丢"; tail -n 5 /tmp/skills-sync-rebase.log; exit 1
fi

# 3. 该推就推；无待推提交则静默退出（cron 不推送空输出）
ahead=$(git rev-list --count "origin/$BRANCH..HEAD" 2>/dev/null || echo 0)
if [ "$ahead" = "0" ]; then
    [ "$changed" = "1" ] && echo "ℹ️ 已提交但仍与远端一致（无待推提交）"
    exit 0
fi
if ! git push -q origin "$BRANCH" 2>&1; then
    echo "❌ skills 同步失败：git push 被拒（远端 HEAD 已变，或 token 无权限）"; exit 1
fi
echo "✅ skills 已同步到 GitHub：$ahead 个提交 @ $(date '+%Y-%m-%d %H:%M')"
```

```bash
chmod +x /opt/data/scripts/skills-sync.sh
```

通过 Hermes cronjob API 创建（每小时执行，no_agent 模式，纯脚本）：

```bash
# 使用 cronjob 工具创建
# action=create, schedule="0 * * * *", script="skills-sync.sh", no_agent=true, deliver=all
# ⚠️ deliver=local 会让同步失败永远没人知道 —— 脚本输出只存进 cron/output/<job_id>/。
#    有输出才推送，安静时不会打扰；定期看 cronjob(action="list") 的 last_status / last_error。
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

1. **只 push 不 pull —— 最隐蔽的坏法。** 推送前必须 `git fetch` + `git rebase origin/main`。多设备场景下别的实例推过之后，单纯 `git push` 会永久返回 `! [rejected] main -> main (fetch first)`，本地改动**再也上不去**，而脚本看起来“跑了”。冲突则 `git rebase --abort` 回滚并告警，绝不强推。
2. **变更检测漏新文件。** 只比较 `git diff`（已跟踪文件）时，单独新建一个 skill 目录不会被提交、也不会同步。`git ls-files --others --exclude-standard` 非空也算有变更。
3. **别用 `|| echo "failed"` 吞掉 push 失败。** 退出码必须传播（cron 靠它定 `last_status`），否则失败静默；脚本日常用 `set -uo pipefail`。
4. **验证要对比远端 ref，不是 `/commits/main`（有缓存，会骗你）：**
   ```bash
   LOCAL=$(git rev-parse HEAD)
   REMOTE=$(curl -s https://api.github.com/repos/HMS091/hermes-skills/git/refs/heads/main \
     | python3 -c "import json,sys; print(json.load(sys.stdin)['object']['sha'])")
   [ "$LOCAL" = "$REMOTE" ] && echo OK
   # 想确认某个文件真的上去了，直接比 blob sha：
   git rev-parse HEAD:mlops/scrapling/SKILL.md   # vs contents API 返回的 .sha
   ```
5. **Token 泄露：** Token 嵌入 git remote URL 后，会在 `.git/config` 中以明文存储。同一设备上可接受，注意别误分享 `.git/config`。
6. **Token 过期：** GitHub PAT 有有效期。推送返回 403 就是过期信号；在 `.env_bot` 标注过期日期。
7. **首次推送大仓库：** skills 目录可能有数百个文件，首次 push 需耐心等待几分钟。HTTPS 略慢但比 SSH 稳定（SSH 22 被 GFW 阻断）。
8. **运行时文件不该入库：** `.bundled_manifest`、`.hub/`、`.curator_*`、`.usage.json`、`.locks/` 都是 Hermes 运行时产物；已误跟踪的先 `git rm -r --cached <path>` 再提交，并补进 `.gitignore`。
9. **skills 目录权限：** `/opt/data/skills/` 可能属于 `hermes` 用户而 git 以 `root` 跑，需 `git config --global --add safe.directory /opt/data/skills` 解决 `dubious ownership`。
10. **DNS 解析：** 中国网络下 `api.github.com` 的 DNS 可能被污染；用 `--resolve` 或换 DNS（如 `114.114.114.114`）。
