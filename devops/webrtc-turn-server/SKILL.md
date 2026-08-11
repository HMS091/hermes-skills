---
name: webrtc-turn-server
description: 诊断和修复 WebRTC 通话问题（Nextcloud Talk / Matrix / Jitsi）：WiFi 能通但 4G/5G 不通 = TURN 服务器缺失或不可达。覆盖 Nextcloud occ 配置检查（配置在数据库不在 config.php）、coturn 容器排查、STUN/端口探测、CGNAT 识别、托管 TURN 服务评估（Metered 等）、修复方案（公网IP转发 / 云服务器 coturn / Cloudflare TCP 隧道）。用户是中文非技术用户，全程代操作，需用户亲自做的步骤（打运营商电话、登录路由器、注册云账号）给话术/截图级指引。
---

# WebRTC TURN 服务器诊断与修复

## 触发条件
- WebRTC 通话（Nextcloud Talk / Matrix / Jitsi）WiFi 正常、4G/5G 无法接通
- TURN/STUN 服务器配置排查、coturn 容器排障
- 家庭网络端口转发、运营商 CGNAT 判断
- 评估托管 TURN 服务（Metered 等）对 Nextcloud 的兼容性

## 核心原理（30 秒版）
- WebRTC 先试 P2P 直连 → STUN 辅助打洞 → TURN 兜底中继
- WiFi（同网段/宽松 NAT）可 P2P 直连；4G/5G 是运营商严格 NAT，打洞必失败，**必须有 TURN 且公网可达**
- "WiFi 通、4G 不通"几乎 100% 指向 TURN：未配置 / 配了内网 IP / TURN 服务器公网不可达

## 诊断工作流（按序执行）

### 1. 读应用侧 TURN 配置（最快定位病根）
- **Nextcloud Talk 的 TURN 配置存在数据库（oc_appconfig 表），不在 config.php**！grep config.php 找不到是正常的
- 读取：`docker exec -u www-data <nc容器> php occ config:app:get spreed turn_servers`
- 读取：`docker exec -u www-data <nc容器> php occ config:app:get spreed stun_servers`
- 典型病根：`server` 字段是内网 IP（如 `192.168.1.200:3478`）→ WiFi 通（同网段可达）、4G 死（私有地址公网不可路由）

### 2. 检查 TURN 服务器（coturn）
- 找容器：`docker ps | grep -i coturn`
- 看配置：`docker exec <coturn容器> cat /etc/coturn/turnserver.conf`
- 关键项核对：`listening-port`、`external-ip`（必须公网 IP 或域名，配成内网 IP 或过期公网 IP 都是病根）、`use-auth-secret` + `static-auth-secret`（必须与 Nextcloud 的 secret 一致）、`realm`
- 监听验证：局域网内发 STUN binding（见 scripts/stun_probe.py），响应 type 0x0101 = 服务正常

### 3. 端口公网可达性测试
- TCP：`timeout 6 bash -c "cat < /dev/null > /dev/tcp/<host>/<port>" && echo OPEN`
- UDP STUN：scripts/stun_probe.py 或 coturn 容器内 `turnutils_stunclient -p <port> <host>`
- ⚠️ **在局域网内测自己公网 IP 受 NAT hairpin 限制，不通 ≠ 转发失败**；最终以手机 4G 实测为准

### 4. CGNAT 识别（转发配了也白配的情况）
- 路由器 WAN IP 落在 **100.64.0.0/10**（100.64.x.x ~ 100.127.x.x）= 运营商大内网，入站端口转发无效
- 确认方法：路由器 WAN 状态页，或 `curl http://ip.3322.net`（国内出口视角，比 ipify 可信；ipify 可能被解析到代理/异常）
- 出路：打运营商电话申请公网 IP / 云服务器 / Cloudflare 隧道

### 5. 评估托管 TURN 服务（如 Metered.ca）
- 判定 TURN 服务是否真活着（端口开 ≠ 服务在）：用与 Nextcloud 同款认证模式实测——
  `docker exec <coturn容器> turnutils_uclient -W <secret> -e <peerIP> -p <port> <server>`（-W = REST/auth-secret 模式）
- Metered 结论（2026 实测）：免费 Open Relay（staticauth.openrelay.metered.ca + openrelayprojectsecret）已停摆（TCP 端口开但 STUN/TURN/HTTPS 全无响应）；付费版仅 username/password 认证，与 Nextcloud 的 auth-secret（HMAC）**不兼容**
- 详见 references/turn-providers.md

## 修复路径（按推荐序）
- **A. 申请公网 IP + 路由器端口转发**（免费、国内直连、质量最优）
  - 话术："我家宽带需要公网 IPv4 用于 NAS 远程访问"（电信 10000）
  - 主路由（拨号那台）转发 UDP+TCP 3478 → NAS；注意拓扑：光猫/主路由/旁路由三层，入站转发必须配在**拨号的主路由**上，旁路由（代理网关）不接收入站流量
  - 更新 coturn external-ip + Nextcloud turn_servers 为公网地址
