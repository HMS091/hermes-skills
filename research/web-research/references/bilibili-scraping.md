# Bilibili UP主信息爬取 + 信誉评价调查

## 本文件涵盖
- B站UP主联系方式查找
- 用户评价收集（装机/服务类博主）
- 浏览器安装方案（当B站API直连失败时）

## 获取UP主信息

### 方法 A：B站搜索 API（推荐，无风控）
```bash
# 搜索UP主
curl -sL "https://search.bilibili.com/upuser?keyword=$(python3 -c 'import urllib.parse; print(urllib.parse.quote(\"排雷数码港\"))')" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```
从HTML中提取 `space.bilibili.com/<UID>`（正则匹配即可）。

### 方法 B：空间页HTML（绕过wbi风控）
B站API `api.bilibili.com/x/space/wbi/arc/search` 需要 wbi 签名且未登录状态下极易触发风控（code -352）。替代方案是直接爬取空间页HTML：
```bash
curl -sL "https://space.bilibili.com/<UID>" -H "User-Agent: Mozilla/5.0"
```
从 `<meta name=\"description\">` 的 `content` 中提取签名/联系方式。例如：
```
<meta name=\"description\" content=\"...装机or投稿请关注微信公众号：排雷数码港...注意马甲虫！切勿上当受骗！\" />
```

### 方法 C：B站综合搜索 API（看视频而非UP主）
```bash
curl -s "https://api.bilibili.com/x/web-interface/search/all/v2?keyword=排雷数码港" -H "User-Agent: Mozilla/5.0"
```
返回包含视频、UP主等分类结果的JSON。但UP主搜索块（upuser）可能为空——B站搜索API对未登录用户有限制。

### 2026-05-31更新：B站API风控加剧 & 浏览器安装方案

**问题描述：** 从Docker容器（直连公网IP，无代理）调用B站API，包括：
- `api.bilibili.com/x/space/acc/info?mid=<UID>` → 返回 `-799` （请求过于频繁）
- `api.bilibili.com/x/space/wbi/arc/search` → 返回 `-403` （访问权限不足）
- 上述curl方案即使使用完整User-Agent也频繁失败

**根本原因：** B站对未登录的Docker/VPS出口IP实施了更严格的频率限制和风控策略。单一IP在无登录态下几乎不可能完成批量数据采集。

**推荐方案：安装Chromium无头浏览器进行页面抓取**

当API全部失效时，安装Chromium做真实的页面渲染 + 内容提取：

```bash
# 1. 确认网络环境：代理是否已死？直连是否可用？
curl -sI --max-time 5 "https://www.baidu.com"  # 应返回200
curl -sI --max-time 5 "https://space.bilibili.com/487605090"  # 确认B站可达

# 2. 清除无效代理（关键步骤！否则apt会尝试连接挂掉的代理）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# 3. 更新apt并安装Chromium
apt-get update -qq
apt-get install -y chromium chromium-headless-shell
# 安装包约200MB，首次下载可能超时，重试1-2次即可
# 如果官方源慢，可换国内镜像：
# sed -i 's|deb.debian.org|mirrors.ustc.edu.cn|g' /etc/apt/sources.list.d/debian.sources

# 4. 验证安装
chromium --version || chromium-headless-shell --version

# 5. 设置NO_PROXY避免走挂掉的代理
export NO_PROXY=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8
```

**Chromium安装后的B站抓取策略：**
- 使用 `puppeteer` / `playwright` / `selenium` 进行真实浏览器渲染（执行JS，等待API响应）
- 或直接使用 `chromium-headless-shell --dump-dom <URL>` 获取DOM纯文本
- **局限：** `--dump-dom` 对B站空间页（SPA）**无效** — 页面是Vue渲染的，dump-dom输出全是CSS/JS框架代码，不含视频数据或UP主简介。只有 `<meta name=\"description\">` 标签是服务端渲染的，但内容有限（仅150字）
- 对B站这种JS重渲染网站，使用 `--dump-dom` 功能有限，需要真实的 `Playwright`/`Puppeteer` 执行JS环境
- **更实用的替代方案**：使用 `/x/web-interface/view?bvid=` 和 `/x/web-interface/search/type` 这两个接口，配合curl调用，比整个浏览器方案快10倍且更可靠

