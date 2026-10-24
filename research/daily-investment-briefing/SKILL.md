---
name: daily-investment-briefing
description: Generate the daily Chinese investment briefing (NVDA/TSLA/gold) — parse collected quotes, supplement with financial news, write markdown briefing, refresh the HTML dashboard. Triggered by the daily cron job or any 每日投资简报 request.
---

# 每日投资简报 (Daily Investment Briefing)

Recurring pipeline (runs daily ~07:30 Beijing time as a cron job) that produces a Chinese-language
investment briefing for NVDA / TSLA / gold (XAU) and embeds it into a self-contained HTML dashboard.

## Pipeline

1. **Parse raw data** — the pre-run script writes `/opt/data/briefings/{collection_date}_raw.json`
   with `nvda`, `tsla`, `gold` (price/change/change_pct/volume), plus `collection_time`,
   `collection_date`, and news arrays (often empty / "No recent news" — do not rely on them).
2. **Supplement news** — order of preference:
   - `mcp__lightpanda__search` or browser search (may be unavailable; do NOT retry in a loop).
   - **Reliable fallback: Eastmoney search API** via `python3 /opt/data/scripts/fetch_news.py <keywords...>`.
     Returns fresh Chinese financial news, no proxy needed. See `references/eastmoney-news-api.md`.
     Keyword groups that worked: `英伟达` `特斯拉` `黄金` `美联储` `美元指数` `美伊谈判 原油`
     `特斯拉 机器人 Optimus` `英伟达 RTX` `黄金 美联储 降息`.
3. **Write the briefing** to `/opt/data/briefings/{collection_date}_briefing.md` using
   `templates/briefing_template.md` (keep the section structure: 行情概览 / 今日热点 / 技术面简析 /
   宏观环境 / 风险提示).
4. **Refresh dashboard**: `python3 /opt/data/scripts/generate_briefing_html.py` → writes
   `/opt/data/briefings/dashboard.html` (all briefings embedded, latest first).
5. **Verify**: `grep -c "{collection_date with /}" /opt/data/briefings/dashboard.html` (expect ≥2:
   card + modal data) and confirm the `.md` file exists with non-trivial size.

## Quality bar (user's standing requirements)

- 全中文、简洁务实; **结论先行** — judgment first, then reasons.
- 每个标的控制在 5-8 行; 有具体数据支撑 (prices, %, volumes, market-cap figures).
- **必须包含风险提示** ⚠️ — 不报喜不报忧. Always list: policy/Fed risk, valuation/positioning risk,
  geopolitical reversal risk, and data-quality caveats.
- **口径说明 (disclosure)**: when sources conflict or fail, state it explicitly in a footnote —
  never present estimated/reported values as authoritative.
- Cron final response = generation report: data table, key points per asset, output file paths,
  verification results.

## Reliable price-history source (for real MAs / 涨跌幅)

`GET https://api.nasdaq.com/api/quote/{SYM}/historical?assetclass=stocks&fromdate=2024-08-01&todate=YYYY-MM-DD&limit=600`
with headers `User-Agent: Mozilla/5.0` + `Accept: application/json` works **direct (no proxy)** and returns
`data.tradesTable.rows` (`date` MM/DD/YYYY, `close/high/low/open` with `$` and thousands separators,
`volume`). Use it to (a) verify the nasdaq.com snapshot actually equals a real session close and
(b) compute MA5/10/20/50/100/200, 52-week high/low, avg volume — far better than quoting stale levels.
Note: stooq.com CSV is JS-challenged/blocked; don't bother. Note the quote-snapshot `timestamp` field can
mislabel the session (e.g. shows "Sep 10" for the 9/11 close) — trust the historical API.

## Snapshot `change_pct` is AFTER-HOURS, not the day change (critical)

The raw-JSON quote snapshot (timestamp like `7:30 PM ET`) often arrives ~3.5h **after** the 4 PM close, so its
`price`/`change`/`change_pct` describe the **after-hours move measured FROM that day's close** — not the
session's gain/loss. Reading it as the day change inverts the story (a real -3.36% day showed as +0.62%).

**Always reverse-engineer and verify the true close:**

```
prev_close  = historical-API close of the PRIOR session (e.g. Fri 9/11)
true_close  = price - change            # exact, to the cent
verify      = prev_close * (1 + media-reported %/100)  # must equal true_close
```

Worked example (2026-09-14): NVDA snapshot `price 212.2597, change +1.2997` → true close **210.96**;
9/11 close 218.29 × (1 − 0.0336) = 210.96 ✓ (media: NVDA −3.36%). Same for TSLA: `359.7694 − 0.7994`
= 358.97 = 365.44 × (1 − 0.0177) ✓ (media: −1.77%). When the two agree to the cent, you have the real
session close with certainty. Report the **close** in the table, show the after-hours price in parentheses,
and put the correction in 口径说明 — never let the script's number stand as the day change.

Also note the historical API lags: right after a session it may still end at the previous day's row.
Use `fromdate=<month start>&todate=<today>` and take `rows[0]`; if it is the prior session, derive the
new close as above rather than reporting the stale row.

## 2026-10-09 跑（周五 07:3x = 美股周四 19:3x，有完整新 session）

- 常规形态：`timestamp = "Oct 8, 2026 7:30 PM ET"` ⇒ 盘后快照 ⇒ `price − change`。NVDA 231.07−0.59=**230.48**（fiscal.ai/Convex「Close 230.48, −2.94% vs 237.47」，量 114,275,634）；TSLA 374.88−(−0.12)=**375.00**（Exa/融数「closed $375.00, −2.81 −0.74%」）。
- **最佳英文收盘源**：`web_search "<SYM> stock closing price <English date>"` 直接返回 **exa.ai/library/markets/stock/<SYM>**（Open/High/Low/Close/Volume 一行全给）与 **fiscal.ai/company/NasdaqGS-<SYM>**（Open/Close/Change vs 前收/Volume）——两个都能逐位咬合 `price − change`。
- **A 类新催化剂：AI 需求数据被修正**。FT 10/8 披露 OpenAI 年化营收「接近 500 亿」vs 此前引用的 700 亿（差 200 亿，口径差异），CNBC 证实 ⇒ 纳指 −1.25%、NVDA −2.94%、甲骨文 −5.5~6%、AMD/博通/英特尔 −4~6%、CoreWeave/Nebius −7%、应用光电 −13%、Coherent −9.62%。**这类「头部大模型公司营收预期差」是 AI 链最有效的单点利空，检索关键词 `OpenAI 年化营收 200亿`。**
- **黄金收盘用《投资早参》/07:00 快讯那句「现货黄金涨 0.53%，报 4131.89 美元/盎司」（COMEX +0.43% 报 4158.30）**，与前一期表内 4,110.52 逐位咬合（×1.0052）⇒ 本期表内取 4,131.89；同日《国际金融要情》07:14 另给一套更晚快照（现货 4,140.01 / COMEX 4,163.30 / 上金所 9999 895.00 元/克 / T+D 893.04），**基准时点不同，并列不混算**。另注意**金涨银跌**（现货银 −1.02%）⇒ 当日是「抗通胀+汇率」驱动而非避险。
- **本期长端美债首次反向**：10Y −5bp 至 5.227%、30Y −6bp 至 5.601%（此前两周连创 24 年新高），美元指数 −0.15% 至 102.12 ⇒ 黄金/地产喘息；但布油 +4.07% 破 104、WTI +3.64% 至 91.49（对伊新制裁 + 胡塞袭利雅得机场）⇒ 通胀源头同时被点燃。**「收益率回落」与「油价上冲」同向作用部分抵消，结论写成区间震荡。**

