# Bounty Claim Pattern — 非可执行 Bounty 检测

## 问题

Rustchain 生态中的 "RTC Bounty Claim" Issue 是奖励申领单，不是可执行的 Bounty。扫描脚本会将其列为新候选，导致浪费分析周期。

**示例**: Rustchain-bounties #13099 (2026-06-04)
- 标题: "RTC Bounty Claim - 63 PR Reviews + 35 Emoji Reactions"
- 正文: 列出 63 个 PR review + 35 个 emoji reaction
- 总价: 43.05 RTC（占总供应量的权重奖励）
- 标签: `needs-human`, `gate-processed` — 已通过 gate 审核
- **结论**: 贡献者已完成 PR review 工作，正在申领奖励。不应视为可执行的开发 Bounty。

## 检测模式

### Title 模式
```python
import re

BOUNTY_CLAIM_PATTERNS = [
    r"^\s*RTC\s+Bounty\s+Claim",         # "RTC Bounty Claim - ..."
    r"^\s*Bounty\s+Claim",                 # "Bounty Claim - ..."
    r"Bounty\s+Claim\s+for\s+",            # "Bounty Claim for ..."
]
```

### Body 模式
- 以 `## RTC Bounty Claim` 或类似 Markdown 标题开头
- 包含 `Wallet Address:` (Solana/Stellar base58)
- 包含 PR 编号列表（格式如 `#13097, #13095, #13094` 或 `Round 1 - repo (N PRs):`）
- 包含表情反应计数（如 `Emoji Reactions (35 reactions = 11.55 RTC)`）
- 总 RTC 计算（如 `Total: 43.05 RTC`）

```python
def is_bounty_claim(issue):
    title = (issue.get("title") or "").lower()
    body = (issue.get("body") or "").lower()
    
    # Title patterns
    if re.search(r"^rtc\s+bounty\s+claim", title) or re.search(r"^bounty\s+claim", title):
        return True
    
    # Body patterns
    if body.startswith("## rtc bounty claim") or body.startswith("## bounty claim"):
        return True
    
    # Combined signature: wallet address + PR numbers + total RTC
    has_wallet = "wallet address" in body
    has_pr_list = bool(re.search(r"#\d{4,5}", body))  # 4-5 digit PR numbers
    has_total = bool(re.search(r"total.*?rtc", body, re.IGNORECASE))
    
    if has_wallet and has_pr_list and has_total:
        return True
    
    return False
```

### Labels 检查
Rustchain-bounties 的 claim Issue 通常有以下 label 组合：
- `needs-human` — 需要人工审核
- `gate-processed` — 已经过自动 gate 处理

如果 Issue 同时有这两个 labels 且标题不含技术描述（fix/feat/docs/refactor 等），很可能是 claim 而非 Bounty。

## 影响

| 指标 | 值 |
|------|-----|
| 每个 mis-detected claim 浪费的脚本周期 | ~2-5s (API 调用来验证) |
| 如果进入 auto-execute 的浪费 | ~3-5 min (fork + AI 生成 + PR) |
| 可用的手动搜索过滤 | 扫描输出中 `RTC Bounty Claim` Issue 直接忽略 |
