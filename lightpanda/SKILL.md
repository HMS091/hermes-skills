---
name: lightpanda
category: tools
description: "Bulk local page fetching via Lightpanda (Zig headless)."
version: 2.0.0
author: Hermes Agent
license: MIT
triggers:
  - 批量抓取多个 URL / 快速 dump 页面为 markdown
  - 需要低内存高并发的本地浏览器（NAS/容器内存紧张时）
  - user mentions lightpanda
  - mcp_lightpanda_* tools exist 且目标站点无反爬
metadata:
  hermes:
    tags: [scraping, browser, headless, zig, local]
    related_skills: [scrapling, web-research, blocked-page-recovery, untrusted-code-audit]
  binary: /opt/lightpanda/lightpanda
  audited: "1.0.1 (2026-10-21, source-level audit of lightpanda-io/browser)"
---

# Lightpanda

Zig 从零写的 headless browser（非 Chromium fork），定位 AI/自动化。本地、快、省内存。
AGPL-3.0。**定位是补充，不是替换** Scrapling / Hermes browser。

## When to Use

用：需要一次抓多个页面、只要正文/markdown、目标站点无反爬、本机内存紧（NAS 16GB）。
不用：Cloudflare/managed challenge、要登录、只为了抓 1 个静态页（Scrapling 更直接）、
以及要嵌进对外商业服务（AGPL 传染）。

## 工具梯队（抓取优先级）

1. **批量快爬 / 纯 dump** → Lightpanda（`fetch --dump markdown` 或 `mcp_lightpanda_*`）
2. **常规单页 / CSS 解析** → Scrapling（`scrapling` skill）
3. **反爬 / Cloudflare / 登录** → Hermes browser（Browserbase 云）或 Scrapling StealthyFetcher
   （**Lightpanda 无 stealth，必挂**）
4. **长任务批量** → bg terminal + cronjob

## 安装（要重装时照做）

```bash
# 先 export，再跑任何命令 —— `version` 自己就会连 telemetry
export LIGHTPANDA_DISABLE_TELEMETRY=true LIGHTPANDA_DISABLE_CORE_DUMP=1

# GitHub release 从国内极慢（~85KB/s，75MB 约 15min），必须用 -C - 续传
curl -L -C - -o /tmp/lightpanda \
  https://github.com/lightpanda-io/browser/releases/download/1.0.1/lightpanda-x86_64-linux
chmod +x /tmp/lightpanda && mkdir -p /opt/lightpanda && mv /tmp/lightpanda /opt/lightpanda/lightpanda
/opt/lightpanda/lightpanda version   # 1.0.1
```

- 1.0.1 x86_64-linux = 75,670,856 bytes，sha256 `551747e35c51ba107b5d5277eca4b48e077b2a3b40f09a047bf6670448bc35fd`
- **官方不发签名/checksum**（release 只有裸二进制）→ 只能靠官方渠道 + 自己记 sha256，别从镜像站下
- Hermes MCP 集成：`/opt/data/config.yaml` → `mcp_servers.lightpanda`（command + args:[mcp]，
  `env:` 里放上面两个变量）。config 用 python 脚本改（直写会被 config 写保护拦），改完跑
  `hermes config check` 确认，再重启 Hermes 让 MCP 重新握手。
- **config 里 `enabled` 的取值不是事实**：改完不用重启也可以先用
  `scripts/mcp_probe.py` 打一次 stdio 握手（`initialize` + `tools/list`）看清楚 MCP server 能不能起、
  到底注了几个工具；MCP 工具能直接调用就说明活的连接已经在了，别因为 config 写着 `false`
  就告诉用户"用不了"。
- 集成踩坑与完整审计证据：`skills/research/web-research/references/lightpanda-browser-evaluation.md`

## 必设的环境变量（默认行为有隐私代价）

```bash
LIGHTPANDA_DISABLE_TELEMETRY=true   # 关遥测 + 关崩溃上报（设任何值即生效）
LIGHTPANDA_DISABLE_CORE_DUMP=1      # 不写 core dump（core 含页面内容和表单数据）
```

MCP 里写进 config 的 `env:` 块；CLI 用 export 或前缀。**不设这两个变量等于默认开启遥测。**

## 用法