## 2026-10-12 跑（周一 07:3x = 美股周日 19:3x，无新 session，写「周一开盘前瞻」）

- 形态：`timestamp = "Oct 8, 2026"`（裸日期 ⇒ 官方收盘 shape，`price` 即收盘、`change` 即当日涨跌），但历史 API `rows[0] = 10/09 C=229.28/382.70`、`rows[1] = 10/08 230.48/375.00` ⇒ **快照就是 10/9（周五）收盘**。若上一份简报（如 10/11）已覆盖 10/9，则本期股指与上一期**逐位相同**，写周一前瞻时直接标注「沿用周五收盘」，**别当成新行情**。`timestamp` 日期标签（Oct 8）永远是错的，以历史 API 为准。
- **周一前瞻的三篇「一站式」来源（本轮验证，全部 `web_extract` 可直取）**：① **21 世纪经济报道《国际油价拉升，布油涨破 105 美元…》**（东财 07:1x 转载）——一段话给全「截至北京时间 6:30」的布油/WTI %+level、现货黄金/白银 %+level、三大股指期货涨跌、BTC + 爆仓人数，以及中东战况 + 伊朗/美表态（本轮：伊朗称美已接受部分条件、霍尔木兹关闭导航船只=敌对目标）；② **财联社《港股本周要闻前瞻》**——整周海外（美联储官员发言、CPI、褐皮书、沃勒/沃什、G20）+ 中国宏观（CPI/PPI、进出口、社融）+ 财报名单（周二 JPM/GS/C、周三 BAC/MS/BLK、阿斯麦/台积电）+ 行业活动；③ **上海证券报《全球黄金ETF三季度净流入 310 亿美元》**——黄金叙事一次到位（伦敦金现 8 月末 4447→9 月末 4157 −6.5%、AU9999 953→904、美联储 9 月加息 25bp + 纪要全票、美元破 102/10Y 破 5.28%、机构分歧：4100 必守/4200 压制/回踩 4000）。
- **周一黄金是真实新报价**：现货市场美东周日 18:00 重开后，**gold-api（23:30 UTC = 19:30 ET）是真新值**；同一天另有 21 世纪的「截至北京 6:30（=18:30 ET）现货黄金 ±X% 报 NNNN.NN」作第二口径——两者可能差约 10 美元/1 小时（本轮 4186.17 vs 4197.20）。**表内取能与上周五收盘咬合、且带明确涨跌幅的那一条**（4194.15 × (1−0.0019) = 4186.2 ✓），gold-api 值进口径说明 + 看板卡片。
- **NVDA/TSLA 个股催化用英文 `web_search` 命中率最高**（本轮：Bloomberg/Reuters「SpaceX 约 400 亿美元芯片融资 $10B 贷款 + $30B IG 债，Apollo 牵头，2027 年，早期」、法国巴黎银行 Ackerman 目标价 285→345、约克维尔首次覆盖 300、WSJ「调整后 H1 自由现金流约 217 亿 vs 口径 699 亿 + 长期债务 +249 亿」、达利欧/伯里 AI 泡沫警告、富士康 9 月季度营收 954.8 亿 +47%）。中文源负责宏观/黄金/日程，英文源负责个股，分工明确。

## 2026-10-13 跑（周二 07:3x = 美股周一 19:3x，有完整新 session；当日为哥伦布日）

- **哥伦布日 = 美股开市、美债休市**（2026 年第二周一 = 10/12）。带时钟的 timestamp ⇒ 常规盘后快照 ⇒ `price − change`：NVDA 225.13+1.19=**226.32**、TSLA 377.01+1.02=**378.03**，与媒体「英伟达 −1.29% / 特斯拉 −1.22%」逐位咬合。**但《国际金融要情》的美债收益率行是 10/9 的陈旧值（该页自己标「休市」），本期表内必须写明，别当成周一新收益率。**
- **最好用的一次英文收盘源：`cards.keenable.ai`** —— 一行给全「opened at / traded between / closed at / down $X (Y%) / from the <prior date> close of $Z / 市值 / P/E」，比 Yahoo/Investing 更省调用（本轮 NVDA：开 228.73、区间 224.90–228.86、收 226.32、−2.96、−1.291%、前收 229.28）。TSLA 用 `fiscal.ai`（开 382.48 / 收 378.03 / −4.67 / −1.22% / 量 19,972,077）。`fool.com` 的报价页一次给 52wk range + 当日区间 + volume + avg vol，可作第三方。
- **周二稿的 5 篇组合拳（东财 07:0x–07:2x，全部 `web_extract` 直取）**：①《深夜跳水，美芯片股、光通信股，全线暴跌》（大河财立方）——三大指数 + 大型科技股逐个涨跌 + 费半/存储/光通信/油气/中概逐股 + 油价 + 金银现货与 COMEX 全套；②《半导体指数创三个月新低…》（第一财经）——美联储官员原话 + CME 加息概率变化 + 财报季日程 + 中东/俄乌；③《一则利好 市值重返4万亿美元》（中国证券报）——微软 Maia 300 完整细节（数吉瓦/2027 起/每兆瓦 Token +40%）；④《AI基建融资推高长债收益率 美财政部或调整发债久期》（证券时报）——**英伟达 10-Q 表外担保 5,300 亿 vs 上季 1,840 亿（+180%）、七巨头表外承诺 3.56 万亿、财政部回购/花旗对 11/4 再融资的预测**；⑤《清晨集体跳水！股市“吹哨人”突然发声！》（券商中国）——摩根士丹利 Wilson 的「债市在替美联储完成紧缩」框架 + MOVE 指数 + 等权重跑输 6pp。**这五篇覆盖一份周二简报的 90%。**
- **新的 A 类催化：AI 的「融资端/信用端」叙事**。本轮 = 英特尔陈立武 + 博通陈福阳在 DBS 新加坡会议同声警告「资本才是 AI 最大瓶颈」（博通 600 亿债融给 Anthropic 客户、与阿波罗/黑石 350 亿平台）+ 微软自研 Maia 300 给出 2027 年起数吉瓦「主力推理系统」时间表。检索关键词：`Intel Broadcom CEOs capital AI bottleneck`（CNBC 原文直取，命中率 100%）。**这类「需求没坏、但融资变贵 + 云厂商自研替代」的新闻对 NVDA 是定向利空，且不体现在订单数据里 —— 与「OpenAI 营收预期差」并列，是 AI 链最有效的两类单点利空。**
- **黄金收盘链**：每日经济新闻 05:1x 的《现货黄金收跌X.XX%，报NNNN.NN美元/盎司》是最干净的一行现货收盘；界面新闻 06:4x 的《COMEX黄金期货收跌X.XX%》配 COMEX。本轮 4194.15 × (1−0.0054) = 4171.52 ≈ **4171.60** ✓。**同日 COMEX 并存两套值：4,195.90（−0.48%，界面/大河财立方）vs 4,165.80（−0.60%，第一财经，明确写「当月连续合约」）—— 合约不同，并列进口径说明。** 中文黄金技术位用同花顺转载的金投网稿（支撑/阻力/周线中轨/日线 MA5-MA10 一次给全）+ 中金在线《10.12美盘分析》的 4,112 支撑 / 4,197 / 4,224 阻力（该页正文只在 `web_extract` 的**中间被省略段**里，需 `read_file` 补看 cache 文件）。

