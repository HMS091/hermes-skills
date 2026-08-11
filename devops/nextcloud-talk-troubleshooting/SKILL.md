---
name: nextcloud-talk-troubleshooting
description: |
  Diagnose and fix Nextcloud Talk call failures (WebRTC audio/video) on self-hosted
  instances — the WiFi-works-but-4G/5G-fails symptom, TURN/STUN configuration,
  coturn on NAS Docker, public reachability testing, and hosted TURN provider
  compatibility (e.g. Metered.ca auth model vs Nextcloud static-auth-secret).
version: 1.0.0
platforms: [windows, linux]
metadata:
  hermes:
    tags: [nextcloud, talk, webrtc, turn, stun, coturn, nas, docker]
    category: devops
---

# Nextcloud Talk troubleshooting (WebRTC / TURN / STUN)

## When to use
- Talk calls work on same-LAN/WiFi but fail on 4G/5G (or any external network)
- Calls fail entirely, one-way audio, or "could not establish connection"
- Need to configure/verify a TURN server (coturn) for Nextcloud Talk
- Evaluating a hosted TURN provider (Metered.ca, Twilio, Xirsys) for Nextcloud

## Core mental model (why WiFi works but mobile fails)
WebRTC tries in order: direct P2P → STUN-assisted P2P → TURN relay (last resort).
- Same-LAN: P2P to private IPs, no NAT → works with zero config.
- External (4G/5G): strict/symmetric carrier NAT → P2P hole-punching usually fails → TURN relay REQUIRED.
- So "WiFi OK / mobile fails" almost always means: TURN missing, unreachable, or the address handed to clients is a private IP.

## Diagnosis workflow (in order)

1. **Locate the Talk TURN config — it's in the DATABASE, not config.php.**
   Modern Nextcloud stores Talk TURN/STUN settings in `oc_appconfig` (app key = `spreed`). Grepping config.php finds nothing and misleads you.
   ```bash
   ssh tmm@192.168.1.200 '/usr/local/bin/docker exec -u www-data <container> php occ config:app:get spreed turn_servers'
   ssh tmm@192.168.1.200 '/usr/local/bin/docker exec -u www-data <container> php occ config:app:get spreed stun_servers'
   ```
   Output is JSON: `[{"schemes":"turn,turns","server":"<host:port>","secret":"...","protocols":"udp,tcp"}]`.
   **CLI alternative (cleaner)**: `occ talk:turn:list` and `occ talk:stun:list` (note: `talk:turn --list` is WRONG — prints the help screen; the command is `talk:turn:list`).
   **Red flag: `server` is a private IP (e.g. 192.168.1.200:3478)** → external clients can't route to it → exactly the WiFi-OK/mobile-fails symptom. This is the #1 root cause; check it before touching coturn.

