# Chinese Web Search via Browser (中文网页浏览器搜索法)

When standard scraping tools (curl, Scrapling Fetcher) return 0 bytes on Chinese search engines and websites, the Hermes browser's accessibility tree bypasses most anti-bot systems.

## Search Engine: Bing China (cn.bing.com)

**URL format:**
```
https://cn.bing.com/search?q=<URL-encoded query>&setlang=zh-Hans
```

**Workflow:**
1. `browser_navigate(url)` — loads Bing China search results
2. `browser_snapshot(full=true)` or compact snapshot — the accessibility tree shows:
   - Search result titles as `<heading>` elements with `<link>`
   - URLs as `<StaticText>` elements
   - Descriptions as `<paragraph>` elements
3. `browser_scroll(direction='down')` — reveals more results below the fold

**What the snapshot reveals (structured):**
```
- link "zhihu.com" [ref=e37]  → source domain
- heading "2026上门按摩平台哪个靠谱？实测5家，说点真话" [level=2] → result title
  - link "..." [ref=e38] → clickable link
- paragraph → result description/snippet
```

**Confirmed working:** cn.bing.com Chinese search results render fully in accessibility tree. No anti-bot issues observed.

**Does NOT work via browser:** Baidu search (times out / returns captcha shell even in browser).

## Direct Site Access (网站直达)

For Chinese websites that block curl/Scrapling (0 bytes), browser navigation often works:

| Site Type | Examples | Browser Works? | Notes |
|-----------|----------|---------------|-------|
| O2O service platforms | bangjiubang.com, moyespa.com, dongjiaotn.com | ✅ Full content | Server-rendered HTML accessible |
| Blog/SPA platforms | 36kr.com, zhuanlan.zhihu.com | ✅ Partial | SPA shell renders, some content needs JS execution |
| Search engines | cn.bing.com | ✅ Full results | Best search option for Chinese queries |
| News portals | 163.com, sohu.com | ⚠️ Sometimes | 404 on some article URLs; refresh or try cached version |

## Parallel Research via delegate_task

When doing multi-faceted Chinese market research, dispatch subagents concurrently:

```
delegate_task(goal="search for market data X", context="...")
delegate_task(goal="search for competitor data Y", context="...")
```

Each subagent gets its own terminal session and browser instance — they work in parallel while you compile the report.

## Real-World Example: O2O Massage Platform Research

From 2026-07-09 session researching Chengdu 上门按摩 market:

1. **Browser to Bing China**: Searched "上门按摩平台 市场规模 2025 东郊到家 营收" on cn.bing.com
2. **Snapshot extraction**: Got 11 search results with titles, URLs, descriptions including:
   - Zhihu article comparing 5 platforms
   - bangjiubang.com (24 cities, 10k+ technicians, pricing data)
   - dongjiaotn.com (东郊到家, founded 2018)
   - moyespa.com (摩耶SPA, Chengdu service available)
   - 163.com buying guide
3. **Direct browser access**: Navigated to bangjiubang.com and dongjiaotn.com to extract pricing, coverage, and company info
4. **delegate_task**: Dispatched 2 subagents for parallel deep-dive searches while continuing to manually verify data

## Pitfalls

- **Browser is slow**: Takes 15-60s to navigate. For bulk data extraction, use browser only when Scrapling fails.
- **Browser may time out intermittently**: First navigation attempt sometimes fails (Chromium not ready). Retry once.
- **Chinese O2O sites are JSON-heavy SPAs**: E.g., dongjiaotn.com shows minimal content in snapshot. Click "关于我们" (About Us) links for usable text.
- **Not all Chinese anti-bot is bypassed**: Baidu search fails even in browser (returns captcha shell). Bing China is the reliable workaround.
