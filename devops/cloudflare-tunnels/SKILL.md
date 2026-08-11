---
name: cloudflare-tunnels
description: |
  Manage and troubleshoot Cloudflare Tunnel (cloudflared) connectors running as
  Docker containers on the NAS — map a dashboard tunnel ID to its container,
  and diagnose "tunnel closed/offline" (QUIC timeout, HTTP/2 blocked, SNI hijack).
  Primary fix for this user's network: OpenWRT dae (eBPF transparent proxy)
  hijacks non-CN traffic via fallback:proxy — add direct routing rules for
  Cloudflare edge IPs in dae's wing.db so the NAS tunnel connects directly.
  Tunnels MUST stay on NAS Docker; the user rejects Windows-host fallbacks.
version: 1.0.0
platforms: [windows, linux]
metadata:
  hermes:
    tags: [cloudflare, cloudflared, tunnel, nas, docker, network, proxy]
    category: devops
---

# Cloudflare Tunnels (cloudflared on NAS)

## When to use
- Cloudflare dashboard shows a tunnel as closed/offline/inactive and user wants it open
- Need to find which NAS container runs a given tunnel ID
- cloudflared logs show QUIC timeouts, TLS handshake errors, or cert errors

## Map dashboard tunnel ID → container (do this FIRST)
Tunnel tokens are JWTs; payload has `a` = account tag, `t` = tunnel ID (some versions use `tunID`). Decode ON the NAS with python3 — never print the token (it's a secret, and Hermes redacts JWT-looking strings in output anyway):

```bash
ssh tmm@192.168.1.200 'python3 -c "
import base64, json
for line in open(\"/volume1/docker/cloudflared-matrix/docker-compose.yml\"):
    s = line.strip()
    if \"eyJ\" in s:
        tok = s.replace(\"- \",\"\").replace(chr(34),\"\").strip(); break
p = tok + \"=\" * (-len(tok) % 4)
d = json.loads(base64.urlsafe_b64decode(p))
print(d.get(\"a\"), d.get(\"t\"))
"'
```

Compare BOTH account tag and tunnel ID against the dashboard URL: `dash.cloudflare.com/<account>/.../cloudflared/<tunnel-id>/...`.

**Pitfall**: docker-compose.yml may hold a placeholder (`把你的CF隧道TOKEN粘贴到这里`) while the RUNNING container has the real token (container was created another way). Extract from the live container instead:
`/usr/local/bin/docker inspect <name> --format "{{join .Config.Cmd \" \"}}"` — grab the `eyJ...` arg. New cloudflared tokens are single-segment (no dots), so base64 padding (`+ "=" * (-len % 4)`) is required.

## Diagnose "tunnel closed" (in order)
1. `docker ps -a` — is the container Up or Exited? Exited → check `docker logs`; e.g. `Error opening metrics server listener ... address already in use` means another process holds the metrics port — find it with `netstat -tlnp | grep <port>`.
2. `docker logs --tail 30 <name>` — match the signature:
   - `Failed to dial a quic connection ... timeout: no recent network activity` → UDP blocked (QUIC = UDP 443/7844). Try `--protocol http2` in the command.
   - `x509: certificate has expired ... current time ... is after 2020-10-17` on an argotunnel edge IP → **SNI hijack**: a middlebox injects a 2020 fake cert for `*.argotunnel.com` SNI. Confirm: `openssl s_client -connect <edge-ip>:443 -servername region1.v2.argotunnel.com` shows the fake 2020 cert, while the SAME command WITHOUT `-servername` shows a current valid cert. **IMPORTANT: TCP to the edge is usually FINE (`/dev/tcp/<ip>/7844` connects) — the block is TLS-level, done by the OpenWRT dae transparent proxy. Do NOT conclude "direct is blocked"; fix dae routing (section below).**
   - precheck lines tell you exactly what's blocked: "Allow outbound QUIC traffic on port 7844 or use HTTP2", "Allow outbound TCP on port 7844", plus "Cloudflare API ... status=pass" (api.cloudflare.com:443 reachable while edge is not).
3. **Do NOT use curl/openssl TLS tests against region*.v2.argotunnel.com as a success signal** — argotunnel edge rejects non-cloudflared TLS clients (handshake failure / EOF / unrecognized name) even on a healthy network. Only cloudflared's own logs prove connectivity.

## Pitfall: a Cloudflare-proxied hostname hides the NAS — UDP services unreachable
`nslookup <domain>` showing 104.21.x.x / 172.67.x.x means the hostname is Cloudflare-proxied, which forwards ONLY HTTP(S) on 80/443. Any UDP service (TURN 3478, QUIC, SIP) or arbitrary TCP port is unreachable through that hostname even when the NAS service is perfectly healthy — the proxy is in the path. Always test the REAL origin IP (coturn `external-ip`, router WAN IP) before concluding the NAS service is broken.
Real case (2026-08): Nextcloud Talk TURN `nc.ncncnc.ccwu.cc` → 104.21.2.66, port 3478 dead via the domain; origin 61.157.253.46:3478 also dead. Two independent layers, both had to be checked separately. **Follow-up correction (same session): the router port-forward was later configured correctly and 3478 STILL dead — the real blockers were (a) the TURN address in the Nextcloud DB was a private IP (192.168.1.200:3478, unreachable from 4G), and (b) the WAN is CGNAT (100.76.32.142, 100.64/10 range) so no public-IPv4 path exists; 61.157.253.46 was a stale reclaimed IP. Resolution moved to IPv6 — see skill `nextcloud-talk-troubleshooting` (references/ipv6-cgnat-bypass-2026-08.md). IPv6 ultimately failed too (TP-LINK ER6229GPE-AC firmware has no IPv6 LAN-config module) — see that skill's final verdict.**

## Primary fix: OpenWRT dae transparent proxy (root cause for this user)
Environment facts (verified 2026-08):
- NAS default gateway + DNS = OpenWRT at 192.168.1.88 (ImmortalWrt 24.10.1). SSH as **root** works keyless: `ssh root@192.168.1.88`.
- OpenWRT runs **daed** (`/usr/bin/daed run --config /etc/daed/ --listen 0.0.0.0:2023`) — an eBPF kernel-level transparent proxy. PassWall and OpenClash are installed but NOT running (`passwall.@global[0].enabled='0'`); dae is the actual hijacker.
- dae routing lives in SQLite `/etc/daed/wing.db`, table `routings` (single row, id=1), column `routing`. nftables shows its tproxy (dns 53 → tproxy :12345, fwmark 0x100).
- Default rule was `fallback: proxy` → every destination NOT geoip:private/cn or geosite:cn goes through the proxy node. Cloudflare edge IPs (198.41.0.0/16, 162.159.0.0/16) are not CN → tunnel traffic forced through proxy → hijacked. This also broke Docker Hub pulls on the NAS.

Fix recipe (backup → stop daed → edit db → start):
```bash
ssh root@192.168.1.88
cp /etc/daed/wing.db /etc/daed/wing.db.bak2
/etc/init.d/daed stop
# write new routing block to /tmp/new_routing.txt on OpenWRT, then:
sqlite3 /etc/daed/wing.db "UPDATE routings SET routing = (SELECT readfile('/tmp/new_routing.txt')) WHERE id = 1;"
/etc/init.d/daed start
```
New routing block — the CF direct lines must come BEFORE `fallback`:
```
routing {
pname(NetworkManager, systemd-resolved, dnsmasq) -> must_direct
dip(198.41.0.0/16, 162.159.0.0/16) -> direct
domain(suffix:argotunnel.com) -> direct
dip(geoip:private) -> direct
dip(geoip:cn) -> direct
domain(geosite:cn) -> direct
dport(53) -> direct
fallback: proxy
}
```
Pitfalls:
- OpenWRT has **no python** — use sqlite3 CLI only; multi-line SQL strings via `readfile('/tmp/...')` (inline multi-line strings break under SSH quoting).
- Stop daed before editing wing.db (it holds the file / caches config); start it after.
- After the dae fix, recreate the tunnel container so it re-runs prechecks: `cd /volume1/docker/cloudflared-<name> && docker compose up -d --force-recreate`. Remove any HTTPS_PROXY env from compose first — direct is the goal.
- Verify: `docker logs cloudflared-<name>` shows precheck `QUIC connection successful` / `HTTP/2 connection successful`, then `INF Registered tunnel connection ... location=laxXX protocol=http2` ×4. Dashboard flips to 正常 within ~1 min.
- One-shot cloudflared on Windows CAN be used as a connectivity PROOF (registers 4 connections), but is NOT the deliverable — see user preference below.

## User preference: tunnels must run on NAS Docker, NOT Windows
User explicitly rejected the Windows-host fallback: *"我要的结果是cloudflared的网络还是走nas docker,不要走windows,要不然电脑关了就无法运行了"* — if the PC is off the tunnel dies. Fix the network (dae routing), keep the connector in the NAS Docker container. Windows-host cloudflared is acceptable ONLY as a temporary diagnostic; never leave it as the solution.

## Diagnostics-only: Windows proxy stack (kept for reference)
These were tried and are NOT the fix (xray egress also can't complete argotunnel TLS — error changed to `unrecognized name`/`EOF`, meaning proxy engaged but its egress node is also blocked):
- `127.0.0.1:10808` = xray.exe (v2rayN) mixed HTTP+SOCKS, localhost-only
- `0.0.0.0:10809` = netsh portproxy → 127.0.0.1:10808, LAN-reachable — Windows inbound firewall blocks NAS until a rule is added: `New-NetFirewallRule -DisplayName "XrayProxy LAN 10809" -Direction Inbound -Protocol TCP -LocalPort 10809 -Action Allow -Profile Any`
- NAS→proxy reachability check: `timeout 5 bash -c "echo > /dev/tcp/192.168.1.58/10809"`
- If ever needed as last resort: add `environment: HTTPS_PROXY/HTTP_PROXY=http://192.168.1.58:10809` to compose + `docker compose up -d --force-recreate`, verify with `docker inspect <name> --format "{{json .Config.Env}}"` (compose edits don't always show in `docker exec env`).

## References
- references/tunnel-inventory-2026-08.md — container → tunnel-ID mapping for this environment, exact failure signatures, dae/proxy stack details, full debug transcript.
