# giffgaff 长期漫游封号事件调研（2026-07-27 ~ 08-04）

调研日期：2026-08-04。用户问"有没有大面积长期漫游封号、没收到邮件要不要管"时使用本文档；引用时注意时效。

## 事件概述
- 2026-07-27 起国内社区（NodeSeek、B站、X）集中出现反馈：giffgaff 对"长期/永久在英国境外使用"的号码批量发终止服务邮件（Account Closure Notice），主要针对长期在中国漫游的用户。7-29~30 大量自救文章/视频，至 8 月初仍在发酵。
- 性质是运营策略调整，不是传统"长期不用回收"——连部分正常使用者也被停。
- 官方没有"封禁所有中国用户"公告，口径是逐案审查（官方帮助页）。2026 年 1 月也有过一次类似恐慌，后很多人没事 → 不是每个案例都停服。

## 终止邮件原文（bayase.com 用户晒出）
> following a review of your account usage, we have made the decision to disconnect your service... services are intended primarily for use within the UK, with roaming provided for short-term travel only. As your usage pattern suggests extended or permanent use outside the UK... your service will be disconnected shortly... Please note this is our final position on this matter.

"final position"=客服层面基本没商量余地，恢复成功率低。

## 检测机制（关键认知）
- 检测的是 **SIM 卡蜂窝网络注册位置**（开机向当地基站注册留下的漫游记录），**不是 IP** → 挂梯子/改英国 IP 没用
- WiFi Calling 不能作为长期规避手段
- 官方 EU 漫游规则：英国居民+英国常用，EU/指定目的地漫游上限 **63 天/4个月**；超期会先发 SMS 通知关闭 RLAH 漫游（然后按 credit 计费）。63 天规则在"欧盟及指定目的地"条款下，不能直接当全球通用解封公式

## 退款/维权现实
- 退款：自己充值的 Purchased Credit 有机会退；Payback Points/活动赠送 Credit 一般不可退
- 有 X 用户实测（2026-08-02）：PAC 转网后账户被关、余额被拒退（引用条款 3.5(k)/5.3）→ 退款不保证
- 官方窗口：**停用后 30 天内**可申请 PAC 与余额退款；超 30 天号码回号码池、余额作废
- 顺序铁律：**先申请 PAC → 完成转网 → 再处理退款/注销**；先注销则无法再转号；余额不随号码转走
- 申诉链：官方代理(24h) → 正式投诉(5 工作日) → deadlock letter → 6 周后 Communications Ombudsman

## 没收到邮件要不要管？（核心答案）
**要管，不用恐慌。没收到邮件 ≠ 安全。**
- giffgaff 风控是"先处理、后通知"；邮件可能延迟/进垃圾箱/邮箱填错
- 官方帮助页：账户审查或服务限制"多数情况下未必另发通知"
- 有案例：申请退款后直接被封且全程无邮件（退款申请本身可能触发风控）

趁能收短信按序做：
1. 登录后台查余额是否变 "Not available"（中招信号）+ 翻垃圾邮件箱
2. **申请 PAC**：发短信 `PAC` 到 `65075`（或后台 Profile & settings），9 位码 30 天有效，先拿不亏
3. 迁移重要账号验证（Google/Apple/Telegram/WhatsApp/银行/交易所等）→ 新号码/认证器/Passkey，存恢复码
4. 降险（只争取时间）：非必要关 SIM、关数据漫游、日常用 WiFi
5. 别做：主动申请退款（可能触发审查）、注销账户、编造英国经历申诉、找号贩子

## 替代方案
- 🇬🇧 英国系（支持 PAC 转网）：CTExcel（中国电信欧洲）、CMLink（中国移动英国）、VOXI、Lyca UK
- 🇺🇸 美国号：Tello（$5/月）、Saily（$0.99/月，接码保号）；国行无 eSIM 可用 ESIMfan 实体承载卡
- 🇭🇰 香港号：CTHK 蓝卡（半年充 50 HKD，内地收短信免费）、HahaSIM
- MollySIM 等电商对其售出的卡提供免费换卡/申诉协助/迁移协助（官方公告 2026-07-30）

## 来源（抓取日期 2026-08-04）
- 海外笔记 haiwaibiji.com《giffgaff卡封号：停服后申诉、PAC转网与余额退款指南》2026-07-30（最全面，已核对官方帮助页）
- 湾区阿瑟 bayase.com/post/giffgaff-ban-refund-port-alternatives/ 2026-07-29（邮件原文、检测机制、替代方案横评）
- duoplus.cn/blog/giffgaff-account-closure-guide/ 2026-07-29（封号通知详情、余额类型退款对照表）
- AI技能智慧站 aishare.jizhiku.net/archives/32989 2026-07-29（"没收到邮件"的原因分析）
- MollySIM 官方公告 2026-07-30（零售商视角确认事件+售后政策）
- giffgaff 官方帮助页（EU 漫游 63 天规则、停用/PAC/退款 30 天窗口）
- X: @Wine92023 2026-08-02（PAC 转网后被封+拒退）；@cuijason1 应急指南 2026-07-28；@9wine 相关帖
- Bing 摘要佐证：NodeSeek 个人帖（无邮件案例）、知乎/B站视频（2026-07-29 起多条）
