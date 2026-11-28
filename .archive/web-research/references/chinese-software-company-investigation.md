# Chinese Software Company Investigation — Worked Example: 陪诊呗

## Target
- **Software**: 陪诊呗 (professional medical companion service platform)
- **Developer claim**: 黄杰 (Huang Jie) — user saw this name associated with the software
- **Goal**: Confirm developer identity, find company registration, assess operating status

## Data Sources Accessed

### 1. Official Website
- URL: `https://www.peizhenbei.com/`
- Title: 陪诊呗 - 专业医疗陪诊服务平台
- ICP: 赣ICP备18000137号-14
- Copyright: 2017-2026
- Company claim on site: 江西陪诊呗科技有限公司
- Address: 江西省南昌市红谷滩区VR产业基地4B栋13楼
- Phone: 400-682-2006
- Email: peizhenbei@peizhenbei.com

### 2. DuckDuckGo HTML Search (most reliable search engine from this env)
- URL: `https://html.duckduckgo.com/html/?q=陪诊呗`
- Fetcher: `scrapling.fetchers.Fetcher.get()` via Scrapling venv
- Result: Found 爱企查 link, iOS App Store link, Sina News articles, script home download page, Zhihu articles
- Key: DuckDuckGo HTML mode bypasses the CAPTCHA blocks that affect Baidu, Bing, Sogou, and Google

### 3. 爱企查 (Baidu Enterprise Database)
- URL: `https://aiqicha.baidu.com/company_basic_35618122538157`
- Data found:
  - 法定代表人: 罗静 (Luo Jing)
  - 注册资本: 100万(元)
  - 实缴资本: 25.4万(元) — only 25% paid in
  - 成立日期: 2017-09-20
  - 曾用名: 南昌蘑楚街电子商务有限公司
  - 统一社会信用代码: 91360125MA369XU759
  - 企业类型: 有限责任公司(自然人投资或控股)
  - 经营状态: 开业
  - 融资: 天使轮
  - 地址: 江西省南昌市红谷滩区九龙大道1177号绿地国际博览城JLH603-D03地块4#商业办公楼1315室
  - 知识产权: 24注册商标, 9软件著作权

### 4. iOS App Store
- URL: `https://apps.apple.com/cn/app/陪诊呗/id6503242498`
- Extraction via Scrapling Fetcher + regex on `developerName`:
  ```python
  import re
  dev = re.findall(r'"developerName":\s*"([^"]*)"', html)
  # Returns: ['杰 黄', ...]
  ```
- Also via meta description: `<meta name="apple:description" content="在 App Store 下载"杰 黄"的"陪诊呗"...">`
- **Conclusion**: Developer = "杰 黄" = 黄杰 (Huang Jie) — confirmed individual developer

### 5. Sina News Articles
- **2024-12-24 funding article**: `https://news.sina.cn/sx/2024-12-24/detail-ineapwes8484259.d.html`
  - Source: 点财网 (press release distributor)
  - Claims: 数百万天使轮融资, from a 健康管理公司
  - Notes the then-company name: 南昌蘑楚街电子商务有限公司 (before rename)
  - Mentions sub-brand: 掌无际
- **2025-12-17 industry article**: `https://news.sina.com.cn/sx/2025-12-17/detail-inhcazqc2248435.shtml`
  - Confirms company rename: 江西陪诊呗科技有限公司 (原名: 南昌蘑楚街电子商务有限公司)
  - Claims: 全网下载量突破1000万, #1 in app store rankings, 中国平安 insurance partnership

### 6. Wayback Machine
- URL: `https://web.archive.org/web/20250518163220/https://www.peizhenbei.com/`
- May 2025 snapshot copyright: "2026 南昌蘑楚街电子商务有限公司" — confirms company rename happened between May-Dec 2025

### 7. Script House Download Page (脚本之家)
- URL: `https://www.jb51.net/softs/991904.html`
- Version: v2.4.3 安卓手机版
- Developer listed: 南昌蘑楚街电子商务有限公司

## Investigation Workflow Summary

1. DuckDuckGo HTML search → discover official sites + app store + news
2. Scrapling Fetcher → extract data from each source
3. Cross-reference developer identity across platforms
4. Track company name changes through Wayback Machine + news articles
5. Assess financial strength via 注册资本 vs 实缴资本
6. Synthesize findings with risk indicators

## Cross-Reference Table

| Source | Developer | Legal Person | Company Name | Notes |
|--------|-----------|-------------|--------------|-------|
| App Store | 杰 黄 (黄杰) | — | — | Individual Apple dev account |
| 爱企查 | — | 罗静 | 江西陪诊呗科技有限公司 | Corporate registration |
| 脚本之家 | — | — | 南昌蘑楚街电子商务有限公司 | Old company name |
| Sina 2024 | — | — | 南昌蘑楚街电子商务有限公司 | Pre-rename |
| Sina 2025 | — | — | 江西陪诊呗科技有限公司 | Post-rename, confirmed |
| Official site | — | — | 江西陪诊呗科技有限公司 | Current branding |

## Risk Signals Identified
1. Legal representative ≠ developer — suggests founder uses family/partner registration
2. 实缴资本 only 25.4% of 注册资本 — thin capitalization
3. "数百万" angel round — typically ¥200-400万, modest for national expansion claims
4. "1000万下载量" — unverifiable claim, potentially inflated
5. No disclosed revenue or profitability data

## Tools Used
- `scrapling.fetchers.Fetcher.get()` — primary HTTP fetcher (always unset proxy env vars first)
- `p.get_all_text()` — extract clean text from response
- `p.html_content` — raw HTML for regex extraction
- `re.findall(r'"developerName":\s*"([^"]*)"', html)` — App Store JSON-LD mining
- `re.findall(r'<meta[^>]*>', html)` — meta tag extraction
- Wayback Machine API: `https://archive.org/wayback/available?url=<domain>`
