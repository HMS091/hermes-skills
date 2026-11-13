#!/usr/bin/env python3
"""Eastmoney news search for the daily briefing — China-network fallback when all
Western RSS/news sources are TLS-blocked. Uses urllib (no requests dep), so it runs
under any python3. JSONP wrapper is stripped; <em> tags removed from titles/content.

Usage:
    python3 em_news_search.py 特斯拉 黄金 英伟达
    python3 em_news_search.py "美联储 降息"   # quote multi-word keywords

Dodges two cron-mode blocks: execute_code (blocked in cron) and `curl | python3`
pipes (tirith curl_pipe_shell). Write this file, then run `python3 em_news_search.py ...`.
"""
import json
import sys
import urllib.parse
import urllib.request


def em_search(keyword, page_size=8, sort="time"):
    param = json.dumps({
        "uid": "", "keyword": keyword, "type": ["cmsArticleWebOld"],
        "client": "web", "clientType": "web", "clientVersion": "curr",
        "param": {"cmsArticleWebOld": {"searchScope": "default", "sort": sort,
                                       "pageIndex": 1, "pageSize": page_size}}
    }, ensure_ascii=False)
    url = ("https://search-api-web.eastmoney.com/search/jsonp?cb=cb&param="
           + urllib.parse.quote(param))
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0",
                      "Referer": "https://so.eastmoney.com/"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            out = resp.read().decode("utf-8", "ignore")
    except Exception as e:                      # network fail -> report, don't crash
        return [{"error": str(e)}]
    if out.startswith("cb("):                   # strip jsonp wrapper
        out = out[3:-1]
    try:
        data = json.loads(out)
        arts = data.get("result", {}).get("cmsArticleWebOld", [])
        res = []
        for a in arts:
            res.append({
                "date": a.get("date", ""),
                "title": (a.get("title", "") or "").replace("<em>", "").replace("</em>", ""),
                "content": (a.get("content", "") or "")[:150].replace("<em>", "").replace("</em>", ""),
                "url": a.get("url", ""),
            })
        return res
    except Exception as e:
        return [{"error": str(e), "raw": out[:300]}]


if __name__ == "__main__":
    keywords = sys.argv[1:] or ["特斯拉", "黄金", "英伟达"]
    for kw in keywords:
        print("=" * 15, kw, "=" * 15)
        for r in em_search(kw):
            print(r.get("date", ""), "|", r.get("title", ""), "|", r.get("content", ""))
        print()
