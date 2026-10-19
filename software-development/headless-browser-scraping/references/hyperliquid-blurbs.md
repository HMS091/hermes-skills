# Hyperliquid 币种简介抓取（已验证）

简介不在任何 API 里，只在 `/trade/<route>` 页面左上角标题旁的**币图标浮层**里。

## 清单来源（只走 info API）
```bash
POST https://api.hyperliquid.xyz/info  {"type":"metaAndAssetCtxs"}                    # 主流永续
POST .../info {"type":"perpDexs"}                                                     # HIP-3 dex 名列表（第 0 个是 null）
POST .../info {"type":"metaAndAssetCtxs","dex":"<name>"}                             # 每个额外 dex
POST .../info {"type":"spotMetaAndAssetCtxs"}                                         # 现货
```
- 成交量字段：`assetCtxs[i].dayNtlVlm`（与 `universe[i]` 同序）。只留 `> 0`，再按成交额降序去重。
- 现货的 `universe[i].name` 是 `@144` 这种 id，标题要用 `spotMeta.tokens` 映射出的 `BASE/QUOTE` 对。
- 实测规模（同一时期）：主流 200+、xyz 115、para/io/mkts 几十，过滤后约 430 个有效标的（perp 341 / spot 91）。

## 路由（错一种就整批 null）
| 类型 | 正确 URL | 备注 |
|------|----------|------|
| 主流永续 | `/trade/BTC` | |
| HIP-3 永续 | `/trade/xyz:GOOGL` | 直接用 API 名，冒号不转义 |
| 现货 | `/trade/QQQ/USDC` | 斜杠形式；`/trade/@144` 会**重定向到 HYPE** |

错误路由的表现：页面 header 变成 `HYPE-USDC` 或干脆空白——必须在抓之前校验身份。

## DOM 结构（点击后）
```
标题：左上角叶子 div，文本形如 BTC-USDC / GOOGL-USDC / NEKO/USDC，
      rect 约 x=43、y=77（无公告条）或 y=112（有公告条）、h=27
div.modal（宽 520，锚在鼠标附近）
  ├─ 关闭 X
  └─ div > img(40px, src="/coins/<id>.svg") + 标题 div + 描述 div[style*="pre-wrap"]
```
- 描述取 `div.modal div[style*="pre-wrap"]` 的 `innerText`，就是完整原文；兜底取 modal `innerText` 去掉第一行标题。
- 点击目标优先 `img[src^="/coins/"]` 的中心；`标题.left-22` 作兜底。两者实测都能开，交替失败是竞态，不是方法错。
- 点击后 7×700ms 轮询 `div.modal`；已打开的浮层先 `Escape` 再离开页面。

## 已知差异
- **现货对基本没有浮层**：图标常是 `/coins/missing.svg`，点开无 modal → 记 null，且不要对 spot 重试 3 次（浪费 40s/个）。
- **展示名 ≠ API 名**：`xyz:SKHX` 的页面标题是 `SKHYNIX-USDC`，且**确实有简介**（"SKHYNIX references 1 SK hynix Inc. common share (KRX: 000660)…"）。按标题文本比对会把这类全部误杀，改用图标 src 校验。
- 美股类写法两种，原样保留：
  - `GOOGL references 1 share of Alphabet Inc. Class A common stock (Nasdaq: GOOGL), quoted in USD. …`
  - `TSM references 1 Taiwan Semiconductor Manufacturing Company Limited ADS (NYSE: TSM), representing 5 common shares (TWSE: 2330), quoted in USD. …`
- 加密原生标的是普通一段话，例如 `HYPE is the native token of the Hyperliquid blockchain.`

## 输出结构
```json
{ "<coin>": { "kind": "perp|spot", "dex": "xyz|null", "vol": 123.0,
              "blurb": "英文原文或 null", "at": "ISO", "note": "仅失败时" } }
```
现货 key 用 `BASE/QUOTE`，另存 `apiId: "@288"` 便于回溯。

## 时间基准
单标的约 20~25s（导航 4s + 标题轮询 + settle 9~12s + 点击/轮询），430 个约 2.5~3 小时。
