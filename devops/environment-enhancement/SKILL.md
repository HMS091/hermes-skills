---
name: environment-enhancement
description: Systematically enhance a Docker/Linux environment with tools and capabilities — browser, media, document processing, development tools, and data extraction. Designed for Docker containers on NAS (Synology) with limited initial tooling.
trigger: "User asks to 'enhance', 'upgrade', 'install all skills', 'make me more capable', 'install tools', '继续安装', '安装所有技能', or mentions lacking specific capabilities (browser, PDF, OCR, video processing). Also: user asks '你能想办法完善你的技能吗' or similar 'make yourself more capable' intents."
tags: [setup, docker, debian, tool-installation, nas]
---

# Environment Enhancement

Systematic approach to installing tools and capabilities in a Docker container environment (Debian, NAS-hosted, with proxy).

## Prerequisites — Network Diagnosis

Before installing anything, diagnose the network:

```bash
# Check proxy
curl -s --max-time 3 -w "\nHTTP: %{http_code}\n" "https://www.baidu.com" -o /dev/null
# Check direct access
curl -s --noproxy '*' --max-time 5 "https://httpbin.org/ip"
# Check apt source
curl -sI --max-time 5 "http://deb.debian.org/debian/dists/trixie/Release"
```

**Proxy restore pattern:** If /etc/environment was modified and user says proxy works, restore from auto-created backup:
```bash
# 查找最新备份
ls -t /etc/environment.bak.* | head -1
# 恢复
cp /etc/environment.bak.$(date +%Y%m%d) /etc/environment
source /etc/environment
```

**Proxy gone → unexpected restore cycle:** In one session, the user first confirmed proxy was dead (connection refused), so it was cleared. Later the user said proxy was actually working but slow. The pattern: **don't permanently delete proxy config on first failure** — backup it first. The NAS-hosted proxy may be restarted or temporarily unreachable. The safe approach is:
1. Save the backup before modification
2. If user later says proxy works, restore from backup and re-try installs WITH proxy
3. Always `export` the proxy vars after restoring /etc/environment — they don't auto-apply to the current shell

## Installation Batches

### Batch 1 — System Packages (apt)
Install all at once for efficiency. Network is the bottleneck, not CPU.

```bash
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  chromium chromium-headless-shell chromium-sandbox \
  ffmpeg \
  tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng \
  sqlite3 \
  ripgrep \
  libpango1.0-dev libcairo2-dev
```

**Troubleshooting:** Chromium package is ~200MB. First download may timeout on slow connections. Retrying 1-2 times usually works. If persistent failure, swap Debian mirror:
```bash
sed -i 's|deb.debian.org|mirrors.ustc.edu.cn|g' /etc/apt/sources.list.d/debian.sources
```

**分批策略（当网络慢时）：** 如果一个长 apt-get install 命令超时，不要直接重试——kill掉后拆成2-3个并行后台进程，每个不超过5个包。用 `notify_on_complete=true` 监听完成：
```bash
# 第一批：浏览器相关
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq chromium chromium-headless-shell chromium-sandbox
# 第二批：媒体+文档（可并行）
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng sqlite3 ripgrep
```

### Environment Detection — Before Installing Anything

Always check these before starting installation:

```bash
# 1. Container detection
cat /proc/1/cgroup 2>/dev/null | head -3  # If shows /docker/, we're in a container
cat /proc/1/sched 2>/dev/null | head -2    # PID 1 scheduler

# 2. Docker availability
docker ps 2>&1  # If "Cannot connect to the Docker daemon" → no Docker-in-Docker
ls -la /var/run/docker.sock 2>/dev/null   # If missing, cannot run containers
apt list --installed 2>/dev/null | grep docker-cli  # CLI-only install

# 3. GPU availability
nvidia-smi 2>&1  # If "command not found" → no GPU, skip GPU-dependent tools

# 4. Python environment type
pip install --dry-run dummy-package 2>&1 | grep "externally-managed"
# If externally-managed → need --break-system-packages or venv

# 5. Available disk space
df -h / | tail -1  # Check if ~5GB+ for model downloads
```

**PEP 668 (externally-managed-environment) 处理：** Python 3.13+ on Debian has this protection by default. Three options:
1. **`--break-system-packages`** — fastest, works for simple installs. Acceptable in a disposable container.
2. **Create a venv** — `python3 -m venv /opt/venv && /opt/venv/bin/pip install ...` — safer, recommended for production.
3. **Use Hermes venv** — Hermes already has `/opt/hermes/.venv/` — `pip install` via that venv's pip:
   ```bash
   /opt/hermes/.venv/bin/pip install --quiet <package>
   ```
   Check with: `ls /opt/hermes/.venv/bin/pip 2>/dev/null`

