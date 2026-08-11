# 检索路径实测：百度优先 + Bing 诱饵结果 + 代理换出口 IP（2026-08）

本环境（Win 桌面 + v2rayN 代理）下 r.jina.ai 匿名搜索的实测结论。SKILL.md 第 2 节的理论版，这里记录实测细节。

## 核心结论
1. **中文查询首选 百度 + r.jina.ai**（问句式查询触发 AI 答案块，内容可直接引用）
2. **Bing + r.jina.ai 走美区出口 IP 时返回诱饵结果**（完全无关，如 Telugu 电影、NCAA 篮球）——先核对相关性，不相关立即换百度
3. r.jina.ai 匿名 401（bad IP reputation）时加 `-x http://127.0.0.1:10808` 换出口 IP 通常可解

## 实测命令
```bash
# 百度（问句式查询触发 AI 答案块）
curl -s -m 90 -x http://127.0.0.1:10808 "https://r.jina.ai/https://www.baidu.com/s?wd=<url编码后的问句式查询>"

# Bing（备用，可能出诱饵结果）
curl -s -m 90 -x http://127.0.0.1:10808 "https://r.jina.ai/https://www.bing.com/search?q=<url编码后的查询词>&mkt=zh-CN&setlang=zh-hans"
```

## 问句式查询触发百度 AI 答案块
- 生效示例："陪聊平台是怎么分成的 主播提成多少"、"聊天软件 每分钟收费 交友 元/分钟" → 返回"最佳答案: …"+"回答时间"块（百度知道/知乎摘要聚合），密度高、可直接引用
- 失效示例：纯关键词堆砌（如"陪聊软件 盈利模式 主播分成"）→ 只返回导航壳/相关搜索，无正文
- 百度资讯 tab（`rtt=1&tn=news`）经 jina 只返回热搜榜，别用

## 提取技巧（jina markdown → 正文切片）
```python
import sys, re
t = sys.stdin.read()
t = re.sub(r'\n{3,}', '\n\n', t)
# 定位 AI 答案块
for m in re.finditer(r'(最佳答案[:：]?|回答时间|答案[:：])', t):
    s = max(0, m.start()-150); print(t[s:m.start()+600]); print('----')
# 或按行业关键词切片（分成/营收/下架/净利…），不要全文输出
```

## 已验证会被挡的路径（别再试）
- Bing 直连 curl → 空结果；Bing 浏览器 → Cloudflare 挑战或重定向到空搜索页
- cn.bing.com 经 jina → JS 渲染空壳（只有页脚）
- 百度 curl 直连 → 超时；百度资讯 tab 经 jina → 热搜榜导航
- 搜狗/360/Yandex → antispider / SmartCaptcha

## 限流节奏
- jina 匿名配额：连续请求 401，两次请求间 `sleep 5`+（本会话用 sleep 5~8 稳定）
- 401 处理顺序：①加 `-x http://127.0.0.1:10808` 换出口 IP ②sleep 10 重试单条 ③换直接 curl 已知站点
- NAS（192.168.1.200）无 v2rayN 代理，只能靠 sleep 节奏，无换 IP 手段

## 浏览器兜底实测
- browser_navigate 到 cn.bing.com/search → 被重定向到 bing.com 首页空搜索框；输入查询回车 → 空页面
- browser_navigate 带中文 URL 参数 → utf-8 解码错误
- 结论：搜索类任务别指望浏览器，第 2 节 jina 路径更快