2. **Inspect the coturn container.**
   - `docker inspect <coturn> --format "{{.HostConfig.NetworkMode}}"` — host network is typical on NAS.
   - Config file lives at `/etc/coturn/turnserver.conf` in the official image (NOT /etc/turnserver.conf).
   - **PITFALL — the config file is mounted READ-ONLY into the container**: `docker exec -u root <coturn> sh -c "echo ... >> /etc/coturn/turnserver.conf"` fails with `Read-only file system` (and `/proc/sys` writes too). On this NAS the editable host paths are `/volume1/docker/talk/coturn/turnserver.conf` (talk-coturn) and `/volume1/docker/talk2/coturn2/turnserver.conf` (talk-coturn2) — the SSH user CAN write `/volume1/docker/`, so edit the HOST file (back it up first), then `docker restart <coturn>`. Find the host path via `docker inspect <coturn> --format "{{range .Mounts}}{{.Source}} => {{.Destination}} (rw={{.RW}}){{end}}"`.
   - Key lines: `listening-port`, `external-ip=<public>/<private>` (address announced to clients), `use-auth-secret` + `static-auth-secret=<secret>` (must equal Nextcloud's `secret`), `realm`, `fingerprint`.
   - `docker logs <coturn>` shows `Default realm`, relay init, listening addresses.

2b. **Check the HPB signaling-server config — clients receive their TURN/ICE list from HERE, not from the Nextcloud DB.** If Talk is fronted by a High Performance Backend (strukturag/nextcloud-spreed-signaling container), the HPB's own config must carry a `[turn]` section; without it clients get an EMPTY TURN list and mobile calls die silently (coturn logs show ZERO connection attempts). Signal: phone shows the incoming call ("有谁打电话了") but no spinner/connecting animation → signaling OK, media has no candidate path. Full recipe below under "High Performance Backend (HPB) signaling".

3. **Test public reachability of the TURN port from OUTSIDE the LAN.**
   - TCP: `timeout 6 bash -c "cat < /dev/null > /dev/tcp/<host>/3478"` → OPEN or unreachable.
   - UDP/STUN: run `scripts/stun_probe.py <host> <port>` (Python 3, sends STUN binding request, expects type 0x0101).
   - Full TURN allocation test (auth-secret mode, same as Nextcloud): from the coturn container, `turnutils_uclient -W <secret> -e 8.8.8.8 -p <port> <host>`. **PITFALL: `-e` (peer address) is mandatory** — without it uclient aborts with "Either -e peer_address or -y must be specified". `-W` = REST auth-secret; `-t` switches to TCP; `turnutils_stunclient -p <port> <host>` for plain UDP STUN (note `-p` is the port flag, position is address).
   - **PITFALL — NAT hairpin**: probing your own public IP from INSIDE the LAN can time out even when port-forwarding is correct (routers vary on loopback support). "Unreachable from home" ≠ "broken"; confirm from real external network (4G phone / online port checker) before blaming the forward.
   - Both failing from outside = router port-forward missing/blocked, CGNAT (next step), or the hostname is behind a CDN proxy (step 4).

4. **DNS/CDN check — a proxied domain hides the real origin.**
   `nslookup <domain>` → Cloudflare IPs (104.21.x.x / 172.67.x.x) mean the proxy forwards ONLY HTTP(S) 80/443. UDP 3478 (TURN) and arbitrary TCP will NEVER reach the NAS through that hostname. Test the real origin IP instead (from coturn `external-ip`, or find via whois). Options: DNS-only subdomain (grey-cloud) pointing at the public IP, or use the IP directly.

5. **Confirm the public IP is real, not CGNAT.**
   `curl -s "http://ip-api.com/json/<ip>?fields=query,isp,org,as,country,city"` — real ISP ASN (e.g. Chinanet AS4134) means port-forwarding will work; carrier NAT (CGNAT) means it won't and you need a hosted TURN / VPS instead.
   **CGNAT signature**: router WAN IP in the `100.64.0.0/10` range (100.64.x – 100.127.x) = carrier-grade NAT (China Telecom/Unicom/Mobile all use it). Port-forwarding is then USELESS — public traffic dies at the carrier's NAT. Verified 2026-08: forwarding was configured correctly yet 3478 stayed unreachable from outside; the coturn `external-ip` (an old, reclaimed public IP) was also stale. CGNAT escape routes: (a) call ISP to open public IPv4 (free on CN home broadband, "我需要公网 IP 用于 NAS 远程访问"), (b) IPv6 (see IPv6 fallback section), (c) VPS with public IP.

## Symptom: incoming call OK, answer → spinner forever (media path dead)
Signaling (HTTPS) works — the call arrives — but WebRTC media never establishes; ICE gathering/connecting is stuck. Every candidate path is dead. Check in this order:
1. **TURN relay candidate addresses poisoned by stale `external-ip`** (verified 2026-08): coturn line `external-ip=<old-reclaimed-public-ip>/<private>` makes the server announce the dead IP to clients → relay unreachable for EVERYONE (both phones spin). **FIX: delete the `external-ip` line entirely** and keep `relay-ip=<lan>` + `relay-ip=<v6-global>` — relay then advertises the LAN addr (WiFi clients OK) and the v6 global addr (4G clients OK). Restart coturn; `docker logs <coturn>` must show both relays initialized.
2. **UDP inbound dead on the NAS** — see "UDP inbound dead on Synology" below. TURN relay traffic is UDP; if inbound UDP is dropped, the relay can never carry media even though TCP 3478 connects fine.
3. **IPv6-only TURN/STUN + WiFi client without IPv6**: TURN/STUN listed as `[240e:...]:3478` is unreachable from a WiFi phone that has no IPv6 (check with `https://api6.ipify.org` on the phone). Same-LAN P2P host candidates can still connect UNLESS the WiFi has AP/client isolation — then even host candidates fail and the call spins.

## Symptom: two 4G phones call OK, but 4G ↔ WiFi pair spins (relay address-family mismatch)
Verified 2026-08: both phones HAVE IPv6 (WiFi on the main router, main-router IPv6 firewall OFF, so it's not firewall/缺少v6). Two-4G calls work (same carrier v6 → P2P direct). 4G ↔ WiFi fails even though both endpoints have v6. Root cause: **TURN relay address family follows the client's connecting address family** — the WiFi phone dials the INTERNAL TURN (`192.168.1.200:3478`, reachable & fast) and gets a relay on `192.168.1.200:port` (LAN-only); the 4G phone dials the v6 TURN and gets a v6 relay. The two relays can't reach each other across networks (4G can't route to 192.168.1.x; WiFi-v6 could reach the v6 relay but the pair is already broken). P2P also fails: 4G srflx (carrier v6 `240e:476:...`) vs WiFi srflx (home v6 `240e:39e:396:6520:...`) — cross-network v6 P2P didn't establish here.
Diagnosis: while the call spins, sample NAS conntrack — `docker run --rm -v /proc/net:/hostproc alpine sh -c 'grep -E "3478|dport=49[0-9][0-9][0-9]" /hostproc/nf_conntrack | head'` — look for BOTH phones' v6→NAS:3478 sessions and any relay-port (49xxx) session. No relay session = media never rode the relay.
**PITFALL — timing & filter scope of the conntrack sample**: (a) don't start a timed sampling window and THEN message the user to begin the test — killing the app, reopening it, and dialing takes longer than a 2.5-min window, so "all empty" may just mean the window expired. Sample IMMEDIATELY after the user hangs up (UDP conntrack entries persist 30–180s after the call). (b) Filter with `grep -E '240e|192.168.1'`, not `240e` alone — a WiFi phone dialing the INTERNAL TURN (192.168.1.200:3478) has a `192.168.1.x` source and a v6-only grep silently misses it. (c) All-empty conntrack while a call spins = the phones never dialed TURN (client-side behavior), NOT a coturn/server problem.
Mitigations (in order of preference, all untested on this NAS yet):
1. Make both phones use the SAME reachable TURN endpoint: remove the internal `192.168.1.200` TURN entry so the WiFi phone also dials the v6 TURN → both relays are v6 → cross-network relay works. (Caveat: an IPv6-only TURN list itself was shown to break iOS ICE gathering — see Connection time optimization warning; combine with a v4/domain STUN entry.)
2. Force P2P v6: verify cross-carrier v6 reachability (4G phone browser to `https://[wifi-phone-v6]:port` is impractical; use a real test or accept the limitation).
3. Get a public IPv4 (call ISP) so relays/STUN have a family both sides share.
No public IPv4 + one side v6-only + other side LAN-only = this call pattern is structurally hard; set expectations with the user.

**Directionality clue — cellular IPv6 inbound is a STATEFUL firewall (verified 2026-08):** the pair direction decides success: "4G dials WiFi → works (most of the time)", "WiFi dials 4G → spins forever". Root cause: carrier mobile v6 (CN `240e:476:...`) permits outbound and the matching REPLY, but blocks unsolicited inbound to the phone (no prior outbound state). So: 4G phone dialing = 4G sends media out first → carrier allows replies → bidirectional call works. WiFi phone dialing = WiFi sends first toward the phone's v6 → carrier drops the unsolicited inbound → the 4G side never receives media → spinner. Two-4G works because both sides' dial-out probes create state. **Ask the user WHICH DIRECTION fails before diagnosing** — a direction-dependent result is a carrier-inbound policy issue, not a TURN/relay-family misconfig.

**Final verdict — pure-IPv6 environment: iOS Talk never dials TURN at all (verified 2026-08).** After STUN v6-only + TURN as domain (`tmmddsm.myds.me:3478`) + schemes `turn` only (no `turns`), conntrack sampled DURING a spinning WiFi→4G call was STILL all-empty (no `:3478`, no `49xxx` sessions): the iOS/WebKit WebRTC client does not initiate TURN allocation in an IPv6-only world. Why: every phone's v6 (cellular and home SLAAC) is itself a public host address, so ICE goes straight to P2P host candidates and relay gathering never triggers before the P2P timeout — the user's ~30s spinner IS that P2P timeout; TURN would only start after much longer. Service-side config is irrelevant at that point. The ONLY robust fix is a **public IPv4 (call the ISP, free on CN home broadband)**: TURN/STUN then get a v4 family iOS uses reliably, WiFi→4G relays work, and IPv4-only visitors can reach the server. Domain-based TURN (`turn:host:3478`) is a friendlier middle state than IPv6-literal URLs but does not change the v6-only outcome.

## UDP inbound dead on Synology NAS (TCP in OK, UDP in times out)
Verified 2026-08 on this NAS: TCP 3478 reachable (LAN + public v6), UDP 3478 times out from EVERY source (Windows PC AND the side router — so it is not a per-client path issue). Outbound UDP is fine: `docker exec talk-coturn turnutils_stunclient stun.l.google.com 19302` returns a reflexive addr.
Diagnostic ladder:
1. `netstat -uln | grep <port>` — confirm coturn listens UDP (multiple sockets per address is normal).
2. Packet capture (see tcpdump pitfall below): packets arrive `eth0 In` but NO response leaves → the drop is in netfilter, NOT coturn.
3. **The iptables toolchain is blind here**: `iptables -L INPUT` and `iptables-legacy -L INPUT` both fail `No chain/target/match by that name` — DSM 7.2's filter table lives in an nft layer the CLI cannot see; only nat (`DEFAULT_PREROUTING`) and mangle tables are legacy-visible. `INPUT_FIREWALL` (DSM's own chain) shows only allow rules; mangle is all-ACCEPT; ovs dump-flows shows nothing.
4. Read `/usr/syno/etc/firewall.d/firewall_settings.json` — `"status": true` means **the DSM firewall IS enabled even if the user believes it's off** (it was re-enabled between sessions). The blocking rule is invisible to the CLI, so the FIX path is the DSM GUI: Control Panel → Security → Firewall (default policy allow/deny) and Security → Protection (DoS protection can rate-limit/drop inbound UDP). Have the user check/change there, then re-probe UDP from outside.