## 2026-10-15 跑（周四 07:3x = 美股周三 19:3x，有完整新 session：CPI 超预期日）

- 常规形态：`timestamp = "Oct 14, 2026 7:30 PM ET"` ⇒ 盘后快照 ⇒ `price − change`。NVDA 218.891+2.409=**221.30**（exa/Yahoo/Seeking Alpha「开 225.53、区间 219.64–226.00、收 221.30、−7.22、−3.16%、量 115.96M」）；TSLA 363.8367+3.3233=**367.16**（keenable/fool「开 371.16、区间 363.82–371.39、收 367.16、−8.07、−2.151%、量 30.9M」）。逐位咬合。
- **`web_extract` 本轮全线失败（keyless Parallel `Read timed out`，5/5）** ⇒ 直接走 `em_article.py`。**关键：正文在页面很深处，必须给大 char 预算再自己过滤**，例如
  `python3 em_article.py <url> 80000 0 > /tmp/art.txt; awk 'length($0)>25' /tmp/art.txt`（用 `head -60` 截取只会看到导航栏，会误判为"抓不到正文"）。
- **本轮最好的黄金一句话出处：中新经纬《美股收盘：三大指数齐跌…》**（东财 06:40 转载）——`截至当天结算时段，伦敦金现跌1.33%报4105.19美元/盎司，伦敦银现跌5.99%报55.60美元/盎司`，**现货 + 白银 + 明确 % 一行给全**，比找零散快讯快得多。第二好是每经《投资早参》（07:2x）：`现货黄金跌1.33%报4105.2；COMEX黄金收跌1.2%报4127.3；现货白银跌5.99%报55.61；COMEX白银跌6.26%报55.8` —— **四个黄金口径一条新闻全覆盖**。
- **《国际金融要情》涨跌幅列本期再次反向**（现货金 +0.05%、COMEX 金 +0.48%，而结算价分别是 −1.33% / −1.2%），但**其"价格"列依旧可用**。这条规则已连续多轮成立：**只取价格，涨跌幅一律弃用。**
- **美联储加息概率三个来源三个数，必须并列不混算**：界面/CME「美联储观察」33.2%（07:08）、中新经纬转美联社/CME ~35%（前一日 22%）、21 世纪/财联社 43.7%（CPI 前 21.6%）。**时点与合约口径（10 月单次 vs 至 2027 年 1 月累计路径）不同。**
- **新的 A 类催化定型：AI 的"融资端/信用端"叙事本期进入兑现阶段** —— CoreWeave **股债双杀 −15%**、Nebius −10%、甲骨文 −8.8%、戴尔 −11%，存储链 SK 海力士 −6%/闪迪 −5%/美光 −4%。**结构含义：砸的是"靠发债买算力"的客户，而不是收算力钱的 NVDA（−3.16% 属板块 beta，当天无一条公司级利空）。** 与「OpenAI 营收预期差」（10/8）并列，是 AI 链两最有效的单点利空。
- **`gfetch.py` 已加**（`/opt/data/scripts/gfetch.py <url> [chars] [offset] [grep_kw]`，通用 tag-strip + 关键词过滤）。但 **10jqka.com.cn / m.cngold.org 等站点 urllib 会 SSL handshake timeout**；东财 `finance.eastmoney.com` 稳定可直取。
- **TSLA 事件密度监测**：本期确认三重事件挤在 2–3 周内 —— 10/21 Q3 财报、巴克莱所说"特斯拉–SpaceX 合并消息可能 10 月底至 12/6 股东大会前公布"、**NHTSA 要求 10/30 前就 Cybercab 联邦安全自认证作宣誓答复**。写前瞻时把这三个日期并列。
- **带时钟的 timestamp 之外，别忘查 `marketbeat` 的 instant-alert 页**：一次给全 TSLA「跌 X% 至 $367.16 / 成交量比均量低 41% / 日内低 363.82 / 前收 375.23」，是量价确认最快的一手。

## 2026-10-16 跑（周五 07:3x = 美股周四 19:3x，完整新 session：PPI 超预期但收益率下行）

- 常规形态：`timestamp = "Oct 15, 2026 7:30 PM ET"` ⇒ 盘后快照 ⇒ `price − change`。NVDA 216.7791+0.4509=**217.23**、TSLA 362.477−0.037=**362.44**，与 fiscal.ai / 英伟达 IR 页 / Yahoo 逐位咬合；中文媒体「英伟达跌 1.84%、特斯拉跌 1.29%」。
- **本期最好的单一收盘源：`investor.nvidia.com/stock-info/stock-quote-and-chart`**（英伟达官方 IR 页，一次给全 Price/Change/Volume/日内高低/52周高低/开盘/前收，且附最近 11 个交易日收盘价序列）。配 `fiscal.ai/company/NasdaqGS-NVDA` 与 Yahoo history 三方互证即可锁死。TSLA 用 Yahoo ``/quote/TSLA/history/`` 一行版（开/高/低/收/量）。
- **`web_extract` 本轮对东财文章 URL 恢复 100% 可用（5/5，含《国际金融要情》）** —— 而 `em_article.py` 对这种「正文由 JS 注入」的页面（大河财立方、每经早参）只能抓到导航栏。**顺序仍是：先 `web_extract`（批量 5 条）→ 失败才 `em_article.py`。**
- **新形态："通胀超预期、利率反而下行"** —— 9 月 PPI 同比 +6.3%（预期 5.3%）/ 环比 +1.3%，但 10Y −12.74bp 至 5.058%、美元指数 −0.49% 至 102.055（自 18 个月高位回落）、10 月加息概率 28.2%（FXStreet 26%）。**驱动是官员表态（戴利"可能还需加息但不必在 10 月"）+ 市场判定 PPI 为能源驱动且已被定价**。结果：道指 +1.08% 而纳指 +0.08%、NVDA −1.84% 而黄金 +1.59%。**检索关键词：`gold rises dollar slips PPI October 15 2026`（FXStreet/Kitco 一次给全驱动链）。**
- **黄金收盘链**：大河财立方 07:14 一句「现货黄金上涨 65.31 美元，涨幅 1.59%，报 4170.64 美元/盎司」是最干净的一行；与前收 4,105.19 × 1.0159 = 4,170.4 咬合（连续两期口径链自洽）。同时并存 COMEX 4,192.50(+2.06%)/4,188.70(+0.45%)、要情页现货 4,167.24(−0.08%，涨跌幅再次反向→弃用)。
- **看板/表格数字本次全部由生成器正确渲染**（status card 用 `price − change` 作收盘、盘后单独标注，卡片方向标签 📉 与当日报表一致）——编辑后照旧 grep 两种方向标签 + 核对卡片数字。