**Docker-in-Docker limitation:** When running inside a container (check `/proc/1/cgroup` for `/docker/`), Docker CLI is often installed but Docker daemon is NOT running. This means:
- `docker compose up -d` will fail with "Cannot connect to the Docker daemon"
- The compose files and startup scripts can be prepared, but need to be deployed elsewhere
- Workaround: prepare `docker-compose.yml` + `.env` + `start.sh` in a known directory, so they're ready when Docker becomes available

**Docker compose fallback pattern:** When Docker daemon is unavailable but you want to prepare for future deployment:
1. Create a services directory: `mkdir -p /opt/data/docker-services/{ragflow,anythingllm,firecrawl,...}`
2. For each service, download or write the `docker-compose.yml` with proper port mappings and volumes
3. Create a unified `start-all.sh` script that checks for Docker first, then launches each service
4. Save `.env` files with default passwords
5. Report the limitation clearly: "Docker daemon not available in this container. Configs prepared at /opt/data/docker-services/ — deploy on your Docker host with `bash start-all.sh`"

### Batch 2 — Python Packages (pip)

Run in parallel with Batch 1 (independent).

**Proxy pitfall:** If proxy env vars are set, pip will try to reach PyPI through the proxy. If the proxy is down, pip fails with connection refused. Always check `env | grep -i proxy` before the pip install and either unset or confirm proxy is working.

**Externally-managed environment fix:** If you get `error: externally-managed-environment`, add `--break-system-packages`:
```bash
pip install --break-system-packages --quiet <package>
```
This is acceptable in a disposable container environment. For production, use a venv instead.

```bash
/opt/hermes/.venv/bin/pip install --quiet --timeout 60 \
  pillow \
  pymupdf \
  openpyxl \
  python-docx \
  beautifulsoup4 \
  lxml \
  yt-dlp \
  youtube-transcript-api \
  pandas \
  numpy \
  requests \
  python-pptx \
  pyyaml
```

**Key packages and their skills:**
- `pymupdf` → PDF text extraction (ocr-and-documents, nano-pdf)
- `yt-dlp` → YouTube downloading (youtube-content)
- `pillow` → image processing (pixel-art, ocr-and-documents)
- `python-pptx`, `openpyxl`, `python-docx` → Office editing (powerpoint)
- `beautifulsoup4`, `lxml` → HTML scraping (forum-research)

**Post-install verification (pip import names differ from package names):**
```bash
/opt/hermes/.venv/bin/python -c "
import PIL; print('pillow:', PIL.__version__)
import fitz; print('pymupdf:', fitz.__version__)
import openpyxl; print('openpyxl:', openpyxl.__version__)
import docx; print('python-docx:', docx.__version__)
import bs4; print('bs4:', bs4.__version__)
import lxml; print('lxml: ok')
import yt_dlp; print('yt-dlp:', yt_dlp.__version__)  # may need try/except
import pandas; print('pandas:', pandas.__version__)
import numpy; print('numpy:', numpy.__version__)
import pptx; print('python-pptx:', pptx.__version__)
import yaml; print('pyyaml:', yaml.__version__)
print('✅ 全部Python包导入成功')
"
```
Note: `yt_dlp.__version__` may be missing on some versions — use `yt_dlp.version.__version__` as fallback or import in try/except block.

### Batch 3 — Node.js Global Tools (npm)
Run in parallel with Batch 1 and 2.

```bash
npm install -g --silent typescript ts-node
```

**CodeGraph (colbymchenry/codegraph) — 代码知识图谱 MCP 工具**

CodeGraph 是 Hermes Agent 原生支持的 MCP 代码智能工具，安装后会在当前 Hermes 会话中直接提供 `codegraph_explore` 工具。它能减少 AI 助手搜索文件的工具调用次数 40-81%。

```bash
# 安装（GFW环境：取消代理后直连）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
npm i -g @colbymchenry/codegraph --noproxy '*'

# 配置 Hermes（自动改 config.yaml，添加 codegraph MCP 服务）
codegraph install --target=hermes --yes

# 在每个项目目录初始化索引（一次，索引后自动文件监听同步）
cd your-project
codegraph init

# 验证状态
codegraph status
```

