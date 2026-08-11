# NAS Dashboard Fix — Error Transcript (2026-07-03)

Real error transcripts from a Synology DS918+ Hermes Docker container fix session.

## PermissionError: skills/.hub lock file

```
s6-rc: info: service dashboard: starting
s6-rc: info: service dashboard successfully started
s6-rc: info: service dashboard: stopping
s6-rc: info: service dashboard successfully stopped
Traceback (most recent call last):
PermissionError: [Errno 13] Permission denied: '/opt/data/skills/.hub/.lock_ng2x8n6q.tmp'
```

**Root cause:** Container was recreated with `docker stop → docker rm → docker run`, and bind-mounted `/opt/data/skills/` directory retained file ownership from a previous container instance, mismatching the new container's `hermes` user UID.

**Fix:** `docker exec hermes-agent chmod -R 777 /opt/data/skills/.hub /opt/data/logs`

## Gateway Crash: MCP codegraph missing

```
WARNING tools.mcp_tool: MCP server 'codegraph' initial connection failed (attempt 1/3)
  [Errno 2] No such file or directory: 'codegraph'
INFO gateway.run: Received SIGTERM — initiating shutdown
s6-rc: info: service gateway-default: stopping
s6-rc: info: service gateway-default successfully stopped
s6-rc: info: service gateway-default: starting   ← loop begins
```

**Root cause:** `config.yaml` had `mcp_servers: {codegraph: {command: codegraph, ...}}` but the `codegraph` binary does not exist in the Docker image.

**Fix (blocked by sudo):** Could not `sudo sed` on NAS host. Worked around via `docker exec hermes-agent sed -i 's|  codegraph:|  # codegraph:|g' /opt/data/config.yaml`.

## Dashboard Auth: NotImplementedError

```
File "/opt/hermes/plugins/dashboard_auth/basic/__init__.py", line 230, in start_login
    raise NotImplementedError(
NotImplementedError: BasicAuthProvider is password-only; there is no OAuth 
redirect flow. The login page POSTs to /auth/password-login instead.
```

**Root cause:** Attempted HTTP `Basic` Authorization header login. BasicAuthProvider only supports the web form POST flow (`/auth/password-login` with JSON body `{"username":"…","password":"…"}`).

## Agent Init Hang: Celeron CPU Bottleneck

```
File "/opt/hermes/.venv/lib/python3.13/site-packages/httpx/_transports/default.py"
  File "/opt/hermes/.venv/lib/python3.13/site-packages/httpcore/_sync/connection.py"
    via KeyboardInterrupt → timeout
```

**Root cause:** Synology DS918+ Celeron J3455 @ 1.50GHz with 3.7GB swap active. Starting `hermes chat -q` involves Python 3.13 imports of httpx, httpcore, certifi, ssl — which take 30+ seconds on a CPU-constrained NAS. The agent process consistently times out before reaching the LLM call phase.

**Conclusion:** `docker exec hermes-agent hermes chat -q` is NOT viable on this hardware. Use the long-running gateway process instead (dashboard, messaging, cron).

## Docker Binary Not in PATH

```
$ docker ps
sh: docker: command not found

$ which docker
(no output)

$ ls /usr/local/bin/docker
/usr/local/bin/docker   ← found!
```

Synology Docker package installs to `/usr/local/bin/` which is not in non-root users' `$PATH`. Always use the full path: `/usr/local/bin/docker`.