**SECOND root cause (2026-08, distinct from the firewall): the NAS default gateway points at a transparent-proxy side router, and the proxy chain eats UDP replies.** Same symptom set (TCP in OK, UDP in times out, capture shows `eth0 In` packet with NO response leaving, UDP outbound fine) — but the cause is NOT netfilter: the coturn reply is routed out the default gateway (192.168.1.88 OpenWrt transparent proxy), which drops it. Tell-tale: the user reports "changing the NAS default gateway to direct-route the main router fixes it instantly". When the user reports that, do NOT keep digging in firewalls — go straight to **policy routing so TURN/STUN replies bypass the proxy** (see references/talk-direct-policy-routing.md + scripts/talk-direct.sh (both in THIS skill): mark mangle OUTPUT by src-port 3478/3479/5349/49152-65535 → `ip rule fwmark 1 table 100` → default via main router; verified working on DSM 7.2 where CONNMARK/connmark/`ip rule sport` are all unavailable but `-j MARK --set-mark` works).

**PITFALL — same-subnet UDP probe timing out does NOT prove the public path is dead.** This session: the Windows PC (same LAN as the NAS) timed out on UDP 3478 the whole time, yet tcpdump caught real 4G-phone STUN requests arriving `eth0 In` AND responses leaving (`Out`) — i.e. the public path was healthy the entire time. The LAN probe traverses a different path (and can be affected by the Windows side). Trust tcpdump on the NAS for arrival/response, and a real 4G phone for end-to-end — not the LAN PC probe.