- **B. 云服务器 coturn**（CGNAT 不给公网时）
  - Oracle Cloud Always Free：ARM 4 核 24GB、10TB/月流量、东京/新加坡节点 → 首选
  - Google Cloud e2-micro：仅美区、1GB/月出站 → 国内不推荐
- **C. Cloudflare 隧道 TCP 暴露 3478**（零成本，仅 TURN over TCP，质量略逊；详见 cloudflare-tunnels skill。注意：Cloudflare 免费隧道只支持 HTTP(S)，任意 TCP 端口需付费 Spectrum，WebRTC 客户端又装不了 cloudflared，实际不可行）
- **D. IPv6 方案**（无公网 IPv4 时的免费尝试，见下节；前提是路由器固件支持 IPv6 LAN 通告——**企业路由器常没有**）

## IPv6 方案（无公网 IPv4 时的免费尝试）

原理：IPv6 无 NAT，家里设备拿到公网地址（240e: 等），4G 手机（运营商网络自带 IPv6）可直接连家里 coturn，绕开 CGNAT 和端口转发。**前提是路由器支持 IPv6 LAN 通告（SLAAC/RA）并正确下发公网前缀。**

快速判定路由器是否通告公网前缀：
- Windows 电脑 `ipconfig` 只有 fe80（链路本地）→ 路由器没下发公网 IPv6，方案不可行
- 路由器 WAN 状态页显示 240e 地址 ≠ LAN 能通告（很多路由器 WAN 自动获取 IPv6 但固件没有 LAN SLAAC 配置界面）

**TP-LINK ER6229GPE-AC 实测（2026-08）：固件支持完整 IPv6**，但菜单位置隐蔽——「传输控制」下确实没有 IPv6（那是 IPv4 NAT/带宽菜单），IPv6 全在「基本设置」里：
- 「基本设置」→「接口设置」：IP协议类型选 **IPv6** → 地址配置方式 **EUI-64** → 前缀授权接口 **WAN1**（自动填 IPv6地址前缀 240e:…::/64 + LAN IPv6 地址）→ 保存（提示网络会短暂中断，正常）
- 「基本设置」→「LAN设置」→「SLAAC」：**新增规则**（服务接口选 LAN、IPv6地址前缀留空=自动用路由器前缀、DNS配置方式 DHCPv6、状态启用）→ 保存
- 「安全管理」→「IPv6防火墙」：**启用状态下拦截外部入站**（4G 手机连不上家里 3478/9800）。入站放行是 4G 通话成败关键
- 配置完成判定：局域网设备出现 240e: 全局地址 + IPv6 默认路由，且 `curl -6 https://api6.ipify.org` 返回自己的 IPv6 = 全链路通
- ⚠️ 开 IPv6 后路由器可能把 IPv6 地址下发为本机 DNS 服务器，该企业路由器当 IPv6 DNS 转发器有 bug（域名解析失败），异常时改回 IPv4 DNS

坑：
- **旁路由 OpenWrt 会干扰 IPv6 通告**：odhcpd 默认 `dhcp.lan.ra='server'` 通告 ULA 前缀（fd87: 等）并宣告自己是 router，抢在主路由前面。关闭：`uci set dhcp.lan.ra=disabled; uci set dhcp.lan.dhcpv6=disabled; uci commit dhcp; /etc/init.d/odhcpd restart`（先 `cp /etc/config/dhcp /etc/config/dhcp.bak-xxx` 备份）
- **Synology NAS 手动配 IPv6**：配置文件 /etc/sysconfig/network-scripts/ifcfg-ovs_eth0（IPV6INIT=static、IPV6ADDR、IPV6PREFIXLENG、IPV6DNS），**网关要单独填**（DSM 界面「IPv6 网关」或 IPV6_DEFAULTGW）；`accept_ra` 内核参数 0→2 通过 DSM 网络接口设「自动」生效
- **ND 邻居诊断**：`ip -6 neigh show <gw>` 显示 FAILED/INCOMPLETE = 网关不存在或不可达（不是网络慢）；链路本地网关地址可反推 MAC（EUI-64：去掉 ff:fe、翻转 U/L bit），与 IPv4 邻居表（`ip neigh` 查路由器 MAC）交叉验证，能识破抄错的 fe80 地址
- NAS 普通用户无 ping 权限（`ping: socket: Operation not permitted`），验证出站用 `curl -6`

