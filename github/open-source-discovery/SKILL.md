---
name: open-source-discovery
description: "Find and evaluate open-source projects on GitHub for reuse/modification — search strategies, quality assessment, red-flag detection, README verification, and project comparison. For users who want ready-made code to modify and deploy."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [github, search, evaluation, open-source, clone, forking]
    related_skills: [codebase-inspection, github-repo-management, web-research]
prerequisites:
  commands: [curl]
---

# Open-Source Discovery & Evaluation

Find and evaluate open-source projects (clones, templates, boilerplates) on GitHub for reuse, modification, and deployment. Covers the full pipeline: search → screen → verify → compare → recommend.

## When to Use

- User asks "find me an X clone on GitHub"
- User wants "something I can modify and use" as a ready-made solution
- User wants to evaluate open-source alternatives for a product/feature
- User is looking for starter code or boilerplates in a specific tech stack

## 1. Search Strategy — Multiple Keyword Angles

Don't rely on a single search query. Use at least 3 complementary approaches:

### Keyword Variants

```bash
# Primary — direct match
curl -s -H "Accept: application/vnd.github+json" \
  "https://api.github.com/search/repositories?q=ONLYFANS+clone&sort=stars&order=desc&per_page=30"

# Secondary — related terms
curl -s -H "Accept: application/vnd.github+json" \
  "https://api.github.com/search/repositories?q=fans+creator+subscription+content+monetize&sort=stars&order=desc&per_page=10"

# Tertiary — tech-stack specific (if user has a preference)
curl -s -H "Accept: application/vnd.github+json" \
  "https://api.github.com/search/repositories?q=ONLYFANS+clone+laravel&sort=stars&order=desc&per_page=10"

# Quaternary — broad platform search
curl -s -H "Accept: application/vnd.github+json" \
  "https://api.github.com/search/repositories?q=creator+subscription+platform+django&sort=stars&order=desc&per_page=10"
```

### Tips for Better Results
- Start broad, narrow by tech stack if user specifies
- Try different keyword orderings
- If results are sparse, use broader terms (e.g. "subscription platform" instead of "onlyfans clone")
- Check the `total_count` field — if < 5 meaningful results, try again with different keywords

## 2. Initial Screening — Parse the Search Results

Parse JSON output to get a quick overview:

```bash
curl -s -H "Accept: application/vnd.github+json" \
  "https://api.github.com/search/repositories?q=KEYWORD&sort=stars&order=desc&per_page=30" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'总结果数: {data[\"total_count\"]}')
for i, repo in enumerate(data.get('items',[]), 1):
    print(f\"{i}. {repo['full_name']} ⭐{repo['stargazers_count']} 🍴{repo['forks_count']} {repo['language'] or 'N/A'}\")
    print(f\"   {repo['description'] or '无描述'}\")
    print(f\"   更新: {repo['updated_at'][:10]} | License: {repo['license']['spdx_id'] if repo.get('license') else '无'}\")
    print(f\"   {repo['html_url']}\")
"
```

### Key Screening Criteria (in priority order)

| Signal | Green Flag | Red Flag |
|--------|-----------|----------|
| **⭐ Stars** | >20 (meaningful community validation) | <5 (possibly abandoned/incomplete) |
| **🍴 Forks** | >0.5× stars ratio (others building on it) | 0 forks (no one else uses it) |
| **🕐 Last Updated** | Within 6 months (actively maintained) | >2 years (abandoned) |
| **📜 License** | MIT, Apache-2.0, GPL (can use/modify) | No license (legal grey area) |
| **📦 Size** | >200KB (has actual code) | <100KB (might be config-only/skeleton) |
| **📝 Description** | Detailed, specific | Vague, keyword-stuffed, salesy |

## 3. README Verification — Check Claims vs Reality

ALWAYS verify a project's README claims by checking its actual file structure:

