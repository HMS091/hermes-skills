# Docker Container 能力增强指南

## 适用场景
用户期望 Hermes Agent 拥有完整的工具链能力（浏览器、媒体处理、文档解析等），但运行环境是受限的 Docker 容器。本文件记录系统性的环境诊断→修复→增强流程。

## 1. 网络诊断（第一步）

Docker 容器最常见的限制。必须先确定网络拓扑，否则 apt/pip/npm 全挂。

### 代理挂掉 vs 代理恢复的两种场景

**场景A：代理彻底挂了（Connection refused）**
→ 清除代理变量，走直连。整套方案的黄金法则。

**场景B：代理是通的但网速慢（能ping通，下载慢）**
→ 保留代理（它能绕过某些网站的访问限制），但安装策略要改为：
- **分批安装**：把一个大安装命令拆成2-3个并行后台任务，每个apt-get install 包数不超过5个
- **不要超时后直接重试**：先kill长时间无输出的进程，重新拆分命令
- **后台通知**：用 `notify_on_complete=true` 监控进度

```bash
# 1a. 检查代理环境变量
env | grep -i proxy

# 1b. 测试代理是否存活
curl -s --max-time 3 "http://<gateway_ip>:<port>"

# 1c. 如果代理已死 -> 清理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
# 持久化清理（需注意安全审批）：
# rm -f /etc/profile.d/proxy.sh
# cat > /etc/environment << 'EOF'
# PATH=...
# NO_PROXY=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8
# EOF

# 1d. 测试直连
curl -s --noproxy '*' --max-time 5 "https://httpbin.org/ip"

# 1e. 检查apt源
curl -sI --max-time 5 "http://deb.debian.org/debian/dists/trixie/Release"
```

### 代理恢复模式
**关键：清理前一定要备份！** 用户可能只是说"代理不通"，但后面又说"代理是通的，网速慢"。
```bash
# 清理前
cp /etc/environment /etc/environment.bak.$(date +%Y%m%d)

# 恢复时
cp /etc/environment.bak.$(date +%Y%m%d) /etc/environment
source /etc/environment
```
**不要假设永久清除代理是正确的**——在中国大陆等受限网络，代理可能是唯一出口。用户可能先说"代理不通"然后又说"代理其实是通的，就是网速慢"，所以每次修改前必须先备份。恢复命令：
```bash
cp /etc/environment.bak.$(ls /etc/environment.bak.* | tail -1 | sed 's/.*bak.//') /etc/environment || true
source /etc/environment
```

## 2. 系统诊断

```bash
# 系统版本
cat /etc/os-release

# CPU/内存
nproc && free -h | grep Mem

# 磁盘
df -h /

# 已装工具
which python3 node npm curl wget git vim tmux htop jq chromium

# Python环境
/opt/hermes/.venv/bin/python --version
/opt/hermes/.venv/bin/pip list

# Node环境
node --version && npm --version
npm list -g --depth=0
```

## 3. 安装清单（按优先级）

### 3.1 浏览器能力

**完整浏览器自动化栈：chromium + playwright + selenium**

| 层 | 工具 | 用途 |
|:--|:--|:--|
| 浏览器引擎 | chromium + chromium-headless-shell | 渲染/抓取 |
| Python自动化(A) | playwright | 现代API，自动下载浏览器，推荐 |
| Python自动化(B) | selenium | 传统方案，复用系统chromium |

#### Step 1: 安装chromium（核心浏览器）

```bash
# 先搜索确认包名（Debian Trixie包名可能有变化）
apt-cache search chromium | grep -i browser

# 安装三个包
apt-get install -y chromium chromium-headless-shell chromium-sandbox
```
安装包约200MB（chromium~82MB, headless-shell~60MB, common~25MB），在NAS环境（Celeron J3455）下载解压需3-5分钟。
apt 进程CPU占用率50%+时说明在解压，不是卡住。如果apt卡住很久且deb已在缓存中，可手动安装：
```bash
# 1. 杀apt进程
kill -9 $(pgrep -f "apt-get install.*chromium") 2>/dev/null
2. 释放锁
rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock
dpkg --configure -a 2>&1 | tail -5
3. 手动装已下载的deb
dpkg -i /var/cache/apt/archives/chromium-common_*.deb 2>&1 | tail -3
dpkg -i /var/cache/apt/archives/chromium_*.deb 2>&1 | tail -3
dpkg -i /var/cache/apt/archives/chromium-headless-shell_*.deb 2>&1 | tail -3
dpkg -i /var/cache/apt/archives/chromium-sandbox_*.deb 2>&1 | tail -3
4. 自动修复剩余依赖
apt-get install -f -y -qq 2>&1 | tail -5
```

