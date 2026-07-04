---
name: crypto-token-dd
description: Crypto token/project due diligence — analyze a contract address or project for scam, rug pull, honeypot, or ponzi indicators. Multi-source data collection, risk signal framework, structured Chinese report with tables and risk flags.
trigger: "User provides a crypto token contract address, project name, or website and asks to analyze whether it's a scam, rug pull, ponzi, or worth investing."
tags: [crypto, blockchain, security, scam-detection, due-diligence, web3]
---

# Crypto Token Due Diligence

Comprehensive analysis of a crypto token/project to assess scam, honeypot, rug pull, or ponzi risk. Delivers a structured report in Chinese with risk flag tables and actionable recommendations.

## Workflow

### Phase 1: Collect Base Info

**0. Network setup (critical in Docker/NAS environments):** Before any API call, unset stale proxy env vars:
```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY
```
Then verify connectivity with `curl -s --connect-timeout 8 -o /dev/null -w "%{http_code}" "https://api.etherscan.io"` — if any major source returns 000/connection refused, the network is blocked and alternative approaches are needed.

**1a. Determine the correct chain first** — the user may say "connected on Binance" (BSC) but the contract is the same address. Always try DexScreener's search endpoint or ask the user. The API path changes per chain.

**1b. DexScreener** — main endpoint:
   - V1 (deprecated): `https://api.dexscreener.com/latest/dex/token/<ADDRESS>` 
   - V2 search (works across all chains): `https://api.dexscreener.com/latest/dex/search?q=<ADDRESS>`
   - Chain-specific V1: `https://api.dexscreener.com/tokens/v1/chain/bsc/<ADDRESS>` (replace bsc with ethereum/polygon/etc.)
   - Returns: pairs, liquidity USD, volume 24h, price, FDV, pair creation time, labels, chainId
   - Key signals: `volume.h24`, `liquidity.usd`, `pairCreatedAt` (very recent = risky), `labels` (e.g. "honeypot")
   - **If DexScreener returns empty/nothing**: this already means no pairs exist → major red flag. Don't retry.

2. **CoinGecko** — `https://api.coingecko.com/api/v3/coins/ethereum/contract/<ADDRESS>`
   - Returns: name, symbol, market_cap_rank, coingecko_rank, links (homepage, twitter, telegram), description
   - No data = extremely small/unknown project
   - **Note**: CoinGecko only indexes ERC-20 tokens on Ethereum. For BSC tokens, try `https://www.coingecko.com/en/coins/<token-name>` (web scrape) or skip.

3. **GoPlus Token Security** — chain-specific URL:
   - Ethereum (chainId=1): `https://api.gopluslabs.io/api/v1/token_security/1?contract_addresses=<ADDRESS>`
   - BSC (chainId=56): `https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses=<ADDRESS>`
   - Returns: honeypot status, owner address, creator address, proxy info, mint/burn flags, tax info
   - Key fields: `is_honeypot`, `is_owner_change_balance`, `can_take_back_ownership`, `slippage_modifiable`

4. **Blockchain explorers** (chain-specific, all use Cloudflare):
   - Ethereum: `https://etherscan.io/address/<ADDRESS>`
   - BSC: `https://bscscan.com/address/<ADDRESS>` (BSC scan pages use Cloudflare too)
   - Try: `curl -sL -H "User-Agent: Mozilla/5.0" "<URL>"`
   - **Cloudflare bypass failed** → just note it. Cloudflare blocking is a neutral signal, not a red flag.
   - **API-based** (requires API key, may be deprecated): `https://api.etherscan.io/api?module=contract&action=getabi&address=<ADDRESS>`

5. **Alternative data sources (when mainstream APIs are blocked/empty)**:
   - **OKX Web3**: `https://web3.okx.com/token/bsc/<ADDRESS>` — returns price, market cap, description in page metadata. Scrape for `<title>` and `<meta description>` tags. Works for BSC.
   - **GeckoTerminal (web scrape)**: `https://www.geckoterminal.com/bsc/pools/<PAIR_ADDRESS>` — if you find a pair via DuckDuckGo, scrape this for pool data.
   - **CoinCarp**: `https://www.coincarp.com/currencies/<token-name>/` — covers obscure tokens.
   - **LiveCoinWatch**: `https://www.livecoinwatch.com/price/<NormalizedName>` — another secondary source.
   - **DexView**: `https://www.dexview.com/bsc/<ADDRESS>` — pool view and chart
   - **Oklink**: `https://www.oklink.com/bsc/token/<ADDRESS>` — BSC explorer alternative

