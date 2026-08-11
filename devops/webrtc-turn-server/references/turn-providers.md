# 托管 TURN 服务评估（2026-08 实测）

## Metered.ca — 不适用 Nextcloud
- **免费 Open Relay**（openrelay.metered.ca 项目，官方文档声称支持 Nextcloud）：
  - 端点 `staticauth.openrelay.metered.ca` + secret `openrelayprojectsecret`（公开凭据）
  - 配置指引：Nextcloud → 设置 → Talk → TURN servers 添加两条（:80 和 :443，schemes=turn）
  - **2026-08 实测已停摆**：DNS 解析正常（216.39.253.123，Toronto），TCP 80/443 端口开着（SYN-ACK 通），但 STUN binding、TURN 分配（turnutils_uclient -W）、HTTPS 全部无响应。判定 = 页面是 SEO 残留，服务已死
- **付费版**（dashboard.metered.ca 注册，`<app>.metered.live`，REST API 生成凭据）：
  - 认证是 username/password（长期或过期凭据），**与 Nextcloud 的 auth-secret（HMAC）不兼容**
  - 有全球/亚洲节点（global.relay.metered.ca 解析到日本 Vultr 等），但 Nextcloud 用不上
- 结论：Metered 两条路都对 Nextcloud Talk 不可用

## 判定托管 TURN 服务是否真活着的标准方法
1. 端口开着（TCP /dev/tcp 通）≠ 服务在
2. 用目标应用同款认证模式实测：
   ```bash
   docker exec <coturn容器> turnutils_uclient -W <secret> -e 8.8.8.8 -p <port> <host>
   ```
   有分配输出 = 活着；只有启动日志卡死 = 死了
3. 国内网络注意：UDP 到海外 IP 常被 QoS/丢包，TCP 更稳；4G 手机实测为准

## 免费云服务器跑 coturn 的评估
| 服务商 | 免费资源 | 亚太节点 | 出站流量 | 结论 |
|--------|---------|---------|---------|------|
| Oracle Cloud Always Free | ARM 4核24GB | 东京/大阪/首尔/新加坡/香港 | 10TB/月 | 首选（需国际信用卡验证） |
| Google Cloud Free Tier | e2-micro 1核1GB | 仅美国 | 1GB/月 | 国内不推荐（延迟+流量） |
| AWS Free Tier | t2.micro | 美区为主 | 100GB/月 | 仅12个月 |
| Azure | 200美元额度 | 部分 | 有限 | 仅1个月 |
| 阿里/腾讯云 | 新用户试用 | 国内 | - | 仅几周 |

## 家庭宽带 CGNAT 要点
- WAN IP 在 100.64.0.0/10（100.64~100.127）= 运营商大内网，端口转发无效
- 出口公网 IP 查询：`curl http://ip.3322.net`（国内视角，比 api.ipify.org 可信；ipify 可能被代理/异常解析污染）
- 申请公网 IP 话术："我家宽带需要公网 IPv4 用于 NAS 远程访问"（电信 10000）
- 光猫/主路由/旁路由多层拓扑：入站端口转发必须配在**拨号的主路由**上
