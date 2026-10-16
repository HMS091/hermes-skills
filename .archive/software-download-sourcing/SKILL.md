---
name: software-download-sourcing
description: Use when 用户要找"纯净/绿色版"软件下载或核验渠道。先定软件形态→找官方源→识别下载墙→核验纯净度，中文报告。
---

# Software Download Sourcing (找"纯净/绿色版"软件下载)

## When to use
用户说"帮我找 X 纯净版/绿色版/免安装版下载"，或问某个下载站靠不靠谱。典型中文互联网场景，此用户会反复出现（务实、价格敏感、要结论先行+负面风险）。

## Workflow
1. **先弄清软件是什么** — 平台(PC/Mac/iOS/安卓)、官方免费还是付费、有没有"破解"概念。
   - "绿色版/纯净版"是 PC 术语，但常被误用：免费软件无破解一说，"纯净"= 防二改夹私货的原始包。
   - 同名不同平台陷阱：macOS 付费 AppsDump(不蓝/Bulan) vs iOS 巨魔免费 AppsDump(bswbw) 是两个完全不同的东西，先按版本号+功能描述对齐再动手。
2. **优先官方/一手源**：GitHub release、作者 TG 频道/公众号、作者博客。镜像站逐个评估：门槛类型 + 免责声明措辞（站方自述"文件来自网络收集、可能有广告弹窗"≈ 可能夹私货，纯净度降级）。
3. **识别中文站下载墙**（curl 抓页后 grep `<a href`/data-*/js 变量；链接不在 HTML 里 = 被挡，别浪费时间深挖源码）：
   - 评论后刷新可见：WordPress 评论隐藏插件，链接由服务端按需返回，页面源码里没有。
   - 登录后下载：会员插件（wpcom-member 等），如 ipa.store 每日限 N 个下载。
   - JS 下载面板：按钮 class 常含 `j-refresh-hidden-download` 之类，真实 URL 仅走 AJAX。
   - 网盘跳转+提取码：蓝奏/夸克/百度盘。
   输出应报告"门槛类型 + 通过方法"（评一条/注册/进 TG 频道），不要把被挡的链接描述成可直下。
4. **纯净度核验**：多渠道文件大小对比；IPA 装前看包内 Info.plist 版本号、装后观察有无广告弹窗/额外描述文件；拿到文件算哈希与镜像对比。
5. **给开源替代**：用户只要核心功能时，开源官方替代常更干净（例：砸壳只要 TrollDecrypt[GitHub/donato-fiore]，AppsDump 独有虚拟定位/账号切换才需镜像）。
6. **绝不伪造下载结果**：拿不到文件就明说被哪道墙挡住，给已核验的页面 URL+通过方法；或让用户把拿到手的直链发回来，代理做哈希/包内容核验。

## 抓取兜底（实测有效）
web_extract DNS 失败 / browser 云超时时：`curl -sL --max-time 25 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36" URL -o /tmp/x.html` 再本地 python 解析（re 提取 title/anchors/文本行）。中文站普遍不反爬 curl。

## 输出风格（此用户偏好）
全中文、结论先行——第一句说清"这是什么软件、有无破解概念、能不能直接下"；表格对比渠道（门槛/纯净度）；真实数据+负面风险（Apple ID 风险、法律边界、检测风险）；不反复确认、主动给下一步。

## Support files
- references/trollstore-ipa-ecosystem.md — iOS 巨魔(TrollStore)IPA 生态速查：支持系统、安装、常用工具、镜像站清单与风险（AppsDump 案例细节）