6. **Chain identification fallback**: If you don't know the chain, search DuckDuckGo for the address to find which explorer listings exist. See Phase 2 below.

### Phase 1b: BSC RPC Direct Queries (Cloudflare Bypass)

When BscScan is behind Cloudflare and you need raw chain data, use BSC's public RPC nodes directly. These work even when web explorers are blocked.

**RPC endpoints** (try in order):
- `https://bsc-dataseed1.binance.org`
- `https://bsc-dataseed2.binance.org`
- `https://bsc-dataseed3.binance.org`
- `https://bsc-dataseed1.defibit.io`
- `https://bsc-dataseed2.defibit.io`
- `https://bsc-dataseed3.defibit.io`
- `https://bsc-dataseed4.defibit.io`

**Python helper pattern** (inside `execute_code`):
```python
import urllib.request, json

def rpc_call(method, params):
    payload = json.dumps({"jsonrpc":"2.0","method":method,"params":params,"id":1}).encode()
    req = urllib.request.Request("https://bsc-dataseed1.binance.org", data=payload,
                                 headers={"Content-Type":"application/json"})
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())
```

**Key RPC methods for token analysis:**

| Method | Params | Returns |
|--------|--------|---------|
| `eth_getBalance` | [address, "latest"] | BNB balance (hex) |
| `eth_getTransactionCount` | [address, "latest"] | Total tx count (nonce) |
| `eth_blockNumber` | [] | Latest block |
| `eth_getLogs` | [{fromBlock, toBlock, address, topics}] | Event logs |

**Querying token transfers for a specific wallet:**
```python
transfer_sig = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Sell side: wallet is `from` (topics[1])
params_sell = {
    "fromBlock": "0x0", "toBlock": "latest",
    "address": token_addr,
    "topics": [transfer_sig, "0x000000000000000000000000" + wallet[2:].lower()]
}

# Buy side: wallet is `to` (topics[2])
params_buy = {
    "fromBlock": "0x0", "toBlock": "latest",
    "address": token_addr,
    "topics": [transfer_sig, None, "0x000000000000000000000000" + wallet[2:].lower()]
}
```

**Timeout handling**: Loop through multiple endpoints. Empty results = wallet never directly transferred this token (but may have swapped via a DEX pair). `eth_getTransactionByNonce` is NOT supported on BSC.

**Important limitation**: RPC only shows direct token transfers. Swaps through PancakeSwap V2 pairs appear as interaction with the pair contract, not the token contract. See Phase 6 below for wallet behavioral analysis workflow.

### Phase 2: Social & Community Research

Search for the project name/address on:

- **DuckDuckGo HTML search** (best bet when Google is blocked in China network): 
  `curl -s "https://html.duckduckgo.com/html/?q=<ADDRESS>+BSC+token" -H "User-Agent: Mozilla/5.0"`
  Parse `class="result__a"` href attributes and `class="result__snippet"` for summaries.
  DuckDuckGo works even when Etherscan/BscScan are Cloudflare-blocked because it cached their index pages.
  
- **Google** (if accessible): `https://www.google.com/search?q=<ADDRESS>+token` 
  Parse `<h3>` tags for result titles.

- **Twitter**: Via DuckDuckGo search for `<TOKEN_NAME> twitter` or check project links from CoinGecko
- **Scam databases** (check if accessible):
  - `https://www.chainabuse.com/reports?search=<ADDRESS>`
  - `https://tokensniffer.com/token/<ADDRESS>` (ETH only)
- **Telegram/Discord**: Check if project has a public community; high member counts + restricted chat = red flag
- **GitHub**: Check if project has public source code; verified contracts on Etherscan are positive

### Phase 3: Risk Signal Framework

Compile findings into a risk matrix. Each signal gets 🟢 (safe), 🟡 (caution), 🔴 (danger):

