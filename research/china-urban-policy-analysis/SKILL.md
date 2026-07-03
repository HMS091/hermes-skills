---
name: china-urban-policy-analysis
description: Analyze Chinese State Council (国务院) and ministerial policy documents related to urban development, land redevelopment, low-utility land (低效用地), shantytown renovation (棚户区改造), demolition/relocation (拆迁), and urban renewal financing. Extract actionable strategies for project acceleration and funding.
trigger: "User shares a gov.cn URL of a policy document (国发/国办发/住建部文件) related to urban renewal, land policy, demolition, or real estate, and asks for analysis of how it affects their project."
tags: [china, policy, urban-renewal, real-estate, land-redevelopment, government]
---

# Chinese Urban Policy Analysis

Analyze State Council and ministerial policy documents to extract actionable intelligence for urban redevelopment projects. The typical user scenario: a company has a project included in low-utility land redevelopment planning, but local fiscal constraints are blocking demolition/relocation.

## Workflow

### Phase 1: Fetch the Document

gov.cn URLs do NOT have Cloudflare protection — direct curl works:

```bash
curl -s --connect-timeout 15 "https://www.gov.cn/zhengce/content/202605/content_7070539.htm" -o /tmp/policy.html
```

**Important**: The raw HTML content is NOT in a clean `<div class="article">` wrapper. Use regex-based tag stripping on the entire `<body>`.

### Phase 2: Extract Full Text

```python
import re

with open('/tmp/policy.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove all HTML tags
text = re.sub(r'<[^>]+>', '\n', html)
text = re.sub(r'&nbsp;', ' ', text)
text = re.sub(r'\n+', '\n', text)
lines = [l.strip() for l in text.split('\n') if l.strip()]
```

### Phase 3: Identify Chapter Structure

Extract chapter/section titles for the overall framework:

```python
chapters = []
for line in lines:
    if re.match(r'^[一二三四五六七八九十]+、', line) or \
       re.match(r'^（[一二三四五六七八九十]+）', line):
        chapters.append(line)
```

### Phase 4: Search for Key Keywords

Always search for these keywords — they are the most valuable signals for real estate/urban renewal projects:

| Keyword | What It Gets You |
|---------|-----------------|
| 低效用/低效用地 | Direct mention of your project type |
| 棚户/拆迁/征收 | Demolition and relocation policy basis |
| 专项债券/专项债 | Most important funding source: local government special bonds |
| REITs | Exit/financing through infrastructure REITs |
| 社会资本 | Private capital participation framework |
| 中央预算/中央财政 | Direct central government funding |
| 盘活存量 | Land/asset revitalization |
| 合作/联合开发 | PPP / multi-party development models |
| 税费减免 | Tax benefits |
| 银团贷款 | Syndicated loan options |
| 项目资本金 | Special bonds as project capital (key leverage tool) |

Search with a loop:

```python
keywords = ['低效用', '棚户', '拆迁', '征收', '专项债券', 'REITs', 
            '社会资本', '中央预算', '中央财政', '盘活', '税费减免',
            '银团贷款', '项目资本金', '合作改造']
for kw in keywords:
    for line in lines:
        if kw in line:
            print(f"[{kw}] {line}")
```

### Phase 5: Build the Analysis Report

Structure the report in Chinese with these sections:

#### 1. 文件概要
- Full title and document number (e.g., 国发〔2026〕12号)
- Release date
- Brief description of scope

#### 2. 与你项目的关联点
Describe how the policy connects to the user's specific situation (project in low-utility land planning, blocked by local fiscal constraints).

#### 3. 核心利好信号

Present as a table with columns: 利好来源 | 文件原文 | 对你的意义

Key patterns to identify:
- **资金渠道拓宽**: New funding mechanisms (special bonds, central budget, social capital)
- **审批加速**: Streamlined approval processes
- **土地政策**: Land use flexibility, transition periods, tax relief
- **优先级提升**: Whether the document prioritizes certain project types (D-class housing, shantytowns, etc.)

#### 4. 核心问题诊断

Analyze the user's bottleneck (e.g., "地方财政没钱 → 拿不出征收补偿款") against what the policy offers.

#### 5. 解决方案分级排序

Rank solutions by feasibility:

| 方案 | 核心政策依据 | 可行性 | 操作路径 |
|-----|------------|--------|---------|
| 申报专项债 | 最关键的条款引用 | ⭐⭐⭐⭐⭐ | Step-by-step |
| 引入社会资本 | 相关条款 | ⭐⭐⭐⭐ | ... |
| 申请中央预算 | ... | ⭐⭐⭐ | ... |
| 申报试点/示范 | ... | ⭐⭐⭐ | ... |

#### 6. 实操建议

Actionable next steps the user can take, ordered by immediacy:
- "尽快让项目进入省级专项债项目库"
- "主动联系地方住建局，以'落实国务院XX号文'为由推动项目纳入年度实施计划"
- etc.

### Phase 6: Add Quantitative Assessment

Always add a summary table like this:

| 维度 | 评价 |
|-----|------|
| 政策信号强度 | ⭐⭐⭐⭐⭐ |
| 资金渠道拓展 | ⭐⭐⭐⭐ |
| [specific topic] | ⭐⭐⭐ |
| 短期实效性 | ⭐⭐⭐ |

## Pitfalls

- **gov.cn does NOT have Cloudflare** — unlike blockchain explorers, government.cn sites can be curled directly. Do not waste time trying browser tools.
- **Document text is in the raw HTML body** — do NOT look for `<article>`, `<div class="content">`, or similar selectors. Strip ALL tags from `<body>`.
- **章/节 numbering**: Chinese government documents use 一、二、三... for chapters and （一）（二）（三）... for sections. Use regex, not substring matching, to find structure.
- **政策信号 vs 实操执行**: A policy may state something favorably but leave implementation to provinces/cities. Note the distinction — national-level "允许" vs local-level "落实" is a material gap.
- **时效性**: New policies (e.g., 2026年5月) are positive signals but need 3-6 months to cascade to provincial implementation rules. Advise on timing.
- **User language**: User is Chinese-speaking. Deliver the full analysis in Chinese. Use concise tables and bullet points. Do NOT ask "should I continue?" — just complete the full analysis.
- **Proactive delivery**: Do not ask for permission to proceed. Collect all data and deliver the complete analysis in one response.