**补充：Docker环境诊断清单**（当代理/网络出问题时）

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 检查代理是否存活 | `curl -s --max-time 3 http://172.17.0.1:7890` | 连接拒绝=代理死了 |
| 检查直连外网 | `curl -s --noproxy '*' https://httpbin.org/ip` | 返回自己IP |
| 检查apt源 | `curl -sI http://deb.debian.org/debian/dists/trixie/Release` | HTTP 200 |
| 检查DNS | `nslookup bilibili.com` 或 `dig` | 正常解析 |
| 检查系统 | `cat /etc/os-release` | 确认OS版本 |
| 检查已装工具 | `which chromium node python3 curl` | 确认可用工具 |

## 视频详情API：提取UP主收费/联系方式（2026-05-31新增）

**关键发现：** 当需要查UP主的具体收费信息时，查他的**视频简介**比搜搜索引擎更直接。B站视频详情API `/x/web-interface/view?bvid=<BVID>` 在未登录状态下可用（返回code=0），可以提取视频标题、简介(desc)、播放量、UP主信息。

```bash
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=BV1Sz91YHEpi" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Referer: https://www.bilibili.com"
```

返回JSON中关键字段：
- `data.title` — 视频标题
- `data.desc` — 视频简介（通常包含收费标准、联系方式、公众号信息）
- `data.owner.name` — UP主名
- `data.stat.view` — 播放量

**收费信息提取策略：**

当用户问"XX博主怎么收费"时，按以下顺序查：

1. **搜他的视频** — 用 `/x/web-interface/search/type?search_type=video&keyword=关键词` 搜"UP主名 装机/报价/价格"
2. **取高播放量视频的BV号** — 播放量高的通常是配置推荐类视频
3. **查每个视频的简介** — 调用 `/x/web-interface/view?bvid=...` 提取 desc 字段
4. **关键词提取** — 在简介中搜：`免费`、`收费`、`手工费`、`装机+`、`VX`、`公众号`、`微信`
5. **交叉验证** — 多个视频简介互相印证（有的视频只写公众号引流，有的会写具体费用）

**案例：排雷数码港收费分析**
从视频《【2274元】终极魔改神机》简介中提取到：
```
装机+置换+回收 关注【VX公众号：排雷数码港】
可免费帮忙写配置哦~
```
→ 结论：写配置免费，装机手工费没明标，需加微信询价。

**重要工具选择：requests vs curl**

B站API对Python的 `requests` / `urllib` 库的风控比 `curl` 更严格。实测：
- `curl` 调用 `/x/web-interface/view?bvid=...` → 正常工作，返回 code=0
- Python `requests.get()` 调用同一接口 → 返回 `412 Precondition Failed`（CDN风控）
- Python `urllib.request.urlopen()` → 同样返回 `412 Precondition Failed`
- **即使经过chromium --headless代理也一样** — 412是CDN层拦截，不是UA问题

**原因：** B站的CDN（可能是Cloudflare或自研）对Python库的TLS指纹和默认User-Agent更敏感。
**解决方案：** 始终使用 `curl` 命令调用B站API，通过 `subprocess` 或 `os.system` 调用curl，
或者用 `execute_code` 中的 `from hermes_tools import terminal; terminal("curl -s ...")` 模式。

```bash
# 推荐：用curl替代requests
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=BVxxx" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Referer: https://www.bilibili.com" | python3 -c "
import sys, json
data = json.loads(sys.stdin.read())
if data['code'] == 0:
    v = data['data']
    print(v['title'])
    print(v.get('desc','')[:200])
"
```

**注意事项：**
- 视频简介中 BVID 可以通过搜索API批量获取，再逐个调view接口（每个约0.3s）
- B站有频率限制，建议 2-3个BV/秒
- `/x/web-interface/view` 比 `/x/space/wbi/arc/search` 稳定得多，几乎不会被风控
- 简介里的HTML标签（如`<em>`）需要用 `re.sub(r'<[^>]+>', '', desc)` 清除
- Python requests库对B站API不可靠——遇到412时改用curl

---

## Playwright绕过B站SPA限制（2026-05-31更新）

当B站API全部失效（412/403风控）或者需要渲染SPA页面时，Playwright + Chromium 方案可以成功绕过。

### 适用场景

| 场景 | curl API方案 | Playwright方案 |
|------|------------|---------------|
| 搜UP主视频列表 | ✅ `search/type?search_type=video` 可用 | 不需要 |
| 单视频简介提取 | ✅ `view?bvid=` 可用 | 不需要 |
| 搜索页完整列表 | ✅ 可用 | ✅ 也能做 |
| **空间页个人简介** | ❌ meta description仅150字 | **✅ 可渲染SPA获取完整内容** |
| **UP主动态/置顶** | ❌ 需要登录 | **✅ Playwright可加载但受限** |
| **登录后内容** | ❌ 未登录 | **⚠️ 未登录状态下内容受限** |