验证：
```bash
which chromium chromium-headless-shell
chromium --version
/usr/lib/chromium-headless-shell/chromium-headless-shell --version
```

#### Step 2: 安装playwright（推荐用于爬虫和自动化）

Playwright会自行下载chromium（与系统安装的独立），约113MB。

```bash
# pip安装
/opt/hermes/.venv/bin/pip install playwright

# 下载内置chromium浏览器（可选，也可以复用系统chromium）
/opt/hermes/.venv/bin/playwright install chromium
```

**Playwright绕过B站风控示例：**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 先访问B站首页获取cookie
    page.goto('https://www.bilibili.com', wait_until='domcontentloaded')
    
    # 搜索页面
    page.goto('https://search.bilibili.com/all?keyword=xxx&order=pubdate', 
              wait_until='domcontentloaded')
    page.wait_for_timeout(3000)
    
    # 提取视频链接和标题
    links = page.query_selector_all('a')
    for link in links:
        href = link.get_attribute('href') or ''
        if '/video/BV' in href:
            bv = href.split('/video/')[1].split('?')[0].split('/')[0]
            title = link.get_attribute('title') or ''
            print(f'BV: {bv}  {title}')
    
    # 查看视频简介
    page.goto('https://www.bilibili.com/video/BVxxxx', 
              wait_until='domcontentloaded')
    page.wait_for_timeout(3000)
    text = page.inner_text('body')
    # 搜索关键词行
    for line in text.split('\\n'):
        if any(k in line for k in ['装机', '微信', '免费', '收费', '配置']):
            print(f'  🔑 {line}')
    
    browser.close()
```

注意：B站新版空间页是Vue SPA，`window.__INITIAL_STATE__` 已被移除。
推荐走搜索接口或直接打开单个视频页查看简介。

#### Step 3: 安装selenium（备选方案，复用系统chromium）

```bash
/opt/hermes/.venv/bin/pip install selenium
```

验证：
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.binary_location = '/usr/bin/chromium'
driver = webdriver.Chrome(options=options)
driver.get('https://httpbin.org/ip')
print(driver.title)
driver.quit()
```

playwright验证：
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://httpbin.org/ip')
    print(page.title())
    browser.close()
```
两个apt-get命令不能并行（dpkg锁冲突），需要串行。如果同时启动了多个，后启动的会因锁冲突失败。处理方式：等第一个完成后重试第二个。

**dpkg锁冲突恢复（当需要杀死挂起的apt进程时）：**
```bash
# 1. 确认哪个进程持有锁
ps aux | grep -E '(dpkg|apt-get)' | grep -v grep

# 2. 强制杀掉
kill -9 <PID>

# 3. 释放锁文件
rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock

# 4. 修复可能损坏的dpkg状态
dpkg --configure -a 2>&1 | tail -5

# 5. 继续剩余的安装
apt-get install -f -y -qq 2>&1 | tail -10
```

### 3.2 网络采集工具
```bash
# jq 已安装，增强版：
apt-get install -y curl jq

# youtube-dl / yt-dlp（需通过pip）
/opt/hermes/.venv/bin/pip install yt-dlp
```

### 3.3 图片/文档处理
```bash
apt-get install -y tesseract-ocr tesseract-ocr-chi-sim ffmpeg
/opt/hermes/.venv/bin/pip install pillow pymupdf python-docx openpyxl pandas
```

### 3.4 开发工具
```bash
apt-get install -y ripgrep
npm install -g typescript ts-node
```
npm全局装好后需要设置NODE_PATH才能被require()找到（见第6节）。

### 3.5 数据工具
```bash
apt-get install -y sqlite3
```

## 4. 安装失败处理

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| apt-get update 超时 | apt CDN不稳定或代理问题 | 重试1-2次；换国内镜像源 |
| pip 安装连接拒绝 | 代理配置残留 | `unset http_proxy https_proxy` 后重试 |
| npm 安装失败 | npm registry被墙 | `npm config set registry https://registry.npmmirror.com` |
| pip联网安装Python包超时 | 代理慢但可用 | 先用`pip list`确认已有包，不要盲目重试；确认代理确实是通的再设--proxy |
| chromium 版本不匹配 | Debian Trixie太新 | 尝试 `apt-cache search chromium` 确认包名 |
| requests返回412 | CDN风控，requests默认UA和TLS指纹与curl不同 | 改用 `curl -s --noproxy '*'` |
| npm exit code 0但包没装上 | 网速慢导致npm输出混淆 | 用 `npm list -g --depth=0` 确认，重装时有`changed N packages`输出才算真成功 |
| dpkg锁冲突（apt-get install并行冲突） | 同时启动了多个apt-get/apt install进程 | 杀进程→释放锁→`dpkg --configure -a`→重试 |
| apt停在配置阶段很久（CPU 50%+） | 大包解压中（chromium约200MB） | 检查CPU/磁盘IO，等待即可，不是卡死 |
| dpkg依赖缺失手动安装失败 | 直接dpkg -i跳过apt依赖解析 | 先dpkg装依赖包→再dpkg装主包→最后`apt-get install -f`修复 |