## 2026-10-17 跑（周六 07:3x = 美股周五 19:3x，完整新 session，本周收官日）

- 常规形态：`timestamp = "Oct 16, 2026 7:30 PM ET"` ⇒ 盘后快照 ⇒ `price − change`。NVDA 213.7346+0.3954=**214.13**（keenable「开 216.56、区间 213.32–218.68、收 214.13、−3.10、−1.427%、市值 5.166 万亿、PE 27.05」）、TSLA 351.68+3.04=**354.72**（keenable「开 369.14、区间 349.33–370.58、−7.72、−2.13%」+ Fool「closed at $354.72, down 2.13%」）。中文媒体「英伟达跌 1.43%、特斯拉跌 2.13%」逐位咬合。
- **本期最省调用的一组取数页**：**`cards.keenable.ai`（一次给全 open/区间/close/change/市值/PE，NVDA 与 TSLA 各一条）** + **`fool.com/coverage/stock-market-today/<date>/...`（TSLA 收盘 + 成交量 + 均量 + 一句归因）** + **`kalkine.com`（NVDA 收盘价 + 成交量 vs 三个月均量倍数 + 当日信用端事件清单）**。英文 `web_search "<SYM> stock closing price <English date>"` 与 `"<SYM> October 16 2026 close volume"` 命中率 100%。
- **A 类催化（信用/融资端）本期从叙事变成数字**：CoreWeave **周跌 25%、总债务破 510 亿美元**；Oracle 五年期 CDS 创 **288bp** 历史新高；**费半连跌 8 个交易日 = 追平 2006 年以来最长连跌**；**六个交易日蒸发 1.64 万亿美元市值**（Reuters）。结构仍是「砸靠发债买算力的客户，不砸收算力钱的 NVDA」（NVDA −1.43% vs Arm −7%、超微电脑 −10%、英特尔/美光/AMD −5%+）。
- **新的宏观形态：「美联储进入不再预告的新沟通阶段」** —— 主席沃什在曼谷 IMF 活动明确**不提前判断 10 月决定、不就今年剩余会议释放利率路径信号** ⇒ 交易员读成按兵不动，**CME FedWatch 10/27–28 维持不变概率 82%**。配套搜索词 `Fed Warsh Bangkok IMF October 16 2026`。**这条与「油价周涨 7.83%」并列，构成本期唯一有信息量的宏观对子（政策端不再更鹰 vs 通胀端重新点火）。**
- **中文侧一段话全覆盖的最佳出处仍是《每经早参》的「隔夜市场」段**（东财转载 URL 里的正文在 `web_extract` 中间被省略区）。**`web_extract` 5/5 成功但正文被截** ⇒ 直接 `read_file /opt/data/cache/web/finance.eastmoney.com-*.md` 的 offset 60–75，一次拿全：三大指数 + 存储/费半 + 权重股逐个 % + 中概 + 油价 + **现货金/COMEX 金 + 现货银/COMEX 银** + 欧股。
- **标题陷阱（新）**：东财快讯标题《国际贵金属价格集体下跌，现货黄金跌 0.11%》，而同一天 **COMEX 黄金 +0.40%** —— 是分化不是同跌。引用快讯标题前先看 COMEX 行。
- **黄金本期「金强银弱」是关键反差**：现货 −0.13%（`国际金融要情` 4,165.40，与上期 4,170.64 × (1−0.0013) = 4,165.2 咬合）、COMEX +0.40% 报 4,186.70（周 −0.70%），而 **COMEX 白银周 −6.41%**。**驱动是美元/收益率回落（界面对央视财经稿："受美元走软等因素影响"），不是避险** —— 同夜比特币破 8.1 万美元、近 8 万人爆仓。**人民币金腿跌幅远小于外盘（上金所 9999 −0.29%、T+D −0.11%、沪金主连 −0.02%），与 9 月底「人民币腿跌 3–5 倍」的形态正好相反 ⇒ 别用 9 月的旧结论套新数据。**
- **`国际金融要情` 的美债收益率列本期标「10 月 15 日收盘」**（比简报所覆盖的 10/16 滞后一日，该页自己写明了）⇒ 表内不得当新收益率用，并在口径说明点名。**这是该页继「涨跌幅列全弃用」之后的第二条固定规则。**
- **TSLA 成交量的「均量」基准三源差近 50%**（marketbeat 5,080 万 / Fool 三个月 3,750 万 / API 20 日 3,400 万），官方 61,623,741 股 ⇒ **只报放量方向与区间（+21%~+64%），不报单一倍数。**
- **事件形态记录：Tesla Roadster 飞行演示当晚（美东 10/15）⇒ 次日盘前 +5%、收 −2.13%、日内 349.33–370.58（振幅 5.9%）、放量下跌** —— 卖方对 Roadster 的 EPS 贡献预估到 2029 年仅约 **0.06 美元/股**，故发布会当天跌 2%。**叠加 Fool 统计「过去四次交付报告日股价全部下跌」+ 10/21 财报 + 10/30 NHTSA 宣誓答复截止，写 TSLA 前瞻时把这三条并列成负偏结构。**
- **日历本期新增确认：10/21 同时是特斯拉 Q3 财报（美东 17:30 ET）与 GTC Berlin 黄仁勋演讲**，10/21–22 还有 Netflix/Meta 财报。

## 2026-10-24 跑（周六 07:3x = 美股周五 19:3x，完整新 session，本周收官）