## Connection time optimization (slow call setup)
Symptom: calls connect but slowly (e.g. ~30s from dial to ring). The dominant cost is **ICE gathering: the client probes EVERY STUN/TURN server in the list, and each unreachable one costs a full timeout wait** (seconds each; a 3-STUN list with 2 dead endpoints ≈ tens of seconds).

**⚠️ WARNING — do NOT trim the list down to IPv6-only (verified 2026-08 on this NAS, with real user impact):** removing ALL IPv4 entries so the client ICE list holds only `[240e:...]:3478` literals made EVERY call spin forever (both 4G AND WiFi) on iOS/WebKit WebRTC — iOS tolerates IPv6-only ICE server lists poorly (the `turns:` scheme also targets 5349, which coturn doesn't listen on). The original "bloated" list (internal `192.168.1.200` + v6 + Google) WORKED: iOS probes in parallel and falls back to host candidates, so unreachable entries cost a few seconds but don't break calls. **Rollback = restore the original JSON arrays in `oc_appconfig` (`appid='spreed' AND configkey='stun_servers'/'turn_servers'`) via a piped SQL file, then `docker restart nextcloud`.** Get connection-time gains elsewhere — the proxy-bypass policy routing (references/talk-direct-policy-routing.md) — instead of shrinking the ICE list. If you must trim, keep at least one IPv4/domain entry per list; never leave only IPv6 literals.
- **If iOS never dials TURN at all (conntrack shows ZERO `:3478` sessions from the phones while a call spins), try switching the TURN schemes to `turn` ONLY (drop `turns`)** — coturn's `tls-listening-port=5349` is often not listening, and a `turns:` ICE URL pointing at a dead TLS port can make WebKit abandon the whole TURN entry. Change (2026-08, outcome pending phone retest): `occ talk:turn:delete turn,turns '<server>' udp,tcp && occ talk:turn:add turn '<server>' udp,tcp --secret=<secret>` → client ICE gets `turn:` (UDP 3478) only. Then `docker exec <nc> apachectl -k graceful` (APCu caches appconfig) and fully kill/reopen the Talk app.
- **coturn's default log level does NOT log successful TURN sessions** — an empty `docker logs <coturn>` grep for allocate/session/peer proves nothing. Judge "did the phone actually use TURN" by sampling NAS conntrack during the spinning call (see the 4G↔WiFi section): all-empty samples (no `:3478`, no `49xxx` relay sessions) = the phones never dialed TURN → problem is client-side ICE config (or iOS not using it), NOT coturn.
- Deletion commands: `occ talk:turn:delete <schemes> <server> <protocols>` (positional, e.g. `turn,turns 192.168.1.200:3478 udp,tcp`) works; `occ talk:stun:delete <server>` may hit the AppConfig bug → DB edit (see Pitfalls).
- After changes: reload the appconfig cache and re-fetch. **Prefer `docker exec <nc> apachectl -k graceful`** (in-container Apache graceful restart — clears the FPM/APCu cache WITHOUT the docker-restart approval prompt; container PID 1 is apache2, verify with `docker exec <nc> ps -p 1`). Fall back to `docker restart nextcloud` only if graceful fails. Clients must fully kill/reopen the Talk app to re-fetch the ICE list.

## E2EE scope (user Q&A — chat only, NOT calls)
Nextcloud Talk E2EE covers **chat messages (1:1) only; it does NOT cover calls/video**. Call media is ALREADY end-to-end encrypted via WebRTC DTLS-SRTP: P2P → keys negotiated directly between phones; via TURN → coturn forwards only encrypted packets. E2EE is experimental: iOS client support incomplete, history may become unreadable after enabling, lost device keys = permanent message loss, and it's enabled per-conversation (client-side), not a server toggle. Default advice: don't enable for calls (no effect); enable only for sensitive 1:1 chat with backups understood.

## The fix (self-hosted coturn)
1. Router: forward TCP+UDP `<listening-port>` (3478) → NAS IP. Basic TURN relay needs no extra port ranges (relay traffic is outbound from the server).
2. Update the DB config to a PUBLIC address (keep `secret` identical to coturn's `static-auth-secret`):
   ```bash
   docker exec -u www-data <container> php occ config:app:set spreed turn_servers --value='[{"schemes":"turn,turns","server":"<public-ip-or-domain>:3478","secret":"<same secret>","protocols":"udp,tcp"}]'
   ```
3. Re-probe 3478 from outside until STUN responds; then test a call from a phone on 4G/5G (clients must reload the Talk page / restart the app to fetch new ICE servers).

## High Performance Backend (HPB) signaling — where clients get their TURN list
When Talk is fronted by spreed-signaling (HPB), the client's ICE/TURN servers come from the **HPB config file**, NOT the Nextcloud `turn_servers` DB value. A missing `[turn]` section = clients get no TURN = 4G fails while WiFi (LAN P2P) still works. This was a real root cause 2026-08 (after TURN/DB/coturn were all correct).
- Find WHICH file the running container actually loads: `docker inspect <signaling> --format "{{range .Mounts}}{{.Source}} => {{.Destination}}{{end}}"` and check the restart log line `Starting signaling server with <path>` + `Listening on 0.0.0.0:<port>`.
  On this NAS: talk-signaling2 mounts `/volume1/docker/talk2/signaling2/server.conf` (port 8083, backend=nextcloud2:9801) — nc2's HPB; `/volume1/docker/talk/signaling/server.conf` (8082, backend=nextcloud:9800) is nc1's. Editing the wrong one (talk/ vs talk2/) silently does nothing. Host files under `/volume1/docker/` are writable by the SSH user; container copies are read-only.
- Add (backup host file first, then `docker restart <signaling>`):
  ```
  [turn]
  secret = <same secret as coturn static-auth-secret>
  url = turn:[<host>]:3478?transport=udp
  url = turn:[<host>]:3478?transport=tcp
  ```
  IPv6 in TURN URLs needs brackets too. Per-instance mapping: nc1 → talk-coturn :3478 / `nextcloud_turn_secret_2026`; nc2 → talk-coturn2 :3479 / `nc2_turn_secret_2026`.
- Also clean the DB `stun_servers` of any dead hosted endpoint (e.g. Metered) — point it at the local coturn (`["<host>:3478"]`) or `stun.nextcloud.com:443`.

## Hosted TURN provider compatibility rule
Nextcloud Talk accepts TURN servers ONLY in `static-auth-secret` mode: Nextcloud mints short-lived HMAC credentials (username=unix timestamp, password=base64(hmac_sha1(secret, username))) and hands them to clients. Any provider that only offers fixed username/password credentials (e.g. Metered.ca) is NOT compatible with Nextcloud Talk, even though its TURN servers speak standard RFC protocols. Evaluate the AUTH MODEL first, not the endpoint list. See references/metered-ca.md.

**Metered Open Relay (free) is DEAD as of 2026-08 — do not configure it.** The docs page `metered.ca/tools/openrelay/` still advertises `staticauth.openrelay.metered.ca` + `openrelayprojectsecret` for Nextcloud (it's the one free endpoint that DID support auth-secret), but live probes show: TCP 80/443 connect, yet STUN binding, TURN allocation (`turnutils_uclient -W openrelayprojectsecret ...` hangs), and HTTPS all get no response. The page is SEO residue. Only the paid product (username/password auth) is still alive. Always verify a hosted TURN with an actual allocation test before wiring it into Nextcloud.

## IPv6 fallback (free CGNAT bypass)
When the ISP won't give a public IPv4, IPv6 often works with zero cost: CN mobile 4G/5G and home broadband both ship IPv6, and IPv6 has no NAT — a 4G phone can reach the NAS directly. Verified path 2026-08:
1. **Router**: enable IPv6 on the main router (PPPoE). WAN gets a `240e:` prefix (China Telecom).
2. **PITFALL — LAN advertises ULA, not the public prefix**: many routers then RA-advertise only a ULA (`fd87:`/`fdxx:` = IPv6 "private") to LAN devices. A ULA address is NOT reachable from 4G. The router's IPv6 page must advertise the PUBLIC `240e:` prefix to the LAN (manually set LAN IPv6 prefix if the model allows).
   **Root cause found 2026-08**: the ULA RA often comes from a SIDE router (旁路由, OpenWrt/ImmortalWrt) running odhcpd, which advertises its own ULA prefix AND announces itself as default IPv6 router (`ip -6 neigh` shows it with the `router` flag) — this shadows the main router's public-prefix RA for every LAN device. Fix on the side router (SSH root):
   ```
   uci set dhcp.lan.ra="disabled"; uci set dhcp.lan.dhcpv6="disabled"; uci commit dhcp; /etc/init.d/odhcpd restart
   ```
   Also: the main router (TP-LINK TL-ER6229GPE-AC, admin UI at `http://192.168.1.2:9000`) ships with **LAN IPv6 off even after WAN IPv6 is enabled** — enable it via 基本设置→接口设置 (IP协议类型=IPv6, 前缀授权接口=WAN1) and advertise via 基本设置→LAN设置→SLAAC (新增条目). The IPv6 module exists but lives under 基本设置, NOT 传输控制 (see CORRECTED VERDICT below). And note the NAS host has no tcpdump, so verify RA arrival by checking `ip -6 addr/route` after disabling the side router.
3. **NAS (Synology DSM)**: `accept_ra=0` on the NICs means the kernel ignores RA → no global address even though the router advertises. Fix via DSM: Control Panel → Network → Network Interface → edit NIC → IPv6 → Auto (flips `accept_ra` to 2). **PITFALL: you cannot flip it yourself — `/proc/sys` is Read-only inside docker exec -u root containers** (non-privileged); must go through DSM or admin SSH.
4. **PITFALL — static IPv6 without gateway**: if configuring IPv6 manually in DSM, you MUST also fill the default gateway (router LAN IPv6 addr, usually prefix::1, e.g. `240e:398:ba01:fa40::1`). Without it `ip -6 route show default` is empty and nothing egresses.
   **PITFALL — wrong gateway value**: a manually entered gateway that isn't the router shows `ip -6 neigh show <gw>` = FAILED/INCOMPLETE and nothing egresses. Cross-check before trusting any value: derive the router's link-local from its MAC (EUI-64) or read the router's LAN IPv6 page. Do NOT copy the router's WAN IPv6 address into the NAS static config (address conflict, silent failure). `prefix::1` is a guess — confirm via ND. Note `ping6` fails for non-root SSH users with "Operation not permitted" (no raw socket); use `curl -6` to an IPv6 endpoint for egress tests.
5. Verify NAS has a `240e:` global addr + default route, then `ping6 2400:3200::1` (AliDNS).
6. Then: coturn must listen/relay on IPv6, the router's IPv6 firewall must allow 3478 (TP-LINK ER default blocks inbound), and Nextcloud `turn_servers` uses `[240e:...]:3478` (brackets required for IPv6). Concrete coturn steps (verified 2026-08):
   ```bash
   # edit the HOST file (container mount is read-only), then restart:
   cp /volume1/docker/talk/coturn/turnserver.conf{,.bak}
   echo "relay-ipv6=<nas-global-v6-addr>" >> /volume1/docker/talk/coturn/turnserver.conf
   echo "listening-ip=::"                 >> /volume1/docker/talk/coturn/turnserver.conf
   docker restart talk-coturn   # same for talk2/coturn2 with its own path + port 3479
   # verify IPv6 + IPv4 STUN from inside the container:
   docker exec talk-coturn turnutils_stunclient -p 3478 <nas-v6-addr>   # expect "IPv6. UDP reflexive addr: <v6>:port"
   docker exec talk-coturn turnutils_stunclient -p 3478 192.168.1.200   # IPv4 still OK
   ```
   Then set Nextcloud DB config with the v6 address: `occ config:app:set spreed turn_servers --value='[{"schemes":"turn,turns","server":"[<v6>]:3478","secret":"<same-secret>","protocols":"udp,tcp"}]'` (IPv6 in brackets). TP-LINK ER IPv6 firewall lives at 安全管理 → IPv6防火墙 — it's a plain enable/disable switch with NO per-rule config; if inbound is blocked, disabling it (or adding access-control rules elsewhere) is the only option. Verify by actually calling from a 4G phone.

**CORRECTED VERDICT (2026-08, session end): the TP-LINK TL-ER6229GPE-AC DOES have a full IPv6 configuration module** — the earlier "no IPv6 module" conclusion was WRONG (we had only checked 传输控制). The IPv6 menu lives under **基本设置** (NOT 传输控制, whose submenu is only NAT设置/带宽控制/连接数限制/流量均衡/路由设置):
- 基本设置 → **接口设置**: set 右侧 IP协议类型 to **IPv6** → 状态=启用, 地址配置方式=EUI-64 (or 手动), 前缀授权接口=WAN1 (auto-fills the public prefix, e.g. `240e:39e:396:6520::`), auto-generates the LAN IPv6 addr from MAC. Save (network blips briefly).
- 基本设置 → LAN设置 → **SLAAC**: click 新增 → 服务接口=LAN1, IPv6地址前缀=leave empty (defaults to router prefix), DNS配置方式=DHCPv6, 状态=启用 → 确定. THIS is the step that makes the router RA-advertise the public prefix to LAN devices.
- Also available: LAN设置 → DHCPv6服务 / IPv6客户端列表 / IPv6静态地址分配.
Verified 2026-08: after 接口设置 saved with WAN1 prefix authorization, the box advertises `240e:39e:396:6520::/64`. NAS then needs DSM IPv6=Auto (accept_ra=2) + auto gateway to pick up a `240e:` global addr + default route.
Pre-check before IPv6 work: `ipconfig` on a LAN PC — if it shows only fe80, the router isn't advertising yet (check an SLAAC entry exists). Fall back to public IPv4 (call ISP) or a VPS coturn only if the router genuinely lacks the 基本设置→接口设置 IPv6 option.

## Pitfalls
- `config.php` is not readable by the SSH user on the NAS (Permission denied) — always read via `docker exec <container> cat/grep`.
- `docker` is NOT on the SSH user's PATH — use `/usr/local/bin/docker` (fallback `/var/packages/ContainerManager/target/usr/bin/docker`).
- 4G/5G failure is not a server problem when the TURN address handed to clients is private — fix the DB config, don't rebuild coturn.
- A Cloudflare-proxied domain makes 3478 look dead even when the NAS TURN works fine.
- **`occ config:app:set ... --type=json` fails with `Unknown type json`** on this Nextcloud build — omit `--type` entirely and store the JSON string; Talk json_decodes it on read (same for `stun_servers`).
- **`occ talk:stun:delete` can fail with `conflict between new type (mixed) and old type (array)`** (Nextcloud 33 AppConfig bug). Workaround: UPDATE `oc_appconfig` directly (`appid='spreed' AND configkey='stun_servers'`, value = JSON array string). Write the SQL to a LOCAL file and pipe it in: `cat fix.sql | ssh tmm@NAS "/usr/local/bin/docker exec -i nextcloud_db mysql -uroot -p'<pw>' nextcloud"` — inline `mysql -e` with nested quotes mangles the JSON and stores invalid `[[addr]:port]`. Verify with `occ talk:stun:list`.
- **`occ talk:turn:delete` takes positional args, not an index**: `talk:turn:delete <schemes> <server> <protocols>` (e.g. `turn,turns 192.168.1.200:3478 udp,tcp`).
- **Unreachable entries in the STUN/TURN list slow EVERY call** — ICE gathering probes each and waits out each timeout (see Connection time optimization).
- **SSH double-quote variable expansion**: `ssh host "cmd ${V6} ..."` expands `${V6}` LOCALLY (empty if only defined on the remote) — a TURN server value silently became `:3478`. Write literal values into the remote command, or single-quote the whole remote command and use `\$VAR` on the local side.
- **NAS host has no tcpdump, but you CAN capture packets** via a privileged docker container (verified 2026-08): `docker run --rm --net host --privileged alpine sh -c 'apk add --no-cache tcpdump >/dev/null 2>&1 && tcpdump -i any -n -vv udp port 3478'` (first `docker run` needs user approval). One capture answers "did the packet arrive / did a response leave" definitively — prefer it over guessing. For RA/prefix verification still use `ip -6 addr` / `ip -6 route show default` / `ip -6 neigh show`.
- **turning on IPv6 at the router is not enough** — check the LAN actually advertises the public prefix, the NAS NIC accepts RA, and a gateway route exists (see IPv6 fallback section).
- Metered's free Open Relay endpoint looks alive (ports open) but is dead — verify hosted TURN with an allocation test, never just a TCP connect.
- **`test-ipv6.com` loading ≠ IPv6 present** — the page opens fine over IPv4 too. Precise phone-side probe: open `https://api6.ipify.org` in the phone browser (blank = NO IPv6; a `240e:…` string = IPv6). Use this before concluding the phone has no IPv6.
- **A domain with ONLY an AAAA record is unreachable from any IPv4-only network** (friend's WiFi, many broadbands, some enterprise nets). Symptom seen 2026-08: "朋友用 WiFi 访问 tmmddsm.myds.me 打不开" while the user's own 4G works. This is the no-public-IPv4 limitation, NOT a config bug — set expectations up front: either get public IPv4 from the ISP (free on CN home broadband) or accept IPv6-only reachability; a tunnel/proxy is the only middle ground if both are refused.
- **Talk UI read**: call-icon lit = that client holds a live signaling connection (online); grey = that device is offline (app killed / backgrounded / session expired) — check the phone/app state, not the server. "Both on 4G, one lit one grey" is a client-connectivity issue, not a TURN config issue.
- **User preference — terminal first**: this user repeatedly asks "你不能在终端里完成吗?" when handed GUI steps. Exhaust terminal paths first (occ, curl to the router's HTTP API, host-file edits via SSH); only hand over unavoidable clicks (TP-LINK menu navigation) as a single precise mouse instruction, and say why terminal can't do it.
- **TP-LINK ER-series admin UI (192.168.1.2:9000) cannot be driven by cua-driver/browser automation** — it's an iframe+JS shell: UIA element/coordinate clicks (background AND foreground) don't register on menus, and direct URL navigation (`/stok=<token>/userrpm/<page>.htm`) is ignored (pages load via JS menu handlers). Do NOT burn turns on this; hand the user a mouse instruction ("click 传输控制 on the left") and read the result. See references/tplink-er6229gpe-ac-admin.md.

## References
- references/nas-setup.md — this user's NAS deployment: both Nextcloud instances, coturn configs, public IP, gateway, current state + pending fix.
- references/metered-ca.md — Metered.ca TURN research: auth model, endpoints, docs map, incompatibility notes.
- references/ipv6-cgnat-bypass-2026-08.md — full IPv6 bring-up transcript (accept_ra, ULA vs public prefix, static-gateway pitfall, coturn/Nextcloud IPv6 remaining steps).
- references/tplink-er6229gpe-ac-admin.md — main-router admin UI (192.168.1.2:9000): login, menu map, why automation can't drive it (hand mouse actions to user).
- references/hpb-turn-config-2026-08.md — spreed-signaling HPB `[turn]` config on this NAS: which container loads which file, per-instance secret/port mapping, symptom transcript.
- references/talk-direct-policy-routing.md — policy routing so TURN/STUN replies bypass a transparent-proxy default gateway: DSM 7.2 toolchain limits, script walkthrough, verification, persistence via DSM Task Scheduler.

## Scripts
- scripts/stun_probe.py — UDP STUN binding-request reachability probe: `python stun_probe.py <host> [port]`.
- scripts/talk-direct.sh — policy-routing installer: mark TURN/STUN src-ports → fwmark 1 → table 100 via main router (run as root on the NAS; persist via DSM Task Scheduler).
