# Free Docker Deploy Platforms (for running VPN / custom containers)

> Researched 2026-06-02 & 2026-06-03. Environment: Docker container on Synology NAS, no browser, no web_search tool. Used curl + Python HTML stripping.

## dcdeploy.com

| Detail | Value |
|--------|-------|
| URL | https://dcdeploy.com |
| Platform | WordPress + Elementor |
| Registration | Email only |
| Credit Card | Not required |
| Free Tier | "Always Free" — 1 service, DCD-1 machine |
| Free Specs | 250MB shared RAM, 5GB storage, 1 CPU |
| Billing | Pay-per-minute prepaid |
| Bandwidth | Unlimited (included) |
| Deploy Source | GitHub repo or Docker Registry |
| Status (June 2026) | Online and reachable |

Use case: Deploy any Docker container including VPN stacks (wg-easy, Algo, Outline).

## Northflank (Reference Benchmark)

The user referenced Northflank as the ideal model. Northflank has:
- Sandbox free tier with Docker support
- **BUT requires credit card verification** for the free plan
- Need to find **no-credit-card alternatives**

## Best Alternatives (No Credit Card Required)

### Tier 1: Railway.app (Best Northflank Alternative)
| Detail | Value |
|--------|-------|
| URL | https://railway.app |
| Registration | Email/GitHub |
| Credit Card | **NOT required** for free trial |
| Free Tier | 30-day trial with **$5 free credits**, then $1/mo Hobby plan |
| Specs | Up to 1 vCPU / 512MB RAM / 500MB volume storage |
| Docker | ✅ Native Dockerfile + GitHub auto-deploy |
| Traffic | 0.015/GB egress (free egress included within credits) |
| VPN | ✅ wg-easy works, any Docker container works |
| Status | ✅ **Best match for Northflank** — same UX, no credit card |

**Signup flow**: Email → get $5 free → deploy Docker → no card needed until upgrade.

### Tier 2: Koyeb (Permanent Free Tier)
| Detail | Value |
|--------|-------|
| URL | https://koyeb.com |
| Registration | Email/GitHub |
| Credit Card | **NOT required** |
| Free Tier | **Permanent free** — 1 Nano service |
| Specs | 1 vCPU (shared), 512MB RAM |
| Traffic | ~100GB/month outbound (free) |
| Docker | ✅ Docker image deploy, GitHub integration |
| VPN | ✅ Can deploy wg-easy or any Docker container |
| Status | ✅ **Cheapest long-term option** — truly $0/mo |

### Tier 3: Zeabur (Flexible)
| Detail | Value |
|--------|-------|
| URL | https://zeabur.com |
| Registration | Email |
| Credit Card | **NOT required** (confirmed: "Can I use Zeabur without a credit card? Yes") |
| Free Tier | Permanent Free plan (2C4G but limited features) |
| Docker | ✅ Docker support |
| VPN | ✅ Feasible |
| Status | ✅ Good for lightweight use |

## Other Checked Options (Excluded)

| Platform | Why Excluded |
|----------|-------------|
| **Northflank** | Requires credit card for free plan |
| **Fly.io** | Requires credit card for free tier |
| **Gitpod** | Free plan cancelled |
| **GitHub Codespaces** | Requires credit card / paid |
| **Play with Docker** | 4-hour session limit, can't persist VPN |
| **Pipedream** | Workflow platform, not Docker VM |
| **Deno Deploy** | No Docker support |
| **OKteto** | Requires credit card for free 60-day trial |
| **Mogenius** | Kubernetes-based, not standalone Docker VM |
| **PikaPods** | Paid only |
| **alwaysdata** | Shared hosting, no Docker VM |
| **cloudno.de** | Free VPS offering unclear, minimal info |

## VPN Stacks to Deploy

- **wg-easy** — WireGuard + Web UI. Most popular. Lightweight. ~30MB image.
- **Algo VPN** — WireGuard-based, automated setup. Best for security.
- **Tailscale** — Free for 3 users. Based on WireGuard. No port config needed.
- **Outline VPN** — Shadowsocks-based. Google-developed. Good for restrictive networks.

## Research Method (no browser)

When browser / web_search tools are unavailable:

```bash
# 1. Check site alive
curl -sL -o /dev/null -w "%{http_code}" https://site.com

# 2. Get full HTML
curl -sL "https://site.com" > page.html

# 3. Extract structured text (strip JS/CSS, keep meaningful content)
curl -sL "https://site.com/pricing/" | python3 -c "
import sys, re
html = sys.stdin.read()
text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', ' ', text)
text = re.sub(r'\s+', ' ', text).strip()
for line in text.split('.'):
    if any(kw in line.lower() for kw in ['free', 'pricing', 'plan', 'traffic']):
        print(line.strip()[:200])
"

# 4. Alternative: DuckDuckGo with proxy
# Docker IPs get rate-limited by DuckDuckGo. Use proxy:
curl -sL -x "http://proxy:port" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
  "https://html.duckduckgo.com/html/?q=..."
```

## Multi-site Bulk Check Pattern

When investigating many candidate platforms simultaneously:

```bash
# Bulk HTTP status check
for url in "site1" "site2" "site3"; do
  code=$(curl -sL --connect-timeout 10 --max-time 15 -x "http://proxy:port" \
    -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
  echo "[$code] $url"
done
```

## Pitfalls

- **DuckDuckGo blocks Docker IPs** — returns CAPTCHA challenge page or empty results. Use proxy (`-x http://proxy_ip:port`) to route through home network.
- **Google also blocks without JS** — returns "enable JavaScript" page. Use DuckDuckGo-HTML with proxy instead.
- **Bing returns empty** — also JS-dependent from Docker.
- **WordPress/Elementor sites** have heavy inline CSS — strip with Python regex before reading.
- **User need clarification**: "Docker deploy" can mean app hosting (PaaS) vs. Docker VM (full control). The user wanted the latter — a place to deploy a Docker container that acts as a VPN server. Confirm which before deep research.
- **Per-minute billing platforms** often need prepaid balance for paid plans, but free tier may still work.
- **"Free" often means "free trial" not "always free"** — check the FAQ section for "always free" or "permanent free" keywords.
- **Some platforms say "No credit card required" for signup** but require one to activate the free tier (e.g. Northflank). Verify by reading the signup/pricing FAQ carefully.
