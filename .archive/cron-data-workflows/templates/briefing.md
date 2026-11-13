# 📋 每日投资简报 — {collection_date}

📡 数据采集时间: {collection_time} (北京时间)

## 📊 三大标的行情概览

| 标的 | 现价 | 涨跌 | 涨跌幅 |
|------|------|------|--------|
| **NVDA 英伟达** | $xxx.xx | +x.xx | +x.xx% |
| **TSLA 特斯拉** | $xxx.xx | +x.xx | +x.xx% |
| **XAU 黄金** | $x,xxx/盎司 | +/-x.xx | +/-x.xx% |

> ⚠️ 数据来源说明：如有数据源异常请在此处说明修正情况。推荐附加52周区间：`NVDA 52周区间: $158-$236 | TSLA 52周区间: $293-$498 | 黄金52周区间: $3,263-$5,586`（来源：Yahoo Finance）

## 🔥 今日热点

### 🖥️ 英伟达 ({nvda_price})
1. **热点标题** — 简要分析（1-2句概括影响）
2. **热点标题** — 简要分析

### 🚗 特斯拉 ({tsla_price})
1. **热点标题** — 简要分析
2. **热点标题** — 简要分析

### 🥇 黄金 ({gold_price})
1. **热点标题** — 简要分析
2. **热点标题** — 简要分析

## 📈 技术面简析

### NVDA ({nvda_price})
短期趋势判断，关键支撑/阻力位，RSI/成交量状态，是否超买/超卖

### TSLA ({tsla_price})
短期趋势判断，关键支撑/阻力位，RSI/成交量状态，MACD信号

### XAU ($x,xxx/oz)
短期趋势判断，关键支撑/阻力位，驱动因素

## 🌐 宏观环境
影响走势的关键宏观因素（利率预期、美元指数、地缘政治、市场情绪）

**推荐加入主要指数数据**（从Reuters/Yahoo Markets页面获取）：SPX, DJIA, IXIC 的涨跌情况，以及欧/亚市场表现（STOXX, FTSE, N225），这些数据从同一页面可一次性获取，极大提升简报的宏观纵深。

## ⚠️ 风险提示
1. 需关注的短期风险
2. 下行风险
3. 预期差风险

---

*免责声明：本简报仅供参考，不构成投资建议。投资有风险，入市需谨慎。*

### Data-Outage Banner Pattern (Full Collapse)

Use when all data sources failed - pre-run script errors + zero network connectivity. Place immediately after the timestamp line:

```
> ⚠️ **数据采集故障说明**：今日所有外部接口（Nasdaq API、黄金API、新闻源）均因网络环境问题无法连接。以下价格为最近可用收盘价（美东时间{date}周{day}收盘）。建议参考昨日趋势线进行判断。如网络持续故障，建议检查代理服务器连通性和SSL/TLS环境配置。
```

And in the closing footer:

```
*⚠️ 本简报基于{date}（周{day}）收盘数据。因网络环境故障，今日实时数据采集失败，已使用最近可用数据。恢复后请参考最新行情。*
```

### Persistent-Outage Escalation Banner (7+ Consecutive Days)

Use when the same infrastructure-level failure has persisted for 7+ consecutive days. The report shifts from "analysis with caveats" to "system-status bulletin":

**Header — replaces the price table header line:**
```
📡 数据采集时间: {collection_time}

> ⚠️ **数据采集连续第{N}天失败 — 本简报不完整**
>
> 所有外部数据源持续无法连接，详细诊断见"风险提示"部分。
> **最近一次有效数据：{last_good_date}（{staleness_days}天前）** — 以下引用数据已严重滞后，不反映当前市场状况。

## 📊 三大标的行情概览

| 标的 | 现价 | 涨跌 | 涨跌幅 |
|------|------|------|--------|
| **NVDA 英伟达** | ❌ 数据不可用 | - | - |
| **TSLA 特斯拉** | ❌ 数据不可用 | - | - |
| **XAU 黄金** | ❌ 数据不可用 | - | - |
```

