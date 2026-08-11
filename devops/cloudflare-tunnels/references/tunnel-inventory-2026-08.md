# NAS cloudflared 隧道清点与排障实录 (2026-08-02)

## 环境事实
- NAS: 192.168.1.200, SSH 用户 tmm (免密), docker 在 `/usr/local/bin/docker` (不在 PATH)
- 每个隧道一个目录: `/volume1/docker/cloudflared-<name>/docker-compose.yml`
- 全部 `network_mode: host`, `restart: always`;新版 token 是**单段** base64url(无点),解码要补 `=` padding

## 容器 → 隧道 ID 映射
| 容器/目录 | 账户 tag | 隧道 ID | 状态 |
|---|---|---|---|
| cloudflared-nc1 | 15585dd3e89d535fb3e498c3271f26ae | 875ecd11-a274-4bb9-9871-3a99352f347c | Up;用 config.yml+credentials.json(非token),ingress mail.rayray.qzz.io→localhost:3001 |
| cloudflared-nc2 | 15585dd3e89d535fb3e498c3271f26ae | 58173062-0ffd-40e7-865f-af5e094c9835 | Up;QUIC 超时 |
| **cloudflared-matrix** | 15585dd3e89d535fb3e498c3271f26ae | **16bb57ca-98ac-4627-a4c0-187af66659c2** | Up 但连不上边缘 → 用户浏览器里"关闭"的那个 |
| cloudflared-raymail | 02b3f68543409877d770adaa61ebf3e2 (**另一个账户**) | 5c4c6ba9-5bb8-4e70-8a64-a587439b03e5 | Exited(1): metrics 端口 20242 `address already in use` |
| cloudflared-matrix2/ (仅目录) | 15585dd3... | 16bb57ca...(同 matrix) | 无容器创建;matrix2 项目容器(synapse等)在跑 |

注意: cloudflared-matrix 的 compose 文件里 token 是占位符 `把你的CF隧道TOKEN粘贴到这里`,真实 token 在容器 Cmd 里 — 必须从 `docker inspect` 提取。

## 故障签名(日志原文)
- QUIC 封锁: `ERR Failed to dial a quic connection error="failed to dial to edge with quic: timeout: no recent network activity"`
- SNI 劫持(直连 http2): `ERR ... x509: certificate has expired or is not yet valid: current time 2026-08-03T...Z is after 2020-10-17T23:59:59Z` — 中间设备对 `*.argotunnel.com` SNI 注入 2020 假证书
- 验证: `openssl s_client -connect 198.41.200.13:443` 无 `-servername` → 拿到 2026 真证书;加 `-servername region1.v2.argotunnel.com` → 假证书
- precheck: UDP/TCP Connectivity 对 region1/region2.v2.argotunnel.com FAIL,但 "Cloudflare API ... status=pass"(api.cloudflare.com:443 通);提示语 "Allow outbound QUIC traffic on port 7844 or use HTTP2" / "Allow outbound TCP on port 7844"
- 走代理后错误**改变**为 `tls: unrecognized name` 或 `EOF` → 说明代理链路生效但出口节点也过不去 argotunnel TLS

## Windows 代理栈 (诊断用,不是解决方案)
- 10808: xray.exe (v2rayN-windows-64\bin\xray\xray.exe),mixed 协议,仅监听 127.0.0.1
- 10809: `netsh interface portproxy` 0.0.0.0:10809 → 127.0.0.1:10808(为 NAS 开放);需先加防火墙入站规则 `XrayProxy LAN 10809`(已加,2026-08-02)
- 走 Windows 代理后错误**改变**为 `tls: unrecognized name` 或 `EOF` → 代理链路生效但 xray 出口节点也过不去 argotunnel TLS → **此路不通,不要作为解决方案**

## 真正的根因与修复: OpenWRT dae 透明代理 (2026-08-03)
- NAS 默认网关 + DNS = **192.168.1.88 (ImmortalWrt 24.10.1)**,SSH root 免密可用: `ssh root@192.168.1.88`
- OpenWRT 装了 PassWall(enabled='0' 未运行)、OpenClash(未运行)、**daed 运行中** ← 真正的劫持者
- daed = eBPF 内核级透明代理;配置在 SQLite `/etc/daed/wing.db` 表 `routings`(id=1,列 `routing`);nftables 可见 tproxy(dns 53 → tproxy :12345, fwmark 0x100)
- 默认规则 `fallback: proxy` → 非 geoip:private/cn、非 geosite:cn 全走代理 → CF 边缘 IP(198.41.0.0/16, 162.159.0.0/16)被劫持 → 假证书 → 隧道"关闭";还导致 NAS 拉 Docker Hub 镜像失败
- 修复: `cp wing.db wing.db.bak2` → `/etc/init.d/daed stop` → 用 sqlite3 `readfile()` 更新路由(在 fallback 前加 `dip(198.41.0.0/16, 162.159.0.0/16) -> direct` 和 `domain(suffix:argotunnel.com) -> direct`) → `daed start`
- 验证: cloudflared 日志 precheck QUIC/HTTP2 成功 + `Registered tunnel connection ... location=lax09/lax11/lax01 protocol=http2` ×4;网页 1 分钟内变"正常"
- **关键纠正**: NAS 到边缘 7844 TCP 其实**通**(`/dev/tcp/198.41.200.13/7844` OK),NAS 不通的是被 dae 劫持的 TLS 层 — 之前"终极方案是在 Windows 跑 cloudflared"的结论是错的

## 关键教训
- **curl/openssl 测 argotunnel 域名不可靠**:边缘只接受 cloudflared 客户端握手,普通 TLS 客户端一律失败(`sslv3 alert handshake failure` / `SEC_E_ILLEGAL_MESSAGE` / `unrecognized name`),即使网络健康。只能看 cloudflared 自己日志。
- 容器 Up 12 天 ≠ 隧道在线:可能一直在重试连不上,网页显示关闭。
- 改 compose 加 env 后必须 `docker compose up -d --force-recreate` 并 `docker inspect ... {{json .Config.Env}}` 验证。
- 边缘连接走 7844 端口(QUIC/UDP + TCP);443 只用于 API。
