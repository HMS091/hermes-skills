# 第二次 Bounty Script 超时事件 (2026-06-03 17:18-17:20)

## 事件经过

| 时间 | 事件 |
|------|------|
| 17:13:33 | 第一次超时 `relayhop/ClaudeEarnSelf-runtime` → agent 生成详细分析报告 |
| 17:18-17:20 | **第二次超时** `dev-kp-eloper/BountyScout` → 同一个 cron job 再次被 120s 杀死 |
| 17:20 | 残留 `/tmp/bounty_79u_l8ea/BountyScout/` 包含部分克隆（`.git`, `README.md`, `scout_bounties.py`, `seen_bounties.json`） |

## 时间线拆解

```
17:13:33  - 第一次超时（relayhop/ClaudeEarnSelf-runtime）
              agent 写了 4361 字节分析报告，提出 A/B/C/D 四个方案，没实施
17:18:xx  - 下一次 cron tick（5分钟间隔）
17:20:xx  - /tmp/bounty_79u_l8ea 创建 → BountyScout 克隆开始
17:20:xx  - 脚本在 clone 完成后 ~很短时间被 120s 超时杀死
```

## 被浪费的资源（每次 tick）

- **~30s**: 15个 GitHub API 搜索查询
- **~5s**: 候选筛选、PR检查、仓库验证
- **~20-40s**: `do_bounty.py` fork + clone（BountyScout 仓库较小 ~54KB，但含 54K+ 的 `seen_bounties.json`）
- **被杀死**: AI 分析 / commit / push 从未有机会执行
- **临时目录残留**: `rm -rf workdir` 在 `finally` 块中，但 SIGKILL 不让 finally 运行

## 根因

120s 总时间限制对于「搜索→验证→执行」完整 pipeline 不够。搜索阶段已经吃掉 20-30s，留给执行的只剩 ~90s。而 clone 本身可能就要 10-30s，加上 AI 分析（20-60s）、commit、push、PR 创建——经常超过 90s。

## 为什么第二次超时不该发生

第一次超时的 agent 已经诊断出根因并给出修复方案。如果它在同一回合内执行了任意一个修复：
- **方案C**: 在 `smart_bounty_search.py` 中添加 `BLACKLISTED_REPOS` 列表 → BountyScout 被跳过 → 下一个 tick 不会超时
- **方案A**: 精简查询到 5-6 个 → 节省 15-20s → 下次也许够用
- **方案D**: 拆分搜索和执行 → 搜索不会超时

**核心教训**: 当 agent 有文件写权限时，诊断出已知修复方案后应直接实施，不要只输出报告等用户操作。下一个 cron tick 几秒后就来了。

## 残留文件清理

```bash
find /tmp -name "bounty_*" -type d -mmin +30 2>/dev/null | while read d; do rm -rf "$d"; done
```

本次残留: `/tmp/bounty_79u_l8ea/` (BountyScout, 17:20)