**今日热点 — becomes analysis-led, not news-driven:**
```
## 🔥 今日热点 — 基于历史存档数据（滞后，非当前交易参考）

由于数据采集系统连续{N}天中断，以下内容引用已存档前几期简报中的核心信息。

### 🖥️ 英伟达
1. **趋势回顾（基于上次有效数据）** — 关键价格走势和核心叙事，标注数据日期
2. 持续的基本面因素

### 🚗 特斯拉
...

### 🥇 黄金
...
```

**Risk section — operational risk becomes primary:**
```
## ⚠️ 风险提示与系统状态

1. **⚠️ 系统故障 — 网络层连续{N}天不可用**：SSL 握手在所有 HTTPS 连接上意外中断。需排查执行环境的网络防火墙、代理配置或SSL证书问题。
2. **⚠️ 数据缺失**：本日无任何市场数据。简报中的历史数据已过时{X}天，不反映当前市场状况。
3. **⚠️ 交易警示**：本简报不包含任何有效的当前市场数据，请勿依据本报告进行任何交易决策。
4. **建议措施**：
   - 检查执行环境的网络连接和 SSL 证书
   - 联系平台运维确认网络策略变更
   - 考虑增加HTTP备用数据源或本地缓存回退机制
```

**Footer:**
```
*简报自动生成 | 系统状态: ❌ 数据采集失败 — 网络不可达（连续{N}天）*
```

### Zero-News Briefing Pattern (When All External Sources Blocked)

Use when ALL web news sources return 0 bytes — Google News RSS, Yahoo, CNBC, Reuters, etc. all fail silently despite internet connectivity.

1. **分析导向代替消息驱动** — Frame "今日热点" as price-action analysis: `NVDA放量反弹+4%, $200支撑确认` instead of fabricating headlines
2. **成交量是核心信号** — With no news, volume is the most informative data point. 148M shares (NVDA) vs 33M (TSLA) signals very different capital flows
3. **百分比差异揭示资金流向** — Compare % changes (NVDA +4% vs TSLA +0.3%) to infer sector rotation even without news
4. **前日简报内容延续** — Pre-baked macro factors (Fed policy, geopolitics, AI capex cycle) change slowly — carry forward from previous briefing
5. **明确标注数据受限** — State clearly that web news was unavailable. Never fabricate headlines. "无新增重大消息" is honest and professional.

### Writing Guidelines

- **全中文、简洁务实** — no English filler, direct to the point
- **每个标的控制在5-8行** — tight bullets, not paragraphs
- **结论先行** — give the judgment first, then supporting reasoning
- **有具体数据支撑** — cite prices, percentages, analyst targets
- **价格写入节标题** — 技术面分析用 `### NVDA ($202.81)` 格式，热点用 `### 🖥️ 英伟达 ($202.81)`，便于快速定位
- **风险条目标注严重等级** — 在风险提示条目尾部标注等级：`（高）` `（中高）` `（中）`，帮助区分优先级
- **必须包含风险警示** — don't sugarcoat, don't hide negatives
- **数据源争议时加脚注** — if script data conflicts with verified sources, add ⚠️ disclaimer footnote
- **周末简报额外要求** — ①强制在数据说明行标注数据滞后天数 ②"今日热点"优先覆盖周末事件 ③技术面分析用条件句（"若开盘后"、"需关注是否守住"）④黄金部分前置地缘政治
- **黄金极端波动（单日$100+/3%+）处理** — ①必须列举3-4个驱动因素（单一因素无法解释极端波动）②RSI即使冲入70+超买区，在极端行情中可维持数日，不要自动视作卖出信号 ③支撑位需重新评估，前阻力位转化为新支撑 ④风险警告上调至"中高"等级 ⑤黄金+股票同时上涨的场景≠risk-off，应归因于宏观因素（降息预期重估、美元走弱）而非避险。详见 `references/gold-extreme-move-analysis.md`