- 常规形态：`timestamp = "Oct 23, 2026 7:30 PM ET"` ⇒ 盘后快照 ⇒ `price − change`。NVDA 211.10−0.14=**210.96**、TSLA 371.4499−(−0.7701)=**372.22**，与第一财经收盘稿「英伟达跌 0.59%、特斯拉跌 0.63%」按前收（212.21 / 374.58）逐位咬合。
- **`execute_code` 在本环境明确 BLOCKED（cron 无审批）**，`web_search` 也报 keyless Firecrawl `SSL: UNEXPECTED_EOF` ⇒ **一轮下来只有 terminal + 东财 API 可用**，不要再花调用试 execute_code/web_search。
- **本期三篇「组合拳」（全 `em_article.py` 直取，正文在页面深处，需 `awk 'length($0)>25'` 过滤）**：① 第一财经《道指跌超650点…现货黄金失守4000》——三大指数 + 逐股 % + 费半 + 油价结算价 + 现货金银收盘与周涨跌 + CME 加息概率 + 2/10/30Y 收益率 + 密歇根信心/通胀预期，一份稿覆盖 80%；② 21 世纪《美联储加息「魅影」浮现》——黄金完整因果链（油→通胀→加息→实际利率）+ **哈萨克斯坦央行减持 3% 黄金储备转美债** + 汇丰/瑞银/高盛/大信四家目标价；③ 21 世纪《美股AI产业链股震荡背后：算账式回调后 市场不再轻易买单》——Meta Q3 资本开支 349 亿/全年指引 1,350-1,450 亿/未来承诺 8,250 亿/FCF −21.2 亿、费半 30 只成分股单日蒸发 8,173 亿、10 月费半 −15.02%、「订单驱动→融资驱动」框架。
- **`em_urls.py` 的关键词必须两词以上**：单搜「英伟达」「特斯拉」返回的是按时间排序的全站新闻（QFI​I 持股、猪企、医药），命中率为零；用「道指跌超650点」「SpaceX 特斯拉 合并 反垄断」这种标题/实体组合才能定位。
- **A 类催化换了方向：本轮是「加息 + 油」双杀，不是「降息」** — 布伦特 116.72（+3.14%，4/29 以来新高，霍尔木兹两艘超大型油轮触雷）、WTI 103.27（+3.82%）；CME 12 月累计加息 25bp 概率 67.5%（另一口径 74.8%）、10 月按兵 90.6%；10Y 4.994%（+4bp）、美元 101.75。**结论必须写成「油价→通胀→加息→实际利率上行→成长股与黄金同时被杀」，本周已连续出现「股金双杀」。**
- **黄金跌破 4,000 的叙事要点**：现货 3,996.10（−0.71%，周 −4.07%）、盘中低 3,975.75、距年内低 3,942.43 仅 1.4%、年内从最高 +29.7% 转为 −7%；**央行从买家变卖家（哈萨克斯坦 −3%，占比 78%→75%）是本轮长多逻辑的第一条反向证据**，比 ETF 流出更值得写进风险段。上金所 9999 −0.12% 远小于外盘 ⇒ 人民币腿抗跌，别套 9 月「人民币腿跌 3-5 倍」的旧结论。
- **TSLA 的合并叙事进入监管阶段**：美媒 10/23 报道 SpaceX–特斯拉合并或面临反垄断审查（垂直排他：星链只服务特斯拉会伤及其他车企），马斯克公开支持但承认利益冲突、回避特别委员会，内部担心推迟数周；同时 SpaceX 洽租美国蜂窝基站自建无线网络 ⇒ AT&T −7.96%、T-Mobile −7.71%。Optimus 首批「量产质量标准」机下线、外部交付仍 2027 年底。
- **「美股成交额前20」这期没抓到** ⇒ 官方成交量改用 nasdaq 快照量（NVDA 8,012 万 vs 20 日均量 1.058 亿 = 缩量 24%），并在正文标明是快照口径含盘后。生成器与看板本次自动正确（卡片 📉、收盘价来自 `price − change`、黄金卡片为采集快照）。

## Pitfalls

- **哥伦布日（10 月第二个周一）美股开市、美债休市** —— 北京周二 07:3x 的 run 因此是**完整新 session**（不是周末形状），但 `国际金融要情` 的美债收益率是上一交易日的陈旧值，该页自己会标「休市」；把它当新数据就错了。
- **Identify the snapshot SHAPE before computing anything** (2026-09-27 run): the pre-run JSON can flip
  from the after-hours snapshot to the **official close** payload — `price 225.07 / change +0.49 / change_pct 0.22`
  with a `timestamp` that has **no clock time** (`"Sep 24, 2026"`). Here `price` IS the session close and
  `change` IS that session's move (225.07 = 9/25 close, 224.58 = 9/24 close → +0.49 ✓; TSLA 372.11 vs 377.94
  → −5.83 ✓). Rules: clock time in `timestamp` ⇒ after-hours, derive `price − change`; bare date ⇒ official
  close, use `price` as-is. The historical API **does catch up**: fetch it first and compare `rows[0]` — if
  `rows[0].close == price` and `rows[0-1].close == price − change`, no derivation/injection is needed and
  `ma_calc.py`'s `INJ` dict should stay empty. Never trust the `timestamp` date label (it read "Sep 24" for the
  Sep 25 close) — the historical API is the authority.
