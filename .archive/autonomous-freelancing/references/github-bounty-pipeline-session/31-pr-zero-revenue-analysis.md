# 31 PRs, $0 Revenue — 2026-06-03 Bounty 管线经济分析

## 摘要

截至 2026-06-03，自动 bounty 管线共提交 **31 个 PR**，其中 **0 个被合并，收入 $0**，成功率 0%。

用户问「能收多少钱」和「把时效性算进去没有」时，才触发这次复盘。之前一直乐观估计「30+ PR 提交了」，但从未核查实际合并率和收入。

## 已提交 PR 状态汇总

| 来源仓库 | PR 数 | 状态 | 分析 |
|----------|-------|------|------|
| SecureBananaLabs/bug-bounty | 7 | 全部开放 | ❌ bot 农场，30天 0 合并，2500+ PR |
| Scottcjn/rustchain-bounties | 2 | 全部开放 | ✅ 仓库活跃(142合并/月)但我们的 PR 没人理 |
| mergeos-bounties/mergeos | 2 | 全部开放 | ✅ 仓库活跃(34合并/月)，但 MRG 仅值 $0.00026 |
| imDarshanGK/localmind | 4 | 全部开放 | ❌ 仓库不活跃，0 合并 |
| supperjumpin/supperjumpin | 2 | 全部开放 | ✅ 活跃(96合并/月) |
| xevrion-v2/agent-playground | 1 | 开放 | ❌ bot 农场，$50 单子 |
| 其他零散 | ~13 | 全部开放 | 各种小仓库 |
| **总计** | **31** | **0 合并** | **收入 $0** |

## 根因分析

### 1. Bot 农场占大多数

SecureBananaLabs/bug-bounty 和 xevrion-v2/agent-playground 占了 8 个 PR（26%）。这些仓库：
- 30 天内合并数为 0
- 但 PR 总数巨大（2500+/233+），说明全是 bot 在互刷
- 不是真实的赏金来源

### 2. 代币面值陷阱

脚本之前的 TOKEN_TO_USD 汇率全是错的：
- MRG 估了 $0.08 → 实际 $0.00026（高估 **300 倍**）
- MRWK 估了 $0.05 → 实际零流动性（≈$0）
- 只有 XLM 和 USDC 是准确的

结果：之前以为的 "1500 MRG = $120" 的单子实际值 **$0.39**。AI 为 39 美分花了几分钟分析+代码生成+API 费用。

### 3. 无门槛 AI-friendly 过滤太松

很多 doc PR（README 修改、CONTRIBUTING.md 添加）提交到了无人维护的仓库。这些不需要付钱，也没人 review。

### 4. 没有做"这仓库是不是真给钱"的验证

没有检查仓库的历史合并率、PR review 活跃度、付款证明。脚本假设「有 bounty 标签 = 会给钱」，但实际上 60-70% 的 bounty 标签只是项目管理标签。

## 教训总结

| 教训 | 严重程度 | 修复 |
|------|---------|------|
| 代币面值 ≠ 美元价值 | 🔴 严重 | 加实时价格验证，用代理查 DexScreener |
| Bot 农场浪费执行周期 | 🔴 严重 | 加仓库黑名单 |
| 无门槛 doc PR 没意义 | 🟡 中等 | 白名单制 + 合并率检查 |
| 没有周期性的效果复盘 | 🟡 中等 | 现已经做了 |

## 行动项

1. ✅ 更新脚本 TOKEN_TO_USD 为实际价格
2. ✅ 添加 TRUSTED_REPOS 和 BLOCKED_REPOS
3. ✅ 添加合并率检查（MIN_MERGE_RATE = 5%）
4. ✅ 非白名单仓库门槛从 $50 提到 $200
5. ❌ 降低搜索频率（5min → 30min）— 待用户确认
6. ❌ 加定期经济复盘（每周自动跑一次 PR 合并率检查）

## 2026-06-04 增量审计：追加 6 个 PR 检查，合并率仍为 0%

在本轮扫描中，对以下 6 个之前标记为「done」的 PR 进行了状态检查：

| PR | Repo | 金额 | 当前状态 | 合并? |
|----|------|------|---------|-------|
| #6849 | Scottcjn/rustchain-bounties (code review) | 无标价 | Closed, 当天创建当天关闭 | ❌ |
| #221 | supperjumpin/supperjumpin (Player Profile) | 无标价 | Closed, not merged | ❌ |
| #222 | supperjumpin/supperjumpin (Growth/auth) | 无标价 | Closed, not merged | ❌ |
| #657 | Suncrest-Labs/nester (security audit) | 无标价 | **Open** | ❌ |
| #207 | mergeos-bounties/mergeos (login modal) | 500 MRG | **Open** | ❌ |
| #206 | mergeos-bounties/mergeos (AI evaluation) | 1500 MRG | **Open** | ❌ |
| **合计** | | | **0 merged / 6 total** | **0%** |

**关键观察**:
- supperjumpin 的两个 PR (#221, #222) 被关闭但**未合并**——可能被驳回或已被其他方案替代
- surency-stables 的其他 PR 仍开放等待 review（nested/texture）
- mergeos 的两个 PR 创建 8+ 天后仍无 review 活动
- **结论：合并率为 0% 的状态自 31-PR 复盘以来完全未改善**。管线能提交 PR 但无法确保 review 和合并。

**对持续运营的影响**:
- 管线应专注于**白名单仓库**（rustchain-bounties、mergeos、supperjumpin、nester）——这些仓库确有活跃的维护者合并 PR
- 但即使是白名单仓库，我们的 PR 也不一定被优先 review。可能需要添加跟进机制（如 issue comment ping）
- 对于 RustChain 的 code review 类 Issue（#6849），当天创建当天关闭——可能门槛不符合或已被其他 reviewer 抢先
