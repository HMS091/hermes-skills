# Nextcloud Talk 跨网通话排障 — 现场诊断记录（NAS 双实例案例）

来源：2026-08 会话。用户环境：Synology NAS Docker 部署 Nextcloud，WiFi 通话正常、4G/5G 失败。

## 现场架构（诊断时确认）
- 两个 Nextcloud 实例并存：
  - `nextcloud` (端口 9800, 域名 nextcloud.skyforgelabs.qzz.io) → coturn `talk-coturn` (3478)
  - `nextcloud2` (端口 9801, 域名 nc.ncncnc.ccwu.cc) → coturn `talk-coturn2` (3479)
- `talk-signaling2` (strukturag/nextcloud-spreed-signaling, HPB 信令) 也部署了；signaling-proxy.conf 经 Apache 反代 `/standalone-signaling/` → `172.21.0.1:8082`
- 网络拓扑：主路由 192.168.1.2（Tenda，拨号），旁路由 192.168.1.88（OpenWrt LuCI，仅代理），NAS 默认路由走旁路由（ovs_eth1/192.168.1.201），coturn relay-ip 绑 192.168.1.200
- 家宽有真实公网 IP（成都电信 AS4134），动态分配

## 根因
Nextcloud 数据库中的 `spreed turn_servers` 配的是**内网 IP**：
```
nc1: [{"schemes":"turn,turns","server":"192.168.1.200:3478","secret":"...","protocols":"udp,tcp"}]
nc2: [{"schemes":"turn,turns","server":"192.168.1.200:3479","secret":"...","protocols":"udp,tcp"}]
```
WiFi 手机与 NAS 同网段 → 内网地址可达 → 通话正常；4G/5G 拿到私有地址 → TURN 不可达 → 通话失败。
另外公网 3478 未做端口转发（实测公网 UDP/TCP 均不通），且 coturn external-ip 是过期公网 IP。

## 诊断命令序列（可复用）
```bash
# Synology docker 定位（不在 PATH）
command -v docker || /usr/local/bin/docker

# 容器清单 + 端口
docker ps --format "{{.Names}} | {{.Ports}}"
docker port talk-coturn
docker inspect talk-coturn --format "net={{.HostConfig.NetworkMode}} cmd={{json .Config.Cmd}}"

# coturn 配置（容器内 /etc/coturn/turnserver.conf）
docker exec talk-coturn sh -c "grep -vE '^#|^$' /etc/coturn/turnserver.conf"

# Nextcloud TURN 配置在数据库而非 config.php
docker exec -u www-data nextcloud php occ config:app:get spreed turn_servers
docker exec -u www-data nextcloud php occ config:app:get spreed stun_servers

# config.php 权限拒绝时从容器内读
docker exec nextcloud grep -nE "trusted_domain|overwrite|instanceid" /var/www/html/config/config.php

# coturn 是否监听（局域网 STUN 探测 → 0x0101 成功）
python stun_probe.py 192.168.1.200 3478

# 公网 IP 探测（多服务交叉验证；ipify/ifconfig.me 在本环境返回异常 35.224.x.x，ip.3322.net 返回真实出口）
curl -s http://ip.3322.net

# 公网端口可达性（TCP + UDP STUN）
timeout 6 bash -c "cat < /dev/null > /dev/tcp/<ip>/3478" && echo open
python stun_probe.py <公网IP> 3478   # 注意 NAT hairpin 限制

# NAS 默认路由/拓扑
ip route | head -5
```

## 发现的错误模式（同类问题直接对照）
1. **turn_servers 配内网 IP** — 最常见根因，WiFi 通/4G 不通的典型特征
2. **coturn external-ip 配成内网 IP**（talk-coturn2 就是 `external-ip=192.168.1.200`）— 客户端拿到的中继地址不可达
3. **external-ip 写死动态公网 IP** — 宽带重拨后 IP 变化即失效，需 DDNS
4. **端口转发配在旁路由上** — 入站流量根本不经过旁路由，必须配主路由
5. **config.php 里 grep 不到 talk 配置就以为没配置** — 实际在数据库 oc_appconfig

## Metered.ca 评估结论（2026-08 调研）
- Nextcloud turn_servers 只支持 secret 模式（use-auth-secret，服务端 HMAC 生成临时凭据）
- Metered TURN 是 username/password 静态凭据（REST API `https://<app>.metered.live/api/v1/turn/credentials?apiKey=` 获取）
- 认证机制不兼容 → Metered 无法接入 Nextcloud Talk
- 其文档站 www.metered.ca/docs（TURN Server Service 分类）无 Nextcloud 集成页；llms.txt 也不存在（404）
- 托管 TURN 评估要点：第一步确认是否支持 static-auth-secret

## 待办（本会话未完成，后续续接）
- 用户在主路由 (192.168.1.2 Tenda, SLP 框架界面) 配置 TCP+UDP 3478 → 192.168.1.200 端口转发（3479 给 nc2）
- 更新 talk-coturn external-ip 为当前公网 IP；修复 talk-coturn2 external-ip（现为内网）
- 改两个实例 turn_servers 地址为公网；手机 4G 实测
- NAS 出站默认路由走旁路由（用户要求走主路由提速；tmm 无 sudo，需 DSM admin 或 root）
