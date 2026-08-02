---
name: github-gfw-sync
description: "Sync git repos to GitHub through the Great Firewall of China — HTTPS + token auth instead of blocked SSH, silent-failure pitfalls, and cron auto-sync."
version: 1.0.0
author: Agent
created_by: agent
metadata:
  hermes:
    tags: [github, gfw, sync, git, cron, china, network]
    related_skills: [hermes-agent]
---

# GitHub GFW Sync

在中国网络环境下同步 Git 仓库到 GitHub。SSH 端口 22 被 GFW 阻断，
必须使用 **HTTPS + Personal Access Token** 替代 SSH key 认证。

适用于：技能库同步（`hermes-skills`）、代码仓库备份、任何需要定期 `git push` 到 GitHub 的自动化场景。

---

## 核心问题

| 问题 | 现象 | 根因 |
|:-----|:-----|:-----|
| SSH 端口被墙 | `kex_exchange_identification: read: Connection reset by peer` | GFW 阻断 GitHub 的 22 端口 |
| 代理不稳定 | 偶尔通偶尔不通 | Clash 代理不是 100% 可靠 |
| **静默失败** ⚠️ | cron 报 `status: ok` 但远程没更新 | `|| echo "Push failed"` 吞掉了退出码 |

---

## 解决方案：HTTPS + Token

### 1. 准备 Token

在 GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens 创建。
需要 `Contents: Read and write` 权限（私有仓库需要）。

```bash
# 在 .env 或 .env_bot 中保存
export GH_BOT_TOKEN="github_pat_xxxxxxxxx"
```

### 2. 设置 Remote URL

```bash
cd /opt/data/skills
git remote set-url origin "https://HMS091:${GH_BOT_TOKEN}@github.com/HMS091/hermes-skills.git"
```

### 3. 验证推送

```bash
echo "test" && git add -A && git commit -m "verify sync" && git push origin main
```

---

## 自动同步脚本

创建 `/opt/data/scripts/skills-sync.sh`：

```bash
#!/bin/bash
set -e

SKILLS_DIR="/opt/data/skills"
cd "$SKILLS_DIR"

# Load GitHub token
source /opt/data/.env_bot 2>/dev/null || {
    echo "Warning: .env_bot not found"
    exit 1
}

# Ensure HTTPS remote with token
git remote set-url origin \
  "https://HMS091:${GH_BOT_TOKEN}@github.com/HMS091/hermes-skills.git"

# Push if changes exist
if ! git diff --quiet --exit-code || ! git diff --cached --quiet --exit-code; then
    git add -A
    git commit -m "auto-sync $(date '+%Y-%m-%d %H:%M')"
    # ⚠️ 不要用 || echo 吞掉错误！见下面的 Pitfalls
    git push origin main 2>&1
fi
```

通过 cronjob 创建：

```bash
# action=create, schedule="0 * * * *", script="skills-sync.sh", no_agent=true, deliver=local
```

---

## 诊断：验证同步是否真的在工作

### 检查本地 vs 远程 HEAD

```bash
source /opt/data/.env_bot
cd /opt/data/skills

echo "=== 本地 HEAD ==="
git rev-parse HEAD

echo "=== 远程 HEAD ==="
curl -s -H "Authorization: Bearer $GH_BOT_TOKEN" \
  "https://api.github.com/repos/HMS091/hermes-skills/git/refs/heads/main" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['object']['sha'])"
```

### 查看远程提交记录

```bash
source /opt/data/.env_bot
curl -s -H "Authorization: Bearer $GH_BOT_TOKEN" \
  "https://api.github.com/repos/HMS091/hermes-skills/commits?per_page=5" \
  | python3 -c "
import json,sys
data = json.load(sys.stdin)
for c in data:
    msg = c['commit']['message'].split(chr(10))[0]
    print(f\"{c['sha'][:10]} {c['commit']['committer']['date'][:10]} {msg}\")
"
```

---

## 仓库可见性：私有 ↔ 公开（2026-08-02：hermes-skills 已改为 public）

### 检查可见性

```bash
# 无 token 请求：200 = 公开可拉取，404 = 私有
curl -s -o /dev/null -w "%{http_code}\n" "https://api.github.com/repos/HMS091/hermes-skills"
# 带 token 看字段
curl -s -H "Authorization: token $GH_BOT_TOKEN" "https://api.github.com/repos/HMS091/hermes-skills" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('private:', d['private'], '| visibility:', d['visibility'])"
```

