---
name: network-ad-blocking
description: "Choose/deploy ad blocking: DNS vs client, YouTube reality."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [adblock, dns, adguard, pihole, youtube, nas, network]
    related_skills: [untrusted-code-audit, synology-nas-remote-ops, open-source-discovery]
prerequisites:
  commands: [curl, python3]
---

# 全屋去广告：选型与部署

## When to Use（触发条件）

- "装个 AdGuard / Pi-hole / 软路由去广告"、"哪个去广告工具最好 / 免费"
- "我主要想过滤 YouTube 广告" ← 这句话会把整个方案推翻，见第一条规则
- NAS / 路由器上已经跑着一个 DNS 过滤器，用户问为什么还有广告

## 第一条规则：先分清 DNS 层和客户端层，再推荐

**DNS 层（AdGuard Home / Pi-hole / Technitium / Blocky / OpenWrt adblock / ESP32 广告盒）拦不到：YouTube 广告、抖音/微信/IG/B 站等信息流与开屏广告、任何与内容同域名的广告。** 广告和视频走同一域名同一 CDN，拦域名 = 连视频一起断；2026 年起 YouTube 还在推 SSAI（服务端把广告拼进视频流），客户端收到的是同一路字节。

所以：

1. 用户说"要去广告" → 追问一句**哪个设备**，再决定层级。
2. 用户说"主要是 YouTube" → **直接给客户端方案（表 3），DNS 方案最多一句带过**。先把 AdGuard 那套讲完再发现他要的是 YouTube，等于白干一轮。
3. 两类一起给时，明确写"DNS 只负责 XXX，YouTube 靠 YYY"，不要混成"去广告"一个词。

## 工具全景（数字为 2026-10 实测/官方定价，写报告前复核）

### 表 1 网关级 —— 全屋一个 DNS 入口

| 工具 | 许可 | 内存 | 内置 DoH/DoT | 适用 |
|---|---|---|---|---|
| AdGuard Home 0.107.x | GPL-3 | 空闲 45MiB / 峰值 66MiB | ✅ 服务端+上游 | **NAS 首选**：界面好、自带加密、支持 AdGuard 语法 |
| Pi-hole v6 | EUPL-1.2 | 空闲 9.3MiB / 峰值 18.6MiB | ❌（cloudflared 方案已被官方弃用） | 只有省内存一个优势；1GB 内存小机才选它 |
| Technitium DNS v15 | GPL-3 / .NET | 110–150MiB | ✅ | 权威 DNS、DNSSEC、递归全都有，家庭属过度配置 |
| Blocky | Apache-2 / Go | ~50MB | ✅ | 无 Web UI，YAML 配置，给会写配置的人 |
| OpenWrt `adblock` | GPL | <10MB | 取决于上游 | 路由上最轻，只有名单无面板 |

### 表 2 云端免费档 —— 手机、出门、没法改路由时

| 服务 | 免费额度 | 超限行为 | 付费档 |
|---|---|---|---|
| NextDNS Free | 30 万次/月，不限设备/配置，全功能 | **降级为只解析不过滤，不断网** | $1.99/月 或 $19.90/年 |
| AdGuard DNS Starter | 30 万次/月，5 设备，100 条规则 | 停止服务 | $2.49/月 或 $19.99/年（10M/20 设备） |
| Control D Free | 公共解析器，无需账号，不限次 | — | $3/月 才有自定义规则 |
| Cloudflare 1.1.1.3 / Quad9 | 不限 | — | 只拦恶意/成人，**不拦广告** |

### 表 3 客户端 —— 唯一能干掉 YouTube 广告的一层

| 设备 | 首选 | 价格 | 备注 |
|---|---|---|---|
| 电脑 | **Firefox + uBlock Origin** | 0 | 唯一还跑完整 uBO 的组合；过滤列表 auto-update 必须开 |
| 电脑（不想换浏览器） | Brave，Shields 调 Aggressive | 0 | 内置 Rust 引擎，不受 MV3 限制 |
| 电脑（死守 Chrome） | uBO Lite / AdGuard MV3 | 0 | 效果最差一档，修复要等商店审核 |
| 安卓（要 App 内） | ReVanced，官方 Manager 自己打补丁 | 0 | 每几周要重打；**现成 APK 站点基本是木马** |
| 安卓电视/盒子 | SmartTube | 0 | 需侧载 |
| iPhone | Brave / Safari + 内容拦截器 | 0 | App 内拦不住，这是 iOS 硬限制 |
| 想全设备省心 | Premium Lite / Premium | $7.99 / $13.99 每月 | Lite 不含音乐视频去广告 |

