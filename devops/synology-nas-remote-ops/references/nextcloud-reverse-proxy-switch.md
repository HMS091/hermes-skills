# 案例：Nextcloud 从 CF 隧道切换 myds.me DDNS 直连（2026-08-05）

用户环境：Synology NAS 192.168.1.200 上两个 Nextcloud 实例（nextcloud / nextcloud2，均 nextcloud:latest Apache 版，33.0.3.2）。之前经 Cloudflare 隧道 + FreeDNS 访问，改为 Synology myds.me DDNS 域名直连，不走隧道。

## 目标架构
```
公网(手机4G, IPv6) → tmmddsm.myds.me:9800/9801
    → 路由器 → NAS nginx-proxy (host 网络, 监听 9800/9801 ssl)
    → proxy_pass 127.0.0.1:19800/19801
    → nextcloud 容器 (仅绑定回环)
```
myds.me 是 Synology DDNS，证书由 DSM 自动从 Let's Encrypt 申请（~90 天续期）。

## 关键前提核查（执行前必做）
1. `nslookup tmmddsm.myds.me 223.5.5.5` → **只有 AAAA**（IPv6 `240e:...:d0eb`）。用户说"有了公网 IP"实际仍是 CGNAT IPv4 + 公网 IPv6。方案照做但必须告知用户：无 IPv6 的网络访问不了。
2. 证书目录 `_archive/Yw6nys` 对应 myds.me：docker 挂载 + `openssl x509 -subject` 验证 `CN=tmmddsm.myds.me`（ECC 与 RSA 两套，选 ECC）。
3. nginx-proxy 容器必须是 **host 网络**（否则 `proxy_pass 127.0.0.1:19800` 连不到宿主回环）。本案例已确认 `NetworkMode=host`。

## 执行步骤（含修复）
1. **证书**：docker 挂载 `-v /usr/syno/etc/certificate:/c:ro -v /volume1/docker/nginx-proxy/certs:/out:rw` cp `ECC-fullchain.pem`→`myds.me.crt`、`ECC-privkey.pem`→`myds.me.key`，chmod 644。
2. **compose 端口**：nc1 `'9800:80'`→`'127.0.0.1:19800:80'`；nc2 `'9801:80'`→`'127.0.0.1:19801:80'`（sed + 备份 + `docker compose up -d`）。
3. **nginx.conf**：追加两个 `server`（`listen 9800 ssl` / `listen 9801 ssl`，`http2 on;`，`server_name tmmddsm.myds.me`，`ssl_certificate /certs/myds.me.crt`，`proxy_pass http://127.0.0.1:19800/19801`，`proxy_set_header X-Forwarded-Proto https`）。同时把旧 8443 server 的 `proxy_pass 127.0.0.1:9800` → `19800`（防 502）。`docker exec nginx-proxy nginx -t` 验证后 `docker restart nginx-proxy`。
4. **occ 配置**（每个实例）：
   ```
   occ config:system:set trusted_domains <新索引> --value=tmmddsm.myds.me   # 先 get 现状定索引，nc1=3, nc2=2
   occ config:system:set overwritehost --value=tmmddsm.myds.me:9800        # nc2 用 :9801
   occ config:system:set overwriteprotocol --value=https
   occ config:system:set overwrite.cli.url --value=https://tmmddsm.myds.me:9800
   occ config:system:set trusted_proxies 0 --value=127.0.0.1
   occ config:system:set trusted_proxies 1 --value=192.168.1.200
   ```
   容器内以 `docker exec -u www-data nextcloud php occ ...` 执行。

## 排障记录（本案例真实踩坑）
| 现象 | 根因 | 修复 |
|------|------|------|
| 外部 9800 = HTTP 000，回环 200；容器日志 `\x16\x03\x03` 400 | DSM `DEFAULT_PREROUTING` 残留 `DNAT tcp dpt:9800 to:172.21.0.3:80`（旧端口映射时代残留，compose down/up 不清） | PTY sudo 删两条规则 |
| 外部 9801 = 502（到 nginx 但后端不通） | 容器刚重建初始化中 | 等初始化完成即恢复 |
| nc2 日志 "New nextcloud instance" | 误报（config.php 存在、installed=1，只是容器重建重跑 entrypoint） | 无需处理，status.php 200 即正常 |
| alpine 容器 iptables 报 `UNKNOWN match` | nft 版与 DSM legacy 表不兼容 | `apk add iptables-legacy` |
| 本机 openssl 读 `/c/Users/...` 失败 | mingw openssl 不认 MSYS 路径 | 用 `C:\Users\...` |

## 验证清单（全部通过）
- `curl --noproxy '*' -sk -H "Host: tmmddsm.myds.me" https://192.168.1.200:9800/status.php` → 200 `{"installed":true,...}`
- 首页 `curl -skI https://192.168.1.200:9800/` → 302 Location `https://tmmddsm.myds.me:9800/index.php/login`（overwritehost 生效）
- IPv6 直连 `curl -g -sk https://[240e:...:d0eb]:9800/status.php` → 200
- 证书 `subject=CN=tmmddsm.myds.me, issuer=Let's Encrypt`

## 遗留事项（告知用户）
- 手机 4G 实测两个域名；不通则查 TP-LINK「安全管理→IPv6防火墙」放行 9800/9801 TCP
- 旧域名（CF / FreeDNS）被 overwritehost 302 到新域名，彻底停用需删 CF DNS 记录（用户用 CF AI 助手）
- DSM 面板端口转发配置（synoportforward.conf）确认无 9800，规则删除不复发
