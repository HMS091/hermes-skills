# Web3 交易终端 / DeFi 项目尽调（数据源地图与口径陷阱）

调研交易终端/机器人（Axiom、GMGN、Photon、BullX、fomo、Trojan 等）或 DeFi 协议时的专用数据源与口径规则。所有数字必须标注「口径 + 来源 + 读取日期」。

## 数据源地图（按可信度）

| 要什么 | 去哪拿 | 陷阱 |
|---|---|---|
| 终端手续费/交易量（链级） | DeFiLlama「Trading App / Telegram Bot」适配器；聚合视图用 Blackroom Alpha screener（`blackroomalpha.com/screener/terminals/<name>`）拿 30d/7d/24h 量费、份额、链分布 | **适配器起算日 ≠ 产品上线日**（Axiom 量数据自 2026-05、费数据自 2025-01 起计），终身数必须注明窗口；最近 ~24h 的日数据会被回补重算，对比以 closed UTC day 为准 |
| 执行质量/速度/费率实测 | OpenChainBench（`openchainbench.com/products/<name>`） | 交易笔数、活跃钱包、均单、执行延迟、实测费率对比 |
| 合约程序级指标 | Solana Compass 程序分析（`solanacompass.com/analytics/programs/<program_id>`） | 累计 tx、独立钱包、CU 效率、归因量；program_id 从终端费钱包/程序 feed 找 |
| 官方收入/融资口径 | **YC 公司页（`ycombinator.com/companies/<slug>`）是尽调金矿**：YC 项目会公开 MRR/月净利（如「$10M MRR, $5M monthly net profit」），还有批次、合伙人、创始人实名与背景 | 页面数据可能是批次时点的旧口径，引用时注明时点 |
| 用户/留存 | Token Terminal（`tokenterminal.com/explorer/projects/<name>`） | 对小终端覆盖不全，DAU 按费用贡献地址计 |
| 费率与竞品对比 | photonguides.com、memecoin.wiki、gmgnguide.com | 每个数字都带读取日期；官方费率（费率表）与实测费率（DefiLlama）是两回事 |
| 收入结构/中文市场 | Odaily、ChainCatcher、Panews 的「收入结构拆解」类稿 | 有返佣后净额、链分布、季度营收；中文市场季度数据 Panews 常有 |
| 负面事件/丑闻 | ZachXBT 帖 + CoinDesk/Cryptobriefing/The Block 转载（转载带全文，X 原帖要登录）+ Polymarket 押注市场热度 + Lookonchain 内幕钱包追踪 | 四者拼出完整负面时间线：爆料原文 → 主流媒体确认 → 市场用脚投票的规模 → 链上获利证据 |

## 口径陷阱（踩过，必查）

- **手续费（fees）≠ 收入（revenue）**：fees 是用户付的毛额，revenue 是扣返佣后的净额——GMGN 终身 fee $240M / revenue $205M，差 14.7% 全是返佣。引用时写明口径，两者混用是报告硬伤。
- **同名公司混淆是常态**：融资聚合站（startupintros、keenable 等）把同名不同实体合并。发现融资数据与已知轮次严重不符时，先对 YC/Sacra/官方公告核实体，报告里点名纠正。
- **链分布漂移快**：GMGN 一年内从 99.5% Solana 变成 BSC 占大头。用旧文章数据前先查最新链分布，旧文章的链分布结论直接作废。
- **「卖铲人」报告必含生命周期风险一节**：终端赛道头部平台可从月收数千万崩跌 99%（Photon）甚至停摆（BullX，收了约 $2 亿费后关闭）——平台轮换是结构性问题，不是尾部风险。竞品对比表要带「状态」列（增长/衰落/停摆/被收购）。

## 开发成本与合规基准（复刻类报告直接引用）

- Turnkey MPC 钱包按签名计费：PAYG $0.10/签 → Pro $99/月、$0.05/签 → 企业级低至 $0.0015/签（turnkey.com/pricing）
- 终端开发外包行情：4irelabs 公开口径基础版 $10–15 万、多链高级版更高；AngelHack 案例 4 个月交付完整 Solana 终端（含 Turnkey 钱包）
- 非托管终端合规底线：离岸实体 + 不碰私钥/资金 + 无人民币法币通道（支付宝/微信协议明文禁止加密交易）+ perps（如 Hyperliquid）按区域屏蔽（美国受限）
- 安全基线（对 Axiom 数据滥用丑闻的通用对策）：RBAC 最小权限、数据访问审计日志、员工自营钱包报备——成本几乎为零，从第一天做

## 报告结构模板（结论先行 + 负面风险）

1. 核心结论（5–8 条，含最大的坑）→ 2. 公司基本面（含融资口径核实与纠错）→ 3. 产品拆解（模块/依托第三方）→ 4. 商业模式与财务（收入来源表 + 里程碑时间线 + 单位经济，推算部分明确标注）→ 5. 负面事件/丑闻时间线 → 6. 竞争格局（含状态列）→ 7. 市场规模锚点 → 8. 复刻路径与成本（技术清单 + 路线预算表 + 运营月成本 + 合规红线）→ 9. 风险清单 → 10. 结论与建议 → 数据来源（逐条标注来源+日期）
