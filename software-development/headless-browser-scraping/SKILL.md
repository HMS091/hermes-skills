---
name: headless-browser-scraping
description: "Scrape data hidden in JS popovers with headless Playwright."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [scraping, playwright, browser, long-running-jobs]
    related_skills: [scrapling, web-research, blocked-page-recovery]
---

# 无头浏览器批量抓取（JS 页面里藏的数据）

## When to Use（何时用）
- 目标数据不在任何 API / HTML 源码里，只在点开/悬浮后才出现的浮层、模态框、tooltip 里。
- 标的数量上百，单次运行要几小时，中间不能因为一个标的失败就整体卡死。
- 用户给的是「路径/坐标/选择器」级别的提示词（常来自另一台机器的猜测），需要照着实现但要自己验证。
- 同一站点的**静态资产**（图标、头像、图片）要批量按 id 下载并校验真伪——这类不需要 Playwright，直接用 HTTP 循环跑第 11 节。

`web-research` / `blocked-page-recovery` 管「打不开怎么办」，`scrapling` 管批量静态抓取；本技能管**必须跑真浏览器 + 要断点续跑**的那一类。

## 0. 先探测，再写正式脚本
不要在没验证的情况下直接写 400 个标的的生产脚本——错的选择器会浪费几小时。顺序固定：
1. 单标的 probe：打开页面 → 打印候选元素的 `textContent` + `getBoundingClientRect()`（找标题、图标）→ 点击 → `document.body.innerText` 前后 diff → 截图用视觉确认浮层真的出现了。
2. 浮层出现后再抓它的 `outerHTML`，从结构里找**语义稳定的选择器**（`div.modal`、`[style*="pre-wrap"]`），不要靠 `innerText.split('\n')` 猜。
3. 用 2~4 个「已知异常样本」（无简介的、名字和 API id 不一致的、spot 而非 perp 的）验证 null 路径不会误判，再放全量。

## 1. 环境：复用已装 Chromium + `playwright-core`
先找现成浏览器，别下载整包：
```bash
find / -maxdepth 6 -name chrome -type f 2>/dev/null | head
# 常见：/opt/data/scrapling-browsers/chromium-*/chrome-linux64/chrome、/opt/hermes/tools/chromium-*/
```
装最小驱动（不下载浏览器，单包、几十秒）：
```bash
cd <脚本目录> && npm init -y && npm i playwright-core
# 使用：chromium.launch({ executablePath: <上面找到的 chrome>, headless: true,
#   args: ['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'] })
```
- `headless: true` 足够——浮层靠点击触发，不靠真实鼠标轨迹。
- `--disable-dev-shm-usage` 在容器里必加（/dev/shm 常只有 64MB）。
- 需要 locale/时区固定时在 `newContext({ locale:'en-US', timezoneId:'UTC' })` 上设，比改系统环境稳。

## 2. `TMPDIR` 必须是可写目录（最常见的「Target crashed」）
Chromium 在 `TMPDIR` 里建共享内存文件；Hermes 的 scratch 目录常对子进程不可写，页面会直接 `Target crashed` / `Creating shared memory ... failed: Permission denied`。
```bash
export TMPDIR=/tmp   # 启动脚本第一行就 export，别依赖继承
```
症状对照：`chrome --dump-dom` 能跑但 Playwright `evaluate` 崩、或日志刷 `platform_shared_memory_region_posix` —— 先换 TMPDIR，不要怀疑选择器。

## 3. 定位并点开隐藏浮层
- **点真元素，别点算出来的坐标**：`img[src^="/coins/"]`、`[aria-label]`、图标节点 → 取其 `getBoundingClientRect()` 中心点击，命中率远高于「标题 left-22」。把提示词里的坐标法留作**第二兜底**（两者都失败才算失败）。
- 标题/元素定位按「视口左上区域 + 叶子节点 + 文本正则」找，不写死坐标：外层有公告条时 y 会整体下移 30~40px。
- 点击后**轮询**等浮层（例如 7 × 700ms），不要一次 `waitForTimeout` 睡死；浮层可能在 300ms 或 3s 后出现。
- 每换一个标的先 `Escape` 关掉上一个浮层再 `goto`——残留模态会吞掉下一次点击。

