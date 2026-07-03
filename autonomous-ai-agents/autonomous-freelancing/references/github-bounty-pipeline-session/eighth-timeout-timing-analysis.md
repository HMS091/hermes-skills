# 第8次超时精确定时分析 (2026-06-04 13:43)

## 此时超时仍在发生

尽管已应用所有 Phase 1+2 修复，且 `MAX_CANDIDATES_PER_TICK=1` 与启动前时间检查已就绪，
脚本在 2026-06-04 13:43 仍被 300s cron 超时杀死。

## 定时拆解（实测基于 API 行为）

```
time(s)  event
───────  ─────
  0      main() 启动
  5      开始 GitHub 搜索 (14 queries × 0.15s delay)
  5-75   搜索阶段：14 个 API 调用
         - 每个 query 返回 ~30 项，14 queries = 最大 420 项
         - 每 query 后 0.15s sleep
         - API 正常 1-3s/次，限速时 5-10s/次
         - 最坏情况：14 × (3s API + 0.15s sleep) = ~44s
         - 含限速抖动：最多 70-80s
 75      filter + sort (2-5s)
 80      打印候选列表
 82      进入候选循环
 83      `check_existing_pr` — 1-2 API 调用 (2-6s)
 89      `check_repo_active` — GET /repos (2-5s)
 94      `check_merge_rate` — 2 API 调用 (4-10s) 
104      验证全部完成
         ┌────────────────────────────────────────────┐
         │ elapsed ≈ 104s                             │
         │ CRON_TIMEOUT 检查: 104 + 240 ≤ 280?        │
         │ 344 > 280 → ❌ 应跳过! 但 line 370 是否   │
         │ 正确执行？                                │
         └────────────────────────────────────────────┘
104      如果 guard 正常: "剩余 176s < 240s 子进程需求" → break

         —— 如果 guard 有 bug (line 418 旧检查): ——
104      line 418: `elapsed > 280?` → 104 < 280 → 放行
104      do_bounty.py 启动
104-344  do_bounty.py 执行 (最多 240s)
         - 读取 Issue (3s)
         - Fork 创建 + 等待 (5s + GH 异步 3s 重试)
         - API 下载 zipball (5-120s, 取决于仓库大小)
         - 解压 + git init (2-5s)
         - DeepSeek API 分析 (3-45s)
         - 创建 blob + tree + commit + push (5-30s)
         - 创建 PR (2-5s)
300      ← cron SIGTERM (cron 超时)
         此时 do_bounty.py 运行了 ~196s
         在 zipball 下载或 DeepSeek 分析阶段
         → do_bounty.py 成为孤儿进程
         → smart_bounty_search.py 被 SIGKILL
         → save_stats() 模块级未执行
         → /tmp/bounty_* 残留
```

## 根因总结

| 因子 | 贡献 |
|------|------|
| 搜索阶段最坏 80s | +80s |
| 验证阶段 30s | +30s |
| 子进程 240s timeout | +240s |
| **合计最坏** | **350s → 超 300s 达 50s** |
| `CRON_TIMEOUT=280` guard | 检查 104+240=344 > 280 → 应拦截 |
| line 370 guard (已修复) | ✅ 正确拦截 `elapsed + SUBPROCESS_TIMEOUT > CRON_TIMEOUT` |
| line 418 guard (未修复) | ❌ `elapsed > CRON_TIMEOUT` 不扣子进程预算 |

## 两种修复路径

### 路径 A: 收紧时间预算（1 行修改）

降低 `SUBPROCESS_TIMEOUT` 从 240 到 **180s**，同时修复 line 418 的 guard：

```python
SUBPROCESS_TIMEOUT = 180  # 240 → 180
CRON_TIMEOUT = 280

# 两处 guard 统一使用 elapsed + SUBPROCESS_TIMEOUT > CRON_TIMEOUT:
# line 370 (候选循环开头): ✅ 已修复
# line 418 (子进程启动前): ❌ 需从 elapsed > CRON_TIMEOUT 改为:
if elapsed + SUBPROCESS_TIMEOUT > CRON_TIMEOUT:
    print(f"   ⏰ 已运行 {elapsed:.0f}s，剩余 {CRON_TIMEOUT-elapsed:.0f}s 不够 {SUBPROCESS_TIMEOUT}s")
    break
```

