# Cron 频率对比测试 — 2min vs 5min (2026-06-03)

## 测试目的

确定最优搜索频率：太慢漏单，太快浪费 GitHub API 配额。

## 测试方法

1. 初始设置：每 5 分钟扫描一次（默认）
2. 2026-06-03 17:22 UTC 改为 **每 2 分钟**
3. 运行约 8 小时（隔夜）
4. 对比两个频率下的指标：
   - 总扫描次数
   - 发现的 Bounty 总数
   - 自动执行/PR 提交数
   - 重复发现数（同一个 Issue 被多次扫描到但状态未变）

## 测试配置

- 搜索脚本: `smart_bounty_search.py` v3（15 个查询，代币检测）
- 历史文件: `.bounty_history.json`
- 统计记录: `.bounty_stats.json`（每次运行自动追加 timestamp）
- 分析工具: `analyze_stats.py`

## 指标

```
总运行次数 = .bounty_stats.json 中 runs 数组长度
PR 提交数 = .bounty_history.json 中 "PR #" 条目数
重复率 = (总发现数 - 唯一 Bounty 数) / 总发现数
```

## 决策规则

- 如果 2min 比 5min 多抢到 real PR（非 BountyScout 类垃圾 PR）→ 保持 2min
- 如果两者效果一样（都只抢到 bot 农场 PR）→ 用 5min，省 GitHub API 配额
- 如果 2min 导致 GitHub API 限流（403/429 增多）→ 降回 5min
