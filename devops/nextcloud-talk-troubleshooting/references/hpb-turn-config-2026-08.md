# spreed-signaling (HPB) [turn] config — this NAS, 2026-08

Symptom that led here: after TURN DB config, coturn IPv6 relay, and IPv6 networking were ALL
verified working (NAS has `240e:` global addr, coturn answers IPv6 STUN, phone has IPv6),
4G calls still failed with "caller shown but no connecting spinner". `docker logs talk-coturn`
showed ZERO connection attempts → clients were never handed a TURN server → HPB config had no
`[turn]` section.

## Container → config-file mapping (do NOT edit the wrong file)
```bash
/usr/local/bin/docker inspect talk-signaling2 --format "{{range .Mounts}}{{.Source}} => {{.Destination}}{{end}}"
# → /volume1/docker/talk2/signaling2/server.conf => /config/server.conf   (talk-signaling2 = nc2's HPB)
/usr/local/bin/docker logs talk-signaling2 | grep -iE "starting|listening"
# → Starting signaling server with /config/server.conf ... Listening on 0.0.0.0:8083
```
- `/volume1/docker/talk2/signaling2/server.conf` — port 8083, `backends = nextcloud2`, urls `http://192.168.1.200:9801` → **nc2**
- `/volume1/docker/talk/signaling/server.conf` — port 8082, backends = nextcloud, urls `http://192.168.1.200:9800` → **nc1**
- nc1's apache proxy `/volume1/docker/nextcloud/signaling-proxy.conf` → `ProxyPass /standalone-signaling/ http://172.21.0.1:8082/`
- There is only ONE running signaling container (talk-signaling2); it currently serves nc2. nc1's HPB (8082) has no running container — nc1 falls back to built-in signaling, so its TURN comes from the DB (`turn_servers`).

## The fix (nc2 example)
```bash
cp /volume1/docker/talk2/signaling2/server.conf{,.bak-turn}
cat >> /volume1/docker/talk2/signaling2/server.conf <<'EOF'

[turn]
secret = nc2_turn_secret_2026
url = turn:[240e:39e:396:6520:211:32ff:fea1:d0eb]:3479?transport=udp
url = turn:[240e:39e:396:6520:211:32ff:fea1:d0eb]:3479?transport=tcp
EOF
/usr/local/bin/docker restart talk-signaling2
```
Mapping (secret + port MUST match the coturn the HPB's Nextcloud talks to):
| Instance | HPB config path | coturn | port | static-auth-secret |
|----------|----------------|--------|------|--------------------|
| nc1 (skyforgelabs.qzz.io, 9800) | /volume1/docker/talk/signaling/server.conf | talk-coturn | 3478 | nextcloud_turn_secret_2026 |
| nc2 (ncncnc.ccwu.cc, 9801) | /volume1/docker/talk2/signaling2/server.conf | talk-coturn2 | 3479 | nc2_turn_secret_2026 |

IPv6 hosts in `url = turn:[...]:port?transport=...` REQUIRE brackets, same as in Nextcloud
`turn_servers` JSON `server` field.

## Also fixed the same session
- `spreed stun_servers` still pointed at dead Metered (`staticauth.openrelay.metered.ca:80`) →
  set to `["stun.nextcloud.com:443"]` (or the local coturn) via occ.
- HPB configs are host files under `/volume1/docker/` (writable by SSH user tmm); container-side
  copies are read-only — same rule as coturn's turnserver.conf.

## Verification after restart
- `docker logs talk-signaling2` shows `Starting signaling server with /config/server.conf` + `Listening on 0.0.0.0:8083`.
- Then test a real call from a 4G/5G phone; the calling client must reload Talk to fetch new ICE servers.
- If still failing, check the router IPv6 firewall (安全管理 → IPv6防火墙 on TP-LINK ER — plain on/off switch, no per-rule UI) and confirm the phone actually has IPv6 via https://api6.ipify.org.