### 路径 B: 修复 line 418 后提升 cron 超时（架构级）

保留 `SUBPROCESS_TIMEOUT=240`，但将 cron 超时从 300s 提升至 **360s**：
- 搜索 80s + 验证 30s + 子进程 240s = 350s < 360s ✅
- 需在 cron config 中改 `script_timeout_seconds: 360`

## 验证方式

```bash
# 启动前清理
find /tmp -name "bounty_*" -type d -delete

# 运行脚本并测时
timeout 310 python3 /opt/data/scripts/smart_bounty_search.py 2>&1

# 确认：
# 1. 无残留 /tmp/bounty_* 目录
# 2. .bounty_stats.json 有新记录（证明 save_stats() 执行到）
# 3. 无孤儿 python3 do_bounty.py 进程
```

---

## 2026-06-04 13:52 第9次超时 — 定时拆解 (faster search, same death)

本会话（第9次超时代理会话）发现了比此前分析更精确定时的失败路径：

### 快速搜索路径（API 响应正常时）

```
time(s)  event
───────  ─────
  0      main() 启动
  0-25   搜索阶段：14 个 API 查询
         - 当 GitHub API 响应快时（~1s/query）
         - 14 × (1s API + 0.15s sleep) = ~16s
         - + 解析/去重/过滤 ≈ 5-8s
 25      打印候选列表
 27      进入候选循环
 28      guard #1 (line 370): elapsed=27s, 27+240=267 < 280 → ✅ 放行
 28-37   verification: check_existing_pr + check_repo_active
         - 对于白名单仓库: skip merge_rate (2-3 API calls, ~6-9s)
 37      guard #2 (line 421): elapsed=37s, 37 < 280 → ✅ 放行 (错误! 应扣子进程预算)
 37      do_bounty.py 启动 → 创建 /tmp/bounty_* 空目录
 37-277  do_bounty.py 执行 (最多 240s)
         - zipball 下载: 5-60s
         - DeepSeek API 分析: 3-45s
         - Git Data API push: 5-30s
         - 创建 PR: 2-5s
277      子进程返回, main() cleanup ~3s
280-283  save_stats() 执行 (如果脚本还活着)
300      ← cron SIGKILL 截止线
```

**当 API 快时**: 总耗时 ≈ 280s → 在 300s 内，**可能存活**。
**当 API 慢时**: 搜索 35s + 验证 20s + 子进程 240s = 295s → 濒临死亡。
**当 API 抖动时**: 搜索 50s + 验证 15s + 子进程 240s = 305s → **超时 5s → SIGKILL**。

### 两个 guard 的行为差异

| Guard | 位置 | 检查公式 | 状态 |
|-------|------|---------|------|
| guard #1 | line 370 (loop start) | `elapsed + 240 > 280` | ✅ 正确 — 扣除了子进程预算 |
| guard #2 | line 421 (pre-subprocess) | `elapsed > 280` | ❌ 错误 — 未扣除子进程预算 |

**guard #1 的副作用**: 当搜索阶段 > 40s 时 (`40+240=280`, guard triggers), guard #1 会拦截。这解释了为什么有时脚本能进入验证阶段（搜索快），有时不能（搜索慢）。**但 guard #1 的快路径放行 + guard #2 的错误放行 = 间歇性超时**。

### 用户声称 vs 现实

用户在 cron 调度提示中说 "脚本修好了git网络问题，不会再超时了"。但：
1. git 网络问题（`github.com:443` 不可达）已于 v5 通过 API-only 迁移修复 ✅
2. **定时预算问题未修复**（guard #2 仍使用旧公式 ❌）
3. `save_stats()` 仍在模块级非 `finally` 块中 ❌
4. 残留 temp 目录清理未在 `main()` 入口执行 ❌

用户将两类不同故障（git 网络故障 vs 定时预算故障）混淆了。定时预算故障自 12:28 起已连续发生 9 次。
