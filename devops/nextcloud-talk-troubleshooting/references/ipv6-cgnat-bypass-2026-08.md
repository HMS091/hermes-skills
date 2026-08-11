# IPv6 CGNAT-bypass case (2026-08) — full transcript of the fix path

Symptom: Nextcloud Talk works on home WiFi, fails on 4G/5G. Metered.ca evaluated and rejected (see metered-ca.md + SKILL.md). ISP (China Telecom Sichuan) is CGNAT (`100.76.32.142` on the Tenda WAN after PPPoE) — port-forwarding configured correctly but 3478 stays unreachable from outside. IPv4 route to public IP is dead. IPv6 is the free escape.

## Network topology (verified this session)
- Main router: Tenda at `192.168.1.2` (PPPoE dial, WAN = CGNAT `100.64-100.127` range). HTTPS admin on 192.168.1.2, self-signed cert, SLP web framework (`data-interface-type="SLP"`, `web-static/` paths) — Tenda-style UI.
- Bypass router: OpenWrt at `192.168.1.88` (LuCI), proxy-only. NAS default route pointed at it (outbound goes through proxy chain) — irrelevant for inbound TURN.
- NAS: `192.168.1.200` (ovs_eth0) + `192.168.1.201` (ovs_eth1); two Nextcloud instances (`nextcloud` :9800, `nextcloud2` :9801); two coturns host-network (`talk-coturn` 3478, `talk-coturn2` 3479).
- DNS: `nc.ncncnc.ccwu.cc` → Cloudflare IPs (proxied; 3478 never reachable via that hostname).

## Debug tools that actually worked
- Read TURN config from DB (not config.php): `docker exec -u www-data nextcloud php occ config:app:get spreed turn_servers` — revealed `"server":"192.168.1.200:3478"` (private IP = root cause for 4G failure).
- Write it back: `occ config:app:set spreed turn_servers --value='[<json>]'` — **omit `--type=json`** (this build errors `Unknown type json`). Store the JSON string bare.
- STUN binding probe from Windows host (python3 stdlib, see scripts/stun_probe.py): succeeded against `192.168.1.200:3478` (0x0101) → coturn itself healthy; timed out against public IPs → forwarding/CGNAT issue.
- `turnutils_stunclient -p 80 <host>` / `-p 443` — UDP STUN against Metered endpoints: no output = dead.
- `turnutils_uclient -W <secret> -e 8.8.8.8 -p 443 <host>` — auth-secret TURN allocation test. **`-e` peer address is mandatory** ("Either -e peer_address or -y must be specified"). Hang with only listener-thread lines = service dead (this is how Metered Open Relay was pronounced dead: TCP 80/443 connect OK, no TURN/STUN/HTTPS response).
- `nslookup staticauth.openrelay.metered.ca 8.8.8.8` → single Toronto IP (216.39.253.123, AS399858) — no APAC node; global.relay.metered.ca (paid) → 158.247.200.82 (Vultr Tokyo).

## IPv6 bring-up sequence (each step verified)
1. Tenda: enable IPv6 (PPPoE). WAN shows `240e:398:ba01:fa40:7cb5:9b65:98e0:40da/64` (China Telecom prefix).
2. NAS had NO global IPv6: `ip -6 addr show` → only `fe80::` link-local. Kernel `accept_ra=0` on ovs_eth0/ovs_eth1 (check: `cat /proc/sys/net/ipv6/conf/ovs_eth0/accept_ra`).
   - `docker exec -u root talk-coturn sh -c "echo 1 > /proc/sys/..."` → **Read-only file system** (non-privileged container). Cannot self-fix; must use DSM GUI or admin SSH.
3. User set DSM NIC IPv6 to Auto (Control Panel → Network → Network Interface → edit → IPv6) → `accept_ra` became 2.
4. Still no global address for 30+ s: the RA that arrived advertised ULA prefix `fd87:2cf7:84c8::/64` (route appeared with expiry timer), NOT the public `240e:` prefix — router LAN was handing out IPv6-private only. 4G unreachable even with an address.
5. User manually set the public prefix on the router LAN side, then set DSM IPv6 to static with:
   - `IPV6ADDR=240e:398:ba01:fa40:7cb5:9b65:98e0:40da`, prefix /64, DNS `240e:56:4000:8000::69` (CN Telecom DNS) — BUT no gateway → `ip -6 route show default` empty → no egress.
   - Gateway must be the router LAN IPv6, normally prefix::1 → `240e:398:ba01:fa40::1` (pending at session end).

## Remaining steps after gateway is set (for the next session)
- Confirm `ping6 2400:3200::1` from NAS.
- coturn: listen + relay IPv6 (host-network coturn inherits NAS IPv6; check `turnserver.conf` for IPv6 relay config).
- Tenda IPv6 firewall: allow inbound 3478 (UDP/TCP) on the LAN interface (Tenda defaults block inbound IPv6).
- Nextcloud `turn_servers`: `"server":"[240e:...]:3478"` (brackets!), schemes turn, protocols udp,tcp, same secret as coturn.
- Test: 4G phone (carrier IPv6 present) ↔ home WiFi device (needs IPv6 on LAN too).