```bash
# Check if the repo actually has source code
curl -s "https://api.github.com/repos/OWNER/REPO/contents/" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if isinstance(data, list):
    for item in data:
        print(f\"{item['type']:5s} {item['name']:30s} {item.get('size', 0):>8} bytes\")
else:
    print('Error:', data.get('message', str(data)))
"
```

### Red Flags to Watch For
- **README is huge (20KB+) but repo has only config files** → Likely a commercial sales page, not actual code
- **Claims "production-ready" but has <10 files and <100KB** → Almost certainly incomplete
- **Has wrong/empty file structure** → The directory structure doesn't match what README describes
- **Missing requirements.txt, package.json, or Dockerfile** → Hard to set up
- **Only at root level, no subdirectories (app/, src/, etc.)** → Skeleton/empty repo

### Check Tech Stack Compatibility

```bash
# Python projects — check requirements
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/requirements.txt" | head -30

# Node/JS projects — check package.json
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/package.json" | python3 -c "
import json, sys; d=json.load(sys.stdin); print(d.get('description','')); print('Deps:', len(d.get('dependencies',{}))); print('DevDeps:', len(d.get('devDependencies',{})))
"
```

## 4. Deep Dive — Check Metadata and Community Health

```bash
curl -s "https://api.github.com/repos/OWNER/REPO" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"仓库: {data.get('full_name')}\")
print(f\"描述: {data.get('description')}\")
print(f\"⭐ {data.get('stargazers_count')} | 🍴 {data.get('forks_count')} | 👁 {data.get('watchers_count')}\")
print(f\"语言: {data.get('language')}\")
print(f\"创建: {data.get('created_at')[:10]}\")
print(f\"更新: {data.get('updated_at')[:10]}\")
print(f\"默认分支: {data.get('default_branch')}\")
print(f\"大小: {data.get('size')} KB\")
print(f\"开源许可: {data.get('license', {}).get('spdx_id', '无') if data.get('license') else '无'}\")
print(f\"Topics: {data.get('topics', [])}\")
print(f\"Issues: {data.get('open_issues_count')}\")
print(f\"有Wiki: {data.get('has_wiki')}\")
"
```

## 5. Read the Actual README

```bash
# Try main branch first, then master
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/README.md" | head -200
# If 404
curl -s "https://raw.githubusercontent.com/OWNER/REPO/master/README.md" | head -200
```

Check for:
- **Installation instructions** — are they complete and working?
- **Demo credentials** — admin login info = good sign
- **Docker support** — docker-compose.yml = easy deploy
- **Documentation** — Sphinx/ReadTheDocs links = well-maintained
- **Screenshots** — visual proof it works

## 6. Comparison Table for the User

Structure your output as a ranked comparison table:

| Rank | Project | ⭐ | Tech Stack | License | Completeness | Notes |
|------|---------|---|------------|---------|-------------|-------|
| 🥇 | name | N | Python/Django | MIT | Full src | Best option |
| 🥈 | name | N | Laravel | None | Config-only | Red flag |

For each, include:
- ✅ Pros
- ⚠️ Cons/Red flags
- 💡 Recommendation (can they use it? what needs modification?)

## 7. Solopreneur / 一人公司 Evaluation Framework

When the user is a **solo operator or small team** looking for low-maintenance open-source software they can run with minimal daily attention, apply this additional filter layer on top of the standard evaluation.

### 7.1 Solopreneur-Specific Criteria (优先级从高到低)

