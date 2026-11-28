# WARP-Clash-API Viability Assessment (July 2026)

**结论：不可用，不建议部署。**

## 项目概况

- **仓库:** vvbbnn00/WARP-Clash-API
- **Stars:** 8.8k | **Forks:** 1.1k
- **状态:** 已归档 (2026-02-21)，只读
- **最后更新:** 2年前 (157 commits 后停更)

## 核心问题

1. **Cloudflare API 已限制:** Issue #234 (2025-02 创建, 2025-10 最后更新) — 多人确认 403 Forbidden on api.cloudflareclient.com
2. **国内 IPv4 WARP 被墙:** Issue #217 (33条评论) — 2024年6月起 GFW 升级封杀 IPv4 WARP 节点
3. **项目停更:** 无人维护，所有分支也全部停更（最高 ⭐9 分支最后更新 2024-05）
4. **刷流量漏洞大概率已修复:** 18秒刷 1GB 的机制依赖的 API 返回 403

## 实测结果

- Cloudflare API 端点存活（HTTP 400，非 403）—— API 本身未死，但认证机制已变
- IPv6 WARP 部分用户还能用，但也不稳定

## 替代方案

### 方案 A: BPB-Worker-Panel（推荐）

- **仓库:** bia-pain-bache/BPB-Worker-Panel
- **Stars:** 12.2k | **Forks:** 31k
- **状态:** ✅ 活跃 (最后更新: 2026-07-04, 每日更新)
- **语言:** TypeScript (GPL-3.0)
- **部署:** Cloudflare Workers / Pages (免费, 无需 VPS)
- **功能:** VLESS + Trojan + WARP + WARP Pro 订阅; Fragment 支持; 私有 DoH; 链式代理; 密码保护面板
- **限制:** Workers 每天 10万请求 (适合2-3人); UDP 支持不完整
- **客户端:** v2rayNG, MahsaNG, Clash Meta, Sing-box, Streisand, v2rayN 等
- **地址:** https://github.com/bia-pain-bache/BPB-Worker-Panel

### 方案 B: warp-config-generator-vercel

- **仓库:** nellimonix/warp-config-generator-vercel
- **Stars:** 942 | **Forks:** 41
- **状态:** ✅ 活跃 (最后更新: 2026-07-03)
- **语言:** TypeScript/Next.js (MIT)
- **部署:** Docker / Vercel / Netlify / Cloudflare Workers / Cloudflare Pages
- **功能:** WARP WireGuard/AmneziaWG/Clash/Throne/Nekoray/Karing/Husi/WireSock 配置生成; 服务选择 (Netflix/YouTube 等走 WARP); 二维码
- **部署方式:** `docker run -d -p 3000:3000 ghcr.io/nellimonix/warp-config-generator-vercel-public:latest`
- **Telegram Bot:** @warp_generator_bot
- **地址:** https://github.com/nellimonix/warp-config-generator-vercel

### 方案 C: cmj2002/warp-docker（需改Proxy模式，不推荐NAS）

- **仓库:** cmj2002/warp-docker
- **Stars:** 970 | **Forks:** 241
- **状态:** ⚠️ 部分可用 (最后代码更新 2025-10, Docker镜像自动构建中)
- **部署:** Docker（官方 WARP 客户端容器化）
- **输出:** SOCKS5/HTTP 代理 :1080
- **Synology 兼容性:** ❌ 默认模式报 nftables 错误 (Issue #16, 13条评论)
- **Workaround:** 切换到 proxy mode (`warp-cli mode proxy`) 可绕过 nftables，但失去 UDP
- **其他风险:** Issue #79 内存泄露 (2026-06 最新反馈)
- **地址:** https://github.com/cmj2002/warp-docker

### 方案 D: baby9/wgcf-socks-docker（NAS可用但无人维护）

- **仓库:** baby9/wgcf-socks-docker
- **Stars:** 12 | **Docker Pulls:** 3181
- **状态:** ⚠️ 低活跃 (代码最后更新 2024-05, Docker 镜像最后推送 2024-06)
- **原理:** wgcf + sing-box (userspace WireGuard) — 不使用官方 WARP 二进制，无 nftables 问题
- **权限:** 不需要 NET_ADMIN/TUN，Synology 可直接运行
- **输出:** SOCKS5:40001 + HTTP:40002
- **部署:** `docker run -d -p 40001:40001 -p 40002:40002 --restart=unless-stopped zenexas/wgcf-socks:latest`
- **Open Issues:** 0
- **地址:** https://github.com/baby9/wgcf-socks-docker
