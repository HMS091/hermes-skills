---
name: hermes-multi-instance
description: "Set up Hermes-to-Hermes communication between two instances (e.g. Windows desktop + NAS Docker) for collaboration — peer chat, task delegation, shared data, and Kanban workflows."
version: 1.2.0
author: Hermes Agent
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [hermes, multi-instance, collaboration, ssh, api-server, kanban]
    related_skills: [hermes-skills-sync, hermes-agent, kanban-orchestrator]
---

# Hermes Multi-Instance Setup

Connect two Hermes instances (e.g. Windows desktop + NAS Docker) so they can collaborate like colleagues: chat, delegate tasks, share data, and coordinate via Kanban.

## When to Use

The user wants to run Hermes on two machines (e.g. desktop + NAS) and have them work together — not just sync skills, but communicate and coordinate in real time.

## Communication Approaches (Ranked)

### 🥇 Option A: API Server (Direct HTTP — Recommended)

Each Hermes exposes an OpenAI-compatible HTTP endpoint. They call each other's API directly over the local network. No external accounts needed.

**Port:** `8642` (default, configurable via `.env`)

**Enable on NAS:**
```bash
# In NAS Docker ~/.hermes/.env:
HERMES_API_SERVER_ENABLED=true
HERMES_API_KEY=<a-secure-token>
```

**Start:** `hermes gateway run` (API server is part of the gateway; it auto-starts when the `.env` flag is set)

**Call from Windows:**
```bash
curl -s http://192.168.1.200:8642/v1/chat/completions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"帮我分析这个日志"}]}'
```

**Endpoints:**
- `POST /v1/chat/completions` — standard chat
- `GET /v1/models` — list available models
- `GET /health` — health check

**Network requirements:** NAS must have port `8642` accessible from the Windows machine on the LAN. If the NAS firewall blocks it, add a rule allowing `192.168.1.0/24` on port `8642`.

**Pros:** Zero external dependencies, LAN-speed, full tool access.
**Cons:** NAS must expose a port; the calling Hermes needs to format API requests.

### 🥈 Option B: Shared Chat Platform (Telegram / Discord / Slack)

Both Hermes instances connect their gateways to the same group chat. They can @mention each other and communicate naturally.

**Setup:**
1. Run `hermes gateway setup` → select platform → link bot
2. Add both bots to the same group
3. Use `@bot_name <message>` to address a specific Hermes

**Pros:** Natural conversation flow, works anywhere (not just LAN), supports all message types (text/images/files/voice).
**Cons:** Requires external platform accounts; bot-to-bot messages use tokens.

### 🥉 Option C: Shared Filesystem + Cron (Simple Polling)

Share a NAS folder via SMB/NFS. Mount it on Windows as a network drive. Both instances write tasks and results to the shared folder, scanned by cron.

```bash
# Windows creates a task
echo "analyze this log" > Z:/shared/tasks/task-001.txt

# NAS cron runs every minute:
#  1. Check Z:/shared/tasks/ for new files
#  2. Process each task
#  3. Write results to Z:/shared/results/
```

**Pros:** No new services, works over any fileshare.
**Cons:** 1-minute latency, no conversational interaction, task format must be pre-agreed.

### Option D: Kanban Shared Board (Coordinated Task Management)

Put a Kanban SQLite database on the NAS shared folder. Both instances' worker profiles point to the same board.

```bash
# In each Hermes config.yaml:
kanban:
  db_path: Z:/shared/hermes-kanban.db
```

Then use `/kanban` slash commands or the `kanban_*` tools to create, assign, and complete tasks across instances.

**Workflow:**
1. Windows Hermes creates a task on the board
2. NAS Hermes (via cron or dispatcher) claims and executes it
3. Windows Hermes reviews and closes

**Pros:** True task delegation with state tracking, retry, blocking.
**Cons:** Requires Kanban setup; SQLite over network filesystem can have locking issues.

### Option E: SSH as Transport

If the NAS Hermes has no API server exposed, SSH into the NAS and send commands to its Docker container:

```bash
ssh tmm@192.168.1.200 "echo 'check disk usage' | docker exec -i hermes-container hermes chat -q"
```

**Pros:** Leverages existing SSH setup, no new ports.
**Cons:** One-off commands only, no session state, must know the Docker container name.

## NAS Docker Hermes Specifics

### Docker Container Discovery

When `docker ps` times out or returns nothing, it usually means the user (`tmm`) lacks Docker socket permissions:

```bash
ssh tmm@192.168.1.200 "groups"               # Check if user is in 'docker' group
ssh tmm@192.168.1.200 "ls -la /var/run/docker.sock"  # Check socket ownership
```

If the user is not in the `docker` group, prepend `sudo` or have the NAS admin add the user.

### SSH Connection Stability

Synology NAS devices have default SSH connection limits that ban IPs after rapid failures. See `hermes-skills-sync` skill for the fail2ban + MaxStartups fix.