| 标准 | 绿色信号 | 红色信号 |
|------|---------|---------|
| **🕐 每日维护时间** | 装好即忘，只需回邮件处理工单 | 需要定期升级/调优/重启 |
| **🔧 部署难度** | Docker一键启动，或纯PHP/MySQL $5 VPS能跑 | 需要Elasticsearch/Redis/GPU/S3等外部依赖 |
| **💻 硬件需求** | 512MB-2GB内存，NAS/共享主机可用 | 需要MongoDB+ES+Kafka等多服务 |
| **📧 邮件即工单** | 直接回复邮件=回复工单，无需打开后台 | 只能在Web后台操作 |
| **🌐 中文支持** | 内置简体/繁体中文 | 只有英文，需自己翻译 |
| **📊 Open Issues** | <50个（项目稳定bug少） | >200（坑多，单人维护负担重） |
| **🔄 最近推送** | 3个月内活跃推送 | 超过1年未更新 |
| **📜 许可证** | MIT/AGPL/GPL-2.0 可自由使用 | 无许可证或无商业条款 |

### 7.2 Search Strategy for Solopreneur Tools

Run at least 4 complementary searches:

```bash
# 1. Direct category search
curl -s "https://api.github.com/search/repositories?q=customer+support+helpdesk+ticketing&sort=stars&order=desc&per_page=30"

# 2. Lightweight/self-hosted angle
curl -s "https://api.github.com/search/repositories?q=self-hosted+helpdesk+simple+lightweight&sort=stars&order=desc&per_page=15"

# 3. Specific tech-stack angle (PHP/Laravel easiest for solo)
curl -s "https://api.github.com/search/repositories?q=helpdesk+ticketing+laravel&sort=stars&order=desc&per_page=15"

# 4. Alternative-name angle (Zendesk/Intercom alternatives)
curl -s "https://api.github.com/search/repositories?q=intercom+alternative+customer+support&sort=stars&order=desc&per_page=15"
```

### 7.3 Solopreneur Deep-Dive Checklist

```bash
# 1. Check deployment complexity
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/docker-compose.yml" | head -40

# 2. Check Chinese language support
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/README.md" | grep -i 'zh_\|中文\|chinese\|lang' | head -5

# 3. Check issue-to-star ratio (stability proxy)
#    If open_issues > stars/10 = potentially buggy
curl -s "https://api.github.com/repos/OWNER/REPO" | python3 -c "
import json,sys;r=json.load(sys.stdin)
stars=r['stargazers_count'];issues=r['open_issues_count']
ratio=issues/stars*100
status='⚠️ HIGH' if ratio > 10 else '✅ OK'
print(f'⭐{stars}  📋{issues} issues ({ratio:.1f}%) {status}')
"

# 4. Check email-to-ticket workflow (key for solopreneurs)
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/README.md" | grep -i 'email\|mail\|imap\|pop3\|inbox' | head -5

# 5. Count external services in docker-compose.yml
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/docker-compose.yml" | grep -c 'image:'
```

### 7.4 Solopreneur Comparison Output Format

```
## 📊 候选方案对比

| 项目 | ⭐ | 技术栈 | 部署难度 | 每日维护 | 中文 | 稳定性 |
|------|----|--------|---------|---------|------|-------|
| 🥇 **推荐** | N | PHP+MySQL | 低(Docker) | ~0分钟 | ✅ | ✅ 仅21 issues |
| 🥈 备选 | N | Ruby+Rails | 中(需Redis) | ~5分钟 | ❌ | ⚠️ 456 issues |
| ❌ 排除 | N | Java+ES | 高(多服务) | ~15分钟 | ✅ | ❌ 1K+ issues |

### 推荐理由（结论先行）
➡️ **结论：首选X** — 理由。

### 为什么不选其他
- 项目A: 技术栈太重，超出单人维护能力
- 项目B: issues过多，修复负担大
```

### Pitfalls for Solopreneur Evaluation

1. **Star count alone is misleading** — Chatwoot ★33,688 but requires Ruby+Rails+Redis+Postgres and has 1,223 issues. Freescout ★4,382 runs on $5 shared hosting with 21 issues. For solo ops, low issues + simple stack > high stars + complex stack.
2. **"Production-ready" ≠ "solopreneur-ready"** — Enterprise systems need ongoing maintenance. Solo operators need "set and forget" solutions.
3. **Email integration is the #1 solopreneur feature** — Less time in dashboard = better. Projects without email-to-ticket require daily login.
4. **Docker != simple** — A compose file with 5 services (app+db+cache+queue+search) is harder than single PHP app+MySQL. Count services.
5. **Check repo redirects** — Some repos have moved (e.g. freescout-helpdesk → freescout-help-desk). API returns "Moved Permanently" for old URLs.