### 改为公开（PATCH API，无需网页操作）

```bash
curl -s -X PATCH -H "Authorization: token $GH_BOT_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/HMS091/hermes-skills" \
  -d '{"visibility":"public"}' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('private'), d.get('visibility'))"
```

### ⚠️ 公开前必须做的安全检查

1. **扫描全仓库文件树**找敏感文件名（.env/token/secret/key/pem/password）：
```bash
curl -s -H "Authorization: token $GH_BOT_TOKEN" \
  "https://api.github.com/repos/HMS091/hermes-skills/git/trees/main?recursive=1" \
  | python3 -c "import json,sys,re; d=json.load(sys.stdin); paths=[t['path'] for t in d.get('tree',[])]; print([p for p in paths if re.search(r'\.env|token|secret|credential|\.pem|\.key|password', p, re.I)])"
```
2. **清理被 `git add -A` 误提交的内部临时文件**（如 `.bundled_manifest_*.tmp`）：`.gitignore` 里的 `.bundled_manifest` 不带通配符，匹配不到带后缀的 tmp 文件，会被 auto-sync 一起提交。用 `git rm --cached <file>` + 删除。
3. **公开后立即用无 token 请求验证**返回 200。

**现状：** hermes-skills 已是 public，其他 agent/设备无需任何凭据即可 `git clone https://github.com/HMS091/hermes-skills.git`。README.md 中已有公开拉取说明。

---

## Pitfalls

### 1. 🚨 `|| echo "Push failed"` 导致静默失败

```bash
# ❌ 致命的错：push 失败但退出码为 0，cron 报 ok
git push origin main 2>&1 || echo "Push failed"

# ✅ 正确做法：让错误传播
git push origin main 2>&1

# 或者保留错误日志但不吞退出码：
git push origin main 2>&1 || {
    rc=$?
    echo "Push failed (exit $rc)"
    exit $rc
}
```

**后果：** 曾因此 26 天未发现同步失败。cron 显示 `last_status: ok`，
但远程仓库停留在 7 月 3 日，本地已有 30 次新提交。

### 2. SSH 被墙误判为 key 问题

`ssh -T git@github.com` 输出 `Permission denied (publickey)` 不一定代表 key 未注册。
可能是 GFW 重置连接后 SSH 回退到 key 认证阶段时已无连接。

**诊断：** 加 `-v` 查看：
```
ssh -vT git@github.com 2>&1 | grep "Connection reset"
# 如果显示 Connection reset by peer，是被墙不是 key
```

### 3. Token 在 .git/config 明文存储

`git remote set-url origin "https://USER:TOKEN@github.com/..."` 会将 token 写入 `.git/config`。
单用户容器环境可接受。如需更高安全性，使用 git credential store：

```bash
git config credential.helper 'store --file /opt/data/.git-credentials'
echo "https://HMS091:${GH_BOT_TOKEN}@github.com" > /opt/data/.git-credentials
git remote set-url origin https://github.com/HMS091/hermes-skills.git
```

### 4. 远程历史分歧

如果另一个设备曾 push 过，本地 push 会被拒绝。用 `--force-with-lease` 安全覆盖：

```bash
git fetch origin
git push --force-with-lease origin main
```

`--force-with-lease` 比 `--force` 安全 — 只覆盖你看到的最新远程状态。

### 5. curl 通过 python3 pipe 超时

```bash
# ❌ 容易超时
curl ... | python3 -c "..."

# ✅ 先存文件再处理
curl ... > /tmp/result.json && python3 -c "import json; d=json.load(open('/tmp/result.json')); ..."
```

---

## 在多台设备间同步

### 主设备（推送方）

见上面的自动同步脚本配置。

### 从设备（拉取方）

```bash
# 克隆（公开仓库，无需任何凭据）
git clone https://github.com/HMS091/hermes-skills.git /opt/data/synced-skills

# 需要写权限（往上游 push）时用带 token 的 URL：
git clone "https://HMS091:${GH_BOT_TOKEN}@github.com/HMS091/hermes-skills.git" \
  /opt/data/synced-skills

# 配置 Hermes 加载同步目录
# 编辑 /opt/data/config.yaml 添加：
# skills:
#   external_dirs:
#     - /opt/data/synced-skills

# 设置自动拉取 cron
# 0 * * * * cd /opt/data/synced-skills && git pull origin main
```