| Category | Signal | Green | Yellow | Red |
|---|---|---|---|---|
| **Exchange listing** | DexScreener has pairs | Yes, >$10k liquidity | Yes, <$10k liquidity | No pairs found |
| **Mainstream trackers** | CoinGecko/CMC | Listed with rank | Listed no rank | Not listed |
| **Liquidity** | Liquidity locked/sufficient | Locked, >$50k | Not locked | Very low or withdrawn |
| **Honeypot** | Can sell? | Verified not honeypot | Suspicious tax | Confirmed honeypot |
| **Ownership** | Contract ownership | Renounced | Timelock | Owner can mint/steal |
| **Code** | Verified on chain | Verified open source | Unverified | Proxy with no logic |
| **Social** | Twitter, website, docs | Active and verifiable | New account, low followers | No social presence |
| **Age** | Contract age | >6 months | 1-6 months | <1 month |
| **Community** | Telegram/Discord | Large organic community | Bots/muted chat | No community |

### Phase 4: Deliver Report

Generate a structured report in Chinese with the following sections:

```markdown
## 合约地址分析报告

### 一、基本信息
| 维度 | 结果 |
|---|---|
| 链 | Ethereum / BSC / ... |
| 代币名 | (name / symbol) |
| 收录情况 | CoinGecko / DexScreener / GoPlus |
| 合约创建时间 | (date, relative age) |

### 二、风险信号分析
(Table of risk flags with emoji indicators)

### 三、高危信号 🚩
(Bullet list of all red flags found)

### 四、该项目可能是什么？
1. **正常项目** — lower probability, explain why
2. **土狗/Meme币** — common pattern, explain
3. **蜜罐代币** — if sell restrictions detected
4. **资金盘/Ponzi** — if referral/rebate patterns
5. **已Rug废弃** — if liquidity withdrawn, no activity

### 六、建议
⚠️ **strong action recommendation**
- Why you recommend this course
- What specific data supports it
```

### Phase 6: Wallet Behavioral Analysis (Advanced)

When the user points to a specific wallet address and claims it's "actively trading" or "profitable" on the token, perform this standalone analysis:

**Step 1: Basic wallet info via BSC RPC**
```python
import urllib.request, json

def rpc_call(method, params):
    payload = json.dumps({"jsonrpc":"2.0","method":method,"params":params,"id":1}).encode()
    req = urllib.request.Request("https://bsc-dataseed2.defibit.io", data=payload,
                                 headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

wallet = "0x..."

# Balance
bal_hex = rpc_call("eth_getBalance", [wallet, "latest"]).get('result','0x0')
balance = int(bal_hex, 16) / 10**18

# Nonce (total tx count)
nonce_hex = rpc_call("eth_getTransactionCount", [wallet, "latest"]).get('result','0x0')
nonce = int(nonce_hex, 16)

# Latest block
latest_block = int(rpc_call("eth_blockNumber", []).get('result','0x0'), 16)
```

**Step 2: Check direct token interaction (fast, conclusive)**
```python
transfer_sig = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
token_addr = "0x..."  # the token they claim wallet trades

# Wallet as sender (sells)
params = {
    "fromBlock": "0x0", "toBlock": "latest",
    "address": token_addr,
    "topics": [transfer_sig, "0x000000000000000000000000" + wallet[2:].lower()]
}
sells = len(rpc_call("eth_getLogs", [params]).get('result', []))

# Wallet as receiver (buys)
params2 = {
    "fromBlock": "0x0", "toBlock": "latest",
    "address": token_addr,
    "topics": [transfer_sig, None, "0x000000000000000000000000" + wallet[2:].lower()]
}
buys = len(rpc_call("eth_getLogs", [params2]).get('result', []))
```

**Step 3: Interpret the results**

| Finding | Meaning |
|---------|---------|
| Direct buys > 0, sells > 0 | Wallet really trades this token |
| Direct buys = 0, sells = 0 | **Wallet may still trade via DEX pair contracts** (PancakeSwap V2 mediates swaps through the pair). Find pair address separately and query Swap events. |
| Nonce > 1000 but no direct token activity | Wallet is a general bot/degen; it may have traded this specific token through DEX pairs. **The user's claim is unverifiable without pair-level data.** |
| Wallet abandoned (no activity in 10K+ blocks) | Suggestive of disposable bot wallet. High nonce + near-zero BNB = operator rotated to a new wallet. |
| BNB balance < $50 | Wallet is effectively abandoned or used as a pass-through |