When sending large batches of commands, **always combine them into a single SSH call** with `&&` chaining:

```bash
# DO: single combined call
ssh user@nas "cmd1 && cmd2 && cmd3"

# DON'T: multiple sequential calls (triggers rate limits)
ssh user@nas "cmd1"
ssh user@nas "cmd2"
ssh user@nas "cmd3"
```

### Non-Technical Users

If the user says "我不懂代码" (I don't understand code):
- Handle all SSH, Docker, config operations yourself
- Only ask the user to approve irreversible actions (e.g. port opens on NAS)
- Use clear step-by-step instructions in Chinese
- When blocked by NAS security (e.g. fail2ban), give the user a ready-to-send prompt for their NAS-side AI to execute

## NAS Hardware Limitations

**Synology DS918+ (Celeron J3455) is too slow for `hermes chat -q`.** Docker container initialization — Python imports, SSL context creation, MCP server discovery — takes 30+ seconds and times out before the agent loop starts. The gateway daemon runs fine (hot caches, long-lived process), but spawning a one-shot agent process for a chat query reliably fails with `KeyboardInterrupt` inside `httpcore`, `httpx`, or `certifi.where()`.

**This means Option E (SSH transport via `hermes chat -q`) is NOT viable on Celeron-class NAS hardware.** The gateway itself works, but you cannot invoke the agent from outside the container via `docker exec hermes-agent hermes chat -q`.

**Recommended approach for low-end NAS:** Option B (Telegram/Discord shared group) — the gateway handles messaging natively with no separate agent spawn. Or Option C (files + cron) — the gateway's cron scheduler invokes the agent inside its own long-running process.

### Docker Container Quirks on Synology

**Docker binary location:** Not in `$PATH` for non-root (and often non-interactive SSH) users. Always use `/usr/local/bin/docker`.

**Docker Hub pull failures (GFW / network):** `docker pull` from Docker Hub often times out on China-based NAS devices. Workarounds:
1. **Registry mirror:** Configure `/etc/docker/daemon.json` with a working mirror (e.g. `https://docker.1ms.run`)
2. **Pull elsewhere, save, transfer:** Pull on a machine with better connectivity, `docker save` to tar, scp to NAS, `docker load`
3. **GitHub clone + local build:** If the image has a public Dockerfile on GitHub, clone the repo and run `/usr/local/bin/docker build -t <name> .` on the NAS (GitHub often has better GFW reachability than Docker Hub)
4. **Alternative images:** Search Docker Hub for forks with the same name (e.g. `dublok/cloudflare-warp` as a replacement for the now-deleted `neilpang/cloudflare-warp`)

### Network & Port Diagnostics on Synology NAS

**Port checking:** Synology NAS often lacks `ss`. Use `netstat -tlnp` instead:

```bash
# Check if specific ports are occupied
ssh <alias> "netstat -tlnp 2>/dev/null | grep -E ':(1080|8888)\s'"

# List all listening ports
ssh <alias> "netstat -tlnp 2>/dev/null | grep LISTEN"
```

**Key pitfall:** Non-interactive SSH sessions (like those from Hermes `terminal()`) have a minimal `$PATH` — many binaries (`docker`, `ss`) won't resolve by name. Always use absolute paths or source the profile first.

**Permission drift after container recreation:** Bind-mounted directories (`/opt/data/logs/`) may lose write permissions after `docker run`, causing `PermissionError: [Errno 13]` on gateway startup. Fix: `docker exec hermes-agent chmod -R 777 /opt/data/logs`.

**Recapturing run parameters:** When recreating a container (e.g. to add port mapping), capture ALL parameters with:
```bash
/usr/local/bin/docker inspect hermes-agent --format '
Volumes: {{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Mode}})
{{end}}
Restart: {{.HostConfig.RestartPolicy.Name}}
' 
```

**Custom start.sh:** Synology Docker Hermes often uses a custom `/opt/start.sh` that patches CORS, injects CSS, and launches `hermes gateway run &` + `hermes dashboard`. Inspect it before assuming default behavior.

**Container recreation template:**
```bash
/usr/local/bin/docker stop hermes-agent && /usr/local/bin/docker rm hermes-agent
/usr/local/bin/docker run -d \
  --name hermes-agent \
  --restart unless-stopped \
  -v /volume1/docker/hermes/hermes_data:/opt/data:rw \
  -v /volume1/docker/hermes/ui/custom.css:/opt/hermes/hermes_cli/web_dist/custom.css:rw \
  -v /volume1/docker/hermes/ui/start.sh:/opt/start.sh:rw \
  nousresearch/hermes-agent:latest
```

### API Server Pitfalls

**Gateway crash from broken MCP servers:** If `config.yaml` references an MCP server whose binary is missing inside the container, the gateway crashes on startup and the s6 supervisor restarts it in a loop. The API server never starts. Disable the crashing MCP server:
```bash
docker exec hermes-agent sed -i 's|  codegraph:|  # codegraph:|g' /opt/data/config.yaml
```

**API Server may not be in older Docker images:** `gateway.api_server.enabled: true` in config + `HERMES_API_SERVER_ENABLED=true` env var may produce no listening socket. Check gateway logs for API startup messages:
```bash
docker exec hermes-agent cat /opt/data/logs/gateways/default/current | grep -i api
```

### Corrupt Lazy Packages

Hermes caches optional Python packages in `/opt/data/lazy-packages/`. Corrupted packages (e.g. `edge_tts` with Python 3.13) block agent init. Remove: `docker exec hermes-agent rm -rf /opt/data/lazy-packages/<broken_package>`.

### Dashboard Troubleshooting

**The Dashboard is a separate s6-supervised service** inside the Hermes Docker container, distinct from the gateway. It does NOT auto-start by default — it requires the `HERMES_DASHBOARD=true` env var.

#### Dashboard Won't Start

The s6 dashboard service checks `HERMES_DASHBOARD` env var. If not set, the service is supervised but permanently marked "down" (exit 125 → s6 permanent failure).

**Fix — set env vars + port mapping at container run:**
```bash
docker run -d \\
  -e HERMES_DASHBOARD=true \\
  -e HERMES_DASHBOARD_BASIC_AUTH_USERNAME=admin \\
  -e HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=yourpassword \\
  -p 9119:9119 \\
  ... (rest of volume mounts)
```

**Dashboard default port: 9119** (configurable via `HERMES_DASHBOARD_PORT`).

#### Dashboard Crash Loop (PermissionError)

**Symptom:** Container logs show `s6-rc: info: service dashboard: starting` → `…successfully started` → `…stopping` → `…successfully stopped` in a tight loop.

**Root cause:** `/opt/data/skills/.hub/` or `/opt/data/logs/` has wrong ownership after container recreation, denying write access to the `hermes` user inside the container.

**Fix:**
```bash
docker exec hermes-agent chmod -R 777 /opt/data/skills/.hub /opt/data/logs
docker restart hermes-agent
```

#### Dashboard Auth (June 2026 Hardening)

As of June 2026, `--insecure` is ignored. The Dashboard **requires** an auth provider on any non-loopback bind:
- **Password auth:** Set `HERMES_DASHBOARD_BASIC_AUTH_USERNAME` + `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`
- **OAuth:** Set `HERMES_DASHBOARD_OAUTH_CLIENT_ID`

The browser login flow: `GET /login` → POST JSON `{"username":"…","password":"…"}` to `/auth/password-login`. HTTP `Basic` Auth headers are NOT supported — use the web form.

#### Verifying Dashboard Health

```bash
# From NAS host
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9119/
# Expect: 302 (redirect to /login = dashboard is up)

# From Windows
curl -s -o /dev/null -w '%{http_code}' http://192.168.1.200:9119/
# Expect: 302

# Check the login page renders
curl -s http://192.168.1.200:9119/login | head -5
```

#### Gateway Crash from Missing MCP Binary

If `config.yaml` references an MCP server (e.g. `codegraph`) whose binary doesn't exist in the container, the gateway crashes on startup → s6 restarts it → crash loop → Dashboard never initializes because the container's s6 init sequence blocks on gateway readiness.

**Fix:**
```bash
docker exec hermes-agent sed -i 's|  codegraph:|  # codegraph:|g' /opt/data/config.yaml
docker restart hermes-agent
```

#### Log Verification After Fix

Check gateway and dashboard logs for clean startup (no crash loop):
```bash
docker exec hermes-agent sh -c 's6-svstat /run/service/dashboard; s6-svstat /run/service/gateway-default'
# Expect: both show "up (pid …) … seconds"
```

See `references/nas-dashboard.md` for full error transcripts (PermissionError, MCP crash, auth NotImplementedError).

### Key Discovery for NAS SSH

When connecting to a NAS with unknown SSH setup, try ALL available keys before asking for password:
```bash
# List available keys
ls ~/.ssh/*.pub | while read pub; do key="${pub%.pub}"; ssh -o ConnectTimeout=5 -i "$key" -o IdentitiesOnly=yes user@nas "echo connected with $key" 2>/dev/null && echo "FOUND: $key"; done
```
Use `-o IdentitiesOnly=yes` to prevent ssh from falling back to password auth and hanging.

## Decision Matrix

| User has... | Choose |
|-------------|--------|
| NAS with SSH only, no open ports | **Check hardware first.** Celeron-class NAS → Option B or C. x86 server → Option E may work. |
| NAS can expose port 8642 | **Option A (API Server)** — but verify Docker image supports it |
| Telegram/Discord account | Option B (shared chat) — **best reliability, zero NAS config** |
| SMB share already mounted | Option C (files + cron) |
| Wants structured task management | Option D (Kanban board) |
| Low-end NAS (Celeron, ≤2GB RAM) | **B or C only** — A and E depend on agent init speed |
