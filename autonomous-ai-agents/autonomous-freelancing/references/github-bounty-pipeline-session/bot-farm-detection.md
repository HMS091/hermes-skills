# Bot 农场检测 & PR 竞争检查

## 🚨 实施状态：文档已就绪，代码未实现

**2026-06-03 确认**: 以下所有代码已完整设计并在此文档中说明，但尚未写入 `smart_bounty_search.py` 和 `do_bounty.py`。

**实际影响**: 当脚本找到 `xevrion-v2/agent-playground` 的 10 个 $50 候选时，所有 10 个在脚本报告的 `comments=0-1` 状态和外部的几分钟内，已经被其他 bot 提了 PR。因为脚本不检查已有 PR，这些执行全部被浪费——fork + AI 分析 + DeepSeek API 费用，全部白费。

**使用者注意**: 在代码实现之前，每发现一批新目标，使用者需要手动检查是否有已存在的 PR 再决定是否执行。

## 背景

2026-06-03: xevrion-v2/agent-playground 的 10 个 $50 Bounty 全部在几分钟内被其他 bot 提了 PR。
搜索脚本报告 `comments=0-1`，等我们开始执行时 PR 已经存在。所有评论者都是 bot。

## 需要在 smart_bounty_search.py 中添加的代码

### 1. 检查已有 PR

在 `check_repo_active()` 之后、调用 `do_bounty.py` 之前添加：

```python
def has_existing_pr(token, owner, repo, issue_num):
    """检查 Issue 是否已有 open PR 被提交"""
    try:
        q = f"repo:{owner}/{repo}+type:pr+%23{issue_num}"
        data = gh(token, f"https://api.github.com/search/issues?q={q}&per_page=3")
        for item in data.get("items", []):
            if item.get("state") == "open":
                pr_url = item.get("pull_request", {}).get("html_url", item["html_url"])
                print(f"   ⚠️ 已有 PR: {pr_url}")
                return True
        return False
    except Exception as e:
        print(f"   ⚠️ PR 检查失败: {e}")
        return False  # 保守起见：检查失败就继续执行
```

### xevrion-v2 实战验证 (2026-06-03)

**场景**: `smart_bounty_search.py` 找到 `xevrion-v2/agent-playground` 的 10 个 $50 AI-friendly 候选，全部 `comments=0-2`。

**脚本判断**: 通过所有过滤器 → 执行第一个 #15 "Implement infinite sequence iterator" → PR #100 成功提交 ✅

**但随后发现**: 其余 9 个全部已有 open PR：

| Issue | 金额 | 脚本报告评论 | 实际已有PR |
|-------|------|-------------|-----------|
| #14 Improve PI calculation | $50 | 2 | PR #76 |
| #11 Unit tests leaderboard | $50 | 1 | PR #74 |
| #13 Unit tests UI Button | $50 | 2 | PR #73 |
| #12 Unit tests user routes | $50 | 2 | PR #75 |
| #10 API route TODO | $50 | 3 | PR #72 |
| #9 Body size limit | $50 | 3 | PR #69 |
| #8 Health check | $50 | 1 | PR #68 |
| #7 Error handling | $50 | 2 | PR #71, #93 |
| #6 Input validation | $50 | 1 | PR #70, #84 |
| #5 Prisma comments | $50 | 1 | PR #65 |

**关键时间线**: 搜索和脚本执行大约差 2-3 分钟，全部 9 个在这几分钟内被其他 bot（KHHH2312, rebel117, vumgg, mr-magaia 等）抢占。如果有 PR 竞争检查，脚本只会做 #15（运气好没被抢），不会列其他 9 个为候选。

**结论**: PR 竞争检查是最高优先级的代码实现。

### 2. Bot 农场检测

```python
def is_bot_farm(token, repo_full_name, issue_num):
    """检测仓库是否 bot 对战平台——检查该 repo 已有 PR 是否都是 [agent] 格式"""
    try:
        q = f"repo:{repo_full_name}+type:pr+is:open"
        data = gh(token, f"https://api.github.com/search/issues?q={q}&per_page=10")
        prs = data.get("items", [])
        if len(prs) < 3:
            return False  # PR 太少，无法判断
        
        # 看 PR 标题是否全是 [agent] 前缀
        agent_prefix_count = sum(1 for p in prs if p.get("title", "").startswith("[agent]"))
        ratio = agent_prefix_count / len(prs) if prs else 0
        
        if ratio > 0.7:
            print(f"   ⚠️ Bot 农场检测: {ratio:.0%} 的 PR 是 [agent] 格式，跳过")
            return True
        return False
    except:
        return False
```

### 3. 修改主循环 + 记录已跳过原因

```python
# 在 candidates 循环中，check_repo_active() 成功后加：

# 检查是否已有 PR
if has_existing_pr(token, target["repo"].split("/")[0], 
                   target["repo"].split("/")[1], 
                   target["url"].split("/")[-1]):
    print(f"   ⏭️ 已有 PR，跳过")
    continue

# 检查是否 bot 农场
if is_bot_farm(token, target["repo"]):
    print(f"   ⏭️ Bot 农场，跳过")
    continue
```

## 额外: [agent] PR 前缀检测（xevrion-v2 信号）

xevrion-v2/agent-playground 的所有竞品 PR 标题都以 `[agent]` 开头（如 `[agent] Fix: Add unit tests for user routes`）。这是一个强信号——人不会这样写 PR 标题。

```python
import re

def is_agent_bot_farm(token, repo_full_name, issue_num):
    """
    检查同一仓库的其他 issue 的 PR 是否都是 [agent] 格式。
    返回 True = 这是 bot 对战平台，跳过整个仓库。
    """
    try:
        # 查该 repo 最近 10 个 open PR
        q = f"repo:{repo_full_name}+type:pr+is:open"
        data = gh(token, f"https://api.github.com/search/issues?q={q}&sort=created&per_page=10")
        items = data.get("items", [])
        if len(items) < 3:
            return False  # PR 太少，不够判断
        
        agent_count = sum(1 for p in items if str(p.get("title", "")).startswith("[agent]"))
        ratio = agent_count / len(items)
        
        if ratio >= 0.5:  # 超过一半的 PR 是 [agent] 格式
            print(f"   🚨 Bot 农场检测: {agent_count}/{len(items)} PR 是 [agent] 格式 ({ratio:.0%})")
            print(f"     特征: 全部 PR 由 bot 提交，非真实 Bounty 平台")
            return True
        return False
    except Exception as e:
        print(f"   ⚠️ Bot 农场检测失败: {e}")
        return False
```

## 需要在 do_bounty.py 添加的检查

```python
def check_pr_exists_before_fork(token, owner, repo, issue_num):
    """放在 fork 之前，避免浪费 API quota"""
    try:
        q = f"repo:{owner}/{repo}+type:pr+%23{issue_num}"
        data = gh(token, f"https://api.github.com/search/issues?q={q}&per_page=3")
        for item in data.get("items", []):
            if item.get("state") == "open":
                print(f"   ⏭️ 已有 PR #{item['number']}，跳过执行")
                return True
    except:
        pass
    return False
```