**Step 4: Pattern recognition for scam signals**

When a user follows a "profitable wallet" and asks you to check a token:
- 🔴 If the wallet has zero direct interaction with the token but user claims it trades it → the data may be fabricated or misunderstood (user saw Pair-level swaps)
- 🔴 If the wallet has high nonce + small BNB balance + recent silence → it was a temporary trading tool, not a long-term "smart money" signal
- 🔴 If the wallet IS active and profitable → it could be the scammer's own wallet creating fake volume to lure victims

**Step 5: Memory & caching**
- Do NOT save wallet addresses or analysis results to memory
- Save the wallet analysis as a `references/` file under the crypto-token-dd skill if the technique or findings are novel
- See `references/wallet-0xe561-wallet-behavioral-analysis.md` for a real-world example

### Phase 7: Network Troubleshooting (Docker/NAS Environment)

If running inside a Docker container on a NAS (Synology, etc.), the network may have constraints:

1. **Default behavior**: Try without any proxy first — `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY` before curl calls. This is the FIRST thing to do.
2. **Stale proxy env vars**: Environment files (`/etc/environment`, `/etc/profile.d/proxy.sh`) may set HTTP_PROXY to a proxy that no longer responds. `Connection refused` on port 7890 = proxy is down. Simply unset the vars and retry.
3. **Test connectivity**: Simple connectivity test before starting analysis:
   ```bash
   unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY
   curl -s --connect-timeout 8 -o /dev/null -w "%{http_code}" "https://api.etherscan.io"
   # 200 = OK, 000 = blocked
   ```