### IPv6 链路完整打通清单（2026-08 实测成功，4G 通话可用）
路由器 SLAAC 通后，还需四层配置缺一不可：
1. **coturn IPv6**：配置文件常只读挂载自宿主机（`docker inspect <coturn> --format '{{range .Mounts}}{{.Source}} => {{.Destination}}'` 找宿主机路径，tmm 可写）。追加：
   ```
   relay-ip=<NAS公网IPv6>       # ⚠️ 不是 relay-ipv6！coturn 4.12 无此参数（报 "Bad configuration format: relay-ipv6" 且 IPv6 relay 不初始化）
   listening-ip=::
   ```
   验证：`docker exec <coturn> turnutils_stunclient -p 3478 <NAS的IPv6>` 返回 IPv6 反射地址；日志出现 `relay <IPv6> initialization done` 才算 IPv6 中继生效
2. **HPB 信令服务器必须有 [turn] 段**（最易漏！客户端 TURN 配置由它下发）：spreed-signaling 的 server.conf 追加
   ```
   [turn]
   secret = <与coturn static-auth-secret 一致>
   url = turn:[<NAS公网IPv6>]:3478?transport=udp
   url = turn:[<NAS公网IPv6>]:3478?transport=tcp
   ```
   注意容器实际挂载的配置文件路径（多实例时易改错文件：talk2 的容器挂 talk2 目录的配置）；改后重启容器。**缺这段的症状：客户端"能看到来电但不转圈不连接"**（没拿到 TURN 候选）；补上后变"转圈"= 在尝试连接了
3. **Nextcloud turn_servers 用 IPv6**：`server` 字段写 `[<IPv6>]:3478`（带方括号）
4. **STUN 可达性**：`stun.nextcloud.com:443` 在中国大陆不可达（curl 返回 000）→ 通话建立被拖到 30 秒（ICE srflx 收集等超时）。改 STUN 为家里 IPv6 coturn 的前提是 **IPv6 入站通**——入站验证法：手机 4G 访问 `http://[<NAS公网IPv6>]:5000`（DSM 端口），**返回 400 = 请求已到达（连接通，400 不是失败）**，打不开/超时 = 入站被拦。2026-08 实测：用户确认 IPv6 防火墙关闭后，IPv6 入站通（400），STUN 切 IPv6 coturn 可行；入站不通时（防火墙拦）STUN 改 IPv6 会导致完全不通，只能回滚 stun.nextcloud.com（能通但 30 秒）。**改 STUN 后客户端须杀 App 重开才生效**

### 排障技巧（本次验证）
- **coturn 日志零 TURN 会话 = 通话是 IPv6 P2P 直连**（没走中继）——媒体通不通与 TURN 无关，问题在信令/TURN 配置下发
- 手机是否有 IPv6 的判定：4G 下浏览器访问 `https://api6.ipify.org`，返回 240e: 地址 = 有 IPv6
- **IPv6 地址未变但通话时通时不通**：先 `ip -6 addr show` 对比配置写死的地址（排除动态前缀变化），容器/服务正常且防火墙已关时，**几乎都是客户端缓存**——杀 App 重开
- **iOS Talk App 视频预览顶部黑边（两个 iPhone 同时复现 = 软件层）**：查 GitHub issues（nextcloud/spreed、talk-android、talk-ios，用 API `api.github.com/search/issues?q=repo:…`）无完全匹配（#16153 是虚拟背景相关）；分层测试定位——手机浏览器开 Talk 视频，同样黑边=WebRTC/服务器层，无=App 层；先更新 App Store 最新版（talk-ios v24.0.2 起有 renegotiation/PiP 修复 #2587/#2624），仍存在则截图发用户看（区分 letterbox 上下对称黑边=正常 vs 单侧黑边=bug）。上下都有黑边是画面比例适配（letterbox，正常现象），单侧黑边才是异常
- **隐私确认（用户常问）**：Nextcloud Talk 通话 = WebRTC 标准 **DTLS-SRTP 端到端加密**（官网 nextcloud.com/talk 标注 encrypted calls），密钥只在通话双方协商，服务器/信令/运营商均无法解密内容；IPv6 直连不经过第三方（比托管 TURN 元数据暴露更少）；元数据（双方 IP、时长、流量）对运营商与通话对方可见
- **改 Nextcloud 配置后手机 App 必须重开/重连才生效**（客户端缓存旧配置，导致同一配置有时通有时不通的假象）；多轮测试前先让用户杀 App 重开
- **域名 DNS 记录丢失症状**：域名在公共 DNS 解析不到（`nslookup <域名> 223.5.5.5` 无 A/AAAA 记录，主域正常）→ 手机 App 靠缓存还能用约 TTL 时长（如 30 分钟），缓存过期后完全连不上（来电都不显示）。检查 DNS 托管方：qzz.io 在 Cloudflare（NS fiona.ns.cloudflare.com）、ccwu.cc 在 FreeDNS（NS a.nic.dnshe.org）

