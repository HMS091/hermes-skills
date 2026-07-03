#!/bin/bash
# Hermes 技能同步 - 新设备安装脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/HMS091/hermes-skills/main/install.sh | bash
# 或者手动复制到设备上运行

set -e

SKILLS_SYNC_DIR="/opt/data/synced-skills"
CONFIG_FILE="/opt/data/config.yaml"
GITHUB_REPO="git@github.com:HMS091/hermes-skills.git"
SCRIPT_DIR="/opt/data/scripts"

echo "========================================"
echo " Hermes 技能同步 - 新设备安装"
echo "========================================"
echo ""

# 检查是否已有 SSH key
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "📢 需要 SSH key 来访问 GitHub..."
    echo "请先去 GitHub 添加一个 SSH key:"
    echo "  1. 打开 https://github.com/settings/ssh/new"
    echo "  2. 标题: Hermes-device-XXXX"
    echo "  3. 把下面这串公钥复制进去:"
    echo ""
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "HMS091" 2>/dev/null
    cat ~/.ssh/id_ed25519.pub
    echo ""
    echo "📢 加好后按回车继续..."
    read -r
fi

# 配置 SSH
mkdir -p ~/.ssh
ssh-keyscan -H github.com >> ~/.ssh/known_hosts 2>/dev/null || true

echo ""
echo "📦 克隆技能仓库..."
git clone "$GITHUB_REPO" "$SKILLS_SYNC_DIR" 2>/dev/null || {
    echo "❌ 克隆失败，请确认 SSH key 已添加到 GitHub"
    exit 1
}

echo ""
echo "🔧 配置 Hermes 读取同步技能..."
# 检查 config.yaml 是否有 external_dirs
if grep -q "external_dirs" "$CONFIG_FILE" 2>/dev/null; then
    # 已有配置，追加路径
    sed -i "s|external_dirs: \[\]|external_dirs:\n    - $SKILLS_SYNC_DIR|" "$CONFIG_FILE"
else
    # 没有配置，新增
    cat >> "$CONFIG_FILE" << 'EOF'

skills:
  external_dirs:
    - /opt/data/synced-skills
EOF
fi

echo ""
echo "⏰ 设置自动拉取（每小时）..."
mkdir -p "$SCRIPT_DIR"
cat > "$SCRIPT_DIR/skills-pull.sh" << 'SCRIPT'
#!/bin/bash
cd /opt/data/synced-skills && git pull origin main 2>/dev/null
SCRIPT
chmod +x "$SCRIPT_DIR/skills-pull.sh"

# 添加 cron（如果不存在）
(crontab -l 2>/dev/null | grep -q "skills-pull") || \
    (crontab -l 2>/dev/null; echo "0 * * * * cd /opt/data/synced-skills && git pull origin main >> /tmp/skills-pull.log 2>&1") | crontab -

echo ""
echo "========================================"
echo " ✅ 安装完成！"
echo "========================================"
echo ""
echo "现在重启这台设备的 Hermes，技能就会自动加载。"
echo "之后技能有更新，每小时自动同步。"
