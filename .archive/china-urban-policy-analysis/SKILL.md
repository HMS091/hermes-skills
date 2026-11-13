---
name: china-urban-policy-analysis
description: Use when 核证中国房地产/土地政策传闻、分析部委文件影响、判断某市征收中地块能否出让。
trigger: "用户带来一条房地产/土地政策消息（尤其含'内部文件''要停''两年内不再批'类传闻）要求核实真伪；给出一份国务院/部委/地方政策文件（含 gov.cn 链接或文号）要求分析对项目的影响；或问某个具体城市在征收/拆迁阶段的地块能否继续挂牌出让。"
tags: [china, policy, urban-renewal, real-estate, land-redevelopment, government]
---

# Chinese Urban Policy Analysis

Analyze State Council and ministerial policy documents to extract actionable intelligence for urban redevelopment projects. The typical user scenario: a company has a project included in low-utility land redevelopment planning, but local fiscal constraints are blocking demolition/relocation.

## When to Use

三类入口，全部适用本技能：

- **核证传闻**：用户听到一条消息（常带"内部文件""要停""两年内不再批"），要求查有没有这回事、源文件在哪 → 走 Phase 0，且不能停在"纯属谣言"。
- **分析文件**：用户给一份国务院/部委/地方文件（gov.cn 链接或文号），问对项目有什么影响 → 走 Phase 1–6。
- **判定属地项目**：用户说某市 N 块地正在征收/拆迁，问还能不能挂牌出让、项目要不要停 → 走 Phase 7 + `references/housing-land-supply-control-rules.md`。

三类共同交付要求（用户已明确、不要退让）：**结论先行**、真实数据带来源与日期、**必须主动给负面风险与"能挂≠能卖"的判断**；中文输出，不得只报喜。

## Workflow

### Phase 0: 传闻核证与文件定位（用户说的是"我听说有个内部文件"时先做这一步）

用户通常不带链接，只带一句被转述的结论（例："两年内不再有新住宅开发项目，内部文件说的"）。顺序：

1. **拆解说法**：把传闻拆进"发文机关／文号／生效时间／适用范围"四个槽位。多数传闻这四个槽位全空——这本身就是信号。
2. **以文号为锚检索**：先按"机关 + 政策主题"搜到文号（形如 `自然资发〔20XX〕XX号`、`建房规〔20XX〕X号`、`国发〔20XX〕X号`），再用**文号本身**当查询词检索，命中率远高于用正文表述去搜。拿全文最快的路径是政府网站的**转载页**：部委门户 → 省级政府门户 → 市县级自然资源/住建局网站，这类页面带"索引号+文号+发文日期+全文"，比新闻稿权威、比门户首屏好抓。
3. **分层取证**，结论里逐层标注来源类型（可信度从高到低）：① 文件原文（政府网站全文页）→ ② 部委新闻发布会实录/司长原话 → ③ 权威媒体（新华社/央广/证券时报/财新/新京报）→ ④ 行业机构数据（中指院、克而瑞、普睿数智、券商研报）→ ⑤ 自媒体（头条号/网易号/公众号"XX看楼市"）。**第⑤层只用于定位传闻的表述形式，绝不作为依据。**
4. **找官方辟谣**：部委对误读通常在**当周**就开发布会澄清，检索"文号 + 解读／发布会／不等于"。
5. **反推传闻配方**（决定怎么向用户解释）：找齐下列原料，多半能完整还原——
   - 同向条款（如"新增建设用地原则上不用于经营性房地产开发"）
   - **反向条款被搬用**：同一文件里方向相反的数字，如给房企的土地款宽限"余款两年内缴清"被读成"两年内不许开发"
   - 机构预测（"预计未来两年供地维持低位"）
   - 券商测算（对开工量/土地成交的跌幅预测）
6. **不要停在"纯属谣言"**：核对用户描述的现象是否对应**另一条真实机制**（最典型：去化周期挂钩供地）。正确结论形态是"文件不存在，但你听到的X有另一条真政策来源 + 该来源的触发条件"——这比单纯辟谣有用得多。

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