参考：`references/codegraph-setup.md`

**npm在代理环境下载失败：** 容器可能有全局 `http_proxy` / `https_proxy` 环境变量指向不可达代理。npm 会走代理连 registry.npmjs.org，连接失败则超时卡住（60s 无响应）。修复：

```bash
# 1. 先检查是否被代理阻塞
env | grep -i proxy

# 2. 取消代理环境变量
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# 3. 安装时加 --noproxy 防止 npm 自己再用代理
npm i -g <package> --noproxy '*'
```

**npm镜像解决不了代理问题：** 如果直连 npm 慢，用国内镜像（npmmirror.com）也可能超时——在 Docker 内它可能 TLS 握手失败。最佳方案是 **`unset proxy` + `--noproxy '*'` + 设 `--timeout=120` 耐心等**。直连 30-60s 通常能完成。

**npm安装成功但require失败的常见原因：** npm全局模块装在`/usr/local/lib/node_modules/`，但Node默认require不搜这个路径。修复：先检查物理目录确认文件存在，然后用`NODE_PATH=/usr/local/lib/node_modules node -e "..."`验证，持久化到`/etc/environment`。

### Subsequent Batches (run after the first three finish)

```bash
# Browser automation (Playwright)
/opt/hermes/.venv/bin/pip install --quiet playwright
/opt/hermes/.venv/bin/python -m playwright install chromium

# Additional Python tools
/opt/hermes/.venv/bin/pip install --quiet \
  selenium

# CSS/image tools for creative skills
apt-get install -y -qq librsvg2-bin
```

## Skill-Capability Mapping

| Skill Category | Depends On | Installed Via |
|---------------|-----------|--------------|
| Browser (B站, web scraping, freelancing) | chromium, playwright, selenium | apt + pip (2-step) |
| PDF/Document (ocr-and-documents, nano-pdf) | pymupdf, tesseract | pip + apt |
| Media (youtube-content) | yt-dlp, ffmpeg | pip + apt |
| Office (powerpoint) | python-pptx, openpyxl, python-docx | pip |
| Visual (pixel-art, ascii-video) | pillow, ffmpeg | pip + apt |
| Development | ripgrep, node, typescript | apt + npm |
| Code Intelligence (CodeGraph MCP) | codegraph (npm) | npm |

## Hermes Multi-Device Skills Sync

当多台设备运行 Hermes Agent 时，需要在各设备间共享创建的技能。Hermes 支持通过 `skills.external_dirs` 配置额外技能目录。

### 原理

Hermes 默认技能目录是 `~/.hermes/skills/`（或 `/opt/data/skills/`），创建的技能存这里。`external_dirs` 可以额外指定**共享技能目录**，两个目录的技能都会被加载：

```yaml
# config.yaml
skills:
  external_dirs:
    - /mnt/nas/shared-skills    # NAS 挂载目录
    # 或
    - /opt/data/synced-skills   # git 同步目录
```

### 方案 A：NAS Samba/NFS 共享（推荐，实时同步）

**前提：** NAS（192.168.1.88）上已开启 Samba 或 NFS 共享。

```bash
# 1. 安装 cifs-utils
apt-get install -y cifs-utils

# 2. 创建挂载点
mkdir -p /mnt/nas/shared-skills

# 3. 挂载 NAS 共享（替换 username/password/sharename）
mount -t cifs //192.168.1.88/shared-skills /mnt/nas/shared-skills \
  -o username=your_user,password=your_pass,uid=$(id -u),gid=$(id -g)

# 4. 验证
ls /mnt/nas/shared-skills/
```

**持久挂载（重启不丢）：** 加到 `/etc/fstab`：
```
//192.168.1.88/shared-skills /mnt/nas/shared-skills cifs username=xxx,password=xxx,uid=0,gid=0,noauto 0 0
```

每台设备都这样配，技能文件放 NAS 上，所有设备实时共享。

### 方案 B：Git 仓库同步（有版本历史）

```bash
# 主设备：初始化共享技能目录
mkdir -p /opt/data/synced-skills

# 现有技能复制过去
cp -r /opt/data/skills/* /opt/data/synced-skills/

# 或从 GitHub 克隆已有仓库
git clone https://github.com/HMS091/hermes-skills.git /opt/data/synced-skills

# 设 cron 自动推送（每小时）
crontab -e
0 * * * * cd /opt/data/synced-skills && git add -A && git commit -m "auto sync $(date)" && git push
```

