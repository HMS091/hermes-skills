# Hermes Agent 技能库同步

这个仓库用来在多台设备之间同步 Hermes Agent 的技能（Skills），**仓库已公开**，任何 Agent / 设备都可以直接拉取使用。

## 本机（已配置好）

- ✅ 每小时自动推送技能更新到 GitHub
- ✅ 技能目录：`/opt/data/skills/`
- ✅ 自动忽略 Hermes 内部文件（`.hub/` `.curator_*` `.usage.json` 等）

## 其他 Agent 直接使用（公开拉取）

无需任何凭据，直接 clone：

```bash
git clone https://github.com/HMS091/hermes-skills.git /opt/data/synced-skills
```

其他 Hermes / Claude / 任意 Agent 机器把 `external_dirs` 指向该目录即可加载全部技能（见下方配置）。每小时 `git pull origin main` 即可保持同步。

## 其他设备安装（写入权限方式）

### 方法一：SSH Key 方式（推荐）

**第一台设备（这台机子）已经有 SSH key 了。其他设备需要：**

1. **生成 SSH key 并添加到 HMS091 账号**
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
   cat ~/.ssh/id_ed25519.pub
   ```
   把输出的公钥添加到这里：https://github.com/settings/ssh/new
   标题写 `Hermes-device-2` 之类的

2. **克隆技能仓库**
   ```bash
   git clone git@github.com:HMS091/hermes-skills.git /opt/data/synced-skills
   ```

3. **配置 Hermes 加载这个目录**
   编辑 `/opt/data/config.yaml`，找到 `skills:` 这一块，改成：
   ```yaml
   skills:
     external_dirs:
       - /opt/data/synced-skills
   ```

4. **设置自动拉取**
   ```bash
   crontab -e
   ```
   加一行：
   ```bash
   0 * * * * cd /opt/data/synced-skills && git pull origin main
   ```

5. **重启 Hermes** 即可生效

### 方法二：直接把整套配置复制过去

如果其他设备网络好，可以直接复制本机的 `/opt/data/skills/` 目录过去：

```bash
# 在本机打包
cd /opt/data && tar czf skills.tar.gz skills/

# 传到其他设备，解压到同目录就行
# 但注意：这样不会自动更新
```
