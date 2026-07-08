# CNN Lite Geopolitics Extraction (Cron Job Source)

**Source:** `https://lite.cnn.com/`
**Reliability:** ★★★★★ — no Cloudflare, no CAPTCHA, clean accessibility tree
**Best for:** Geopolitical context for gold/macro sections of daily briefings

## Pattern

CNN Lite renders a flat list of article links as an accessibility tree, making it trivial to extract headlines relevant to financial markets:

```python
# Step 1: Navigate
browser_navigate("https://lite.cnn.com/")

# Step 2: Scan the snapshot for geopolitics/finance headlines
# Keywords to grep for in the snapshot text:
#   Iran, Middle East, oil, crude, strike, sanctions, Fed, Fed minutes,
#   Federal Reserve, tariff, trade, NATO, China, tariffs, inflation,
#   Ukraine, Russia, OPEC
```

## Keywords-to-Section Mapping

| Keyword | Briefing Section |
|---------|-----------------|
| Iran, sanctions, oil, Middle East, Strait of Hormuz | 宏观环境 + 🥇 黄金 |
| Fed, Federal Reserve, inflation, rate, Powell | 宏观环境 |
| tariff, trade, USMCA, China | 宏观环境 |
| NATO, defense, military | 宏观环境 |
| AI, semiconductor, chip, Nvidia/NVDA | 🖥️ 英伟达 |
| EV, electric, Tesla, auto, tariff | 🚗 特斯拉 |

## Limitations

- Only shows ~50 most recent headlines (not searchable)
- Headlines are truncated on the front page — click through for full text
- No price/market data (purely news)
- US-centric news perspective (minor, given US market focus)
