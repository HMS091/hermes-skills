# Docker Container Proxy via OpenWRT Gateway

When running Hermes Agent inside a Docker container behind an OpenWRT (or similar router-based) proxy, the proxy is typically accessible on the gateway IP. Follow this procedure to discover and configure it.

## Discovery

1. **Find the gateway IP** — commonly the router LAN IP (e.g. `192.168.1.1` or `192.168.1.88` for OpenWRT)
2. **Probe common proxy ports:**

```bash
for port in 7890 7891 1080 1081 8080 3128; do
  timeout 3 bash -c "echo -n > /dev/tcp/192.168.1.88/$port" 2>/dev/null && echo "OPEN: $port" || true
done
```

Typical findings:
- `7890` — Clash HTTP proxy
- `7891` — Clash SOCKS proxy  
- `1080` — SOCKS5 proxy
- `8080` — HTTP proxy (various)

## Verification

Set the proxy and test blocked sites:

```bash
export http_proxy=http://192.168.1.88:7890
export https_proxy=http://192.168.1.88:7890

# Test blocked sites
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 10 "https://www.google.com"
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 10 "https://huggingface.co"
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 10 "https://lite.duckduckgo.com"
```

## Persisting the Config

The proxy env vars are **not set by default** inside the container. To make them persistent:

### Option A: Docker run flags
```bash
docker run -e http_proxy=http://192.168.1.88:7890 -e https_proxy=http://192.168.1.88:7890 ...
```

### Option B: Write to /etc/environment (if persistent)
```bash
echo "http_proxy=http://192.168.1.88:7890" >> /etc/environment
echo "https_proxy=http://192.168.1.88:7890" >> /etc/environment
```

### Option C: docker-compose.yml
```yaml
environment:
  - http_proxy=http://192.168.1.88:7890
  - https_proxy=http://192.168.1.88:7890
```

## Pitfalls

- The proxy env vars must be set **before** curl/wget commands run — setting them mid-session via terminal works, but a new shell inherits from the parent process
- `host.docker.internal` is **not available** on Linux Docker by default (only Docker Desktop on macOS/Windows). On Linux, use the gateway IP directly
- SOCKS proxies (`1080`) work for most protocols but HTTP proxies (`7890`) are simpler for `http_proxy`/`https_proxy` env vars
- Some docker images strip `http_proxy`/`https_proxy` from the env — check with `env | grep -i proxy` after setting