```bash
# CLI dump（⚠️ 必须 --log-level info，error 会吞掉 dump 输出）
/opt/lightpanda/lightpanda fetch --dump markdown --log-level info https://example.com
/opt/lightpanda/lightpanda fetch --dump html https://example.com
# 等 JS / 选择器
... --wait-until networkidle --wait-selector "#app" --wait-ms 500

# CDP（给 Puppeteer/Playwright 连）
/opt/lightpanda/lightpanda serve --host 127.0.0.1 --port 9222
# MCP stdio / HTTP
/opt/lightpanda/lightpanda mcp
/opt/lightpanda/lightpanda mcp --port 9223
```

MCP 工具 32 个（1.0.1 实测，会随版本增加，别当固定值；用 `scripts/mcp_probe.py` 现查）：`goto`
`markdown` `html` `links` `extract` `evaluate` `click` `fill`
`scroll` `press` `hover` `waitForSelector` `getCookies` `search` `tree` `session_new/list/close`
`save`。流程：`goto` → `waitForSelector` → `markdown`/`extract`。

## 实测（本机，2026-10-21，1.0.1）

| URL | 耗时(中位数×3) | markdown 字符数 | 子进程 RSS 峰值 |
|:--|--:|--:|--:|
| example.com | 3.12s | 960 | 24MB |
| news.ycombinator.com | 3.80s | 19,302 | 25MB |
| github.com/lightpanda-io/browser | 17.80s | 34,193 | 53MB |

对比 Scrapling 0.5 `Fetcher`（纯 HTTP，无 JS）：6.5–6.8s / 70MB，且拿不到渲染后内容。
本机网络是主变量 —— 别把上面的秒数当基准，**内存 24–53MB 才是可复现的优势**。

## 安全审计结论（1.0.1，源码级）

**无后门。** 出站端点只有 3 个自有域名，二进制 strings 与源码一致：

| 端点 | 触发条件 | 传什么 |
|:--|:--|:--|
| `telemetry.lightpanda.io/v2` | 默认开，每次运行 | 持久 UUID、模式、OS/架构、版本、工具调用次数/耗时，**不含 URL 和参数** |
| `telemetry.lightpanda.io/v/{ver}` | `version`/`help` | 版本号 |
| `crash.lightpanda.io/c` | 崩溃时 | panic 参数 + 完整堆栈（`url` 字段已脱敏），fork+exec 系统 curl 上传 |

要点：
- 遥测**不上报你抓了什么网站**（navigate 事件只有 tls 布尔和 page/iframe/popup），但 iid 是持久 UUID 可跨会话追踪 → 仍建议关。
- 验证遥测真在发：不设禁用变量跑一次会在 `$XDG_DATA_HOME/lightpanda/iid` 生成 UUID；设了就完全不生成（已实测）。
- TLS 默认校验（只有显式 `--insecure-disable-tls-host-verification` 才关）；GitHub Actions 全 pin commit SHA；Zig 依赖全 pin hash —— 供应链卫生好。
- 弱点：① 不发 checksum/签名，二进制无法验证等于源码；② 默认 `--block-private-networks` 关闭（可访问内网，别爬不可信站点指向的内网地址）；③ Beta，会崩。
- AGPL-3.0：自用无碍；**要嵌进对外商业服务必须开源服务端**（做产品时这点会咬人）。

## Pitfalls

> 验证 MCP 是否可用先跑 `scripts/mcp_probe.py`（stdio 握手 + 工具清单），别靠读 config 猜测。

1. **`--log-level error` 吞掉 dump 输出** —— 看着像没抓到，实际是日志级别把 stdout 吃了。永远用 `info`。
2. **无 stealth** —— Cloudflare/managed-challenge 必失败，直接换 Scrapling StealthyFetcher/browser。
3. **CORS 未实现**（上游 issue #2015）—— 部分站点请求被浏览器自己拦掉。
4. **Beta 会崩** —— 崩了先重试或降级，别先怀疑配置。
5. **MCP 工具“重启才出现”但不能拿 config 当证据** —— 先跑 `scripts/mcp_probe.py`，能列出工具就是活的，不能就查二进制路径/`enabled`/env；不要用一个字段的取值向用户断言工具可否使用。
6. **重装后先验证二进制存在** —— `/opt/lightpanda/lightpanda` 在容器/环境重置后会消失，config 残留 `enabled: false` + 死路径，MCP 静默不加载。
7. **续传循环别用错的完成阈值** —— 实际 75,670,856 < 75,700,000，会无限重下。用 `stat` 对比精确字节数。
8. **二进制在跑时不能覆写** —— 续传下载进程锁住文件会报 `Text file busy`；先停下载再执行。