### Playwright启动配置（关键）

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 重点：--ignore-certificate-errors 跳过证书错误
    #        --no-sandbox 用于Docker环境
    browser = p.chromium.launch(
        headless=True,
        args=['--ignore-certificate-errors', '--no-sandbox']
    )
    page = browser.new_page(ignore_https_errors=True)
    
    page.goto('目标URL', wait_until='domcontentloaded')
    page.wait_for_timeout(3000)  # 等待JS渲染完成
    
    # 提取内容
    text = page.inner_text('body')
    
    # 或提取元素
    links = page.query_selector_all('a')
    for link in links:
        href = link.get_attribute('href') or ''
        if '/video/BV' in href:
            bv = href.split('/video/')[1].split('?')[0].split('/')[0]
```

### Playwright提取B站搜索页视频列表

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    page = browser.new_page()
    
    page.goto('https://search.bilibili.com/all?keyword=%E6%8E%92%E9%9B%B7%E6%95%B0%E7%A0%81%E6%B8%AF&order=pubdate',
              wait_until='domcontentloaded')
    page.wait_for_timeout(3000)
    
    # 提取所有视频链接的BV号
    links = page.query_selector_all('a')
    for link in links:
        href = link.get_attribute('href') or ''
        if '/video/BV' in href:
            bv = href.split('/video/')[1].split('?')[0].split('/')[0]
            title = link.get_attribute('title') or link.inner_text()[:40]
            print(f'BV: {bv}  {title}')
    
    browser.close()
```

### 关于B站未登录限制

即使使用Playwright渲染，未登录状态下B站空间页和视频页面依然会显示登录弹窗。具体限制：
- **空间页**：显示"扫描二维码登录"覆盖层，看不到UP主的个人简介/签名/视频列表
- **视频页**：显示"登录后你可以：免费看高清视频..."，但简介文本（desc）依然可见
- **搜索页**：完全可用，无登录限制，能获取完整视频列表和标题

### 代理环境变量传递问题（关键pitfall）

Playwright在Docker中运行时不继承shell的 `export` 环境变量（在Python script内部的`os.environ['http_proxy']` 设置也可能失效）。正确的做法：

**方案A：在终端export后再调用python（可靠）**
```bash
export http_proxy=http://192.168.1.88:7890
export https_proxy=http://192.168.1.88:7890

python3 << 'PYEOF'
from playwright.sync_api import sync_playwright
# ... playwright代码
PYEOF
```

**方案B：在playwright context中设置代理（更可靠）**
```python
context = browser.new_context(
    proxy={'server': 'http://192.168.1.88:7890'}
)
page = context.new_page()
```

**方案C：在launch中用env参数传递环境变量**
```python
browser = p.chromium.launch(
    headless=True,
    env={'http_proxy': 'http://192.168.1.88:7890',
         'https_proxy': 'http://192.168.1.88:7890'}
)
```

### Playwright可用性验证

安装后验证：
```python
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
b = p.chromium.launch(headless=True, args=['--no-sandbox'])
page = b.new_page()
page.goto('https://httpbin.org/ip')
print(page.title())  # 应显示页面标题
print(page.inner_text('body'))  # 应显示IP信息
b.close()
p.stop()
```

### 常见错误及解决

| 错误 | 原因 | 解决 |
|------|------|------|
| `net::ERR_CERT_DATE_INVALID` | 目标网站证书过期 | `launch(args=['--ignore-certificate-errors'])` + `new_page(ignore_https_errors=True)` |
| `Navigation to "..." interrupted by another navigation to "chrome-error://..."` | 网络不可达/被墙 | 检查代理配置和网络连通性 |
| `Timeout 15000ms exceeded` | 页面加载超时 | 增加timeout参数，或检查代理连通性 |
| `playwright install`下载慢 | 网速慢 | `playwright install chromium` 只装Chromium（比装所有浏览器快） |

---

## B站搜索API直连方案（2026-05-31新增）

**关键发现：** 虽然 `/x/space/wbi/arc/search`（空间页视频列表）和 `/x/space/acc/info`（用户信息）需要wbi签名且极易触发风控（-403 / -799），但 **`/x/web-interface/search/type`（综合搜索）可以在未登录状态下正常使用**！

```bash
# 搜索UP主相关视频（无需wbi签名，未登录可用）
curl -s "https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=$(python3 -c 'import urllib.parse; print(urllib.parse.quote(\"排雷数码港\"))')&page=1" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Referer: https://search.bilibili.com"
```

