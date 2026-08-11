# Eastmoney Search API — Chinese financial news (no proxy needed)

The environment ships `/opt/data/scripts/fetch_news.py`, which queries the Eastmoney search API.
This is the reliable news fallback when lightpanda/browser tools are down, and it works with a
direct connection (no proxy). Returns news sorted by time — excellent for same-day macro/market
roundups (美股收盘, 财经早餐, 早报) that bundle NVDA/TSLA/gold/oil/Fed data in one article.

## Usage

```bash
python3 /opt/data/scripts/fetch_news.py "英伟达" "特斯拉" "黄金"          # multiple keywords, prints date | title | content
python3 /opt/data/scripts/fetch_news.py "美联储" "美元指数" "美伊谈判 原油"
```

## API mechanics (as implemented in fetch_news.py)

- Endpoint: `https://search-api-web.eastmoney.com/search/jsonp?cb=cb&param=<urlencoded JSON>`
- param JSON:
  ```json
  {"uid":"","keyword":"<kw>","type":["cmsArticleWebOld"],"client":"web","clientType":"web",
   "clientVersion":"curr","param":{"cmsArticleWebOld":{"searchScope":"default","sort":"time",
   "pageIndex":1,"pageSize":8}}}
  ```
- Response is JSONP: strip leading `cb(` and trailing `)` before `json.loads`.
- Articles live at `data["result"]["cmsArticleWebOld"]`; fields: `title`, `date`, `content`, `url`.
- Titles/content contain `<em>` highlight tags — strip them.
- Headers needed: `User-Agent: Mozilla/5.0`, `Referer: https://so.eastmoney.com/`.

## Proven keyword groups for the briefing

| Topic | Keywords |
|-------|----------|
| NVDA | `英伟达`, `英伟达 RTX` |
| TSLA | `特斯拉`, `特斯拉 机器人 Optimus` |
| Gold | `黄金`, `黄金 美联储 降息` |
| Macro | `美联储`, `美元指数`, `美伊谈判 原油` |

## Gold-price recovery trick

When the gold API fails, the daily roundup articles (e.g. 东方财富财经早餐 / 美股收盘 posts) always
contain 伦敦现货黄金 and COMEX黄金期货 quotes plus 上金所 prices (元/克). Extract those and label
them 媒体口径 in the briefing footnote. Same trick gives 美元指数, WTI/布伦特 oil prices, and
CME FedWatch rate-hike probabilities — enough to fill the 宏观环境 section entirely from one or two
article batches.

## Gotchas

- Multiple sources in the same batch may disagree slightly (e.g. 现货金 4052 vs 4055, COMEX 4110 vs
  4113). Cite the value repeated by most articles and mention the range if it matters.
- The API returns the freshest articles first; same-day articles from 东方财富 are usually published
  within minutes of the US close (Beijing morning), which is exactly the cron run window.