## 国内名单：只加国外列表等于没装

StevenBlack / HaGeZi / OISD 对微信、抖音、淘宝、B 站 App 内广告**基本无效**。必须加国内源。实测可用（URL 均返回 200）：

```
AdGuard DNS filter  https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt
HaGeZi Multi PRO    https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt
anti-AD（国内）      https://anti-ad.net/easylist.txt
OISD Big            https://big.oisd.nl/domainswild
```

上游用国内 DoH 防污染：`https://dns.alidns.com/dns-query` + `https://doh.pub/dns-query`。

## 部署顺序（NAS 上已有 AdGuard Home 的典型路径）

1. **先探测现状**，别凭记忆：`:3000` 返回 302 `/login.html` = AdGuard Home；`/control/install/get_addresses` 返回 403 = 认证已开。
2. **证实它到底有没有在拦**——登录页在跑不代表过滤器在工作，用 `check_dns_blocking.py`（见 `untrusted-code-audit`）打一发 `doubleclick.net`；常见结果是返回真实 IP（列表没启用）。
3. 加名单 + 上游 DoH + 把路由器 DHCP 的 DNS 指向 NAS。
4. 客户端层单独配（表 3），**不要承诺 DNS 能解决 YouTube**。
5. 提醒单点故障：NAS 重启/休眠时全屋断解析；要兜底就配第二个解析器（第二台设备或公共 AdGuard DNS）。

## 管理员密码丢了（用户常见，且你没有 SSH 凭据）

**不要在聊天里索要或接收密码。** 两条路，都让用户在 DSM「控制面板 → 任务计划 → 新增 → 用户定义的脚本 → 用户 root」里粘一次：

- **A. 授权公钥**（推荐，之后全部由你远程做）：`for H in /root /var/services/homes/admin; do mkdir -p $H/.ssh; echo '<你的公钥>' >> $H/.ssh/authorized_keys; chmod 700 $H/.ssh; chmod 600 $H/.ssh/authorized_keys; done`
- **B. 一次性改配置**：跑 `scripts/agh-reset-auth.sh` —— AdGuard 的 `users: []` 等于关闭认证（官方 wiki），重启后直接进后台设新密码；脚本自带备份、健康检查和失败回滚。

写这种配置脚本前必须先本地验证：造一份合成 YAML，跑同一段 `awk`，用 PyYAML 解析确认 `users` 变成 `[]` 且其它键原样保留（PyYAML 缺失就 `uv pip install pyyaml --default-index https://mirrors.aliyun.com/pypi/simple/`）。YAML 写坏的后果是全屋断解析。

## 报告形状（这个用户）

结论先行，表格优先，0 元方案排第一：

1. **一句话答案**：哪个最合适 + 哪个方向根本无用（例："DNS 那套对 YouTube 零效果"）。
2. 按设备一张表（电脑/安卓/iPhone/电视），每行给方案、价格、效果、代价。
3. 他要的那台设备给逐步操作；其他设备一段带过。
4. 诚实写上限与时间表（SSAI、免费云档超限行为、Chrome 已无 uBO）。
5. 结尾一个问题定方向："你主要在哪个设备上看？"——不要一次抛五个问题。

## 陷阱

1. **别在用户说出真实目标前就铺开整套 DNS 方案**——先问设备/场景，再选层级；否则 YouTube 这类目标会让整篇报告作废。
2. **"有 AdGuard Home" ≠ "在去广告"**：默认安装后列表可能没启用，必须发真实查询验证。
3. **推荐 Chrome 上的 uBlock Origin 是错的**：Chrome 138 起 MV2 全禁，扩展已从商店下架；Chrome 只能给 uBO Lite / AdGuard MV3，并说清会漏。
4. **云免费档超限是"停止过滤"不是"断网"**，别吓唬用户，也别隐瞒。
5. **ESP32/Pi-hole 小盒对个人用户没有性价比**——已有 NAS 的人，0 元的 AdGuard Home 全面胜出；只在"NAS 挂了兜底"这个场景才值得买。
6. **改 YAML 前先备份 + 合成样例验证 + 重启后健康检查回滚**，三件套缺一个就可能把用户家 DNS 弄挂。

## 参考

- `references/youtube-ad-blocking.md` — YouTube 广告为什么拦不住（含 SSAI 时间线）、各客户端方案现状、失败排查。
- `scripts/agh-reset-auth.sh` — AdGuard Home 忘记后台密码时关闭认证并安全重启（带备份与回滚）。
- 审计第三方广告盒/固件：`untrusted-code-audit`；NAS 上跑脚本与提权：`synology-nas-remote-ops`。
