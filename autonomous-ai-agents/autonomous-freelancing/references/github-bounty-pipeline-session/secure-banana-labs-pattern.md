# SecureBananaLabs Bug Bounty 特殊规则

## 仓库概况

- **Stars**: 150 | **Forks**: 475 | **Open issues**: 3120
- **活跃度**: 高 (持续推送，活跃维护)
- **技术栈**: JavaScript
- **奖励范围**: $10 - $700+

## ⚠️ 关键限制：Issue Creator Restriction

SecureBananaLabs 的一个独特规则：**许多高额 Bounty Issue 仅限 Issue 创建者（Creator）尝试解决。** 这是通过 Issue body 中的一段固定文本声明的：

```
This issue is limited only to the creator of this issue.
This means that only the issue author can attempt to solve this issue.
If you would like to work on it, please create another issue with the same
contents and refer to issue #743 for more information.
```

### 含义

| 场景 | 能否直接执行 |
|------|------------|
| Issue 创建者是你自己 | ✅ 可以 |
| Issue 创建者是别人（最常见） | ❌ 不能直接 Fork + PR |
| 你创建了一个内容相同的副本 Issue | ✅ 可以，但需要先创建 Issue |

### 绕过策略

如果发现一个 SecureBananaLabs 的高额 Bounty（如 $700），但不是你创建的：

1. **自查**：确认该 Issue 是否标记了 creator-restriction 文本
2. **创建副本**：用相同内容创建一个新的 Issue，并在描述中引用 #743
3. **等待**：新的 Issue 会创建后你就是 creator，可以开始执行
4. **执行**：按照 normal pipeline Fork → 代码 → PR

### 检测方法

在 `do_bounty.py` 的预检步骤中，扫描 Issue body 是否包含：
```python
RESTRICTION_KEYWORDS = [
    "limited only to the creator",
    "only the issue author can attempt",
    "refer to issue #743"
]

def is_creator_restricted(issue_body):
    body = (issue_body or "").lower()
    return any(kw.lower() in body for kw in RESTRICTION_KEYWORDS)
```

如果检测到限制且当前用户不是该 issue 的 creator → 可以选择：
- **自动创建副本 Issue**（需要 `POST /repos/{owner}/{repo}/issues` 权限）
- **或跳过**，记录到历史，等待下一个周期

## 标签体系说明

SecureBananaLabs 使用一致化标签：

| 标签 | 含义 |
|------|------|
| `💎 Bounty` | 确认有赏金的 Issue |
| `$700` | 美元金额标签（数字随金额变化） |
| `AI agent friendly` | 适合 AI 自动完成的 Issue |
| `bug` | Bug 修复类 |
| `bug bounty` | Bug Bounty 类 |
| `good first issue` | 入门级任务 |

## 竞争情况

- 很多 SBL Issue 的新建速度为每天数十个
- 2026-06-03 当天就产生了数十个新 Issue（#3908-#3934）
- 这些当天 Issue 的 comments=0，无竞争
- 但大多数是新用户创建的、带有 creator-restriction 的 Issue（无标价）
- 🆕 **重要发现 (2026-06-03)**: $430 和 $780 级别的部分 Issue **没有** creator-restriction，且带有 `AI agent friendly` 标签。如 #1783 ($430, 3 comments)、#2849 ($780, 6 comments)、#2845 ($780, 6 comments)。这些属于可直接执行的目标。
- 🆕 **$1k+ Issue 可能仍有价值？**: #2885 "#1.2k Calculate the exact value of PI" 有14条评论但未标注 restriction，但可能是个玩笑 Issue。

## 检测流程修正

**Previous assumption**: 所有高额 SBL Issue 都是 creator-restricted.
**New finding**: 只有 body 中含有以下关键词的才是受限的：

```python
RESTRICTION_KEYWORDS = [
    "limited only to the creator",
    "only the issue author can attempt",
    "refer to issue #743"
]
```

$430 和 $780 的 Issue **不一定**包含这些文本。每次遇到 SBL 的 Issue 都必须实际扫描 body，不能靠金额过滤。**推荐**：在 smart_bounty_search.py 中针对 SBL 仓库添加一步 body 扫描，未受限的直接列入可执行列表，不用等到 do_bounty.py 阶段。

## 决策建议

- 高额（$700+）的 Issue **部分**是 creator-restricted（如 #1426 $700 有限制文本）
- 但 **$430 和 $780 级别的 Issue 可能没有 creator-restriction**（如 #1783 $430、#2849 $780 等均为公开可执行）
- creator-restriction 的判断必须以 body 文本扫描为准，不能仅凭金额大小
- **无标价或小额** → 直接跳过，不值得两轮（创建 Issue + 执行）的 token 成本
- **creator 就是你自己** → 正常执行 pipeline