## 8. Ecosystem Landscape Survey — Cross-Category Project Discovery

When the user wants a **broad survey** of open-source projects across multiple categories/domains (e.g., "find me the top AI tools in every category"), use this pattern.

### When to Use

- User says "search GitHub for star > X in categories A, B, C, D..."
- User wants a technology landscape overview / competitive radar
- User wants to know "what's the best open-source tool for X category"
- User is evaluating which tools to install/integrate

### Workflow

#### Step 1: Define Categories
List specific categories and examples the user cares about. Search one category at a time.

#### Step 2: Search via GitHub Topics (Primary Method)

GitHub Topics pages are the most efficient way to find top projects in a domain:

```bash
# Navigate to: https://github.com/topics/<topic-name>?o=desc&s=stars
# Examples of topic names:
#   llm-inference, retrieval-augmented-generation, vector-database,
#   ai-agents, coding-assistant, ocr, speech-recognition, text-to-speech,
#   data-extraction, ai-chat, ai-tools, llm, large-language-models
```

Each topic page shows the top projects sorted by stars. Extract: project name, star count, description, language, tech stack tags.

#### Step 3: Set a Star Threshold

Use a consistent star threshold (e.g., >20,000) to filter meaningful projects from the topic page. The topic page already sorts by stars, so you can stop scrolling once results fall below the threshold.

#### Step 4: Verify Key Projects via GitHub API

For each project you'll report, verify stats via API:

```bash
curl -s "https://api.github.com/repos/OWNER/REPO" | python3 -c "
import json,sys;r=json.load(sys.stdin);print(f'Stars: {r[\"stargazers_count\"]}')
print(f'Forks: {r[\"forks_count\"]}');print(f'Open Issues: {r[\"open_issues_count\"]}')
print(f'Language: {r[\"language\"]}');print(f'License: {r.get(\"license\",{}).get(\"spdx_id\",\"N/A\")}')
print(f'Updated: {r[\"pushed_at\"][:10]}')
"
```

Also check HuggingFace for model downloads/likes if the project has model weights there.

#### Step 5: Check Installation Status

After identifying relevant projects, check if any are already installed in the current environment:

```bash
pip list 2>/dev/null | grep -iE "vllm|sglang|docling|..."
which ollama vllm sglang 2>/dev/null
docker ps --format "{{.Names}}" 2>/dev/null
```

#### Step 6: Categorize into Priority Matrix

For each category, create a priority matrix:

| Priority | Project | Stars | Installation | Notes |
|----------|---------|-------|-------------|-------|
| 🔴 High | name | N | pip install | Directly useful |
| 🟡 Medium | name | N | Docker | Useful but heavy |
| 🟢 Low | name | N | Cloud API | Saas alternative |

### Output Format

Present findings per category with:

```markdown
### 🏷️ Category Name

| 项目 | Stars | 语言 | 说明 |
|------|-------|------|------|
| **owner/repo** | **~Nk** | Lang | Description |

**集成建议：** Which projects to prioritize, what they add.
```

End with an aggregate summary table and specific installation recommendations.

---

## 9. Single-Tool Deep-Dive Evaluation

When the user asks to **investigate a specific open-source tool** — how it works, what hardware it needs, is it any good — use this comprehensive evaluation pattern.

### Workflow

#### Phase 1: Basic Reconnaissance

