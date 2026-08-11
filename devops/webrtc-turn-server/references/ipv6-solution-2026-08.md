# Nextcloud Talk 4G 通话 IPv6 方案完整排障记录（2026-08 实测成功）

环境：NAS 192.168.1.200/201（Synology，Docker），主路由 TP-LINK TL-ER6229GPE-AC（192.168.1.2:9000，PPPoE 拨号），旁路由 OpenWrt（192.168.1.88，代理），运营商电信 CGNAT（无公网 IPv4），已开通 IPv6（240e:39e:396:6520::/64，动态前缀）。两个 Nextcloud：nextcloud:9800（skyforgelabs.qzz.io / nextcloud.skyforgelabs.qzz.io）、nextcloud2:9801（nc.ncncnc.ccwu.cc）。

## 症状时间线
1. WiFi 能通话，4G/5G 完全不通（TURN 配内网 IP + CGNAT）
2. Metered 免费 Open Relay 停摆、付费版认证不兼容 → 排除托管 TURN
3. IPv6 方案：路由器 SLAAC 配置成功 → NAS 拿到公网 IPv6
4. 配置 coturn IPv6 + HPB [turn] 段 + Nextcloud turn_servers 后 4G 通话成功（P2P IPv6 直连，30 秒建立）
5. STUN 优化尝试失败回滚；域名 DNS 记录丢失导致断连

## 路由器 IPv6 配置（TP-LINK ER6229GPE-AC）
- 「基本设置」→「接口设置」：IP协议类型 IPv6 → EUI-64 → 前缀授权接口 WAN1 → 保存
  - 自动生成：IPv6地址前缀 240e:39e:396:6520::，IP地址 240e:39e:396:6520:7eb5:9bff:fee0:40d9（EUI-64 基于路由器 MAC 7C-B5-9B-E0-40-D9）
  - 保存时网络短暂中断属正常
- 「基本设置」→「LAN设置」→「SLAAC」→ 新增：服务接口 LAN、前缀留空（自动）、DNS配置方式 DHCPv6、状态启用
- 「安全管理」→「IPv6防火墙」：启用=拦入站（4G 手机连不上家里）；需关闭或加放行规则
- 注意：开 IPv6 后路由器下发 IPv6 为 DNS 服务器，其 IPv6 DNS 转发有 bug（域名解析失败），Windows 上 nslookup 会报"不存在的记录"——不是域名问题

## 旁路由干扰（必须先处理）
OpenWrt odhcpd 默认 dhcp.lan.ra='server' 通告 ULA（fd87:）并自封 router → 抢在主路由前。关闭：
```
uci set dhcp.lan.ra='disabled'
uci set dhcp.lan.dhcpv6='disabled'
uci commit dhcp
/etc/init.d/odhcpd restart
```

## NAS (Synology) IPv6
- DSM 控制面板→网络→网络接口→编辑→IPv6→「自动」；默认 accept_ra=0（收不到 RA），设自动后变 2
- 手动配过静态：/etc/sysconfig/network-scripts/ifcfg-ovs_eth0（IPV6INIT=static/IPV6ADDR/IPV6PREFIXLENG/IPV6DNS + 网关需单独填）
- 网关坑：手动填 240e:…::1 或乱抄的 fe80 地址都会 ND FAILED；正确网关=路由器 LAN 的链路本地地址（fe80::7eb5:9bff:fee0:40d9）。交叉验证：链路本地 EUI-64 反推 MAC 与 ip neigh 的 IPv4 路由器 MAC 对比
- 普通用户无 ping 权限，出站验证用 `curl -6 https://api6.ipify.org`

## coturn IPv6（配置文件只读挂载自宿主机）
- 挂载：/volume1/docker/talk/coturn/turnserver.conf → /etc/coturn/turnserver.conf（rw=false）；tmm 可直接改宿主机文件
- **relay-ipv6 参数不存在**（coturn 4.12 报 "Bad configuration format: relay-ipv6"）→ 用 `relay-ip=<IPv6>`（relay-ip 支持 IPv6，可多行）
- 追加：`relay-ip=240e:…d0eb` + `listening-ip=::`
- 验证：日志 `relay 240e:… initialization done`；`turnutils_stunclient -p 3478 <IPv6>` 返回 IPv6 反射地址
- talk-coturn2 同理（/volume1/docker/talk2/coturn2/turnserver.conf，端口 3479）

## HPB 信令服务器（spreed-signaling）[turn] 段
- talk-signaling2 挂载 /volume1/docker/talk2/signaling2/server.conf（**不是 talk/signaling/server.conf**，多实例别改错文件）
- 缺失 [turn] 段 → 客户端拿不到 TURN → 4G 通话"能看到来电但不转圈"；补上后"转圈"（在尝试连接）
- 格式（IPv6 带方括号）：
```
[turn]
secret = <与coturn一致的secret>
url = turn:[240e:…]:3478?transport=udp
url = turn:[240e:…]:3478?transport=tcp
```
- 改后 `docker restart talk-signaling2`

## Nextcloud 配置
```
docker exec -u www-data <nc> php occ config:app:set spreed turn_servers --value='[{"schemes":"turn,turns","server":"[240e:…]:3478","secret":"…","protocols":"udp,tcp"}]'
docker exec -u www-data <nc> php occ config:app:set spreed stun_servers --value='["stun.nextcloud.com:443"]'
```
- 不用 --type=json（部分版本报错）
- ssh 双引号内 ${V6} 变量不会在远程展开（本地 shell 先展开成空）→ IPv6 地址要写死在单引号 JSON 里
- stun.nextcloud.com:443 国内不可达（curl 000）→ 30 秒建立
- **STUN 最终结论**：用户确认 IPv6 防火墙关闭后，手机 4G 访问 `http://[<NAS-IPv6>]:5000` 返回 **400 = 请求到达 DSM（入站通，400 是 HTTP 层响应不是失败）** → STUN 切 IPv6 coturn（`[\"[240e:…]:3478\"]`）为正确方向；此前"完全不通"是因为当时 IPv6 入站被防火墙拦。改 STUN 后须杀 App 重开才生效
- 用户已声明 IPv6 防火墙永久关闭，**不要再让用户确认/开关防火墙**（明确摩擦点）

## 排障技巧
- coturn 日志零 TURN 会话 = P2P IPv6 直连成功（不走中继）
- 改配置后手机 App 必须杀进程重开（缓存旧配置→同一配置时通时不通的假象）
- 域名 DNS 记录丢失：`nslookup <域名> 223.5.5.5` 无 A/AAAA（主域正常）= 记录被删；手机靠缓存撑 TTL（30分钟）后完全断连。qzz.io 在 Cloudflare、ccwu.cc 在 FreeDNS（he.net）

## 遗留/下一步
- IPv6 前缀动态（PPPoE 重拨可能变）→ 需 DDNS/动态更新 AAAA；排查"又断连"先对比 `ip -6 addr show` 与配置写死地址
- NAS 443 证书过期（HTTPS 直连需修复）
- IPv6 防火墙已由用户确认关闭（不会再开）；未配置精准放行规则（临时靠关闭）
- 视频预览"小窗上一块黑"：两个 iPhone 复现 = 软件层；GitHub issues（spreed/talk-android/talk-ios）无完全匹配，talk-ios 最新 v24.0.2（含 #2587 重协商修复）；分层测试（浏览器 vs App）定位，上下对称黑边=letterbox 正常，单侧黑边=bug 待报
- 通话加密已确认：WebRTC DTLS-SRTP 端到端加密（官网 encrypted calls），可答复用户隐私疑虑
