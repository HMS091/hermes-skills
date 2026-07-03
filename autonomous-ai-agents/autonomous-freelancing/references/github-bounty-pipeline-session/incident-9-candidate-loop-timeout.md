# 第9次超时分析 — 候选人循环无上限 (2026-06-03 18:05)

## 现象

smart_bounty_search.py 在 300s 定时器超时后被 SIGKILL。这次与之前 8 次不同：脚本运行正常，创建了 PR #340，但开始处理第2个候选人后被杀死。

## 时间线

| 时间 | 事件 | 耗时 |
|------|------|------|
| 18:05:00 | 搜索阶段（21个API查询） | ~20s |
| 18:05:20 | 筛选 288→186→找到多个候选人 | ~3s |
| 18:05:23 | 开始处理 imDarshanGK/localmind#321 | 0s |
| 18:05:23~18:06:53 | Fork + clone + AI分析 + commit + push + PR | **~90s** |
| 18:06:53 | ✅ PR #340 创建成功 | — |
| 18:06:55 | 开始处理 imDarshanGK/localmind#320 (第2个) | 0s |
| 18:06:55~18:10:00 | Fork + clone + AI分析进行中... | — |
| 18:10:00 | **SIGKILL** — cron 300s 超时 | — |

## 根因

`smart_bounty_search.py` 的循环 `for target in candidates:` 没有任何候选人数量限制。每个 do_bounty.py 约需 90s，300s - 30s(搜索) = 270s，理论最多处理 3 个。但实际中 DeepSeek API 高峰期 120s、git clone 大仓库 90s+ 都可能拖慢，实际只能安全处理 1-2 个。

## 竞争窗口丢失

第2个候选人（localmind#320 "Add contributor onboarding guide"）在第1个 PR 提交后开始执行。如果第1个处理期间其他 bot 抢了第2个，则竞争窗口永久丢失。

## 修复

在 candidate 循环前添加计数器限制：

```python
MAX_CANDIDATES_PER_TICK = 2
processed = 0
for target in candidates:
    if processed >= MAX_CANDIDATES_PER_TICK:
        print(f"   ⏸️ 达到本轮上限 ({MAX_CANDIDATES_PER_TICK}个)，剩余 {len(candidates)-processed} 个等待下轮")
        break
    # ... existing processing code ...
    processed += 1
```

## 学习

1. **每个候选人处理时间不可预测** — DeepSeek API 延迟、git clone 大小、git push 速度都是变量
2. **宁可保 2 个成功也不要 0 个成功** — 之前 8 次超时是 0 成功，这次是 1 成功 1 丢
3. **历史记录防止重复但竞争窗口是单次** — 一旦时间窗口到，该 tick 内的后续候选就丢了