**GFW（中国防火墙）下同步的注意事项：**

在 China 网络环境下，SSH 到 GitHub 的端口 22 和 443 均被封锁，无法使用 SSH 方式 clone/push。必须改用 HTTPS + Personal Access Token：

```bash
# 1. 生成 GitHub Personal Access Token
#    去 https://github.com/settings/tokens/new
#    勾选 repo 权限，生成以 ghp_ 开头的 token

# 2. 配置 git 缓存 token
git config --global credential.helper store

# 3. 第一次 push/pull 时会提示输入用户名和密码
#    用户名：HMS091
#    密码：粘贴 token（不是 GitHub 登录密码）

# 4. 配置 git 身份（用于 commit 记录）
git config --global user.name "HMS091"
git config --global user.email "your-email"  # 填你的 GitHub 注册邮箱

# 5. 验证
git push origin main  # 第一次输 token 后永久记住
```

**删除 SSH key 避免冲突：** 如果已经生成过 SSH key 但 GFW 导致 SSH 连接失败，git 可能自动尝试 SSH 失败后不切换 HTTPS。确保 remote URL 是 HTTPS 格式：
```bash
git remote set-url origin https://github.com/HMS091/hermes-skills.git
```

其他设备只拉取（cron 每小时 `git pull`）。

### 使用效果

- `skill_manage(action='create')` 或 `action='patch'` 创建/更新的技能写入**默认目录**
- 手动或 cron 将新技能复制/推送到**共享目录**
- 其他设备重启 Hermes 后自动加载新技能
- 不需要改 `external_dirs` 也可用共享目录—Hermes 会自动合并所有目录的技能

### Pitfalls

1. **创建技能仍写入默认目录** — `skill_manage` 创建技能默认放在 `~/.hermes/skills/`（或 `/opt/data/skills/`），**不会自动写入共享目录**。需要手动复制或设 cron 同步。
2. **NAS 挂载断连** — 如果 NAS 重启或网络问题导致挂载丢失，Hermes 启动时找不到目录不会报错，只是那些技能不加载。建议用 `noauto` fstab 选项避免 boot 时卡住。
3. **git 冲突** — 如果多台设备同时修改同一个技能文件，git push 会失败。简单场景（一人多设备）很少遇到，信号量低的场景足够用。
4. **重启才生效** — Hermes 在启动时扫描技能目录。新技能加入共享目录后，需要 `/reset` 或重启 hermes 进程才能加载。`/reload-skills` 斜杠命令也能触发重扫。

## Appendix: Container Hardware Inspection

When a user asks about host hardware (CPU, RAM, motherboard model, memory type) from inside a Docker container where `/dev/mem` is inaccessible, use this approach:

### Step 1: Gather what's accessible from /sys
```bash
cat /sys/class/dmi/id/product_name
cat /sys/class/dmi/id/board_name
cat /sys/class/dmi/id/board_vendor
cat /sys/class/dmi/id/sys_vendor
lscpu
cat /proc/cpuinfo | grep "model name" | head -1
free -h
cat /proc/meminfo | head -5
```

### Step 2: Install tools (limited inside container)
```bash
apt-get install -y dmidecode lshw
```
These fail to read `/dev/mem` inside the container — confirm they can't work, then move to inference.

### Step 3: Infer memory type from known hardware
- **Synology DS918+**: Intel Celeron J3455 → DDR3L-1866 SO-DIMM. Board has 4GB soldered + 1× slot. Official max: 8GB, community: up to 16GB.
- **Intel Celeron/Pentium J/N series**: DDR3L or DDR4 depending on generation.
- For unknown hosts, look up `board_name` from `/sys/class/dmi/id/` + CPU model.

### Key Constraints
- **Docker containers cannot read /dev/mem** — dmidecode/lshw fail with "Can't read memory from /dev/mem". This is a container security boundary, not a bug.
- **Memory shown as "15GiB"** = binary GiB reading. 15GiB ≈ 16GB, 31GiB ≈ 32GB.
- **Swap can mislead** — some NAS/NUC setups provision large swap files. Don't confuse swap with physical RAM.
- If exact SPD data is needed, recommend SSH to host (`sudo dmidecode -t memory`) or physical inspection.

---

## Pitfalls

