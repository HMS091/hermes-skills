# 多设备技能同步（GitHub 方案）

## 概述

在多台运行 Hermes Agent 的设备之间同步技能库。本方案使用 **GitHub 私有仓库**作为中继，一台设备推送，其他设备拉取。

## 架构

```
Device A (主设备)              GitHub                    Device B (从设备)
/opt/data/skills/  ──git push──▶  HMS091/hermes-skills  ──git pull──▶  /opt/data/synced-skills/
        │                                                                    │
  cron 每小时自动推送                                                  cron 每小时自动拉取
        │                                                                    │
        ▼                                                                    ▼
  skills.external_dirs: []  (默认)                                  skills.external_dirs:
                                                                      - /opt/data/synced-skills
```

## 主设备设置（一次性）

### 1. 准备 SSH key

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "HMS091"
cat ~/.ssh/id_ed25519.pub
```

把输出的公钥加到 GitHub：https://github.com/settings/ssh/new

> **注意 SSH key 路径：** 如果 `$HOME` 指向 `/opt/data/home/` 但进程以 `root` 运行，key 会被写入 `/opt/data/home/.ssh/` 但 `ssh` 命令可能在 `/root/.ssh/` 里找。解决：复制一份到 `/root/.ssh/` 或直接指定 `ssh -i`。

### 2. 验证 SSH 连接

```bash
ssh -T git@github.com
# 输出: Hi HMS091! You've successfully authenticated...
```

> **GFW 问题：** 在中国网络环境下，SSH 端口 22 和 443 可能被封锁导致 `Connection closed`。此时 HTTPS 仍然可用（`curl https://github.com` 返回 200），需要使用 Personal Access Token (PAT) 走 HTTPS 推送。

### 3. 创建 GitHub 仓库

```bash
# 需要 GitHub Token（ghp_... / github_pat_...）
source /opt/data/.env_bot  # 如果 token 存在 .env_bot 中
curl -sL -X POST "https://api.github.com/user/repos" \
  -H "Authorization: Bearer $GH_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"hermes-skills","private":true}'
```

### 4. 初始化本地 Git

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
git remote add origin git@github.com:HMS091/hermes-skills.git
git push -u origin main
```

### 5. 设置自动推送（cron）

创建脚本 `/opt/data/scripts/skills-sync.sh`：

```bash
#!/bin/bash
set -e
cd /opt/data/skills
if ! git diff --quiet --exit-code || ! git diff --cached --quiet --exit-code; then
    git add -A
    git commit -m "auto-sync $(date '+%Y-%m-%d %H:%M')"
    unset http_proxy https_proxy
    git push origin main 2>&1 || echo "Push failed"
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

### 1. 生成 SSH key 并添加到 HMS091 账号

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

去 https://github.com/settings/ssh/new 添加。

### 2. 克隆仓库

```bash
git clone git@github.com:HMS091/hermes-skills.git /opt/data/synced-skills
```

### 3. 配置 Hermes 加载同步目录

编辑 `/opt/data/config.yaml`：

```yaml
skills:
  external_dirs:
    - /opt/data/synced-skills
```

### 4. 设置自动拉取

```bash
crontab -e
# 加一行：
0 * * * * cd /opt/data/synced-skills && git pull origin main
```

### 5. 重启 Hermes 生效

## 验证

```bash
# 查看技能是否加载
ls /opt/data/synced-skills/

# 如果 Hermes 正在运行，新技能会在启动时自动加载
# 配置 external_dirs 后不需要手动 import
```

## Pitfalls

1. **SSH key 路径不一致：** `$HOME` 和进程实际 uid 的 home 可能不同。ssh 找 key 的路径取决于实际 uid，不是 `$HOME` 环境变量。调试用 `ssh -v git@github.com 2>&1 | grep "identity file"` 查看实际搜索路径。
2. **GFW 封锁 SSH：** 中国网络环境下 SSH 端口 22/443 可能被墙。备选方案：使用 HTTPS + token 推送，或通过代理（Clash）中转。
3. **SSH key 授权：** key 必须添加到 GitHub 账号的 Settings → SSH and GPG keys 中，且需与本地私钥匹配。
4. **首次推送大仓库：** skills 目录可能包含数百个文件（本文案例 654 个文件/161K+ 行），首次 push 需要耐心等待。
5. **Hermes 内部文件：** `.bundled_manifest`、`.hub/`、`.curator_*`、`.usage.json` 等是 Hermes 运行时文件，不应入版本控制。务必配置 `.gitignore`。
6. **skills 目录权限：** `/opt/data/skills/` 可能由 `hermes` 用户拥有，但 git 操作以 `root` 运行。需要 `git config --global --add safe.directory /opt/data/skills` 解决 `dubious ownership` 错误。
