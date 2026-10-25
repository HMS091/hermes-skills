---
name: web-research
description: 调研类任务（热点事件、产品/账号封禁、市场信息等）在搜索全被反爬/CAPTCHA 挡住时的可靠检索路径与 HTML 文本抽取流水线。用 r.jina.ai 渲染代理 + Bing 搜索 + 直接 curl 已知站点，按序降级；把踩过的坑（哪些引擎必出验证码、哪些能过）和抽取脚本固化下来。
---

# Web Research（反爬环境下的网页调研）

## 触发场景
任何需要上网查证的任务：热点事件、账号封禁/服务终止公告、产品信息、新闻时间线等。尤其是从中国网络环境发起（Google/Bing/DDG 对自动化访问反爬极严），以及目标站带 Cloudflare/Turnstile 防护时。

## 检索路径（按可靠性从高到低，命中即停）

### 1. 直接 curl 已知站点（首选，最快）
已知或猜出 URL 的目标站（博客、官方帮助页、电商公告），直接 curl + 文本抽取：
```bash
curl -s -m 40 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36" \
  -H "Accept-Language: zh-CN,zh;q=0.9" "https://目标站/..." | python scripts/html_to_text.py
```
- 中文站点**必须**带 `Accept-Language: zh-CN,zh;q=0.9`，否则部分站返回空/默认英文
- **政策/法规/官方数据类站点**：优先抓部委门户、省级政府门户、市县级自然资源局/住建局网站的**转载页**（带"索引号+文号+全文"，比新闻稿权威、比门户首屏好抓），并用**文号**（形如 `自然资发〔20XX〕XX号`、`建房规〔20XX〕X号`）当查询词，命中率远高于用正文表述去搜；政府站基本不反爬。政策类查证的完整分层取证流程见 `china-urban-policy-analysis`。
- **官方帮助中心/FAQ（Intercom、Zendesk 系）**：先拉 `sitemap.xml`，按关键词筛文章 URL（`zh-CN` + 支付/付款/法币/充值/订单），比站内搜索和浏览器快得多；正文就在原始 HTML 里（含一份转义 JSON），curl + 去标签即可。`web_extract` 对部分 help 子域会返回空或判为内网地址，不要据此认定页面读不了，换 curl。
- 国内个人博客（Typecho/WordPress 系）基本不反爬，直接抓即可
- 抓到的正文用 `grep`/`find` 定位关键词段落（如 `python -c` 里 `t.find('关键词')` 后切片）

### 2. r.jina.ai + Bing 搜索（搜索被挡时的主力路径）
搜索需求先用这个：免费渲染代理把 Bing 结果页转成干净 Markdown，标题+摘要+**解码后的真实 URL**一步到位：
```bash
curl -s -m 90 "https://r.jina.ai/https://www.bing.com/search?q=<url编码后的查询词>"
```
- 中文/英文查询都行；`site:xxx.com` 等运算符照常有效
- 返回的链接已解码（Bing 的 /ck/a 重定向 URL 会展开成真实地址），可直接二次抓取
- **注意限流**：匿名配额有限，连续请求会返回 401 "blocked due to bad IP reputation"。两次请求间 `sleep 5`+，不要并发轰炸

### 3. r.jina.ai 抓单页（X 帖子、被 Cloudflare 挡的页面）
```bash
curl -s -m 90 "https://r.jina.ai/https://x.com/用户名/status/帖子ID"
```
- X 的**单条 status 帖**可抓；`x.com/用户/article/...` 文章链接即使走 jina 也要登录，抓不到就改用 Bing 摘要
- 论坛/社区站（如 giffgaff community）即使走 jina 也过不了人机验证（返回 "solve a puzzle"），放弃，改用第 2 步的 Bing 摘要佐证

### 4. DuckDuckGo html 端点（仅应急）
`https://html.duckduckgo.com/html/?q=...` 第一次请求通常能过，但**同一分钟内第二次必出 anomaly/captcha 页**（LEN≈14k 的挑战页）。只用在别的路全挂时，且只发一条。

### 5. 浏览器（最后手段，预期会被挡）
浏览器访问 Bing/DDG/Sogou/360/Yandex 全部命中人机验证（Turnstile 图片拼图、SmartCaptcha 等）。**不要花时间解图片验证码**——点"获取新拼图"刷题属于死胡同，直接换路径。

## 已验证会被挡的路（别再试，浪费配额）
- Bing 直连 curl → 空结果（机器人检测）；Bing 浏览器 → Cloudflare 挑战
- 搜狗 sogou.com/web → antispider 跳转；360 so.com → 连接超时；Yandex → SmartCaptcha（复选框后还有图片码）
- 百度 curl 搜索 → 超时被终端拦截

## HTML 文本抽取
统一用 `scripts/html_to_text.py`（读 stdin，去 script/style 标签、去标签、unescape、压空白，输出纯文本）。见脚本注释。

## Pitfalls（本环境特有）
- **Windows git-bash 下 curl -o 写 /tmp 或 /c/... 路径不可靠**（wc 找不到、python 有时能找到，行为不一致）。一律用管道：`curl ... | python ...`，不要 `-o 文件` 再读
- jina 匿名限流 401 时：sleep 5~10 秒重试单条，或改走直接 curl
- 抓取目标站前先 `wc -c` 判断长度（0 字节=被挡/域名失效），别浪费 python 处理
- 调研结论要标注来源+日期（文章发布日期≠事件日期，事件时间线要单独梳理）
- **融资聚合站的同名混淆**：多个同名公司（如「Axiom」法律科技 vs 「Axiom Trade」交易终端）会被融资数据库合并成一家，轮次/金额/投资方全部串线。看到融资数据与已知轮次严重不符时，回 YC 公司页、Sacra 或官方公告核实体，并在报告里点名纠正——一字之差差一个数量级

## 参考文件
- `references/business-company-research.md` — 公司/产品尽调：多源三角验证、实体与融资口径，以及**资金流/支付通道核验**（用户问「他们支付宝/微信怎么入金的」时先看这一节）
- `references/software-app-vetting.md` — App/软件尽调全流程：GitHub→代码→商店三区元数据→二进制校验→报告结构
- `references/crypto-trading-terminal-research.md` — Web3 交易终端/DeFi 项目尽调：链上费用/收入数据源地图、口径陷阱（fees≠revenue、同名公司混淆）、YC 公司页用法、开发成本与合规基准
- `references/giffgaff-roaming-ban-2026.md` — 2026年7-8月 giffgaff 长期漫游封号事件完整调研（邮件原文、检测机制、退款/申诉窗口、无邮件应对、替代运营商、来源列表），用户问"我有卡怎么办"时直接引用
