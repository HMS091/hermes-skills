# iOS 巨魔(TrollStore) IPA 生态速查

来源：AppsDump 4.8 调研会话（2026-09）实测抓取。

## 巨魔商店(TrollStore)要点
- 永久签名装任意 IPA，无需证书/越狱/账号；利用系统漏洞，仅限特定系统。
- 支持范围约：iOS 14.0–16.6.1 及 17.0(成功率低)；**iOS 16.7–16.7.5 与 17.0.1+ 不支持**。
- 安装：Safari 下 .tipa/.ipa → 分享 → TrollStore → Install。用 SideStore 等自签工具装会提示 "please install via TrollStore"（属正常，非损坏）。
- 巨魔2 用户装后闪退：设置里开"开发者模式"。

## 常用工具
| 工具 | 作者 | 功能 | 获取 |
|---|---|---|---|
| AppsDump | bswbw | 砸壳提取 IPA(脱壳)+虚拟定位+切换 App Store 账号+联网权限管理+多开打包；免费；IPA 非全权限但够用 | 无官方 GitHub；中文镜像/作者 TG 频道 @iosjumo 更新 |
| TrollDecrypt | donato-fiore | 只做砸壳脱壳，开源 | GitHub 官方 release（最纯净） |
| TrollFools | i_82 | dylib 注入 | GitHub |
| TrollRecorder | Lessica | 通话录音(巨魔版) | GitHub/商店 |

## AppsDump 案例细节
- 版本演进：AppDump2 → AppsDump3(多渠道提取/账号切换/数据目录管理) → AppsDump4(4.x) → 4.8(2026 更新)。
- 特性注意：砸壳导出非全权限 IPA；
- iOS 17.4.1 实测不可用（无巨魔）。

## 中文镜像站清单（2026-09 实测门槛）
| 站 | 内容 | 门槛 | 纯净度 |
|---|---|---|---|
| a.iosxn.cn（小昕官网） | 一手更新页（含 4.8） | 评论后刷新可见链接 | 较高 |
| codeun.com/archives/1797.html | AppsDump4 4.4MB | 下载面板需刷新/登录(JS) | 中，自述可能有广告弹窗 |
| ipa.store | 旧版为主 | 注册+每日限额 | 中 |
| t.me/iosjumo（iOS越狱巨魔玩家） | 作者更新公告+文件 | 进频道 | 作者一手源 |
| idownloadblog 教程内 Google Drive | 2023 老版 .tipa | 无 | 已过时 |

## 风险清单（报告时必带）
1. 砸壳工具权限极大（账号切换/权限管理/虚拟定位）——镜像二次打包夹私货风险高，**勿登主力 Apple ID**；装后查广告弹窗/额外描述文件。
2. 虚拟定位打卡会被检测（真实案例：钉钉打卡扣工资）。
3. 砸自己的 App 自用合法；砸后分发=侵权。
4. 巨魔通道装前先确认设备系统在支持范围内，否则白折腾。

## 下载墙技术特征（可复用识别法）
- WordPress 评论隐藏：`此处内容已隐藏，请评论后刷新页面查看` → 链接服务端给，HTML 无痕迹。
- codeun 类下载面板：class `j-refresh-hidden-download`，真 URL 走 AJAX+（可能需登录态）。
- 页面常有免责声明段（"资源网络搜集/下载风险自负/24h删除"）= 站方自认非一手、可能带广告。