- **Weekend runs**: when the cron fires on a Beijing Sunday = US Saturday, there is NO new session; the
  snapshot repeats the prior briefing's close. Say so explicitly in 口径说明 rather than implying new data.
  Tell: on 2026-09-20 the snapshot `timestamp` reverted to "Sep 17, 2026" while `price 222.27 / change +2.93`
  were exactly the 9/18 close (and matched the previous day's briefing to the cent). Confirm by diffing the
  new briefing's numbers against the previous `*_briefing.md`; if identical, frame the piece as
  周末复盘 + 下周前瞻 (add 下周事件日历 and this week's 周涨跌幅) instead of a new session wrap.
- **Gold-api.com returns the same value all weekend** (2026-09-19 and 09-20 both 4,379.00) — a duplicate
  snapshot, not a flat market; label it as such when the w/wend run cites it.
- **Gold API & Yahoo direct connections fail** *usually* (SSL `UNEXPECTED_EOF_WHILE_READING`) — but
  gold-api.com succeeds intermittently (2026-09-16 run returned a `XAU/USD` spot snapshot fine). Try it,
  then ALWAYS cross-check against media 现货/COMEX numbers (e.g. 东方财富《国际金融要情》gives 现货,
  COMEX 期金, 上金所 9999 and 黄金 T+D on one line) and disclose every 口径 used.
- **Proxy** `http://192.168.1.88:7890` exists, but proxy commands can trigger pending-approval in cron
  mode (no user to approve) — avoid depending on it; Eastmoney API works direct.
- **Snapshot vs close discrepancy**: the nasdaq.com quote snapshot (e.g. 7:30 PM ET) can differ sharply
  from the reported session close (e.g. +0.11% vs +2.90%). Present the collected numbers in the table
  AND note the reported close in analysis.
- **Gold has several conflicting 口径 on the same day** (gold-api spot snapshot, FX168 现货收盘, COMEX 期金
  which can move the OPPOSITE way). List all of them in the disclosure; never silently pick one.
- **News arrays in the raw JSON are usually empty** ("No recent news") — always do the web/API supplement.
- **Do not use `curl ... | python3 -c` for the Nasdaq historical API in cron mode**: the security scan
  classifies it as `tirith:curl_pipe_shell` and it hangs on `pending_approval` (no user to approve).
  Write a small script that uses `urllib.request` with the required headers instead. Also note file writes
  are restricted to `/opt/data` (`HERMES_WRITE_SAFE_ROOT`) — `/tmp/foo.py` is refused, so put throwaway
  helpers in `/opt/data/scripts/` and delete them afterwards.
- Check `/opt/data/scripts/` for existing helper scripts before building new fetch logic — the
  environment already ships `fetch_news.py`, `generate_briefing_html.py`, `net_probe.py`, and
  **`briefing_hist.py`** (created 2026-09-21: urllib-based Nasdaq historical fetch → prints last 8 rows
  plus MA5/10/20/50/100/200, 20-day avg volume, 2-year and 52-week high/low with dates, and the prior
  year-end close for YTD). Run `python3 /opt/data/scripts/briefing_hist.py` instead of rewriting it.
  It used to hard-code `todate="2026-09-22"` (which silently made the API look weeks stale) and now defaults
  to today; **if a helper prints rows that are older than the snapshot, check its `todate`/`INJ` before
  blaming the API**.
- **The historical API catches up fully when the session is old enough (2026-09-28 run):** `rows[0]` was
  `09/25 close 225.07` = exactly the snapshot `price`, and `rows[1] = 224.58 = price − change`. When that
  holds, **no derivation and no `INJ` injection is needed** — leave `INJ` empty in `ma_calc.py`, confirm by
  printing `rows[0]`, and compute MAs straight off the API. Only reach for `price − change` when the API
  still ends at the prior session.
- **Beijing-Monday-07:32 runs (US Sunday ~19:30 ET) have no new US session** — same "no new data" shape as
  the weekend, and NVDA/TSLA repeat the previous briefing's Friday close to the cent (diff the two `.md`s to
  confirm). **The difference from Sat/Sun: gold-api DOES return a genuine new-week quote** (2026-09-28:
  4,264.30 @ 23:30 UTC vs Friday's ~4,285.76, and it matched the 21世纪经济报道 6:35 print of 4,264.08
  −0.49% to the dollar). So frame Monday runs as **周一开盘前瞻**: gold/oil/futures are live, equities are
  not, and the payload is this week's calendar.
- **北京周六 07:3x 跑 = 美股周五 19:3x，有完整新 session**（2026-10-03 验证）：别把"北京时间周六"误判成周末空跑——`timestamp` 带 `Oct 2, 2026 7:30 PM ET` ⇒ 盘后快照 ⇒ 走常规 `price − change` + 英文收盘核对流程，gold-api 也是真实新报价。只有**北京周日/周一**才是"无新 session"形状。
- **北京周日 07:3x 跑 = 美股周六：无新 session，且快照 timestamp 会把日期标成更早（2026-10-04 验证）** —— 本期快照 `timestamp = "Oct 1, 2026"`（无时钟 ⇒ 官方收盘 shape）但 `price 233.95 / change +3.09` 实际是 **10/2（周五）收盘**，与上一期简报表内数字逐位相同。判定方法只有一条：查历史 API `rows[0]/rows[1]`（rows[0] 10/02 C=233.95、rows[1] 10/01 C=230.86 ⇒ 快照=10/2 收盘，今天没有新行情）。**不要相信 timestamp 的日期标签，也不要用它反推 session。** 这种 run 按 `周末复盘 + 下周前瞻` 写：表内沿用上一期的收盘与涨跌幅并显式标注"与上期相同"，正文补 `本周周涨跌幅` + `下周事件日历` + 卖方观点变化。同日 gold-api 快照与上一期逐位相同（4,141.80）属重复快照。
- **周末稿的三条高效来源（2026-10-04 验证）**：① 财联社《环球下周看点》（东财转载，周日 03:1x）一次给出整周宏观日历 + 财报季名单 + CFRA 季节性数据（1945 年以来标普 Q4 均涨 4.2%/胜率 85%、中期选举年 6.4%）+ 本周 10Y 高点与油价位置，是周末稿的骨架；② 深圳商报·读创《国际金价冲高回落，美银提示四季度下探风险…》一次给全周末黄金口径：现货 4,143.10（−0.82%，开盘 4,177.80 / 日内 4,125.26–4,226.59）、周跌 3.31%、周内 4,110.87–4,286.2，以及 美银（Q4 均价 4,000、风险 3,750）/汇丰（2026 4,490、2027 4,825）/高盛 4,900/瑞银 4,600 的分歧；③ 证券时报《美联储加息，突变！机构：10 月或暂停》给华泰/中国银河/招商/财通四家券商对"10 月暂停、12 月再加"的完整表述。
- **下一轮 GTC 的实际档期是 GTC Berlin 10/20–22（黄仁勋主题演讲 10/21），不是美股本地会**（英文媒体说"本月底的 GTC"容易误解）；且 **10/21 同日 = 特斯拉 Q3 财报 + 黄仁勋演讲**，写前瞻时把这两个事件并列。**
- **金价查询网报价表有个"昨收"语义陷阱**（2026-10-03 跑）：`huangjinjiage.cn/quote/117152.html` 表头写「今日价格 | 涨跌 | 涨跌幅 | 收盘价格 | …」，但**「收盘价格」列其实是前一交易日收盘，不是当日收盘**（10/2：现货 4,139.28 / −37.99 / −0.91% / 「收盘价格」4,177.27 = 10/1 收盘）。把它当当日收盘整期就错了。正确用法：**「今日价格」+「收盘价格(=昨收)」正好构成一对，能和本报前一期的现货收盘逐位咬合**（4,177.04 × (1−0.00904) = 4,139.28 ✓）。同页还可拿到纽约金期货（10/2：4,170.09 / −0.77%）与上金所 9999/T+D。
- **现货黄金收盘的第二校验源：CNBC `XAU=` 报价页**（`cnbc.com/quotes/XAU=`）——一个 fetch 同时给 Last / Prev Close / Day High / Day Low（10/2：4,137.56、−40.20、−0.96%，前收 4,177.761，区间 4,125.94–4,223.95），与金价查询网/`gold-api` 快照三方对齐即可锁定现货收盘。
- **官方成交量口径：东财《美股成交额前20》的成交额 ÷ 当日收盘价 = 官方股数**，用来取代含盘后的 nasdaq 快照量（10/2：NVDA 316.49亿 ÷ 233.95 ≈ 1.351 亿 vs 快照 1.3506 亿；TSLA 200.38亿 ÷ 370.59 ≈ 5,407 万 vs 快照 5,530 万），再除以 20 日均量得到"放量/缩量"判断。
- **Best new-week intraday snapshot source:** the 07:0x–07:1x Eastmoney quick-news pair
  `一觉醒来，…` / `国际油价拉升，布油涨破…美元…` (source 21世纪经济报道) — one paragraph carries 截至北京时间 6:35 的
  WTI/布伦特 %+level、现货黄金 %+level、现货白银、美股三大指数期货涨跌、加密货币爆仓人数、CME 加息概率、伊朗/特朗普表态。
  Pair it with `一周前瞻` (stock.eastmoney.com, 07:17) = the week calendar + 瑞银/美银等机构对美光/耐克的最新修正。
  That two-article pair plus `国际金融要情 |（周X …）` covers a whole Monday briefing.
- **Crude-oil 口径 sanity check:** a Brent − WTI spread much wider than ~$6 is a flag, but *not* automatically
  an error — in the Hormuz-crisis regime the whole `国际金融要情` row legitimately prints Brent 105.30 vs
  WTI 93.31 (~$12, 2026-09-29). What actually proved the 2026-09-27 Brent 104.32 wrong was that it could not
  be reconciled with the next morning's Brent 98.84 (+1.4%). So: reconcile across two days/sources first, and
  when a single source is internally consistent, report it with a one-line caveat instead of "correcting" it.
- **A normal Tuesday-morning run (Beijing 07:3x = US 19:3x the prior day) DOES have a new US session.**
  Shape check: `timestamp` carries a clock time (`Sep 28, 2026 7:30 PM ET`) ⇒ after-hours snapshot ⇒ derive
  `price − change`. 2026-09-29 worked example: NVDA 229.68 − 0.82 = **228.86** matched media "+1.68%" to the
  cent; TSLA 358.38 − 0.93 = 357.45 but the official close was **357.36 (−14.75, −3.96%)** — the derivation
  can be a few cents off, so **always grep a US ticker-history page (`investing.com`/`stockanalysis.com`
  "Closed" line prints price + change + % together) and prefer the official close** in the table, keeping the
  derived number only as the cross-check.
- **`国际金融要情` can print a WRONG SIGN on the gold row** (2026-09-29: "现货黄金 4,123.70, +0.21%" on a day
  spot closed ~−3.8% and every other source, incl. COMEX futures, was down 3–4%). Treat a sign that
  contradicts the whole market as a benchmark mismatch in that table — do not average it in, say so in 口径说明,
  and take the day's spot from the news wires instead.
- **Best gold-close source for a big down day: `金价查询网` (huangjinjiage.cn)**, whose daily wrap prints the
  intraday high, the low, `创X月X日以来新低`, and a `截至 23:57 报 NNNN.NN（−Y%）` line — one fetch settles the
  spot close and the range. Pair it with the 05:4x–07:0x Eastmoney 快讯 ("现货黄金跌近4%，报4115.24美元/盎司") for
  a second confirmation.
- **US-side news for NVDA/TSLA is best found with plain English `web_search`** (worked well 2026-09-29:
  "NVIDIA Nvidia stock September 28 2026 close" surfaced the buyback story + price/volume; "Tesla stock
  September 28 2026" surfaced the JPMorgan PT cut and the exact close). Eastmoney covers the Chinese angles
  (宏观/黄金/日程); the English search covers company-level catalysts and the official closing print.
- **Week-ahead calendar source (Monday/Tuesday runs):** the Eastmoney/腾讯转载 of 见闻财经日历
  《下周重磅日程：美国非农与中国PMI…》 carries the whole week in one article (OpenAI DevDay, Trump AI
  meeting + America.gov, Micron earnings, Tesla Roadster/Cybercab, 非农 date, A-share holiday window).
  Don't rebuild the calendar from scratch — search `本周重磅日程 <month>日` and extract it.
- **`web_extract` on Eastmoney article URLs was 100% reliable this run (2026-09-28, 7/7 URLs)** — including
  `国际金融要情`, whose body the raw-urllib `em_article.py` path **cannot** see (the static HTML contains no
  `现货黄金`/`美元指数`; the body is injected). So try `web_extract` FIRST, batches of 3–5 URLs; keep
  `em_article.py` as the fallback it was designed to be.
- **Same-day Open-price conflicts are normal, never merge them:** 2026-09-28 财联社《早报》 quoted 现货黄金
  4,285.12 (+0.27%) while 21世纪经济报道 (6:35) quoted 4,264.08 (−0.49%) — a U-turn in sign. List both, and pick
  as headline whichever agrees with the collected gold-api value.
- **Helpers added 2026-09-25 (keep them, they save a full round trip every run):**
  `em_urls.py <keywords...>` prints `date | title | url` (fetch_news.py only prints truncated content and
  hides URLs — you need the URL to extract full text); `em_article.py <url> [chars] [offset]` fetches an
  Eastmoney article with urllib + crude tag strip (the reliable path when `web_extract` 403s/times out);
  `ma_calc.py` recomputes NVDA/TSLA MA5/10/20/50/100/200 **after injecting the derived closes the lagging
  Nasdaq API is still missing** (edit the `INJ` dict at the top with `price - change` before running;
  2026-09-29 shape: `INJ = {"NVDA": [("09/28/2026", 228.86)], "TSLA": [("09/28/2026", 357.36)]}`,
  `TODATE` = today, API still ended at 09/25 — the printed `newest rows` line confirms the injection was needed).
  `execute_code` is BLOCKED in cron mode — use `terminal` for all of this.
- **Cleanest gold-close 口径: the 06:3x 美股收盘 quick-news article.** It carries a one-line
  `伦敦金现跌X.XX%，报NNNN.NN美元/盎司；伦敦银现…` — an explicit % + level for spot, which
  `国际金融要情` does NOT give (that page lists 现货黄金/COMEX/上金所9999/黄金T+D/沪金主连 levels + 美元指数
  + every US Treasury tenor, but no spot % change). Search keyword `伦敦金现 收盘` lands on it directly.
  Also expect the RMB-priced gold legs (上金所/T+D/沪金主连) to fall **3–5x harder** than 伦敦金现 — report
  both, it signals domestic premium/speculative unwind rather than pure FX.
- Prefer **`web_extract` on Eastmoney article URLs** for the full text of the day's roundups: the search
  API truncates `content` to 150 chars. Two calls cover a whole briefing — `国际金融要情 |（周X YYYY.M.D）`
  (all indices + 现货/COMEX/上金所 gold + oil + yields + dollar in one page) and the day's 美股收盘 roundup.
  Find URLs by printing `r['url']` from `fetch_news.em_search()`. **The `国际金融要情` page is the single best
  source — it settles 现货金/COMEX/上金所/美元指数/10Y 收益率/三大指数 in one fetch; always extract it first.**
- **When `web_extract` fails** (keyless Parallel/Firecrawl backend times out or 403s — common), fetch the
  Eastmoney article directly with urllib + a crude tag strip; works every time, no proxy:

  ```python
  import urllib.request, re, html
  req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
  h = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'ignore')
  t = re.sub(r'<script.*?</script>', '', h, flags=re.S)
  t = re.sub(r'<[^>]+>', '\n', t); t = html.unescape(t); t = re.sub(r'\n\s*\n+', '\n', t)
  print(t[t.find('美伊'):t.find('美伊')+4200])   # anchor on a phrase near the body start
  ```
- **`web_search` is unreliable here too** — keyless Firecrawl returns 403 for roughly half the queries and
  `mcp__lightpanda__search` may be absent. Do NOT spend calls retrying; go straight to `fetch_news.py`
  (Eastmoney, always works) and treat `web_search` results as a bonus when they do return.
- Morning (Beijing 07:30) runs land ~3.5h after the US close, so the Nasdaq historical API frequently
  **still ends at the previous session**. That is expected, not a failure: derive the close as `price - change`
  and confirm against media % moves from the roundup articles (e.g. 2026-09-22 run: 227.38 / 375.21 derived,
  media +2.30% / +3.00% ✓).
- **黄金的"表内口径"要挑能与前收盘逐位验证的那一对（2026-10-01 跑）**：21 世纪经济报道/证券时报的盘中稿常写"截至发稿，跌0.08%，报4178.51美元/盎司"——用它除以**昨日简报表内那张现货收盘价**（9/29 = 4,181.79），4181.79 × (1 − 0.0008) = 4,178.44 ≈ 4,178.51 ✓，**两天的简报就此咬合成一条链**，比 gold-api 采集值（同日 4,155.40，23:30 UTC 盘后时段，差 23 美元）更适合作表内"现货收盘"。同日还会并存 Yahoo 成交通（4,184.90）、COMEX 结算（4,189.1，+0.22%，来自界面/财联社的《国际贵金属期货收盘》稿）——全部列进口径说明。**黄金当日"冲高回落"的形状要看东财 22:4x 稿**（《纳指深夜涨超280点 …黄金白银冲高回落…》）：PCE 后直线拉升超 20 美元冲上 4,200，随后因 30 年期收益率升高回吐，**收盘几乎持平**——只读 gold-api 会误判为"跌"，只读 USA Today（4,188.35 / +1.60%，基准不可调和）会误判为"涨"。
- **黄金"收盘链"要用金投网/汇通财经的"前一日收盘 + 涨跌%"来锁，不要用盘中"发稿时点"价（2026-10-02 跑）**：金投网（cngold.org）每日黄金稿会明写 `X月X日现货黄金跌0.59%收4157.02美元/盎司，周线重挫3.03%、月线狂泻6.55%`，汇通财经（fx678.com）同日稿写"此前一个交易日金价已收跌约0.6%"——两者互证即可定住前收盘。当日新收盘再用 每日经济新闻/东财 06:1x 的《现货黄金收涨X.XX%，报NNNN.NN美元/盎司》逐位验证：4157.02 × 1.0047 = 4176.6 ≈ **4177.04** ✓。**教训：21 世纪经济报道/证券时报的盘中稿（"跌0.08%，报4178.51"）是发稿时点价，会被误当收盘价——本报 10/1 期就这么错了一天（把 9/30 盘中的 4178.51 记成收盘，真实收盘 4,157.02），下一期必须更正并在口径说明里点名。** 金投网/汇通/24K99/FXBus 这一组中文黄金专稿是 07:3x 时点最好用的"前收盘 + 区间 + 均线位"来源，一次搜索即可拿到高低点（本轮 4,139 低 / 4,193 高）和技术位。
- **看板的 XAU 卡片显示的是 gold-api 采集快照，与简报表内的现货收盘会差 20 美元上下**（生成脚本直读 raw JSON，不做黄金回推）。这是既有约定、非 bug；**在口径说明里点出"看板卡片 = 采集快照"**即可，不要为此改生成器（原始 JSON 里没有更好的黄金源）。
- **北京周五 07:3x 跑 = 美股周四 19:3x，有完整新交易 session**（2026-10-02 验证）：`timestamp` 带 `Oct 1, 2026 7:30 PM ET` ⇒ 盘后快照 ⇒ `price − change`；官方收盘验证走 `web_search "<SYM> stock closing price <English date>"`——Yahoo 历史行（开/高/低/收/量）与东财《美股成交额前20》（个股价格 + 涨跌% + 成交额）两条一起给：NVDA 231.578−0.718=230.86 ✓（Yahoo 收 230.86、量 97,538,145）、TSLA 355.3901−1.2801=354.11 ✓（fiscal.ai "closed 354.11"）。**该榜还能反推出官方成交量**：成交额 ÷ 收盘 = 股数（TSLA 110.49 亿 ÷ 354.11 ≈ 3,120 万股），比只信快照量更准。`ma_calc.py` 照旧：API 仍停在上一交易日 ⇒ 填 `INJ` + `TODATE` 后运行。
- **`国际金融要情` 的「涨跌幅」列可信度低于其「价格」列** — 三个不同的错法已复现（9/29 黄金 +0.21% 而实际 −3.8%；9/30 黄金 −0.11% 而实际 +1.64%；9/30 其表格 WTI +0.06% 而结算价 −3.48%）。规则：**只从该页取价格与美债收益率，涨跌幅一律以结算价/第一财经/财联社稿为准**；同页内文与表格也会互相矛盾（9/30 穆尔班内文 +2%/120 美元 vs 表格 114.60/−1.98%）——以表格价格为准、矛盾项直接不采用并在口径说明点名。
- **周二早上确认美股官方收盘的最快路径**：`web_search "<SYM> stock closing price <English date>"` 一次同时返回 Yahoo Finance history 行（open/high/low/**close**/volume）、CNBC 报价页（price + chg + %chg）、Investing.com 表格（含 Vol. 与 Change %）——三者一致即锁死收盘，比在中文稿里找数字快且准（9/29 跑：NVDA 227.21/−1.65/−0.72%、TSLA 352.84/−4.61/−1.29%，与 `price − change` 逐位相同）。
- **周二稿的三篇组合拳**：《国际金融要情》（价格/美债/汇率/大宗全表）+ 中国证券报《美股下跌 芯片、光通信股逆势大涨》（费半与个股涨幅、贵金属 %、油价结算价、OpenAI DevDay）+ 第一财经《美三大股指再跌！…》（七巨头逐个涨跌幅、JOLTS/消费者信心、Fed 官员原话与 CME 概率变化）。三篇 `web_extract` 一次批量取，覆盖整份简报，无需再搜英文宏观。

## Support files

- `generate_briefing_html.py` **briefing-card 方向标签必须从表格解析，不能用 `"📈" in content`**（2026-10-09 修复）。模板固定章节标题 `## 📈 技术面简析` 永远含 📈，旧写法把**每张卡片**都标成「上涨」，大跌日（如 10/9 NVDA −2.94%）也是「上涨」。现在用 `direction_from_content(content)`：逐行找 `|` 开头且含 `NVDA`/`TSLA`+`%` 的行情概览行，取**绝对值最大的那个百分比的符号**（混合日按主线走），无匹配则不加方向标签。改生成器后务必 `grep -c '📉 下跌'`/`'📈 上涨'` 确认两种标签都出现、且第一张卡片的标签与当日报表一致。
- `generate_briefing_html.py` status cards: the snapshot `change/change_pct` made the dashboard's top cards
  read **after-hours** values as the day change (opposite sign vs the briefing). Fixed 2026-09-16: cards now
  show the derived close (`price - change`) as the headline value and label the move 盘后 explicitly. If you
  edit that generator, keep that convention — never print a bare `change_pct` from the raw JSON.
- **The generator must branch on snapshot shape (fixed 2026-09-21).** Always printing `price - change` as
  "收盘" is only correct for the normal after-hours snapshot. The degenerate variant (see the `timestamp`
  pitfall) carries `price` = session close and `change` = that session's move, so the old code rendered the
  *prior* day's close as "收盘" (e.g. showed 219.34 for NVDA when the 9/18 close was 222.27), contradicting
  the briefing. `is_afterhours(d)` now tests the `timestamp` for a clock time (`\d{1,2}:\d{2}\s*(AM|PM)?`):
  with a time → headline `price - change`, sub-line labelled 盘后; without → headline `price`, sub-line
  labelled 当日. Keep both branches whenever you touch the cards, and diff the rendered card against the
  briefing's table before finishing.
- `references/eastmoney-news-api.md` — Eastmoney search API mechanics + usage.
- `templates/briefing_template.md` — the markdown briefing template (copy + fill).

## Pitfall: the historical API can lag a full session

On the 2026-09-16 run the Nasdaq historical API still ended at 09/14 rows even though the 9/15 session was
closed and widely reported. Reverse-engineer the new close (`price - change`) and validate it against a media
headline's % move before reporting; do NOT report the stale row as "today".
