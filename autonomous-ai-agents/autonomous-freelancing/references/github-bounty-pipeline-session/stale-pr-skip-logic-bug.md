# Stale PR Skip Logic Bug — 2026-06-04 发现

## 问题

`smart_bounty_search.py` 的 `check_existing_pr()` 在发现任何 open PR 引用该 issue 时就标记为 SKIP。但未合并的旧 PR（7天以上、无 review、被 CI 忽略）不应阻挡新提交。

## 受影响的 Bounty

### Warpspeed (warpspeedopen-source/warpspeed-bounties)

| Issue | 金额 | 旧 PR | 旧 PR 提交者 | 旧 PR 日期 | 新 PR (6月4日) | 状态 |
|-------|------|-------|-------------|-----------|---------------|------|
| #9 音频笔记 | $750 | #17 | lqkhanh295 | 5月29日 | #53 | 未合并，已停滞7天 |
| #7 笔记锁定 | $660 | #11 | lqkhanh295 | 5月29日 | #54 | 未合并，已停滞7天 |
| #6 图片预览 | $660 | #14 | lqkhanh295 | 5月29日 | #55 | 未合并，已停滞7天 |
| #5 图片编辑 | $660 | #15 | lqkhanh295 | 5月29日 | #56 | 未合并，已停滞7天 |
| #3 投票创建 | $440 | #29 | kejuunuy | 5月31日 | #57 | 未合并，已停滞4天 |
| #2 收件箱UI | $330 | #10 | lqkhanh295 | 5月28日 | #58 | 未合并，已停滞7天 |

**关键观察**:
1. 旧 PR 全部未合并，无任何 review 活动
2. 6月4日新竞争者提交了完全相同的 6 个 PR
3. 脚本连续 4+ 个扫描周期 (18:33 至 02:49) 都因旧 PR 阻挡而零候选
4. 旧 PR 提交者 lqkhanh295 的 5 个 PR 全部是 5月28-29日批量提交的

## 根因

`check_existing_pr()` 的简化逻辑:
```python
def check_existing_pr(token, owner, repo, issue_num):
    q = f"repo:{owner}/{repo}+type:pr+%23{issue_num}+state:open"
    results = gh_search(token, q).get("items", [])
    return len(results) > 0  # ❌ 任何 open PR 就 block
```

### MergeOS (mergeos-bounties/mergeos)

| Issue | 金额 | PR | 状态 | 脚本标记 | 实际情况 |
|-------|------|----|------|---------|---------|
| #8 USDT 支付 | 1000 MRG | #121 | **关闭未合并** | SKIP (有PR) | ❌ 脚本错了 — PR 被拒绝，issue 仍开放 |
| #7 PayPal | 1000 MRG | #145 | 开放未合并 | SKIP (有PR) | 正确 — 仍有活跃 PR |
| #3 AI评估 | 1500 MRG | #206 | **开放未合并** | DONE | ❌ 脚本错了 — 脚本标记为"done"但 PR 从未合并 |
| #13 登录响应式 | 500 MRG | #207 | **开放未合并** | DONE | ❌ 脚本错了 — 同 bug |

## 修复方案

参见 SKILL.md 中的 **Pitfall 31: Stale Open PR Blocks Valid New Submissions**。

核心逻辑变更：
1. 检查 PR 的 `updated_at` — 超过 7 天未更新 → 视为废弃
2. 检查 PR 的 `mergeable` 状态 — 不可合并 → 视为废弃
3. 检查 PR 是否有 review — 无 review 活动 → 视为废弃
4. 对于 `CLOSED + NOT MERGED` 的 PR — 直接忽略，issue 仍开放

## 涉及的其他 Bug

### MergeOS "done" 标记错误

脚本将 MergeOS PR #206 和 #207 标记为 "done"（PR #206 - done），但这两个 PR 从未合并。PR #206 在 6月3日创建，仍然开放。PR #207 同样在 6月3日创建，仍然开放。

**原因**: 脚本的 PR 状态检查可能只检查了 PR 是否存在，未区分 `merged=True` 和 `state=closed`。PR #206 的 `state=closed` 可能被误读为 "已合并"。

**正确逻辑**:
```python
if pr.get("merged_at") or pr.get("merged") is True:
    status = "merged"
elif pr.get("state") == "closed":
    status = "closed_unmerged"  # 关键: 关闭 ≠ 合并
else:
    status = "open"
```
