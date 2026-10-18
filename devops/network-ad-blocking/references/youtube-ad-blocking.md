# YouTube 广告：为什么拦不住，什么才有用

## 机制（决定一切）

- 广告与视频同域名、同 CDN（`*.googlevideo.com`），DNS 只能整域放行或整域阻断 → 阻断即断视频。
- 2023–2025 年 YouTube 用客户端注入的广告元数据（`youtube.com/api/stats/ads`、player 配置对象），浏览器扩展能在播放器读到之前把广告槽从数据里删掉 —— 这是 uBlock Origin 的 scriplet 路线。
- 2026 年起灰度 **SSAI（Server-Side Ad Insertion）**：广告在边缘节点被拼进 HLS/DASH 清单与媒体分片，客户端拿到的是同一路字节，**没有任何 API 响应可以截**。测试自 2026 年初开始，截至 2026-09 仍是有限灰度，业界估计 6–12 个月内推开。铺开之后 uBO / Brave / ReVanced 会同时失效，唯一还能用的是服务端层面的 Premium。
- 推论：任何"装个盒子/改个 DNS 全家没广告"的说法，对 YouTube 都是错的。用户被这句话骗过一次，你的整份报告都会被怀疑。

## 现状矩阵（写报告时按设备查）

| 设备 | 免费可行方案 | 失效方式 |
|---|---|---|
| 桌面 Firefox | uBlock Origin（完整版，MV2 仍被 Firefox 支持） | YouTube 改播放器结构后需等几小时到几天的过滤器更新；SSAI 铺开后失效 |
| 桌面 Brave | Shields → Aggressive（Rust 引擎，内置不依赖扩展 API） | 同上，恢复通常更快 |
| 桌面 Chrome/Edge | uBO Lite / AdGuard MV3（DNR，3 万条规则上限） | 修复必须等商店审核，YouTube 打补丁期会连续漏广告 |
| 安卓 App 内 | ReVanced（官方 Manager + 自己打补丁） | YouTube 改 API 后要重打；GmsCore 登录偶发失效 |
| 安卓浏览器 | Firefox for Android + uBO / Brave | 无后台播放、不能投屏（部分版本支持） |
| 安卓电视/盒子 | SmartTube | 侧载，跟随 YouTube 变更较慢 |
| iPhone/iPad | Safari/Brave + 内容拦截器（AdGuard、1Blocker） | 只覆盖浏览器；官方 App 内无法拦截 |
| 全设备兜底 | Premium Lite $7.99（不含音乐视频）/ Premium $13.99 | 唯一服务端生效的方案 |

## 排查顺序（"装了还是在放广告"）

1. 过滤列表 `purge caches → update now`，硬刷新；这一步解决一大半。
2. 只留一个拦截器——两个同时开互相打架，还会触发检测。
3. 换浏览器验证：Firefox + uBO 仍漏 → 大概率是 SSAI 灰度到的账号/视频。
4. 退出账号看是否仍漏（账号级灰度会影响结果）。
5. 确认没在用 Chrome 上的"完整 uBO"——它已经被禁用，图标在但没功能。

## 常见误判

- "黑屏 5 秒"或"加载转圈"不是失败，是 YouTube 的反拦截探测；更新过滤器即可。
- 广告只在某几个视频里出现 → 这些视频走了 SSAI，与本地配置无关。
- SponsorBlock 跳的是创作者口播赞助，不是 YouTube 插播广告，两者不要混为一谈。
