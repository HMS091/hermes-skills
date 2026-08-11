# Metered Open Relay 接入 Nextcloud Talk（2026-08 实测验证）

来源: https://www.metered.ca/tools/openrelay/#turn-server-for-nextcloud-talk

## 兼容性结论（易踩坑）
- **付费版** TURN（global.relay.metered.ca）：username/password 认证（REST API `GET https://<app>.metered.live/api/v1/turn/credentials?apiKey=...` 返回 username+credential）→ **不兼容 Nextcloud**，Nextcloud Talk 只支持 auth-secret（静态密钥 HMAC）模式
- **免费 Open Relay**：提供 staticauth 端点 → 兼容 Nextcloud / Matrix+Synapse（文档明确写了 Matrix）

## 配置参数（实测有效）
- TURN 服务器 1: `staticauth.openrelay.metered.ca:80`（schemes=turn, protocols=udp,tcp）
- TURN 服务器 2: `staticauth.openrelay.metered.ca:443`（schemes=turn, protocols=udp,tcp）
- secret: `openrelayprojectsecret`（公开共享密钥，所有用户通用，无需注册）
- STUN: `staticauth.openrelay.metered.ca:80`
- 免费额度：20GB/月；跑在 80/443 便于穿透防火墙；支持 UDP/TCP/TURNS

## occ 配置命令（两个实例实测成功）
```bash
# 读
docker exec -u www-data <容器> php occ config:app:get spreed turn_servers
docker exec -u www-data <容器> php occ config:app:get spreed stun_servers

# 写（注意：老版本 Nextcloud 的 occ 不支持 --type=json，直接存 JSON 字符串）
docker exec -u www-data <容器> php occ config:app:set spreed turn_servers --value='[{"schemes":"turn","server":"staticauth.openrelay.metered.ca:80","secret":"openrelayprojectsecret","protocols":"udp,tcp"},{"schemes":"turn","server":"staticauth.openrelay.metered.ca:443","secret":"openrelayprojectsecret","protocols":"udp,tcp"}]'
docker exec -u www-data <容器> php occ config:app:set spreed stun_servers --value='["staticauth.openrelay.metered.ca:80"]'
```
改后即时生效，无需重启容器。界面等效操作：管理员 → 设置 → Talk → TURN servers → + 添加（schemes 选 turn:only，secret 填 openrelayprojectsecret）。

## 网络表现（中国大陆视角）
- `staticauth.openrelay.metered.ca` 解析到 **216.39.253.123（加拿大 Toronto, AS399858, 单一节点）**——无论从 8.8.8.8 / 1.1.1.1 / 223.5.5.5 解析都是同一 IP，无亚洲节点
- 国内 TCP 443 可达（实测 NAS→443 通）；UDP 80/443 可能被运营商 QoS 或旁路由代理链路影响
- 预期延迟 150-250ms：语音可通但延迟明显；免费版无法选区域
- 付费版 global.relay.metered.ca 解析到 Vultr 日本节点（158.247.x.x），有全球节点但认证不兼容 Nextcloud

## 适用决策
- 无公网 IP / CGNAT / 不想动路由器的场景：先用它"让 4G 能通"
- 长期体验优化：申请公网 IP 自建 coturn（国内直连零延迟），或云服务器选香港/新加坡节点