4. **Fallback order when sources fail** (IN ORDER):
   - If initial curl to any well-known API fails → unset proxy, retry
   - If DexScreener returns empty → note "no pairs found on DexScreener" (this is itself a signal, don't retry)
   - If DexScreener search endpoint also empty → try **DuckDuckGo HTML search** for the address to find chain/name
   - If CoinGecko returns error → note "not listed on CoinGecko" (major red flag for Ethereum tokens; normal for other chains)
   - If GoPlus returns empty → skip, note "not on GoPlus security" (red flag)
   - If Etherscan/BscScan blocked by Cloudflare → note "blocked by CF" and move on — DON'T retry with different User-Agents
   - **If mainstream APIs all return nothing but DuckDuckGo found results**: scrape OKX Web3, GeckoTerminal, LiveCoinWatch, CoinCarp for secondary data
   - **Key principle**: A source returning nothing IS data — it tells you the project hasn't met basic listing criteria
5. **API key note**: Etherscan API V2 requires an API key. For ad-hoc analysis, use the web HTML endpoint or skip Etherscan data if both API and web are blocked. The lack of Etherscan data is noted as "limited data availability" rather than "no data exists."
6. **DuckDuckGo as primary search engine**: In Chinese network environments where Google is blocked, DuckDuckGo HTML search (`html.duckduckgo.com/html/?q=...`) is the most reliable search. It returns structured HTML that can be parsed for result titles, URLs, and snippets via regex.
7. **Session search as last resort**: If **all** external sources (API, RPC, DuckDuckGo) are unreachable or return nothing useful, use Hermes' `session_search(query="<CONTRACT_ADDRESS>")` to recover prior analysis of the same contract. This is faster than retrying failed endpoints and avoids redundant work. The session DB may contain prior findings including token name, chain, risk signals, and on-chain evidence from previous successful RPC calls. _This only helps if the contract was analyzed before — it is not a substitute for first-pass analysis when network is blocked._

### Phase 5: Honeypot Detection via balanceOf Cross-Verification (Critical!)

A definitive technique to detect fake-balance honeypots: **Compare the actual on-chain `balanceOf()` return value against what BscScan/Etherscan's "Holders" page displays.**

**Why this works:** Many honeypot tokens override `balanceOf()` to return inflated values, creating the illusion of massive holdings. The BscScan holders page queries this same overridden function, so it also shows fake numbers. But direct RPC calls to `balanceOf()` also return the same fake numbers — so how do you detect the lie?

**Key insight:** Cross-reference TWO independent signals:

1. **Check if actual Transfer events exist** for the purported holdings. If BscScan shows wallet A holds 2M PRO tokens, but `eth_getLogs` on the Transfer event for wallet A → token returns zero (or tiny) entries, the listed balance is fabricated.

2. **Direct balanceOf() via RPC** — returns the contract-state value. Compare against the number of on-chain Transfer events. A wallet with billions in `balanceOf()` but zero transfer events is holding fabricated tokens.

3. **Verify with minimal BNB gas** — If the supposed "top holder" wallet has 0 BNB (can't pay gas to transfer), and the `balanceOf()` shows huge numbers, it's either:
   - A contract that mints tokens to the wallet without the wallet doing anything (scam)
   - A wallet that received tokens long ago and drained its BNB (abandoned)
   - The `balanceOf()` is being faked to show inflated values on explorers

**Python detection script (for `execute_code`):**

```python
def detect_fake_balance(token_addr, wallet_addr, rpc_url="https://bsc-dataseed2.defibit.io"):
    import urllib.request, json
    
    def rpc(method, params):
        data = json.dumps({"jsonrpc":"2.0","method":method,"params":params,"id":1}).encode()
        req = urllib.request.Request(rpc_url, data=data, headers={"Content-Type":"application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=15).read())
    
    # 1. Check BNB balance of the wallet
    bal_hex = rpc("eth_getBalance", [wallet_addr, "latest"]).get("result","0x0")
    bnb_balance = int(bal_hex, 16) / 1e18
    
    # 2. Call balanceOf() on the token contract
    # balanceOf selector: 0x70a08231
    data = "0x70a08231" + "000000000000000000000000" + wallet_addr[2:].lower()
    bal_result = rpc("eth_call", [{"to": token_addr, "data": data}, "latest"])
    token_balance = int(bal_result.get("result","0x0"), 16) / 1e18
    
    # 3. Count actual Transfer events involving this wallet
    transfer_sig = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    params = {
        "fromBlock": "0x0", "toBlock": "0x600000",  # bounded range to avoid timeout
        "address": token_addr,
        "topics": [
            transfer_sig,
            None,  # any from
            "0x000000000000000000000000" + wallet_addr[2:].lower()
        ]
    }
    incoming = rpc("eth_getLogs", [params]).get("result", [])
    
    params2 = {
        "fromBlock": "0x0", "toBlock": "0x600000",
        "address": token_addr,
        "topics": [
            transfer_sig,
            "0x000000000000000000000000" + wallet_addr[2:].lower(),
            None
        ]
    }
    outgoing = rpc("eth_getLogs", [params2]).get("result", [])
    
    print(f"BNB balance: {bnb_balance:.4f}")
    print(f"Token balanceOf(): {token_balance:.4f} TOKEN")
    print(f"Incoming transfers: {len(incoming)}")
    print(f"Outgoing transfers: {len(outgoing)}")
    
    # Flag if balanceOf() is huge but Transfer events are zero/few
    if token_balance > 1000 and len(incoming) == 0:
        print("🚨 HIGH CONFIDENCE: balanceOf() returns large value but ZERO incoming transfers!")
        print("   → The contract overrides balanceOf() to show fake holdings")
    elif token_balance > 1000 and len(incoming) < 3:
        print("⚠️ WARNING: Large balanceOf() but very few incoming transfers")
        print("   → Suspicious, likely fabricated or a mint-to-many distribution")
    elif bnb_balance < 0.001 and token_balance > 1000:
        print("⚠️ WARNING: Large token holdings but near-zero BNB gas balance")
        print("   → Wallet cannot move these tokens — may be inactive or honeypot")
```

**⚠️ Critical: decimals mismatch can produce false positives**

Always verify token decimals before interpreting balanceOf() results. The token's `decimals()` function might return non-standard values (e.g., 9 instead of 18). Dividing by 10^18 when the token has 9 decimals produces results off by 10^9 (1 billion times wrong).

```python
# ALWAYS check decimals first:
dec_hex = rpc_call("eth_call", [{"to": token_addr, "data": "0x313ce567"}, "latest"]).get("result","0x0")
decimals = int(dec_hex, 16) if dec_hex != "0x" else 18  # default 18 if not found
actual_balance = token_balance_raw / (10 ** decimals)
```

**Real-world example (Pro Token PRO on BSC) — illustrating the decimals trap:**
- Token decimals: **9** (not the default 18!)
- Wallet `0xc002...8ee8` claimed to hold 2,010,000 PRO
- `balanceOf()` raw hex: `0x000000...072d2c866bc94c` → 3,675,882,446,875,117 wei
- ❌ Divided by 10^18 → **0.0037 PRO** (wrong! → false positive "honeypot")
- ✅ Divided by 10^9 → **3,675,882 PRO** (53.08% of supply → matches BscScan)
- BNB balance: **0 BNB** (wallet is a contract, not an EOA — cannot pay gas directly)
- Incoming Transfer events: zero (may be minted or distributed via factory)

**Lesson:** Always check `decimals()` before interpreting balanceOf(). A wallet with 0 BNB may be a contract, not a dead EOA. Zero Transfer events could mean tokens were minted directly, not transferred. Cross-reference ALL three signals before concluding "fake balance."

**The corrected conclusion for PRO:** The token is NOT a balance-faking honeypot. It has $86M in real LP liquidity on PancakeSwap V2 (43M USDT / 715K PRO), the contract owner is renounced, and the contract source is verified on BscScan. However, 53% supply concentration in one address and the absence of any public team/social presence remain 🚩🚩 risk signals.

**When to use this technique:**
- ALL tokens where BscScan shows extreme concentration (top 10 > 80%)
- Any token flagged by DexScreener/GoPlus as suspicious
- Tokens with no verified source code on BscScan
- Tokens where BscScan is Cloudflare-blocked (you can still do this via RPC!)
- Any project the user asks about that has a contract address on BSC/BSC

**Important:** This technique detects one specific scam class (balance-faking honeypots). A clean balanceOf() check does NOT mean the token is safe — check other signals (honeypot sell tax, mint functions, ownership) separately.

### Phase 5b: Proxy Contract Detection & Analysis

When a top holder on BscScan is a **contract address** (not a regular wallet/EOA), analyze what type of contract it is. Proxy contracts as top holders are a major red flag.

**Step 1: Detect if address is a contract**

```bash
curl -s -X POST "$BSC_RPC" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getCode","params":["<ADDRESS>", "latest"],"id":1}'
```
- Result > `0x` + 10 chars → contract
- Result = `0x` or very short → EOA (normal wallet)

**Step 2: Identify EIP-1967 UUPS Proxy**

A UUPS proxy has these bytecode signatures:

| Feature | Bytecode Pattern | Meaning |
|---------|-----------------|---------|
| Solidity preamble | `60806040` | Standard Solidity start |
| Admin check | `7f000000000000000000000000<ADMIN>` | PUSH32 with whitelisted admin address |
| EIP-1967 slot | `360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc` | Logic contract storage slot (upgradeable) |
| Solc version | ends with `64736f6c63` + version | Compiler metadata |

**Step 3: Extract the admin address**

The admin is encoded in the PUSH32 byte after `7f`:

```python
code_hex = bytecode[2:]  # strip 0x
idx = code_hex.index('7f') + 2
push32 = code_hex[idx:idx+64]
admin = '0x' + push32[-40:]  # last 20 bytes
```

**Step 4: Proxy-specific risk flags**

| Signal | Risk Level |
|--------|-----------|
| EIP-1967 UUPS proxy | 🟡 (may be legit if logic is verified) |
| Proxy + uniswapV2SwapCall selector | 🔴 (flash-loan capable, liquidity manipulation) |
| Proxy + uniswapV2Pair selector | 🟡 (DEX interaction capability) |
| Multiple proxies as top holders | 🔴🔴 (project team concentrating supply under different identities) |
| Proxy + same bytecode template as other top holders | 🔴🔴 (same factory, same team) |
| Proxy + zero Transfer events | 🔴🔴🔴 (balanceOf() is faked or tokens are shadow-minted) |

**Step 5: Compare multiple proxies for same-factory detection**

When two proxy contracts have identical bytecode (except admin address), they were deployed from the same factory. This proves the project team controls both:

```python
# If code is identical except for the admin at position after 7f:
code1_without_admin = bytecode1.replace(admin1_hex, '')
code2_without_admin = bytecode2.replace(admin2_hex, '')
if code1_without_admin == code2_without_admin:
    print("Same factory deployment: one team controls both")
```

**Step 6: Cross-reference with balanceOf() (from Phase 5a)**

Proxy contracts that appear as top holders on BscScan must also pass the balanceOf() verification. Apply the Phase 5a detection script to each proxy address.

**See also:** 
- `references/bsc-proxy-contract-bytecode-analysis.md` — real-world case study with Pro Token (PRO)
- `references/olympus-ohm-legitimate-project-comparison.md` — counter-example showing what a legit project (OHM/DeFi) looks like through the same tools

**Important: Always compare scam signals against a known-legitimate reference like OHM.** A high holder concentration does NOT automatically mean scam (treasury-backed protocols like OHM hold 70%+). The difference is:
- Legit: open source, CoinGecko-listed, audited protocol, real community, balanceOf matches Transfer events
- Scam: proxy contracts as top holders, balanceOf returns fake values, no mainstream listings, hidden/upgradable logic

### Phase 5c: Contract Storage Slot Reading via `eth_getStorageAt` ("Renounced-but-Manipulated" Detection)

Direct storage slot reading verifies the **current state** of a contract, especially parameters the owner may have changed **before** renouncing. This detects the pattern where the owner renounces only AFTER extracting maximum value.

**When to use:**
- After Phase 5a, to understand fee structure and control
- When the contract is renounced but you suspect the owner changed parameters first
- To verify actual configuration vs frontend claims

**Key RPC method:**
```python
import urllib.request, json
payload = json.dumps({
    "jsonrpc": "2.0", "method": "eth_getStorageAt",
    "params": [contract_addr, slot_hex, "latest"], "id": 1
}).encode()
req = urllib.request.Request(rpc_url, data=payload, headers={"Content-Type":"application/json"})
result = json.loads(urllib.request.urlopen(req, timeout=15).read()).get("result","0x0")
```

**Common Solidity storage slot mapping:**

| Slot | Common mapping | Signal |
|------|---------------|--------|
| 5 | `owner()` / `_owner` | 🟢 if `0xdead` (renounced) |
| 6 | `controller` / `operator` / `_auth` | 🔴 if different from deployer |
| 7 | `marketingWallet` / `feeWallet` | Tax fee recipient |
| 9 | LP pair address | DEX pair |
| 10-12 | uint parameters (tax, threshold) | Compare vs initial |
| 13 | `liquidityWallet` | 🔴 if different from deployer |
| 14 | Timestamp of last config change | 🚩 if recent |

**Detection workflow:**
1. Read constructor bytecode → extract initial slot values (e.g., tax=100, threshold=300)
2. Read current storage → compare (e.g., tax=500 → **was modified!**)
3. Check slot 14 (timestamp) → confirms recent activity
4. Check slot 6 (controller) → if different from deployer, control was delegated
5. Conclusion: "Renounced" means "owner extracted what they wanted and walked away"

**Real-world example (Pro Token PRO, BSC):**

| Parameter | Constructor | Current | Changed? |
|-----------|------------|---------|----------|
| Slot 05 (owner) | deployer | `0xdead` | Renounced |
| Slot 06 (controller) | deployer | `0x96079ef9...` | **Changed** |
| Slot 10 | 100 | 500 | **5x increase** |
| Slot 12 | 300 | 250 | Changed |
| Slot 13 (liq wallet) | deployer | `0x543302e9...` | **Changed** |
| Slot 14 | 0 | 1781982105 (2026-06-20) | **Active 2 weeks before renounce** |

**From terminal (more reliable than execute_code):**
```bash
for slot in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14; do
  curl -s -X POST "$BSC_RPC" -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getStorageAt\",
         \"params\":[\"$CONTRACT\",\"0x$(printf '%x' $slot)\",\"latest\"],\"id\":1}"
done
```

**Lesson:** Never trust "renounced" at face value. Verify what the owner did **before** renouncing.

## Pitfalls

- **JS-heavy token analytics sites (Ave.ai, DexTools, etc.) are not scrapable**: Sites like `ave.ai/token/...` are Nuxt.js SPAs that render zero content in text-based browsers or via curl. Their HTML is a bare `<div id=\"__nuxt\"></div>` with no data. When a user shares an ave.ai link, extract the `token/0x...-bsc` segment from the URL for the address and chain, then proceed with conventional data sources (DexScreener, BSC RPC, etc.). Do NOT attempt to scrape the ave.ai page itself.
- **Cloudflare protection on ALL blockchain explorers**: Both Etherscan AND BscScan use Cloudflare challenge pages that resist curl. When blocked, move immediately to alternative data sources (OKX Web3, DuckDuckGo cached listings, GeckoTerminal). Do NOT waste retries with different User-Agents.
- **Rate limiting**: Free API endpoints (DexScreener, CoinGecko, GoPlus) may rate-limit or return empty. Batch all queries in `execute_code`, not sequential `terminal()` calls.
- **False positives**: A lack of listings is not conclusive — legitimate brand-new projects also won't be on CoinGecko. Cross-reference with social presence and code verification.
- **False negatives**: Some legit projects use proxies/upgradable contracts — don't flag "proxy" as automatically bad.
- **Chinese user reports**: If user is Chinese-speaking, search Baidu/Bilibili/小红书 for project name + 骗局/跑路/资金盘 as well.
- **"Connected on Binance" ambiguity**: When a user says "connected on Binance" / "在币安连上的", they almost always mean the BSC chain (PancakeSwap), not a real CEX listing. Explain the distinction gently and proceed with BSC analysis.
- **Do NOT recommend buying**: Even if analysis is inconclusive, never recommend purchasing. Report the data, flag the risks, let the user decide.
- **Slippage / tax**: High buy/sell tax isn't automatically a scam — some legit tokens have tax for rewards/burn. But if tax is modifiable by owner → 🔴.
- **Memory**: Do NOT save token addresses, wallet addresses, or analysis results to memory. These are session-specific artifacts, not durable facts. Instead, write reference files under the skill's `references/` directory if the technique or findings are novel enough for future sessions.
- **DexScreener endpoints change frequently**: If the standard token/search endpoints return empty, try chain-specific V1 URLs (`/tokens/v1/chain/bsc/<ADDRESS>`) or the generic `latest/dex/search?q=<ADDRESS>`. An empty response from ALL DexScreener variants = no public pair exists = 🚩🚩🚩
- **Price from LP reserves**: When DexScreener/CoinGecko have no price data but a PancakeSwap V2 pair exists, calculate real price from LP reserves. See `references/lp-price-calculation.md`.
- **BscScan HTML scraping via curl**: Even when the browser is Cloudflare-blocked, `curl -H "User-Agent: Mozilla/5.0" "https://bscscan.com/token/<ADDRESS>"` often returns the full HTML page. From that you can extract holders count, token rep, verified bytecode, and contract metadata. See `references/bscscan-curl-bypass.md`.
- **PancakeSwap V2 swaps don't appear as direct token transfers**: If a wallet swaps BNB↔TOKEN on PancakeSwap, the Transfer event goes between the wallet and the PAIR contract, not the token contract. Querying `eth_getLogs` on the token contract with the wallet address will return ZERO results even if the wallet actively traded the token. To detect swap activity, you need the pair address — find it via DuckDuckGo or DexScreener first.
- **High nonce ≠ PRO token trades**: A wallet with 3000+ nonce may be a sniper bot, rug pull aggregator, or just a memecoin degen. Don't conflate general trading activity with interest in the specific token being analyzed. Check the specific token first.
- **Abandoned wallet ≠ scam proof**: A wallet that was active then went silent doesn't prove a project is dead. Some traders abandon hot wallets. Cross-reference with on-chain liquidity and social activity.
- **RPC eth_getLogs timeout on full range**: Scanning from block 0 to latest for a popular token can timeout (BSC free-tier RPC has limits). In `execute_code`, always use `TimeoutError` handling. If a full-range scan returns empty, the wallet genuinely never interacted with that token contract — but see the PancakeSwap pitfall above.
- **User links proxy contract as if it's a wallet**: Users may share a BscScan URL for a proxy contract address (e.g. `0xc0021...8ee8#code`) expecting it to be a regular wallet or the token contract itself. The `#code` tab specifically shows the contract's bytecode — verify with `eth_getCode` first, note the distinction, and explain: (1) whether it's the token contract or a separate proxy, (2) that proxies can be upgraded, (3) the implications for holding the token. The user may confuse "holder page data" with "contract source code" — clarify both.