```bash
# Get core metadata
curl -s "https://api.github.com/repos/OWNER/REPO" | python3 -c "
import json,sys;r=json.load(sys.stdin)
print(f'Stars: {r[\"stargazers_count\"]} | Forks: {r[\"forks_count\"]}')
print(f'Description: {r[\"description\"]}')
print(f'Language: {r[\"language\"]} | License: {r.get(\"license\",{}).get(\"spdx_id\",\"N/A\")}')
print(f'Created: {r[\"created_at\"][:10]} | Last push: {r[\"pushed_at\"][:10]}')
print(f'Open Issues: {r[\"open_issues_count\"]}')
print(f'Topics: {r.get(\"topics\",[])}')
"
```

#### Phase 2: README Mining

Fetch and analyze the full README for:
- **Core features** (headline + key features section)
- **Installation instructions** — how hard is it?
- **Hardware requirements** — any mention of GPU, VRAM, RAM, disk?
- **Base model dependencies** — does it need a large base model? (e.g., Wan2.1 14B)
- **Quick start commands** — actual runnable examples
- **Demo links / screenshots** — does the thing actually work?
- **Citation / tech report** — academic paper link for deeper understanding

```bash
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/README.md" | head -200
# If 404, try master branch
```

#### Phase 3: GitHub Issues Mining — The Real Story

GitHub Issues reveal the truth that READMEs hide. Focus on:

**Hardware/VRAM issues** — look for keywords: vram, memory, gpu, 显存, 显卡, 配置, requirement:
```bash
curl -s "https://api.github.com/repos/OWNER/REPO/issues?state=all&per_page=100&sort=reactions" \
  | python3 -c "
import json,sys;data=json.load(sys.stdin)
for i in data[:20]:
    if isinstance(i,dict):
        t=i['title'].lower()
        if any(k in t for k in ['vram','memory','gpu','显存','显卡','配置','requirement']):
            print(f'#{i[\"number\"]} [{i[\"state\"]}] 👍{i.get(\"reactions\",{}).get(\"total_count\",0)} | {i[\"title\"][:100]}')
"
```

**Bug/quality issues** — look for keywords: error, bug, problem, fix, crash, issue:
```bash
# Check total open issue count — if > 50 for a < 10k star project, that's a red flag
```

**Performance/speed concerns** — look for keywords: speed, slow, acceleration, 速度, fast:
```bash
# Check highly-upvoted issues (comments or reactions > 5)
```

**Key technique: Sort Issues by reactions for community pain points:**
```bash
curl -s "https://api.github.com/repos/OWNER/REPO/issues?state=all&per_page=30&sort=reactions" \
  | python3 -c "
import json,sys;data=json.load(sys.stdin)
for i in data:
    if isinstance(i,dict):
        print(f'#{i[\"number\"]} [{i[\"state\"]}] 👍{i.get(\"reactions\",{}).get(\"total_count\",0)} | {i[\"title\"][:100]}')
"
```
High reaction counts (👍 > 3) on open issues = community pain points. READMEs show best case; Issues show real problems.

**Example from this session:** InfiniteTalk Issue #130 (4👍): "到底什么机器能跑通呀 4张4090 显存直接爆掉了" — revealed a multi-GPU bug that the README didn't mention.

**Cross-reference Issues with hardware type** — check for issues mentioning: `vram`, `memory`, `gpu`, `显存`, `显卡`, `OOM`, `out of memory`, `crash`, `killed`. These reveal the actual VRAM floor vs the advertised minimum.

#### Phase 4.5: HuggingFace / Model Hub Check (Adoption Signal)

If the project has model weights on HuggingFace, check these signals:

```bash
curl -s "https://huggingface.co/api/models/OWNER/MODEL" | python3 -c "
import json,sys;r=json.load(sys.stdin)
print(f'Downloads: {r.get(\"downloads\",\"?\")}')
print(f'Likes: {r.get(\"likes\",\"?\")}')
"
```

**Spaces count as adoption proxy:** On the HF model page, note how many Spaces use the model. 14+ Spaces = active real-world community. This is independent of GitHub stars — a 7k⭐ project with 14 Spaces has more actual deployment evidence than a 20k⭐ project with 0 Spaces.