## 5. 国内镜像源配置

### Debian / Ubuntu
```bash
# 备份
cp /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.bak
# 换中科大源
sed -i 's|deb.debian.org|mirrors.ustc.edu.cn|g' /etc/apt/sources.list.d/debian.sources
# 或清华源
sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources
```

### npm
```bash
npm config set registry https://registry.npmmirror.com
```

### pip (在 venv 外)
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

## 6. 特别注意事项

### B站API风控策略
B站对无登录态的API请求限制严格：
- **code: -352** → 风控失败，需要wbi签名（动态时间戳+密钥hash）
- **code: -403** → 访问权限不足，需要cookies
- **code: -799** → 请求过于频繁
- **HTTP 412** → CDN层拦截，requests库比curl更容易触发
- **HTML SPA页面** → 主页用Vue渲染，`window.__INITIAL_STATE__`已被移除，curl抓取不到视频数据

有效策略：
1. **通过搜索接口** `api.bilibili.com/x/web-interface/search/type` 获取视频列表（不需要wbi签名）
2. **单个视频详情** `api.bilibili.com/x/web-interface/view?bvid=BVxxx` 获取简介（需要登录cookies）
3. **装好chromium后用浏览器打开** — B站不对浏览器(有完整UA+JS环境)做拦截
4. 始终设置 `Referer: https://www.bilibili.com` 和完整Chrome UA

### npm全局包的NODE_PATH问题
`npm install -g` 装好后，`require()` 找不到全局模块（即使 `npm root -g` 路径正确）。
这是因为 `NODE_PATH` 环境变量未设置。修复方法：
```bash
# 验证安装
npm list -g --depth=0   # 确认包存在
ls $(npm root -g)       # 确认文件存在

# 设置NODE_PATH（临时）
export NODE_PATH=/usr/local/lib/node_modules
node -e "const ts = require('typescript'); console.log('ok:', ts.version)"

# 持久化到/etc/environment
echo "NODE_PATH=/usr/local/lib/node_modules" >> /etc/environment
```

### 安装后验证清单
每次批量安装后做验证，比用户使用时才发现缺失更好。**用表格呈现进度给用户看**：
```markdown
| 类别 | 工具 | 状态 |
|:--|:--|:--:|
| **浏览器** | chromium v148.0.7778.178 | ✅ |
| **Python包** | pillow, pymupdf, bs4, ...(N个) | ✅ |
| **Node** | typescript v6.0.3 | ✅ |
```

```bash
# Python包验证
/opt/hermes/.venv/bin/python -c "
import PIL, fitz, openpyxl, docx, bs4, lxml, pandas, numpy, pptx, yaml, requests
print('✅ 核心Python包全部可用')
import yt_dlp
print('✅ yt-dlp可用')
"

# Node工具验证
NODE_PATH=/usr/local/lib/node_modules node -e "
const ts = require('typescript');
console.log('✅ typescript:', ts.version);
"

# 系统工具验证
which chromium chromium-headless-shell ffmpeg tesseract sqlite3 rg
```

### requests vs curl差异
在受限网络环境中，`requests` 库有时会返回 `412 Precondition Failed` 或触发CDN风控，
而 `curl` 命令能正常工作。这是因为 `requests` 的默认 User-Agent 和 TLS 指纹与 `curl` 不同。
遇到HTTP 412时，优先用 `curl -s` 替代 `requests.get()`。B站API尤其敏感——Python的
urllib/requests比curl更容易触发风控。

### 后台安装策略
- apt-get install 一个长列表容易超时（尤其网络慢时），应拆分到2-3个background=true进程，每个5个包以内
- 用notify_on_complete=true监听完成
- npm第一次exit code 0但实际没装成功是常见情况，需要验证（`npm list -g --depth=0`）

### 环境变量持久化注意事项
- `/etc/environment` 修改后**只在下次登录时生效**，当前shell需要手动 `export`
- `rm -f /etc/profile.d/proxy.sh` 同时清理
- 修改前一定备份：`cp /etc/environment /etc/environment.bak.$(date +%Y%m%d)`
