# Nextcloud Talk TURN/STUN 配置机制

## 配置存储位置（关键）
- **不在 config.php**！TURN/STUN 配置存在数据库 `oc_appconfig` 表（app=`spreed`）
- 通过 occ 命令或 Talk 管理界面（设置 → Talk → TURN servers）读写
- grep config.php 找不到任何 talk/turn 配置是正常的，不代表没配置

## occ 命令
```bash
# 读取（返回 JSON 字符串）
docker exec -u www-data <nc容器> php occ config:app:get spreed turn_servers
docker exec -u www-data <nc容器> php occ config:app:get spreed stun_servers

# 写入（⚠️ 不要加 --type=json，部分版本报 "Unknown type json"）
# 直接存 JSON 字符串，Talk 读取时自行 json_decode
docker exec -u www-data <nc容器> php occ config:app:set spreed turn_servers \
  --value='[{"schemes":"turn","server":"host:3478","secret":"SECRET","protocols":"udp,tcp"}]'

docker exec -u www-data <nc容器> php occ config:app:set spreed stun_servers \
  --value='["host:3478"]'
```

## turn_servers JSON 字段
| 字段 | 取值 | 说明 |
|------|------|------|
| schemes | `turn` / `turns` / `turn,turns` | turn=明文（UDP/TCP），turns=TLS。Metered 指引用 `turn` |
| server | `host:port` | **必须公网可达地址**。配内网 IP（如 192.168.1.200:3478）= WiFi 通 4G 死 |
| secret | 字符串 | static-auth-secret（HMAC 模式），必须与 coturn 的 `static-auth-secret` 一致 |
| protocols | `udp,tcp` | 客户端生成的 candidate 传输 |

## 认证机制（为什么第三方服务常不兼容）
- Nextcloud 用 secret 生成**临时凭据**：username=unix 时间戳，password=base64(hmac_sha1(secret, username))（coturn REST API 规范）
- TURN 服务器必须配 `use-auth-secret` + 相同 `static-auth-secret` 才能验证
- 只提供静态 username/password 的托管服务（如 Metered 付费版）**不兼容** Nextcloud

## 配套 coturn 配置（docker-compose 部署参考）
```conf
listening-port=3478
tls-listening-port=5349
external-ip=<公网IP或DDNS域名>/<内网IP>   # 配错=手机拿到错误通告地址
fingerprint
use-auth-secret
static-auth-secret=<与Nextcloud一致>
realm=<nextcloud域名>
no-multicast-peers
no-loopback-peers
```
- host 网络模式 + `docker exec` 时注意：精简容器（debian/alpine）里可能没有 ip/route/python 命令
- coturn 镜像自带 turnutils_stunclient / turnutils_uclient，可做协议级测试

## 测试方法
```bash
# STUN 可达性（服务活着且监听正常）
docker exec <coturn> turnutils_stunclient -p 3478 <host>

# TURN 实际分配测试（auth-secret 模式，与 Nextcloud 同款认证）
docker exec <coturn> turnutils_uclient -W <secret> -e 8.8.8.8 -p 3478 <host>
# 有 relay 分配成功输出 = TURN 服务可用；只有启动日志后卡死 = 服务不响应协议
```