## 关键命令速查
```bash
# Nextcloud TURN/STUN 配置（数据库）
docker exec -u www-data <nc容器> php occ config:app:get spreed turn_servers
docker exec -u www-data <nc容器> php occ config:app:set spreed turn_servers --value='[{"schemes":"turn","server":"host:port","secret":"...","protocols":"udp,tcp"}]'
# ⚠️ 不要加 --type=json（部分版本报 "Unknown type json"），直接存 JSON 字符串，Talk 读取时自行解析

# coturn 配置
docker exec <coturn> cat /etc/coturn/turnserver.conf
docker logs <coturn> | grep -iE "realm|auth|listening"

# TURN 实际分配测试（auth-secret 模式，与 Nextcloud 同款）
docker exec <coturn> turnutils_uclient -W <secret> -e 8.8.8.8 -p <port> <server>
# STUN 测试
docker exec <coturn> turnutils_stunclient -p <port> <server>
```

## 坑
- Nextcloud TURN 配置在数据库（occ config:app:get spreed turn_servers），grep config.php 是徒劳
- occ config:app:set 加 `--type=json` 会报 "Unknown type json"（部分版本），直接存 JSON 字符串
- coturn `external-ip` 配内网 IP 或过期动态公网 IP → 手机拿到通告地址连不上
- 家庭宽带公网 IP 是动态的：长期方案用 DDNS 域名，coturn 4.5+ external-ip 支持域名自动重解析
- 局域网内测公网端口有 hairpin 限制，判断转发成败以手机 4G 实测为准
- TURN 服务器宿主机的默认路由若指向旁路由（代理网关），UDP relay 流量可能被代理规则劫持/丢弃；改宿主路由需 root（可用 host 网络容器 `docker exec -u root` 改共享 netns，但精简容器里可能没有 ip/route 命令）
- 用户协作：不懂代码、中文、全程代操作；用户必须亲自做的（打运营商电话、登录路由器、注册云账号）给话术和截图级步骤，不要甩命令行
- **用户明确声明过的状态视为既定事实，不要反复确认**：如用户说"IPv6 防火墙已关、不会再开"后，后续排障不得再让用户确认/开关防火墙——多轮排障中重复问同一件事是明确的用户摩擦点（原话"以后不要再问这个问题"）。改配置前如需前提条件，先自查（日志/端口探测），确认不了的再一次性问清

## TP-LINK 企业路由器（9000 端口）操作经验

型号 TL-ER6229GPE-AC（普联，多 WAN 企业路由器），管理界面 http://192.168.1.2:9000，UI 是 JS + iframe 结构：
- **cua-driver 自动化点击无效**：后台 PostMessage 和前台 SendInput 对左侧菜单都不响应（JS 菜单不处理合成事件），**菜单点击必须用户真实鼠标**。协作模式：让用户点菜单项 → `get_window_state` 读 Edge/Chrome 地址栏 URL → 拿到真实页面名，之后尽量终端操作
- **curl API 模式**：`http://192.168.1.2:9000/stok=<token>/userrpm/<page>.htm`；stok 令牌**绑定来源 IP**（NAS 访问 401、浏览器所在本机 200）；部分页面即使带 stok 仍 404（浏览器有 Cookie 而 curl 没有，如 ipv6.htm）——所以页面存在性以浏览器为准，不要凭 curl 404 断定页面不存在
- 菜单树在 JS 里动态加载（tree.js / treestore.js 抓不到页面列表），页面真实文件名从浏览器地址栏或用户点击后的 URL 获取
- SSH/Telnet 默认关闭，无法命令行管理；**IPv6 配置不在「传输控制」而在「基本设置」→「接口设置」（IP协议类型选 IPv6）+「LAN设置」→「SLAAC」**
- 页面读取用 `cua-driver page action=get_text`（只读、无需 CDP）；`query_dom` 支持有限 tag（a/li/span/input），UIA 对自定义 radio（div.radio-unit 样式）不可见——单选靠用户点，文本靠 get_text 读
- 多标签页时 `get_window_state` 的地址栏 value 可能残留之前 set_value 的 URL（不代表实际导航），以页面 get_text 的实际内容为准

## 支持文件
- scripts/stun_probe.py — UDP STUN binding 探测脚本（验证 TURN/STUN 端口监听）
- references/nextcloud-talk.md — Nextcloud Talk TURN 配置机制、occ 命令、JSON 格式细节
- references/turn-providers.md — 托管 TURN 服务评估（Metered 等）实测结论
- references/ipv6-solution-2026-08.md — IPv6 方案完整排障记录（TP-LINK SLAAC 配置、coturn relay-ip、HPB [turn] 段、STUN/DNS 坑），2026-08 实测 4G 通话成功
