---
name: coturn-turn-server
description: TURN/coturn 服务器配置与 WebRTC 跨网通话排障（Nextcloud Talk 等）。症状：WiFi/局域网通话正常但 4G/5G 或异地失败；自建 TURN 端口转发；托管 TURN 服务（如 Metered.ca）兼容性评估。
---

# coturn / TURN 服务器配置与排障

## 触发条件
- WebRTC 通话（Nextcloud Talk / Jitsi / Matrix）局域网 WiFi 正常，4G/5G 或跨网络失败
- 配置 coturn：external-ip、use-auth-secret、listening-port
- 路由器端口转发 TURN 端口（3478 等）
- 评估托管 TURN 服务（Metered.ca、Twilio 等）能否接入自建应用

## 核心诊断流程

### 1. 症状 → 根因定位
- **WiFi 正常 + 4G/5G 失败 ⇒ TURN 服务器问题**（移动网络是严格 NAT，P2P 打洞失败，必须 TURN 中继；WiFi 同局域网内网可达所以能通）
- 完全不通 ⇒ 信令/端口/其他问题

### 2. 检查 TURN 配置在哪里（Nextcloud 特有）
- Nextcloud Talk 的 TURN 配置存在**数据库**（oc_appconfig），**不在 config.php**，config.php grep 为空是正常的：
  ```
  docker exec -u www-data <nc容器> php occ config:app:get spreed turn_servers
  ```
- 返回值 JSON 格式：`[{"schemes":"turn,turns","server":"host:port","secret":"...","protocols":"udp,tcp"}]`
- **经典错误：server 字段填内网 IP**（如 `192.168.1.200:3478`）→ WiFi 同局域网能通，4G/5G 手机拿到私有地址必然失败。修复时改成公网 IP 或域名。

### 3. 检查 coturn 容器配置
- 配置文件：`/etc/coturn/turnserver.conf`（容器内，`docker exec <coturn> cat`）
- 关键项：
  - `listening-port=3478` / `tls-listening-port=5349`
  - `external-ip=<公网IP>/<内网IP>` — 通告给客户端的地址；**配成内网 IP 是常见错误**
  - `use-auth-secret` + `static-auth-secret=<密钥>` — 必须与 Nextcloud turn_servers 的 secret 一致
  - `realm=<域名>`
- 局域网内验证 coturn 活着：对 `内网IP:3478` 发 STUN binding request，收到 type=0x0101 即正常（见 scripts/stun_probe.py）

### 4. 公网可达性验证（关键：NAT hairpin 陷阱）
- UDP 用 STUN binding request 探测（scripts/stun_probe.py）；TCP 用 `timeout 6 bash -c "cat < /dev/null > /dev/tcp/<ip>/3478" && echo open`
- **NAT hairpin 陷阱：从局域网内测自己的公网 IP 不通 ≠ 端口转发失败**（很多路由器不支持回环）。必须从真公网验证：手机 4G 访问在线 STUN 测试页 / trickle-ice 页面（webrtc.github.io/samples/src/content/peerconnection/trickle-ice/），输入 `stun:<公网IP>:3478` 和 `turn:<公网IP>:3478`
- 公网 IP 探测要**交叉验证**：ipify/ifconfig.me 可能因 DNS 劫持/代理返回异常 IP，国内环境用 `curl http://ip.3322.net`（花生壳）更可靠

### 5. 端口转发配在"入站流量到达的设备"上
- 拓扑判断：NAS 上 `ip route` 看默认网关（gateway 是真正出网的设备）
- **旁路由陷阱**：主路由拨号 + 旁路由做代理网关时，端口转发必须配在**主路由**（公网入站流量先到它）；旁路由只处理代理出站，配在旁路由上无效
- 光猫路由模式 vs 桥接：若路由器 WAN IP 是 192.168.x（不是公网），说明光猫还挡一层，需在光猫上也转发或做 DMZ

## 修复 Nextcloud Talk 跨网通话（标准动作）
1. 路由器（主路由）端口转发：TCP+UDP 3478 → NAS 内网 IP（第二条实例用不同端口如 3479 时各加一条）
2. coturn external-ip 更新为当前公网 IP —— **家庭宽带 IP 动态变化，写死会过期**，长期方案用 DDNS 域名
3. 改 Nextcloud turn_servers 为公网地址：
   ```
   docker exec -u www-data <nc容器> php occ config:app:set spreed turn_servers \
     --value='[{"schemes":"turn,turns","server":"<公网IP或域名>:3478","secret":"<原secret不变>","protocols":"udp,tcp"}]' --type=json
   ```

## 托管 TURN 服务评估（Metered.ca 等）
- Nextcloud Talk 的 turn_servers **只支持 secret 模式**（use-auth-secret：Nextcloud 服务端用 secret 生成临时凭据 username=unix时间戳 / password=base64(hmac_sha1(secret, username))）
- Metered.ca 提供的是 **username/password 静态凭据**（REST API `api/v1/turn/credentials` 生成），**认证机制不兼容，无法接入 Nextcloud Talk**；它的文档（www.metered.ca/docs）也没有 Nextcloud 集成页
- 评估任何托管 TURN 服务，第一步确认认证模式；不支持 static-auth-secret 的直接排除

## coturn IPv6 配置（无公网 IPv4 时经 IPv6 直连，2026-08 实测）
- **`relay-ipv6=<ip>` 参数不存在**：coturn 4.12 报 `WARNING: Bad configuration format: relay-ipv6` 且 IPv6 relay 不初始化（日志只出现 IPv4 relay）。用 **`relay-ip=<IPv6地址>`**（该参数支持 IPv6，可多行），另加 `listening-ip=::`
- 配置文件常**只读挂载**（容器内 /etc/coturn/turnserver.conf 不可写）：`docker inspect <coturn> --format '{{range .Mounts}}{{.Source}} => {{.Destination}} (rw={{.RW}}){{println}}{{end}}'` 找宿主机路径（如 /volume1/docker/talk/coturn/turnserver.conf），直接在宿主机改（tmm 可写）再 `docker restart`
- 验证 IPv6 中继生效：日志出现 `relay <IPv6> initialization done`；`turnutils_stunclient -p <port> <IPv6>` 返回 IPv6 反射地址
- 客户端 TURN 配置由信令服务器（spreed-signaling HPB）下发：其 server.conf 必须有 `[turn]` 段（secret + `url = turn:[IPv6]:端口?transport=udp/tcp`），缺了客户端拿不到 TURN 候选（症状："能看到来电但无连接动作"）

## 陷阱清单
- Synology NAS：docker 不在 PATH，用 `/usr/local/bin/docker` 或 `command -v docker` 定位
- config.php 普通用户读不了（Permission denied）→ `docker exec <nc容器> grep ... /var/www/html/config/config.php`
- SSH 用户无 sudo（改路由/网络需 DSM admin）；host 网络容器共享宿主 netns 但精简镜像常无 ip/route 命令
- Nextcloud 有两个实例时（nextcloud / nextcloud2）各配一套 coturn + turn_servers，容易只修一个
- 诊断前先查记忆/问清网络拓扑（主路由/旁路由/光猫桥接），避免在错误的设备上配置

## 支持文件
- scripts/stun_probe.py — STUN/UDP 端口探测脚本（验证 TURN 公网可达性）
- references/nextcloud-talk-debug.md — 完整诊断命令序列 + 现场发现的错误模式（NAS 双实例案例）
