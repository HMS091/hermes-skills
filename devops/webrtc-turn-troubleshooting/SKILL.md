---
name: webrtc-turn-troubleshooting
description: 排查 WebRTC 通话（Nextcloud Talk/Matrix/Jitsi）跨网络连不上、TURN/STUN 配置与 coturn 排障、CGNAT 判断、托管 TURN 方案选型（Metered 等）
---

# WebRTC TURN/STUN 故障排查（Nextcloud Talk / Matrix / Jitsi）

## 触发场景
- 自建服务（Nextcloud Talk、Matrix、Jitsi）语音/视频通话**同一 WiFi 内正常**，但**跨网络（4G/5G 或异地）无法接通**
- TURN/STUN 服务器配置、coturn 排障、托管 TURN 选型
- 判断家宽是否 CGNAT、端口转发配了为何不生效

## 核心原理
WebRTC 优先 P2P；严格 NAT（4G/5G 运营商网络、企业防火墙）下打洞失败，必须经 TURN 中继。
**"WiFi 通、4G/5G 不通" = TURN 缺失或不可达**（铁律）。原因：TURN 配成内网 IP 时，WiFi 用户同局域网可用；4G 手机拿到内网 TURN 地址必然连不上。

## 排查流程（按顺序）

### 1. 读服务端 TURN 配置
Nextcloud 的 TURN 配置在**数据库**（app=spreed），不在 config.php（config.php 里 grep 不到是正常的）：
```bash
docker exec -u www-data <nc容器> php occ config:app:get spreed turn_servers
docker exec -u www-data <nc容器> php occ config:app:get spreed stun_servers
```
- 常见故障：`server` 字段是内网 IP（如 192.168.1.200:3478）→ 公网客户端连不上
- 修改（turn_servers 是 JSON 字符串数组）：
```bash
docker exec -u www-data <nc容器> php occ config:app:set spreed turn_servers --value='[{"schemes":"turn","server":"host:port","secret":"...","protocols":"udp,tcp"}]'
```
- **老版本 occ 不支持 `--type=json`**（报 `Unknown type json`）→ 直接存 JSON 字符串即可，Talk 读取时自行 json_decode；`schemes` 取值 turn / turns / turn,turns，界面里的 "turn:only" 即 schemes=turn

### 2. 检查 coturn
容器内 `/etc/coturn/turnserver.conf` 关键项：
- `use-auth-secret` + `static-auth-secret=<secret>`（必须与 Nextcloud 的 secret 一致）
- `external-ip=<公网IP>/<内网IP>`（relay 通告地址）——**家用宽带公网 IP 动态变化，external-ip 会过期**，通话忽然全挂先查它
- `realm=`、`listening-port=3478`、`relay-ip=`
- 验证 coturn 本身正常：局域网内 STUN 测试能通即可（见 scripts/stun_test.py）

### 3. 测公网可达性（STUN Binding）
UDP 发 STUN Binding Request（type=0x0001 + magic cookie 0x2112A442 + 12B 随机 transaction id），收到 0x0101 即通。用 scripts/stun_test.py。
- coturn 镜像自带 `turnutils_stunclient`：用法是 `turnutils_stunclient -p <port> <host>`（`-p` 指定端口，别把端口当位置参数）
- **局限**：从局域网内测自家公网 IP 走 NAT hairpin，很多路由器不支持，测不通 ≠ 转发没配好；必须从真实公网（4G 手机/在线工具）验证

### 4. 判断 WAN 是否 CGNAT（关键分叉）
路由器 WAN IP 落在 **100.64.0.0/10**（100.64.x.x~100.127.x.x）= 运营商大内网：
- **端口转发配了也无效**（公网流量到运营商 NAT 网关就停）
- 出路：打运营商客服（电信 10000）申请公网 IP（家宽一般免费）；或托管 TURN / 云服务器 coturn
- 注意：从 NAS 出口查到的公网 IP 是**运营商共享出口**，不是路由器 WAN IP；以路由器 WAN 口显示为准

### 5. 拓扑确认
- **入站端口转发必须配在主路由**（公网流量先到主路由）；旁路由只做代理网关，入站不经过它，配了没用
- NAS 默认路由走旁路由（代理）时，UDP 出站可能被代理规则劫持/丢弃——测 UDP 不通先排除这条链路（TCP 通则说明外网基本可达）

## 解决方案选型

| 方案 | 条件 | 特点 |
|------|------|------|
| 自建 coturn + 主路由端口转发 | 有真实公网 IP | 零成本、国内直连低延迟；IP 动态需 DDNS 或定期改 external-ip |
| Metered Open Relay（免费托管） | 无需公网 IP | 立即生效、零配置成本；仅加拿大节点，国内延迟 150-250ms；20GB/月免费 |
| 云服务器自建 coturn | CGNAT/无公网 IP | ¥30-50/月，选香港/新加坡节点低延迟，一劳永逸 |

**Metered 兼容性易踩坑**：
- 付费版 TURN（global.relay.metered.ca）是 username/password 认证 → **不兼容 Nextcloud**（Nextcloud 只要 auth-secret 静态密钥模式）
- 免费 Open Relay 提供 staticauth 端点 → 兼容 Nextcloud/Matrix，配置详见 references/metered-openrelay-nextcloud.md

## Pitfalls
- 本机（Windows）配置了系统代理时：curl 走代理、bash /dev/tcp 和 python socket 直连——同一目标测试结果可能不同，先分清测试走哪条链路
- stun.l.google.com 在国内可能不可达，别依赖它当 STUN
- 多 DNS（8.8.8.8 / 223.5.5.5 / 223.5.5.5）解析 TURN 域名，可判断服务商是否有亚洲/本地节点（决定延迟）
- 改完 Nextcloud TURN 配置后即时生效，无需重启容器
- 免费托管 TURN 的共享 secret（如 openrelayprojectsecret）是全互联网公开的，仅适合个人使用场景，注意隐私边界（媒体流本身端到端加密）

## 支持文件
- scripts/stun_test.py — UDP STUN 可达性探测脚本
- references/metered-openrelay-nextcloud.md — Metered Open Relay 完整接入参数与 occ 命令