## 4. 抽取文本：结构化选择器 > innerText 切行
浮层内通常有「标题行 + 描述块」。优先 `modal.querySelector('div[style*="pre-wrap"]').innerText` 拿原文（保留换行/空格）；兜底才 `innerText.split('\n').slice(1).join('\n')`。
- 用「文本长度区间 + 排除已知面板关键词（Order Book / Buy / 公告…）+ 宽度区间」筛候选模态框，再取其中最短的那个，能避开包住整页的布局容器。
- 只存原文，不翻译、不改写缩写（`ADS (NYSE: TSM), representing 5 common shares` 这类原样保留）。

## 5. 校验「抓到的确实是这个标的」
用**机器标识**校验，不要用展示名：图标 `src` 带 id（`/coins/xyz:SKHX.svg`）、或路由/URL 带 id；展示名会和 API id 不一致（`SKHX` 页面显示 `SKHYNIX-USDC`）。只按标题文本比对会把一整批资产误判成 null。

## 6. 断点续跑骨架（必须，不是加分项）
- 主状态：`{id: record}` 的 JSON。**每抓到一个立刻**写盘：写临时文件 + `rename` 原子替换。
- 同时 append-only 写一份 `.jsonl`；JSON 损坏时能重建。
- 启动先读已有文件，跳过已完成 key；`null` 也算已完成（否则失败项被无限重试，3 小时变 8 小时）。补抓用 `--retry-nulls` 单独一轮。
- 每标的 3 次尝试，仍失败记 `null` + `note`（写明失败原因），**绝不 raise 到主循环外**。
- 浏览器每 ~60 个标的重启一次（`close()` + 重新 launch），避免内存爬升和长跑后事件丢失。

## 7. 节奏与资源
- **单并发**：一个 page 顺序跑。多 tab 并行在长跑场景只会抢内存、更容易被风控。
- 标的间 sleep 1~2s（带随机）；页面 settle 9~12s（图表/悬浮处理器挂载）。
- 先算预算再开跑：`标的数 × 单标的秒数`，把小时数写进汇报。20~25s/标的、400+ 标的 ≈ 2.5~3 小时。

## 8. 后台启动 + 一句汇报（用户明确要求）
用户对长任务的期待是**一行结论**，不是过程直播：`脚本已后台启动，PID=xxx，预计 x 小时，约 HH:MM 完成`。开工前不要逐条播报探测细节。
```bash
# 守护脚本（node 崩了自动续跑，本身兼容断点续跑）
for i in 1 2 3 4 5 6; do node scraper.mjs >> run.log 2>&1; [ $? -eq 0 ] && break; sleep 15; done
```
启动用 `terminal(background=true, persist_on_release=true, notify=true)`；45 秒后回读日志确认已落 2~3 条再报 PID，不要「已启动」却其实立刻崩了。

## 9. 停止（用户说「停止所有任务」时）
- 先杀守护脚本，再杀子进程（node / chrome），最后确认无残留：`pgrep -a node`、`pgrep -c chrome`。僵尸 `[chrome] <defunct>` 不用管。
- **`pkill -f <pattern>` 会杀掉当前 shell 自己**——Hermes 的包壳命令行里就含这个 pattern，结果是命令以 SIGTERM(-15) 结束、后续清理没执行。正确做法：`pgrep -a node` 看 PID → 按 PID `kill`，且别在同一条命令里写会匹配到自己的字符串。
- 停止后如实说明：哪些已停、哪些从未创建（例如定时任务没建），不要含糊说「都停了」。

## 10. 产物约定
- 主文档（供下游直接消费）+ `progress.log`（每 100 条一行：完成/总数、成功、失败、时间）+ `DONE.txt`（总数、成功、失败、起止时间、失败清单）。
- 标的清单只走 API（枚举接口），不要爬列表页——虚拟滚动会漏项。
- 先过滤死标的（成交额 > 0），常能砍掉一半运行时间。

