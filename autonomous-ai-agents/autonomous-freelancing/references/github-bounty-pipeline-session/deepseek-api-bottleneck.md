# DeepSeek API Bottleneck — The Compound Timeout Killer

## 发现时间
2026-06-03 18:15 UTC (第10+次超时)

## 症状
`smart_bounty_search.py` 找到了合格的 Bounty 目标，完成了 fork → clone → 创建分支，但在 AI 分析阶段（`analyze_issue_and_repo()` 中的 DeepSeek API 调用）卡住，最终被 300s 外定时器 SIGKILL。

## 两次不同模式的证据 (18:15 vs 18:23 UTC)

### 第1次 (18:15) — DeepSeek 直卡
目标: `mergeos-bounties/mergeos` Issue #8 (fork → HMS091/communication-guides)
- ✅ Fork 创建
- ✅ git clone 完成
- ✅ 分支 `fix/bounty-8-task--comm-guide--pa` 已创建
- ❌ **无新文件** — AI 分析未完成，DeepSeek API 调用卡住 120s
- 残留: `/tmp/bounty_6l_nxruh/communication-guides/` — 代码完整克隆但 AI 输出未写入

### 第2次 (18:23) — DeepSeek 通过但父超时
目标: `all-aboard-ohio/communication-guides` Issue #7
- ✅ Fork 创建
- ✅ git clone 完成  
- ✅ 分支 `fix/bounty-6-task--comm-guide---h` 已创建
- ✅ **DeepSeek 分析完成** → AI 生成了修改
- ✅ **文件已写入**（工作树 clean，说明 commit 已完成）
- ✅ **git push 已完成**（远程 refs/origin/ 存在）
- ✅ **PR #10 已创建**（在 `.bounty_history.json` 中确认）
- ❌ **父进程 `smart_bounty_search.py` 仍 timed out** → `save_stats()` 未运行、清理未执行
- 残留: `/tmp/bounty_0ykkk8ot/communication-guides/` — 分支已推送、提交已完成，但父进程被 SIGKILL

**关键区别**: 18:15 是 DeepSeek 自身来不及（卡死 120s），18:23 是 DeepSeek 完成了但子进程总时间 ~90s + 搜索阶段 ~30s + 其他开销 → 跨过 300s 线。后者证明即使 DeepSeek 正常工作，**其他步骤的累计耗时**也可以刚好压线。

## 具体证据 (原始记录)

| 阶段 | 耗时 | 状态 | 关键代码 |
|------|------|------|---------|
| GitHub API 搜索 (14 查询) | ~25-35s | ✅ 完成 | 第 201-211 行 |
| Fork 创建 | ~3-5s | ✅ 完成 | 第 240-248 行 |
| git clone fork | ~15-40s | ✅ 完成 | 第 264-269 行，120s timeout |
| 创建分支 | ~1s | ✅ 完成 | 第 288-293 行 |
| **DeepSeek API 分析** | **~60-200s** | **❌ 卡住** | **第 73-78 行，120s timeout** |
| 文件写入 | <1s | 未到达 | 第 327-330 行 |
| git commit + push | ~10-60s | 未到达 | 第 339-356 行 |
| PR 创建 | ~3s | 未到达 | 第 388-394 行 |

**残留证据**: 执行后 `/tmp/bounty_6l_nxruh/communication-guides/` 中的仓库被克隆完成，分支 `fix/bounty-8-task--comm-guide--pa` 已创建，但无新 commit（AI 输出未写入），验证了卡在 AI 分析阶段。

## 目标详情
- **仓库**: mergeos-bounties/mergeos (fork → HMS091/communication-guides)
- **Issue #8**: "1000 MRG Bounty - Implement USDT Crypto Payment Gateway Intake"
- **MRG 真实价值**: $0.00027/枚 → 1000 MRG = $0.27
- **脚本 TOKEN_TO_USD 估值**: $0.08/枚 → 1000 MRG = $80 (高估 296 倍)
- **AUTO_EXEC_MIN_USD**: 10 (脚本值) → 脚本认为 $80 ≥ $10，触发执行
- **实际价值**: $0.27，完全不值得执行

## 根因分析

### 1. DeepSeek API 延迟可变性
DeepSeek API 的响应时间波动很大（20s-120s+），取决于:
- 当前模型负载（北京时间凌晨/白天差异大）
- Issue 复杂度（需要分析的仓库文件数）
- 输入长度（仓库文件树 + 关键文件内容）

在 300s 窗口中，搜索阶段已消耗 ~30s，DeepSeek 如果花 90s+，留给 git push 和 PR 创建的时间只有 ~80-120s。大仓库 push 慢的话很容易压线超时。

### 2. 高估的代币价值导致低价值目标被触发
MRG 标称 1000 MRG (脚本估值 $80) 实际上只值 $0.27。脚本白白浪费了一整个执行周期去分析一个几乎无价值的 Issue。如果在 `check_existing_pr()` 和 `check_repo_active()` 之后加一步代币价值验证，可以直接跳过此类目标。

### 3. DeepSeek 120s timeout 过长
`urllib.request.urlopen(req, timeout=120)` 在高峰期可能真的等满 120s。如果改为 `timeout=45` + 重试（2 次），总等待时间从 120s 降至 90s，并且更早放弃慢响应。

## 修复建议

### 短期（立即见效）
```python
# 在 do_bounty.py 中：缩短 DeepSeek API timeout
# 第 73 行修改
resp = json.loads(urllib.request.urlopen(req, timeout=45).read())  # 原 120s
```

### 中期（显著降低无效执行）
```python
# 在调用 do_bounty.py 之前加代币价值验证
# 如果最大 USD 价值来自 MRG/MRWK 但实际链上价格 < $50，直接跳过
if token_symbol in ("MRG", "MRWK"):
    # 跳过 — 已知面值陷阱
    print(f"   ⏭️ {token_symbol} 代币面值陷阱：标称 ${listed_amount} 实际 ≈ $0.xx")
    continue
```

### 长期（架构级）
- 将 DeepSeek API 调用移到独立 cron job，不共享 300s 窗口
- 使用本地 LLM（llama.cpp）做代码生成，完全消除网络延迟不确定性