返回的JSON结构（code=0时成功）：
```json
{
  "code": 0,
  "data": {
    "result": [
      {"title": "...", "play": 1000, "comment": 50, "bvid": "BV1xxx", "author": "排雷数码港"}
    ]
  }
}
```

**参数说明：**
- `search_type=video` — 搜视频；也可用 `search_type=bili_user` 搜UP主
- `keyword` — URL编码后的关键词
- `page=1` — 分页
- **关键Header**：必须有 `User-Agent`（移动端/桌面端均可）和 `Referer: https://search.bilibili.com`

**返回字段提取（Python）：**
```python
import sys, json, re
data = json.loads(sys.stdin.read())
if data.get('code') == 0:
    for v in data['data']['result']:
        title = re.sub(r'<[^>]+>', '', v['title'])  # 搜索结果标题带<em>标签
        print(f"{title} | {v['play']}播放 | BV:{v['bvid']} | 作者:{v.get('author','')}")
```

**用途场景：**
- 查UP主最近发布什么内容（看视频标题就知道他在做什么业务）
- 找客户反馈视频（搜索"感谢 XXX 装机"）
- 查硬件报价视频（搜索"XXX 价格"或"XXX 报价"）
- 查配置推荐视频（搜索"XXX 配置 推荐"）

**局限性：**
- 不返回用户个人简介/联系方式——那需要 `/x/space/acc/info` API
- 播放量和评论数只是基本统计，不返回评论区内容
- `search_type=bili_user` 可能因风控返回空结果（建议用 `search_type=video` 再筛选author字段）
- **重要**：这个接口对Python `requests` 库不可靠（返回412），必须用 `curl` 调用

## 联系渠道识别
B站UP主常见的公开联系方式：
| 渠道 | 位置 | 搜索技巧 |
|------|------|----------|
| 微信公众号 | 个人签名/description | grep "公众号\|微信" |
| 商务邮箱 | 签名/置顶动态 | grep "@\|邮箱\|mail" |
| QQ群 | 签名/视频简介 | grep "QQ\|群" |

## 消费者评价收集

### 受限网络环境下的搜索策略（Google/Bing/百度不可用时的替代方案）

| 搜索引擎 | 可用性 | 说明 |
|----------|--------|------|
| **搜狗搜索** | ✅ 可用 | 能返回B站、抖音链接和相关结果 |
| Google | ❌ 被墙 | Docker容器内无法直连 |
| Bing | ❌ 可能被墙 | 返回空页面 |
| 百度 | ❌ 可能被重定向 | 容器内网络受限 |

### 评价搜索查询策略

```bash
# 搜狗搜索评价（最可靠的搜索引擎手段）
curl -sL "https://www.sogou.com/web?query=%22UP%E4%B8%BB%E5%90%8D%22+%E8%A3%85%E6%9C%BA+%E8%AF%84%E4%BB%B7" -H "User-Agent: Mozilla/5.0"
```

推荐关键词组合（按优先级）：
```
1. "UP主名" + 装机 + 评价
2. "UP主名" + 靠谱/翻车/坑
3. "UP主名" + 感谢 + 装机          （找客户晒单反馈）
4. "UP主名" + 抖音                 （抖音用户评价）
5. "UP主名" + 图脱                （闲鱼/图吧/贴吧讨论）
```

### 评价判断框架

| 信号 | 正面 | 负面 |
|------|------|------|
| B站官方签名 | 有"注意马甲虫"说明UP主被假冒过，说明有一定名气 | — |
| 客户晒单 | 搜到"感谢XX帮我装机的机器"类内容 | 搜到"被骗""翻车""垃圾"类内容 |
| 主动送主机 | 在做活动回馈粉丝 | — |
| 抖音评价 | 正面评论多 | 负面评论多 |
| 防假冒提示 | UP主自己提醒防骗 → 有信誉要维护 | — |

### 重要提示
- **B站的"注意马甲虫"警告是正面信号**：说明UP主有一定知名度，骗子开始假冒他
- **搜狗搜索结果中提取关键词频率**：用 `re.findall(r'(差评|好评|坑|靠谱|翻车|骗|推荐|垃圾|良心|不错|踩雷)', html)` 统计正负面词频
- **无法获取B站评论区时的折中方案**：搜狗搜索会将B站视频标题和抖音内容展现在搜索结果中，通过这些摘要片段可以拼凑出大致口碑
