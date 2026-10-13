---
name: app-reverse-engineering
description: Use when 逆向 APK/二进制/Electron 以复刻功能。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [reverse-engineering, decompile, apk, jadx, apktool, ghidra, electron, clone]
    category: software-development
    related_skills: [web-debugging, codebase-inspection]
---

# App 逆向 / 功能复刻

核心判断：**没有一个工具能通吃**。先定目标形态，再选工具。REA（morluto/rea）是聚合器，在 Debian 主机上被 `doctor` 判为 `unsupported_host` 而拒跑；专用工具反而能跑。

## When to Use

- 用户给一个 APK / exe / dll / so / Electron 应用，问“它这个功能怎么做的 / 能不能抄一个”
- 需要评估竞品 App 的技术栈、后端接口、第三方 SDK
- 需要判断 REA 这类逆向聚合器在**当前主机**能否跑（先看 host 支持列表，别先装）
- 不适用：只需读源码仓库结构时用普通代码检索，不要上反编译链

## 按目标选路线

| 目标 | 工具 | 本机实测 |
|---|---|---|
| Android APK | jadx（看 Java）+ apktool（看资源/manifest） | ✅ Debian 13 通过 |
| Android 动态 | Frida / frida-gadget / CreditTone-hooker（运行时 hook，看真实数据） | 需 root 设备或模拟器 |
| 原生 exe/dll/so/Mach-O | Ghidra + GhidraMCP / ReVa / ida-pro-mcp | Ghidra 可跑（需 JDK 21）；IDA Pro 要付费，不推荐 |
| Electron | asar 解包 + 静态 JS 分析 | ✅ |
| 网页 JS | ben-sb/javascript-deobfuscator；浏览器抓包 + sourcemap 反查 | ✅ |
| Unity 游戏 | Il2CppDumper + Il2CppInspector | 未实测；仓库 2024-08 后停更 |
| iOS | 必须 macOS + 越狱设备 / 解密 IPA | ❌ 无 Mac 做不了 |

## 已装好的 Android 逆向环境（/opt/data/re-tools）

```bash
export JAVA_HOME=/opt/data/re-tools/jdk-21.0.12.1+1
export PATH=$JAVA_HOME/bin:$PATH
JADX=/opt/data/re-tools/jadx/bin/jadx
APKTOOL=/opt/data/re-tools/apktool.jar
```

反编译 Java（大 App 用 `--no-res` 提速，资源另用 apktool）：
```bash
$JADX -d out --no-res target.apk                   # 产出 out/sources/**.java
java -jar $APKTOOL d -f -s -o apk-out target.apk   # 产出 AndroidManifest.xml + smali
```

实测基准（J3455 4核）：F-Droid 客户端 12MB APK → 11,949 个 Java 文件 / 124MB，耗时 **2分37秒**，147 个方法失败（≈1.9%，正常）。

## 交付物格式（用户要的是这个）

拿到 APK 后按顺序产出中文报告：包名/SDK/权限 → 组件清单（Activity/Service/Receiver/Provider）→ 第三方 SDK 与后端域名（grep `https?://`、`Retrofit`、`api.`）→ 关键功能类的真实实现摘录 → 可复刻功能清单。

## 坑（已验证）

- 本机**没有 `unzip`**，原本也无 `java`：用 `python3 -c "import zipfile;zipfile.ZipFile(p).extractall(d)"` 解压；JDK 用 Temurin 21 tarball（`api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jdk/hotspot/normal/eclipse`）。
- jadx 是纯 Java，跨平台无主机白名单；Ghidra/IDA 插件同理，但 IDA Free 不支持 headless 插件路径。
- jadx-ai-mcp（MCP）依赖 JADX-GUI，无桌面环境要用无头实现或直接走 CLI。
- 商业 App 上 R8/加固（360、梆梆）后类名变 a/b/c、方法体空：静态分析只能到 30–50%，其余靠 Frida 动态 + 抓包。反调试会检测 Frida 并退出。
- 4 核 J3455 跑大 App 反编译 10 分钟以上，重活放 Windows 机器。

## 红线

只分析自己拥有或已获授权的 App。不破解付费软件、不绕过授权/DRM、不生成注册机。GPL 代码有传染性，抄之前先看许可证。
