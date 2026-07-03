# 代币价值验证 — 实时价格查询参考

## 为什么需要这个

GitHub Bounty 经常标明代币数量（如「500 MRG」「600 MRWK」「150 points」）而不是美元金额。脚本的金额解析器可能将 `500 MRG` 误读为 `$500`，但实际价值可能只有几美分。这个文档记录了验证代币实时美元价值的方法。

## 已验证的代币

### MRG (MergeOS)

| 属性 | 值 |
|------|-----|
| 链 | Arbitrum |
| DEX | OreoSwap |
| 合约地址 | `0x6c2B3D4f12CCb955EFcE402DbcE9d6CA75e01905` |
| 2026-06-03 价 | ~$0.0002694 |
| 500 MRG ≈ | **$0.13** |

**API 查询**（DexScreener，无需认证）：
```python
# 用 DexScreener 搜索 MRG
curl -s "https://api.dexscreener.com/latest/dex/search?q=MRG"
# 或直接查配对
curl -s "https://api.dexscreener.com/latest/dex/pairs/arbitrum/0x8e800C9EBeb1Be1AD90b0663538cF27B8C76BB95"
```

### MRWK (MergeWork)

| 属性 | 值 |
|------|-----|
| 链 | Solana |
| DEX | Meteora (DLMM) |
| 2026-06-03 价 | ~$0.0001-$0.001 级 |
| 600 MRWK ≈ | ~$0.06-$0.60 |

**API 查询**：
```python
curl -s "https://api.dexscreener.com/latest/dex/search?q=MRWK"
```

### XLM (Stellar)

| 属性 | 值 |
|------|-----|
| 链 | Stellar |
| 2026-06-03 价 | ~$0.20-0.30 |
| 价格稳定度 | 中等（相对代币更稳定） |

**API 查询**（CoinGecko，无需认证）：
```python
curl -s "https://api.coingecko.com/api/v3/simple/price?ids=stellar&vs_currencies=usd"
```

## 通用的代币价值验证工作流

```python
import json, re
from urllib.request import urlopen

def fetch_json(url):
    """简单 GET 请求，无认证"""
    with urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())

def extract_token_amount(issue_body: str, issue_title: str) -> tuple[str, int] | None:
    """从 Issue 标题或 body 提取代币类型和数量。返回 (symbol, amount) 或 None。"""
    text = f"{issue_title} {issue_body}"
    
    # 匹配 "500 MRG", "600 MRWK", "150-points" 等
    for symbol in ["MRG", "MRWK", "XLM"]:
        m = re.search(rf'(\d+(?:,\d+)?)\s*{symbol}', text, re.IGNORECASE)
        if m:
            return (symbol.upper(), int(m.group(1).replace(',', '')))
    
    return None

def to_usd(symbol: str, amount: int) -> float | None:
    """查询代币实时价并返回 USD 价值"""
    try:
        if symbol == "MRG":
            data = fetch_json("https://api.dexscreener.com/latest/dex/search?q=MRG")
            # 取第一个 pair 的 USD 价
            for pair in data.get("pairs", []):
                if pair.get("chainId") == "arbitrum":
                    return amount * float(pair["priceUsd"])
            return None
        
        elif symbol == "MRWK":
            data = fetch_json("https://api.dexscreener.com/latest/dex/search?q=MRWK")
            for pair in data.get("pairs", []):
                if pair.get("chainId") == "solana":
                    return amount * float(pair["priceUsd"])
            return None
        
        elif symbol == "XLM":
            data = fetch_json("https://api.coingecko.com/api/v3/simple/price?ids=stellar&vs_currencies=usd")
            return amount * float(data["stellar"]["usd"])
        
        return None
    except Exception as e:
        print(f"   ⚠️ Token 价格查询失败 ({symbol}): {e}")
        return None
```

## 无效代币类型的处理

以下情况应跳过执行：

1. **Unknown token**: 代币符号不在上述列表中 → 无法验证 → 跳过
2. **DexScreener 无数据**: 查询返回空 pairs 列表 → 流动性不足 → 跳过
3. **Points/积分**: `points`, `Stars`, `wave-eligible` 等非代币标签 → 直接跳过，不尝试查询
4. **代币价值 < $50**: 即使有流动性，价值不足 → 跳过并记录

## 2026-06-03 实际扫描数据

| 目标 | 面值 | 查询价格 (USD) | 实际价值 | 决策 |
|------|------|---------------|---------|------|
| mergeos #13 | 500 MRG | $0.0002694 | $0.13 | ❌ 跳过 |
| mergework #800 | 600 MRWK | ~$0.0001-0.001 | ~$0.06-0.60 | ❌ 跳过 |
| SecureBananaLabs #743 | $700 (美元) | — | $700 | ❌ Creator-restricted |
| godamongstmen/loot-vault #9 | 150 points | — | 0 (积分) | ❌ 跳过 |
