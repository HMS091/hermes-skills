# 300s 嵌套超时事故分析 (2026-06-03 17:57)

## 事件

`smart_bounty_search.py` 作为 cron 数据收集脚本超时（300s）。

## 根因

**内外超时完全重叠无缓冲**:
- 外部 cron: `script_timeout_seconds: 300` — 整个脚本必须 300s 内完成
- 内部 `do_bounty.py` subprocess: `timeout=300` — 子进程也设 300s
- 搜索阶段本身耗时约 20-30s（14 个 API 查询 + 筛选）
- 留给 do_bounty.py 的实际窗口 **最多 270s**，但 inner timeout 设为 300s

## 步骤级超时拆解

| 步骤 | 超时设置 | 典型耗时 | 风险 |
|------|---------|---------|------|
| GitHub API 调用 | 30s (urllib) | 1-3s | 低 |
| DeepSeek AI 分析 | 120s (urllib) | 20-60s | **中高** — 高峰期模型负载大 |
| git clone fork | 120s (subprocess) | 15-90s | **高** — 大仓库 + 慢网络 |
| git commit | 10s | <1s | 低 |
| git push | 120s (subprocess) | 10-60s | **中** — 大仓库推送慢 |
| fork 等待 + branch + 其他 | 5-15s | 3-5s | 低 |
| **最坏情况累加** | — | **~210-280s** | 只有 20-90s 缓冲 |

## 为什么前 8 次是 120s 超时这一次变成了 300s?

之前的 `script_timeout_seconds` 默认是 120s。第 8 次修复（~17:49）将其改为 300s，解决了 120s 超时问题。但 **do_bounty.py 内部的 subprocess timeout 没有同步降低**，仍然保持 300s。结果内外相等 = 无缓冲。

## 对比 120s vs 300s 超时

| 维度 | 120s 版本 (第1-8次) | 300s 版本 (第9+次) |
|------|--------------------|---------------------|
| 搜索阶段耗时 | 20-30s | 20-30s |
| 剩余窗口 | ~90s | ~270s |
| do_bounty.py 内部超时 | 300s (远远超剩余窗口) | 300s (等于而非小于剩余窗口) |
| 实际瓶颈 | 搜索+clone 用完 120s | DeepSeek(60s)+clone(90s)+push(60s)=210s，接近 270s 上限 |
| 残留临时目录 | 是 (SIGKILL) | 是 (SIGKILL) |
| 彻底解决需要 | 降低内层 timeout 或增加外层 | 将内层从 300→270 且加仓库大小检查 |

## 发现过程

1. 检查 cron 输出发现脚本 timeout after 300s
2. 读 `smart_bounty_search.py` 发现 300s 的 subprocess timeout
3. 读 `do_bounty.py` 发现各个子步骤超时设置：DeepSeek=120s, clone=120s, push=120s
4. 未搜索 session 历史 — 已有 skill 文档证明之前是 8 次 120s
5. 结论：300s 修复解决了 120s 问题但引入了嵌套相等超时

## 相关文件

- `/opt/data/scripts/smart_bounty_search.py` — 入口脚本，subprocess timeout=300
- `/opt/data/scripts/do_bounty.py` — 执行引擎，各步骤 timeout 120s/120s/120s
- `/opt/data/scripts/.bounty_history.json` — 历史记录，显示已有 26 次执行记录
- `/opt/data/scripts/.bounty_stats.json` — 被外部覆写，统计不可信
