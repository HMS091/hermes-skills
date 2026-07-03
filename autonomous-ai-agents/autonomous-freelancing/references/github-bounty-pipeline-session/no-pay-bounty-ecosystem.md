# 无支付 Bounty 标签生态系统 (Bounty-Label-No-Pay)

## 问题定义

许多 GitHub 仓库使用「bounty」作为 Issue 标签但不提供任何实际支付机制。这些 Issue 通过脚本的「+bounty」搜索就会命中，但它们不是真实 Bounty——它们是**错误信号**。每次扫描中，这类 Issue 占「AI-friendly」结果的大多数（~60-70%）。

## 识别特征

### 1. 社区文档/教程项目（最普遍）

**特征**:
- 仓库主题：文档、教程、社区指南
- Issue 内容：编写说明、故障排除、贡献指南
- 无标签或只有 `documentation`、`enhancement`、`help wanted`
- 仓库通常 < 500 stars，维护者 1-2 人

**2026-06-03 扫描实例**:

| 仓库 | Issue 类型 | 判断理由 |
|------|-----------|---------|
| imDarshanGK/localmind | macOS 安装故障排除、贡献者指南、发布说明 | 文档类需要社区帮助，非商业 | 
| all-aboard-ohio/communication-guides | 铁路宣传指南、数据可视化说明 | 非营利组织社区文档 |
| Pushkarini579/retina | API 文档实现 | 个人项目文档需求 |
| mohitkumhar/business-ai-agent | 100+ 个 docstring 添加 Issue | 每个 Issue 加一个函数的 docstring，批量 bot 生成的代码质量需求 |

**判断方法**: 检查 repo 的 `description` 和 `topics`，以及 Issue 提出的内容是否为「写文档」「加注释」「做教程」。如果是 → 跳过。

实际脚本输出表现为：全部「无标价」，且 body 内容为请求社区贡献（不是有现金赏金的 Bounty）。

### 2. 游戏/爱好项目 Issue 追踪

**特征**:
- 非商业游戏或社交项目
- Issue 是规则澄清或 UI 反馈，不是 Bounty
- 创建者使用「bounty」词汇只是因为 GitHub 有这个标签

**2026-06-03 实例**:
- johnchampaign/star-wars-rebellion (#108, #109): 桌游规则澄清
- shipshitgames/deadlane (#5): FPS 游戏系统实现

**判断方法**: 查看是否有任何付费历史（标签中是否有 `$`、`bounty` 与金额同列）。游戏仓库通常只使用「bounty」作为增强标签。

### 3. 趋势追踪/聚合机器人

**特征**:
- 自动抓取趋势 GitHub 项目并发布为 Issue
- Issue 内容：「发现趋势项目 X (N stars)」，附链接
- 无任何代码需求

**2026-06-03 实例**:
- clowlove/Harmes-House (#335): `⭐ 发现趋势项目: airecon (637⭐)` — 仅仅是趋势通知

**判断方法**: Issue 标题含 `发现趋势项目`、`Trending`、`Daily trending`、`⭐`。全部是自动生成的聚合通知。直接跳过。

### 4. 安全文档/笔记仓库

**特征**:
- 安全类文档汇总或个人笔记
- Issue 是安全简报或产品提案，不是 Bug Bounty

**2026-06-03 实例**:
- coreintentdev/ZYNTHIO_MASTER_DOCS (#252): 「Grok/xAI Abuse + Cloudflare Security Insights Hardening」— 安全笔记，非赏金
- qazbnm456/awesome-web-security (#185): 「Link health report」— 链接可用性报告

**判断方法**: 查看 repo 名是否含 `docs`、`notes`、`awesome-`、`MASTER_DOCS`。这类仓库使用 Issue 做笔记/报告，无 Bounty 可用。

### 5. 个人/实验性项目

**特征**:
- 明显是学生或个人实验
- Issue 数量少（< 20），仓库很少更新
- 使用「bounty」标签是为了好玩或学习

**2026-06-03 实例**:
- vansh-09/BountyScout (#12): 「14 New Opportunities found」— 该仓库本身就是在追踪 Bounty，不是 Bounty 来源
- supperjumpin/supperjumpin (#122, #123): PRD 产品需求文档

**判断方法**: 检查仓库 owner 是否为个人（vs 组织）且仓库描述与 Bounty 无关。这些项目的 Issue 是 PRD 或追踪自己项目的需求，不是付钱请人做。

## 综合判断流程

```python
def is_no_pay_bounty(repo_full_name, issue_title, issue_body, repo_description):
    """
    判断 Issue 是否只是借用了「bounty」标签但没有任何实际付款。
    返回 True = 无支付可能，跳过。
    """
    text = f"{issue_title} {issue_body}".lower()
    repo_text = f"{repo_full_name} {repo_description}".lower()
    
    # (1) 趋势/聚合通知
    if re.search(r'(发现趋势|trending|⭐.*stars?|daily trend)', text):
        return True
    
    # (2) 文档类 Issue
    if re.search(r'(add (doc|troubleshoot|guide)|javadoc|docstring|contributor.*guide|release.?note)', text):
        # 检查是否真的有金额
        if re.search(r'\$\s*\d+', text):
            return False  # 有金额可能是真赏金
        return True  # 无金额 → 社区贡献需求
    
    # (3) 游戏/爱好仓库
    hobby_keywords = ['board game', 'game', 'rpg', 'clarification', 'rule question']
    if any(kw in repo_text for kw in hobby_keywords):
        return True
    
    # (4) awesome-/notes/docs 仓库
    if re.search(r'(awesome-|notes|docs|master_docs)', repo_full_name, re.I):
        return True
    
    return False  # 不确定 → 不跳过
```

## 对 Pipeline 的影响

如果将此检查加入 `smart_bounty_search.py` 的 filter 链中，在搜索阶段即可过滤掉约 60-70% 的「假 Bounty」结果。这会大幅减少最终报告的长度，并使真正的 Bounty（即使是零星的）更容易被发现。

## 和已知过滤器的关系

| 过滤器 | 针对的假 Bounty 类型 | 重叠 |
|--------|---------------------|------|
| Bot 农场检测 (bot-farm-detection.md) | xevrion-v2 式 bot 对战平台 | 无重叠 |
| Token 价值验证 (token-value-verification.md) | 标大额但实际无价值的代币 | 无重叠 |
| **本文件 (No-Pay 生态)** | 使用「bounty」标签但不付款的项目 | 无重叠 |
| Creator-restriction (secure-banana-labs-pattern.md) | 金额很高但仅创建者可操作的 Issue | 无重叠 |

四个过滤器覆盖了四种不同的虚假信号。加上基础过滤器（金额、AI友好、时效、仓库活跃），自动执行的命中率可从 <1% 提升到 ~5-10%（估算）。
