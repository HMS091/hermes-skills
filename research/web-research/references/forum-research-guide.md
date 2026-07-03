# Forum Research & Community Crawling Guide

Detailed procedural knowledge for deep-dive research into technical forums (NodeBB, Discourse, XenForo, Flarum) and Chinese content platforms (Bilibili).

## Forum Platform Identification

- **NodeBB**: Page source contains `"csrf_token":"<hex>"` in config JSON, URLs like `/api/categories`, `/api/search?term=`
- **Discourse**: URLs like `/t/{slug}/{id}`, `/c/{category}/{id}`
- **XenForo**: URLs like `/forums/`, `/threads/`, `?_xfToken=`
- **Flarum**: URLs like `/d/{id}-{slug}`, `/api/forum`
- **Custom**: Check for CSS class patterns and script tags

Check accessibility: `curl -sL -o /dev/null -w "%{http_code} %{url_effective}" <url>`

## NodeBB Registration Flow (3-Step)

### Username & Password Conventions
- Use natural Chinese names (e.g., 小明学AI, 老王聊科技). Avoid system-like names. Keep 2-16 chars.
- Password: at least 6 chars, human-chosen looking (e.g., `LearnAI2025!`), not `P@ssw0rd123`.

### Step-by-Step

1. **GET `/register`** — save cookies to file (`/tmp/<site>_cookies.txt`). Extract the CSRF token from TWO sources:
   - Hidden input: `name="_csrf" value="<hex>"`
   - Page config JSON: `"csrf_token":"<hex>"` (more reliable, grep directly from raw HTML)

2. **POST `/register`** with: `username`, `password`, `password-confirm`, `_csrf`. Expected response: `{"next":"/register/complete"}` with HTTP 200.

3. **GET `/register/complete`** — this page has its own form with `csrf_token` (NOT `_csrf`). Extract the new `csrf_token` from config JSON again.

4. **POST `/register/complete`** with: `email` (leave blank — optional), `gdpr_agree_data=on`, `gdpr_agree_email=on` (both checkboxes required), and `csrf_token`.

**Verification**: Check the site homepage — if the username appears instead of "游客", registration succeeded. If POST `/register/complete` returns 404, it was already submitted — check the homepage directly.

### Gotchas
- **emailPrompt caveat**: Check `emailPrompt` in page config JSON. If `emailPrompt=1`, the site WILL require email on the complete page (though users can often provide a disposable one or skip if left blank).
- **CSRF token name difference**: On `/register`, the field is `_csrf`. On `/register/complete`, it's `csrf_token`. Don't mix them up.
- **Save credentials**: Use `memory(action='add', target='memory', content='<site> account: username=X, password=Y')` after successful verification.
- **Cookies**: Store to a file (`/tmp/<site>_cookies.txt`) for reuse across curl calls.

## NodeBB Search & Topic Extraction

### API Endpoints

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `GET /api/categories` | List all categories | JSON with slugs, descriptions, CIDs |
| `GET /api/category/<cid>` | Topic listing for a category | JSON with topics array |
| `GET /api/search?term=<urlencoded>` | Search posts | JSON with `posts[]` array (each: content, topic.title, user.username, pid, tid) |
| `GET /api/topic/<tid>?page=N` | Topic content with pagination | JSON with `posts[]` (up to ~20 per page) |
| `GET /api/users?page=N&perPage=50` | User list (newest first) | JSON with users array |
| `GET /api/user/uid/<uid>/posts` | User's posts | May return empty due to NodeBB permission scoping |
| `GET /api/user/uid/<uid>/topics` | User's topics | May return empty for non-admin viewing another user |

### Search Strategy
- Search each GPU model name as a separate term AND search cross-comparison terms ("vs", "对比", "还是")
- For Chinese text, URL-encode: `$(python3 -c 'import urllib.parse; print(urllib.parse.quote("中文词"))')`
- The search is scoped to posts by default; results include parent topic metadata
- To browse: `GET /api/categories` lists everything

### Content Extraction
- Post content is HTML, not plain text. Clean: `re.sub(r'<[^>]+>', '', content)`
- Or pipe to `python3 -c "import sys,json; ..."` to parse JSON and print results

### Batch Topic Extraction (Critical for Efficiency)
Do ALL topic fetches inside a SINGLE `execute_code` call to avoid tool-call-iteration limits:

```python
from hermes_tools import terminal
import json

tids = [242, 315, 78, 193, 251]  # up to 12+ topics
for tid in tids:
    result = terminal(f"curl -sL -b /tmp/site_cookies.txt \"{BASE}/api/topic/{tid}?page=1\"")
    data = json.loads(result['output'])
    # parse posts
    import time; time.sleep(0.5)
```

Split into 2-3 `execute_code` blocks if you have 12+ topics or 50+ search terms.

## lcz.me Specific Knowledge