- **Proxy vs direct access mismatch**: The container may have proxy env vars set in /etc/environment, but the proxy server (e.g. 192.168.1.88:7890 on the NAS host) might be down. Always check `curl --max-time 3` to the proxy first.
- **Proxy can come back**: User may restart the proxy after you've cleared the config. Always backup before deleting. Restore from `/etc/environment.bak.<YYYYMMDD>` if needed.
- **Chromium installation timeout**: On 1.5GHz Celeron (NAS CPU) with slow network, chromium takes 2-5 minutes to download. Use background mode with notify_on_complete so you don't block waiting.
- **apt安装卡住（包已下载但配置阶段无响应）**: 用`ps aux | grep apt`找到apt进程，如果包确实已缓存（`ls /var/cache/apt/archives/chromium*.deb`），可以kill apt进程后手动dpkg安装：
  1. `kill -9 <apt_pid>`
  2. `rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock`
  3. `dpkg -i /var/cache/apt/archives/chromium*.deb`
  4. `apt-get install -f -y -qq`（修复依赖）
  注意：如果锁文件存在但为空且没有apt/dpkg进程在运行，直接`rm -f`即可。
- **pip can use proxy env vars**: If proxy is set but dead, pip will fail. Either restore proxy or unset it. Check `env | grep -i proxy` before pip installs.
- **`pip index versions` for fast version checking**: When checking if packages need updates, `pip install --upgrade --dry-run` is slow on limited networks (downloads full metadata). Use `pip index versions <pkg>` instead — it only fetches version metadata and is 3-5× faster. Parse output with `grep "^<pkg>" | head -1` to get the latest version string.
- **Don't mix system and pip installs in the same terminal call**: They're independent — run them in parallel in separate background terminals.
- **Node v20 ships with npm 9**: Fine for most tools. If npm install fails, check `npm config get registry` — default registry.npmjs.org is usually fine from China-based Docker.
- **npm全局模块安装后无法require（node -e找不到模块）**:
  - 安装：`npm install -g typescript ts-node` 报 exit code 0 但 `node -e "require('typescript')"` 失败
  - 原因：npm 全局模块装在 `/usr/local/lib/node_modules/`，但 Node.js 的默认 require 路径不包括这个目录（不会自动搜索 $NODE_PATH）
  - 修复：**先检查物理目录** `npm root -g && ls $(npm root -g)` 确认文件存在
  - 验证：`NODE_PATH=/usr/local/lib/node_modules node -e "const ts = require('typescript'); console.log('ok:', ts.version)"`
  - 持久化：将 `NODE_PATH=/usr/local/lib/node_modules` 写入 `/etc/environment`
- **Don't install playwright browsers via npx**: Use `python -m playwright install chromium` after pip install playwright — more reliable in Docker.
- **agent-browser (Hermes内置浏览器工具) 安装**：agent-browser 已经在 `/opt/hermes/node_modules/agent-browser/` 下，但需要额外安装 Chrome。运行 `cd /opt/hermes && npx agent-browser install`（通过代理下载 ~177MB）。装好后 cache 在 `/opt/data/home/.agent-browser/browsers/`，但 browser 工具会去 `/root/.agent-browser/browsers/` 找。修复：`mkdir -p /root/.agent-browser && ln -sf /opt/data/home/.agent-browser/browsers /root/.agent-browser/browsers`。npx install 下载较慢（受代理速度影响），设 120s 超时足够。
- **Playwright验证**：不能只验证import成功——要实际启动浏览器验证：
  ```python
  from playwright.sync_api import sync_playwright
  p = sync_playwright().start()
  b = p.chromium.launch(headless=True)
  page = b.new_page()
  page.goto('https://httpbin.org/ip')
  print(page.inner_text('body'))
  b.close(); p.stop()
  ```
  如果Playwright报错"chromium not found"，是没执行`playwright install chromium`。
- **Memory pressure**: Installing large packages (chromium ~200MB) while other processes run (Hermes, Docker overlay) on 16GB NAS may slow down. Monitor with `htop`.
- **pip import names ≠ package names**: `pillow` → `import PIL`, `pymupdf` → `import fitz`, `python-pptx` → `import pptx`. Verify with the post-install script above.
- **B站API风控分级**: Even after installing all tools, B站 may block automated scraping. The `/x/web-interface/view` endpoint (video details) is most stable; `/x/space/wbi/arc/search` (profile video list) is most strict. Always try the simpler endpoint first. Headers required: `User-Agent` (desktop Chrome) + `Referer: https://search.bilibili.com` or `https://www.bilibili.com`.