### Phase 7: 判定地方项目能否继续（征收中的地块能否挂牌出让）

问题是"某市这N块地还能不能拆迁完挂牌出让"时，按此顺序判，不要用全国结论替代：

1. **先定城市，再写答案。** 可执行结论随城市去化周期档位翻转（见 `references/housing-land-supply-control-rules.md`）；拿到城市名之前写的全国层面长篇分析基本作废。
2. **定地块性质**：是"存量建设用地盘活"（旧城/城中村/棚改，城镇开发边界内既有建设用地）还是"新增建设用地"（农用地/未利用地转用）。前者不受"新增建设用地不用于经营性房地产开发"约束，后者受双重约束。
3. **查该市口径的去化周期档位**（>36个月 / 18–36个月 / <18个月），这直接决定新增商品住宅用地能否放行。
4. **区分"批准环节"与"成交环节"**：法规上征收批复→拆净→挂牌这条链不受辟谣类传闻影响；真正卡项目的是①去化周期档位限制供地、②增存挂钩（新增指标不得超过盘活存量面积）、③销售制度改革后的出让条件（自有资金购地、优先现房销售、土地款可分期）让房企不敢拿地。
5. **给"能不能卖出去"，不只给"能不能挂"**：查该市近月住宅用地成交与流拍、溢价率、出让金同比、房价同比。地挂出来零成交的城市，"政策允许"没有意义。
6. **时间压力反向提醒**：征地批准文件满两年未用地或未实施征地补偿安置方案会**自动失效**，所以项目方的时间压力是"要快"，不是"等政策"。

## Pitfalls

- **先确定城市再写长答案**：房地产/土地政策的可执行结论取决于**城市**（去化周期档位决定供地能否放行）。未拿到城市名就展开全国层面分析，等于写一半要重写；用户报出城市后按 Phase 7 重做属地判定，不要在主答案上打补丁。
- **省级口径 ≠ 市级口径，引用必须标层级**：省级通稿常称"全省去化周期连续处于合理区间"（由省会/核心城市拉高），同期同省非省会地市仍可能远超36个月。把省级表述当成某市的依据是硬错误；引用时写明"省级口径/市级口径"和数据来源机构。
- **反向条款是传闻的主要原料**：同一文件里方向相反的数字最容易被搬到谣言里（给企业的宽限被读成对企业的禁止）。核证时逐条比对传闻表述能否在原文找到字面对应，找不到字面对应基本就是拼接。
- **区分"文件不存在"与"现象不存在"**：辟谣只解决前者，用户真正要的是后者——务必回到"有没有另一条真机制"那一步。
- **gov.cn does NOT have Cloudflare** — unlike blockchain explorers, government.cn sites can be curled directly. Do not waste time trying browser tools.
- **Document text is in the raw HTML body** — do NOT look for `<article>`, `<div class="content">`, or similar selectors. Strip ALL tags from `<body>`.
- **章/节 numbering**: Chinese government documents use 一、二、三... for chapters and （一）（二）（三）... for sections. Use regex, not substring matching, to find structure.
- **政策信号 vs 实操执行**: A policy may state something favorably but leave implementation to provinces/cities. Note the distinction — national-level "允许" vs local-level "落实" is a material gap.
- **时效性**: New policies (e.g., 2026年5月) are positive signals but need 3-6 months to cascade to provincial implementation rules. Advise on timing.
- **User language**: User is Chinese-speaking. Deliver the full analysis in Chinese. Use concise tables and bullet points. Do NOT ask "should I continue?" — just complete the full analysis.
- **Proactive delivery**: Do not ask for permission to proceed. Collect all data and deliver the complete analysis in one response.

## 参考文件
- `references/guofa-2026-12-urban-renewal-key-clauses.md` — 国发〔2026〕12号城市更新关键条款摘录
- `references/housing-land-supply-control-rules.md` — 现行住宅用地供应管控规则集（新增建设用地用途限制、增存挂钩、去化周期挂钩供地分档、销售制度改革后的出让条件、征地批复时效）+ 城市级去化周期/房价/土地成交/出让公告数据源清单 + 库存口径陷阱