## 11. 静态资产下载（CDN 图标/图片）：200 不等于「有文件」
图标、头像这类按 id 取的文件端点**不需要浏览器**，直接 HTTP 循环下载即可；但 SPA 站点对不存在的路径会返回 **200 + 兜底 HTML 页**，状态码完全不可信。
- 校验三件套（缺一不可）：`content-type` 含目标类型（`svg`/`image`）、正文 magic bytes 对得上（`<svg`、`\x89PNG`）、字节数 > 阈值（占位/兜底页常见 100~500B 或整页 6~7KB）。只写 `if resp.ok` 会把几 KB 的 HTML 当图存进去。
- 先摸平台命名约定，再定 id：同一资产在列表页、API、图标路径里可能三个名字。图标常常是 `<BASE>_spot` 这种**后缀约定**（现货）或带 dex 前缀的裸名（`xyz:AVGO`，分隔符**不要** percent-encode）。
- 一个标的只试 1~2 个候选 id（约定名 + 去前缀/去后缀的变体）。生成几十个变体轮询是纯浪费：站点没有的图标怎么变都没有，实测一次 135 个占位只新增 38 个。
- 并发 5~8 + 每请求 15~20s 超时 + 2 次重试足够；超时/连接重置是常态，别当成「站点封了」。
- 占位文件的识别靠**文件名 glob**（`*.PLACEHOLDER.svg`），不要靠元数据字段——占位记录的 meta 往往连 `logoFile` 键都没有，按字段筛会得到 0 条而误判「已全部补齐」。
- 分层存档（`raw/` + 按类别分类的副本 + 翻译副本）同一个占位会被数好几遍：先按标的 id 去重再报「还有多少」。
- 覆盖前先 `tar czf backup/placeholders_before_$(date +%Y%m%d_%H%M%S).tar.gz <占位清单>`——原地覆盖不可逆。
- 用户说「覆盖同名占位文件」就是**原地覆盖、文件名不变**，不要顺手重命名成 `<stem>.svg`；把 `hasLogo:true / logoSource / logoBytes` 写进 meta，让消费方照 `logoFile` 读。
- 收尾必做两类回读校验：逐文件（magic bytes、尺寸、不含占位标记语如 `NO LOGO`、大小与记录一致、meta 与磁盘一致）+ 逐成员（`tar tzf` 数量、成员正文再验一遍 magic bytes，防占位混进交付包）。
- 交付汇报格式：新增成功数 / 仍失败数 + 失败名单前 20 + 失败原因分类 + 包路径 + 字节数 + 成员数 + md5。只说「已打包」不算完成。

## 陷阱速查
- **坐标必须在 settle 之后重读**：公告条/图表加载完，标题和图标会整体下移 30~40px；用 settle 前取的 rect 点击会整批点空（实测把 218 个有简介的标的误记为 null，多花了 1 轮重跑）。流程：取 rect → 等 9~12s → **再取一次 rect** → 点击。
- `TMPDIR` 指向不可写目录 → `Target crashed`，不是选择器问题。
- 死等 `waitForTimeout(15000)` 再抓 = 慢一倍；改成「轮询标题出现 → 再 settle 一小段」。
- 只按展示名校验标的 → 名称不一致的资产全变 null（用 id / 图标 src）。
- 失败重试没上限、或 null 不算完成 → 长跑永远跑不完。
- 只到最后写整份 JSON → 崩一次全丢；每标的原子写 + jsonl。
- 用 `pkill -f` 清理 → 自杀式 SIGTERM。
- 提示词里的「预期行为」（某标的一定抓不到）可能过时——照抓，抓到就是真实数据，记录下来而不是按预期写 null。
- 把 `200 OK` 当「下载成功」→ 存进去的是 SPA 兜底 HTML（常见 6831B）；必须验 content-type + magic bytes + 长度。
- 按元数据字段筛占位 → 占位记录没有 `logoFile` 键，筛出 0 条，误报「全部补齐」。

## 参考与模板
- `references/hyperliquid-blurbs.md` — Hyperliquid 的已验证细节：清单 API、简介浮层 DOM、路由、spot/perp 差异，以及 logo CDN（`/coins/<id>.svg`、`_spot` 约定、占位/失败签名）。
- `templates/resumable-scraper.mjs` — 断点续跑抓取器骨架（原子写、jsonl、重试、浏览器回收、progress/DONE）。
- `scripts/backfill_asset_icons.py` — 占位图标批量回填器（严格 SVG 校验、现货 `_spot` 候选、原地覆盖、dry-run 默认、结果 JSON）。