**Vendor/team background:** Extract the organization/team name from the HF model card or GitHub org page. Corporate backing (e.g., MeiGen-AI = 美团 Meituan) adds reliability. Solo/academic projects may have different sustainment risk. Note the distinction.

Also check the HF model tree for quantized variants:
```bash
curl -s "https://huggingface.co/api/models/OWNER/MODEL/tree/main" | python3 -c "
import json,sys; data=json.load(sys.stdin)
for f in data:
    if any(k in f['path'] for k in ['fp8','int8','gguf','awq']):
        print(f['path'])
"
```
Quantized variants = lower VRAM possible. Their presence or absence tells you if the community cares about consumer-GPU accessibility.

#### Phase 5: Hardware Requirement Estimation

Use this heuristic table to estimate requirements based on model size:

| Model Size | Minimum VRAM | Recommended VRAM | Typical GPU |
|-----------|-------------|-----------------|-------------|
| < 1B params | 2-4 GB | 4 GB | RTX 3060 |
| 1-3B params | 4-6 GB | 8 GB | RTX 4060 |
| 7-8B params | 8-12 GB | 16-24 GB | RTX 4090 |
| 13-14B params | 16-24 GB | 40-80 GB | A100 80GB |
| 30B+ params | 32+ GB | 80+ GB | A100/H100 |
| Multiple models stacked | Add per-model | Add per-model | Multi-GPU |

**Case study — Talking video generation (InfiniteTalk/Meituan, 2025):** Base model (Wan2.1-I2V-14B = 14B params) + audio encoder (wav2vec2) + control module = 1.5× to 2× base VRAM.
- 480P resolution: ~40-50 GB VRAM (RTX PRO 6000D 84GB ✅, single A100 80GB ✅)
- 720P resolution: ~60-70 GB VRAM (RTX PRO 6000D 84GB ⚠️ tight, dual A100 ✅)
- FP8 quantized: ~16-18 GB VRAM (RTX 4090 24GB ✅)
- Multi-person + 720P: ~80+ GB VRAM (only H100/A100 multi-GPU)
- **Consumer GPU reality check:** The single-user 4090 24GB can only run the FP8 quantized 480P mode. Standard 480P needs A100 80GB. Don't trust "consumer GPU compatible" claims without checking the actual model size.

**Stacked-model heuristic:** When a tool combines multiple models (base + encoder + control adapter + upscaler), add VRAM per-model. Total = base_model_vram × (1 + 0.3×N_adapters + 0.2×N_encoders).

**Consumer GPU reality check:** Projects with "14B" in the name almost never run well on consumer GPUs (4090 24GB). Look for:
- Quantized versions (FP8/INT8) that reduce VRAM by 30-50%
- Community forks with lower-VRAM optimizations (e.g., Wan2GP for InfiniteTalk)
- "Low VRAM mode" flags in the code (e.g., `--num_persistent_param_in_dit 0`)

#### Phase 6: Pros/Cons & Community Sentiment

Synthesize from all sources:

**Pros sources:**
- README claims (verify with screenshots/demos)
- Technical paper / academic backing
- Active development (recent commits)
- Community forks and adaptations
- Low VRAM workarounds provided

**Cons sources:**
- GitHub Issues complaints (especially high-reaction ones)
- Missing features (check TODO list vs promises)
- Complex installation (multiple framework requirements)
- Stale base model (e.g., still on Wan2.1 when Wan2.2 is out)
- Multi-GPU bugs (common with newer frameworks)
- Color shift / quality degradation over long generations

### Output Format

Structure as a comprehensive report:

```markdown
## 🔍 Project Name Investigation

### 📌 项目概况
| Field | Value |
|-------|-------|
| Stars | ~N |
| License | X |
| Team | Organization |
| Type | Core capability description |

### 🎯 核心功能
- Feature 1: description
- Feature 2: description

### 💻 硬件配置要求
| Config | GPU | VRAM | Quality |
|--------|-----|------|---------|
| 🟢 Recommended | A100/H100 | X GB | 720P |
| 🟡 Minimum | RTX 4090 | X GB | 480P/FP8 |

### 👍 优点
### 👎 缺点
### 🌟 一句话判断
```

---

## References

See `references/ai-llm-ecosystem-survey-202606.md` for the comprehensive AI/LLM open-source landscape survey across 8 categories.
See `references/customer-support-systems-202606.md` for the solopreneur customer support system survey (Freescout, Chatwoot, etc.).

## Pitfalls

1. **Don't trust READMEs blindly** — always check actual file structure. A 21KB README with 56KB of config files is a sales page, not open-source code.
2. **Stars can be misleading** — a project with 56 stars from 2021 using Django 3.1 might be worse than a 4-star project with Django 5.0 + MIT license.
3. **Always check License** — no license = legal uncertainty for commercial use.
4. **Browser not required** — GitHub API via curl works without Chrome. Only use browser if you need to view rendered README or UI screenshots.
5. **Rate limiting** — unauthenticated GitHub API: 60 requests/hour. If doing heavy searching, consider if time constraints matter.
6. **Forks may be better** — a well-maintained fork of an abandoned project can be more valuable than the original.
7. **Topic pages beat keyword search** for broad category surveys — GitHub Topics are curated and already sorted by stars. Use `https://github.com/topics/<topic>` instead of raw search for faster results.
8. **GitHub Issues are the real review system** — READMEs show the best case, Issues show the pain points. Always check high-reaction issues for hardware/performance/bug complaints.
9. **Check HF Spaces count** — number of Spaces using a model is a proxy for real-world adoption, independent of GitHub stars.
10. **Don't over-trust star count for hardware-heavy AI projects** — a 7k⭐ project might need A100 GPUs; a 700⭐ project might run on a laptop. Check actual requirements.
11. **Browser navigation can time out on heavy GH pages** — when browsers fail, fall back to curl + GitHub API which is more reliable from restricted environments.

12. **Browser search engines (Google/Bing) may block or return irrelevant results** — for niche AI tool research, Google may present CAPTCHA and Bing may return unrelated content (e.g., a boat launch page for "Coventry Lake" when searching "InfiniteTalk"). When this happens, pivot to:
    - **GitHub Issues** as the primary user review source (the README is marketing, Issues are truth). Sort by reactions to find community pain points. High-reaction open issues (👍 > 3) reveal real problems the README hides.
    - **HuggingFace model card** for model-based projects (download counts, Spaces count, quant variants available)
    - **GitHub API** for direct metadata queries (avoids page rendering entirely) — metadata + README + issues + forks all available via API
    - **Alternative search strategy** — search the tool name directly on GitHub (not via search engines), use GitHub Topics pages which are curated, or read the project's own citation/tech report links
    - Do NOT keep retrying different search engines — it wastes time and tokens. Pivot immediately upon detecting a block.

13. **Search engine block detection** — quickly verify if a search engine returned useful results:
    - Google: redirect to `google.com/sorry/index` = CAPTCHA block. Response time ~1s with no results.
    - Bing: results unrelated to query (e.g., searching "InfiniteTalk AI video generation" returns "Coventry Lake Boat Launch") = search quality degradation.
    - DuckDuckGo HTML: response <15KB with no `result__a` class elements = CAPTCHA/anomaly page.
    - If any of these are detected, abandon search engines for this session and use GitHub Issues + HF model cards as the primary source.

14. **Hardware-constrained environments** — when installing tools for evaluation, always check:
    - `nvidia-smi` for GPU availability (if missing, no GPU acceleration)
    - `docker ps` for Docker daemon (container-in-container may not have /var/run/docker.sock)
    - Python version compatibility (3.13 may break some packages)
    - Memory pressure with `free -h` before large model downloads