- **Site**: 抡锤者 — Chinese AI forum about local LLM deployment, hardware, agents
- **Key users**: terry (UID=1, admin), stakira, CHIA AN YANG, 张鑫磊 (UID=492)
- **Key categories**: CID=6 (AI硬件), CID=7 (LLM讨论区), CID=8 (AI音视频画图), CID=12 (AI Agent)
- **Registration**: username+password only, no email required. The `/register/complete` page shows an email field but it's optional — leave it blank.
- **No User-Agent blocking** or rate limiting observed
- **User search**: Iterate `/api/users?page=N&perPage=50` (up to 20 pages, ~1000 users, newest first)
- **User content**: `/api/user/uid/<uid>/posts` and `/api/user/uid/<uid>/topics`
- **Deep-drilling**: The most reliable way to find a user's posts is searching their username in the general search, then filtering results by `user.uid`
- **Reading full threads**: API pagination with `?page=N`. Each page returns ~20 posts. `postcount` field tells total posts.

## User Profiling from Forums

When asked about a specific user's "philosophy" or approach:

1. Get their profile: `/api/user/uid/<uid>`
2. Get their posts: `/api/user/uid/<uid>/posts` (may be empty — fallback to general search filtered by uid)
3. Get their topics: `/api/user/uid/<uid>/topics` (may also be empty)
4. Extract: hardware choices, software workflow, power management, learning path, unique tools
5. Present as a structured philosophy summary

## Bilibili Content Creator Research

### Finding Contact Info
1. **Search for the UP主**: 
   - `curl -s "https://api.bilibili.com/x/web-interface/search/all/v2?keyword=<NAME>"`
   - Or: `curl -sL "https://search.bilibili.com/upuser?keyword=<NAME>"`
   - Extract `space.bilibili.com/<UID>` from HTML

2. **Get profile info**: 
   - Space page API requires wbi signing (returns code -352). Use HTML scraping instead:
   - `curl -sL "https://space.bilibili.com/<UID>" -H "User-Agent: Mozilla/5.0"`
   - Extract meta description: `<meta name="description">` content attribute
   - Contains UP主签名, 联系方式, 商务合作渠道

3. **Payment/Pricing extraction**:
   - Use `/x/web-interface/view?bvid=<BVID>` via `curl -s` (NOT Python requests — triggers 412)
   - The `desc` field contains 收费标准, 微信公众号, contact info
   - Key grep terms: 免费, 收费, 手工费, 装机, 置换, 回收, 公众号, 微信, VX
   - Combine with search: `/x/web-interface/search/type?search_type=video&keyword=<UP主名>`
   - Note: 写配置 is typically free, but 装机手工费 is rarely listed — need to ask via 微信

4. **B站 API call notes**:
   - Always use `curl -s` not Python `requests`/`urllib` (B站 CDN TLS fingerprint blocks Python HTTP libs)
   - `x/web-interface/search/type?search_type=video` still works without wbi signing
   - `x/space/wbi/arc/search` and `x/space/acc/info` now return -403 from Docker IPs
   - Playwright can bypass 412 but is slow (3-5s/page) and still faces login overlays

### Consumer Evaluation (Assessing UP主 Reliability)
When user asks "is X reliable/trustworthy":

1. **Search engine**: In China-restricted environments, **搜狗搜索 (www.sogou.com)** is the most reliable alternative when Google/Bing/Baidu are blocked.
2. **Keyword combos** (priority order):
   - "UP主名" + 装机/服务 + 评价
   - "UP主名" + 靠谱/翻车/坑/骗
   - "UP主名" + 感谢 + 装机 (find customer testimonials)
   - "UP主名" + 抖音
3. **Word frequency**: Use regex to count positive/negative keyword frequency from Sogou search HTML results
4. **Judgment framework**:
   - B站官方签名写"注意马甲虫" → positive signal (has reputation worth faking)
   - 搜到"感谢XX装机" B站/抖音内容 → real customer testimonials
   - UP主主动送主机/做活动 → maintaining reputation
5. **Limitation**: Unauthenticated B站 comment scraping is impossible (strict anti-bot). Can only assess via search engine snippets.

### Playwright for Bilibili (When Curl Fails)

```python
from playwright.sync_api import sync_playwright
import os

# Always export proxy env vars BEFORE launching — Playwright browser is a separate process
os.environ['http_proxy'] = 'http://192.168.1.88:7890'
os.environ['https_proxy'] = 'http://192.168.1.88:7890'

p = sync_playwright().start()
browser = p.chromium.launch(headless=True, args=['--ignore-certificate-errors', '--no-sandbox'])
page = browser.new_page(ignore_https_errors=True)
page.goto("https://search.bilibili.com/all?keyword=<NAME>")
# Extract BVIDs, descriptions
```

**Key notes:**
- Playwright browser does NOT inherit in-process Python `os.environ` changes — set in the shell before launching the Python script
- Search page renders fine without login
- Video page shows title and ~20 lines of description without login
- Space page shows login overlay — only meta description is available
- Page load is 3-8s on Docker container (slow proxy); prefer curl API when they work
- Cannot get without login: full space page content, video comments, follower counts

## Reference Files (from forum-research consolidation)

- `references/bilibili-scraping.md` — Full Bilibili scraping reference with code examples, search strategies, Playwright setup, and API call patterns
- `references/local-llm-gpu-guide.md` — GPU comparison data for local LLM deployment (from forum threads)
- `references/gpu-comparison-2026-05-30.md` — Latest GPU benchmarks and pricing from forums
