# NAS Nextcloud Talk deployment (verified 2026-08)

## Topology
- Synology NAS 192.168.1.200, SSH user `tmm` (key `justfans_nas_deploy_key`, no passwordless sudo).
- docker binary: `/usr/local/bin/docker` (also `/var/packages/ContainerManager/target/usr/bin/docker`); NOT on SSH user's PATH.
- Home broadband: real public IPv4 **61.157.253.46** (Chinanet SC / AS4134, Chengdu, CN) — port-forwardable, not CGNAT.
- Windows desktop default gateway: 192.168.1.2 (https management UI, self-signed cert `CN=LOCAL-20190801`). NOTE: cloudflare-tunnels skill records the NAS gateway as OpenWRT 192.168.1.88 — two gateways exist on the LAN; confirm which device fronts the WAN before advising port-forwarding.

## Nextcloud instances
| container | port | domain | Talk app | TURN in DB (`spreed turn_servers`) |
|---|---|---|---|---|
| nextcloud | 9800 | nextcloud.skyforgelabs.qzz.io | spreed | `192.168.1.200:3478`, secret `nextcloud_turn_secret_2026` |
| nextcloud2 | 9801 | nc.ncncnc.ccwu.cc (Cloudflare-proxied) | spreed + patch_login_fix/flow | `192.168.1.200:3479`, secret `nc2_turn_secret_2026` |

- HPB signaling: nextcloud mounts `signaling-proxy.conf` proxying `/standalone-signaling/` → `172.21.0.1:8082` (talk-signaling2 container, host network).

## coturn containers (all host network, Up)
- `talk-coturn` → nextcloud (realm `nextcloud.skyforgelabs.qzz.io`); `talk-coturn2` → nextcloud2 (realm `nc.ncncnc.ccwu.cc`); `matrix-coturn`/`matrix2-coturn` = Matrix (unrelated).
- `/etc/coturn/turnserver.conf` (talk-coturn, verified):
  ```
  listening-port=3478
  tls-listening-port=5349
  relay-ip=192.168.1.200
  external-ip=61.157.253.46/192.168.1.200
  fingerprint
  use-auth-secret
  static-auth-secret=nextcloud_turn_secret_2026
  realm=nextcloud.skyforgelabs.qzz.io
  total-quota=100
  no-multicast-peers / no-loopback-peers / no-rfc5780
  ```
- Container Cmd is only `--log-file=stdout --external-ip=$(detect-external-ip)`; the real config is the mounted `/etc/coturn/turnserver.conf`.

## Diagnosis result (2026-08) — WiFi OK / 4G-5G fails
- Root cause: `turn_servers` in the DB point at **private IPs** (192.168.1.200:3478/3479) — unreachable from carrier networks. WiFi phones are on the same LAN, so they work.
- Public reachability: `61.157.253.46:3478` UDP+TCP BOTH unreachable from outside → router port-forward never configured. `nc.ncncnc.ccwu.cc` resolves to Cloudflare (104.21.2.66 / 172.67.128.217) → proxy doesn't forward UDP 3478.
- coturn config itself is complete; DB secrets match `static-auth-secret`.

## Pending fix (next session can pick up)
1. Port-forward TCP+UDP 3478 (and 3479 for nc2) on whichever gateway fronts the WAN → 192.168.1.200.
2. Update DB config to the public address (keep secrets identical):
   - nextcloud: `occ config:app:set spreed turn_servers --value='[{"schemes":"turn,turns","server":"61.157.253.46:3478","secret":"nextcloud_turn_secret_2026","protocols":"udp,tcp"}]'`
   - nextcloud2: same pattern with `61.157.253.46:3479` / `nc2_turn_secret_2026`
   - Prefer a DNS-only (grey-cloud) subdomain over the raw IP if one exists.
3. Re-probe STUN from outside (`scripts/stun_probe.py`), then user tests a 4G call.

## User preference reminder
User is non-technical, Chinese-speaking, wants agent to do everything; router access needs their password or guided steps. User's stated alternatives: they asked about Metered.ca — verdict: not compatible (see references/metered-ca.md).
