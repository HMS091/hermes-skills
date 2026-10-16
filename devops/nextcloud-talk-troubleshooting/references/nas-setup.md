# NAS Nextcloud deployment — current state

## Topology
- Synology NAS 192.168.1.200 (hostname DY), SSH user `tmm` (password-based; `administrators` + `docker` groups).
- docker binary: `/usr/local/bin/docker` (NOT on the SSH user's PATH); `docker compose` v2 available.
- **Default gateway = 192.168.1.88** (OpenWrt transparent-proxy side router, `dev ovs_eth1`): v4 egress shows a
  proxy exit IP (AWS), not the home WAN. Second NIC `ovs_eth1` = 192.168.1.201 — it has NO global IPv6, which
  matters for anything that resolves "the default interface" (see DDNS).
- Router (TP-LINK TL-ER6229GPE-AC, 192.168.1.2:9000) advertises a public `240e:` prefix to the LAN; the ISP
  re-delegates the /64 often — prefixes observed: `240e:39e:396:6520` → `...:399:2b70` → `...:3c5:1a90` → `...:3c8:71b0`.
  **Anything holding an address literal (coturn relay-ip, DDNS record, Talk TURN entry) goes stale on every change.**

## Nextcloud instances
| container | port map | domain / entry | Talk app | notes |
|---|---|---|---|---|
| nextcloud | 127.0.0.1:19800→80 | `tmmddsm.myds.me:9800` (direct, IPv6 + myds.me cert), also 8443 vhost | spreed 23.0.4 | 9 users, ~23 rooms, the one in real use (users `tom`, `yc`, iOS Talk v24/v25) |
| nextcloud2 | 127.0.0.1:19801→80 | `tmmddsm.myds.me:9801` / `nc.ncncnc.ccwu.cc` (Cloudflare) | spreed | **stopped by the user** — stopping it does not affect the other instance, but both share the same Redis pattern |

- Entry points are fronted by the `nginx-proxy` container (`/volume1/docker/nginx-proxy/nginx.conf`): 9800/9801
  (server_name tmmddsm.myds.me, cert `certs/myds.me.crt`), 8443 (server_name nextcloud.skyforgelabs.qzz.io),
  8081/8123 for other services. Local vhost check: `curl -sk --resolve <host>:8443:127.0.0.1 https://<host>:8443/status.php`.
- **Cloudflare routes are dashboard-managed** (all cloudflared containers use `--token` except
  `cloudflared-nc1`, whose local `config.yml` only serves mail.rayray.qzz.io). `nextcloud.skyforgelabs.qzz.io`
  currently returns Cloudflare 400 `The plain HTTP request was sent to HTTPS port` → the tunnel origin is set to
  `http://…:8443`; only fixable in the CF dashboard (`https://localhost:8443` + No TLS Verify, or `http://127.0.0.1:19800`).
  Since the NAS is IPv6-only for inbound, a working CF route is the prefix-independent access path.

## Redis (why Nextcloud broke once already)
- `config.php` had `redis.host = lumina-redis` — a container belonging to the **lumina** project, attached to
  `nextcloud-net` (and nextcloud2's network) by hand. A batch stop of the lumina stack took Nextcloud's
  distributed cache/locking down and made Talk unusable while `/status.php` still returned 200.
- Fixed: dedicated `nextcloud-redis` (redis:7-alpine, appendonly, 128mb allkeys-lru, `restart: always`) added to
  `/volume1/docker/nextcloud/docker-compose.yml`, data in `/volume1/docker/nextcloud/redis`; `occ config:system:set redis host --value=nextcloud-redis`.
- `lumina-redis` is currently Up because nextcloud2's config still points at it; keep it running while nc2 is off.

## coturn
- `talk-coturn` (host network, realm `nextcloud.skyforgelabs.qzz.io`, `static-auth-secret=nextcloud_turn_secret_2026`)
  and `talk-coturn2` (port 3479, realm `nc.ncncnc.ccwu.cc`, `nc2_turn_secret_2026`) — config files live at
  `/volume1/docker/talk/coturn/turnserver.conf` and `/volume1/docker/talk2/coturn2/turnserver.conf` (host-writable, mount is read-only).
- Current talk-coturn lines that matter:
  ```
  listening-port=3478
  listening-ip=0.0.0.0
  listening-ip=::            # without this coturn only bound ::1 for v6 -> no remote relay
  relay-ip=192.168.1.200
  relay-ip=<current global v6>   # refresh on every prefix change (there is no relay-ipv6 directive)
  use-auth-secret / static-auth-secret=…
  ```
  `tls-listening-port=5349` is set but NOT listening (no cert key in the container) → never advertise `turns:`.
- **talk-coturn2 still carries the stale v6 relay-ip** — apply the same fix before re-enabling nextcloud2.

## Talk ICE config in the DB (`oc_appconfig`, app `spreed`)
- `turn_servers` = `[{"schemes":"turn","server":"[<current v6>]:3478","secret":"nextcloud_turn_secret_2026","protocols":"udp,tcp"}]`
  (the earlier `global.relay.metered.ca:80` username/password entry was removed — unreachable from this network).
- `stun_servers` = `["[<current v6>]:3478","192.168.1.200:3478"]` (was `[]`, which hands clients NO STUN at all).
- `signaling_servers` is unset → Talk uses built-in signaling; the leftover apache `signaling-proxy.conf`
  pointing at `172.21.0.1:8082` (talk-signaling, exited) is inert. `talk-signaling2` (8083) serves the stopped nextcloud2.

## DSM DDNS (tmmddsm.myds.me) — repaired
- `/etc/ddns.conf` (root-only) held `status=disabled` and `interface_v6=default`; "default" resolved to ovs_eth1
  which has no global IPv6, so the AAAA record froze on an old prefix → every client (4G and WiFi) failed to connect.
- Fix applied: `interface_v6=ovs_eth0`, `status=enabled`, `ipv6=<current v6>`, then
  `systemctl restart ddnsd` + `systemctl restart heartbeatd` (via the chroot-as-root trick). Record updated within seconds.
- `ddnsd -a` is the diagnostic for what DSM thinks the external IP is (here: a proxy exit IP for v4, zeros for v6).

## Entry points summary
1. `https://tmmddsm.myds.me:9800` — direct IPv6, verified working from an external fetch proxy. Primary for the apps.
2. `https://[<current v6>]:8443` — direct, cert mismatch only (works).
3. `nextcloud.skyforgelabs.qzz.io` — broken at the Cloudflare side (400), fix in the CF dashboard if prefix-independence is wanted.
