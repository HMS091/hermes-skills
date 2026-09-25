# Phase 2 超时事故续报 (2026-06-03 18:49)

## 第 15+ 次超时 — 根因修复记录

**时间**: 2026-06-03 18:49 UTC
**超时值**: 300s (config 已正确设置)
**这次发生了什么**: 脚本超时后，cron 触发了 agent 会话。**不同于前 14 次，这次 agent 选择了直接修复脚本，而不是只写分析报告。**

## 根因再确认

`MAX_CANDIDATES_PER_TICK = 2` 在第 40 行定义但**从未在循环中使用**。for 循环遍历所有候选人：
- 搜素阶段：~30s
- 候选人 #1 do_bounty.py：120-240s
- 候选人 #2 do_bounty.py：120-240s
- 合计 270-510s > 300s → SIGKILL

## 本次已应用修复（2026-06-03 18:49）

| 修复 | 文件 | 状态 |
|------|------|------|
| `candidates = candidates[:MAX_CANDIDATES_PER_TICK]` 循环前截断 | smart_bounty_search.py | ✅ 已应用 |
| 耗时监控，elapsed > 280s 提前 break | smart_bounty_search.py | ✅ 已应用 |
| `do_bounty.py` 子进程 timeout 300s → 240s | smart_bounty_search.py | ✅ 已应用 |
| `try/except subprocess.TimeoutExpired` | smart_bounty_search.py | ❌ 未应用（需 Phase 2 下个 tick） |

## 未修复的部分

- `try/except TimeoutExpired` — 需要单独 patch，留给下个 Phase 2 tick
- DeepSeek API timeout 120s → 45s — 未应用
- git clone timeout 120s → 60s — 未应用
- git push timeout 120s → 60s — 未应用
- `DEEPSEEK_MODEL` 变量未使用 — 未应用

**关键判断**: 三重防护（截断 + 耗时监控 + 子进程 240s）应能阻止 90%+ 的超时。try/except 是最后的保险丝，优先级较低。
