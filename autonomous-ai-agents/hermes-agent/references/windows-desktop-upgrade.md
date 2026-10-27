# Windows 桌面壳升级（Hermes Desktop）

Windows 上 Hermes 有**三个独立的版本面**，混在一起就会误判：

| 面 | 看什么 | 典型现象 |
|---|---|---|
| 模型 | `config.yaml` 的 `model.default` | 配置改了但当前会话没变（会话开局锁模型） |
| 后端 / CLI | `hermes --version` | 打印 `vgit.<sha>.dirty (…）· stable · local` ≠ 报错：tag 解析失败时就会这样显示 |
| 桌面壳（Electron） | `apps/desktop/release/win-unpacked/Hermes.exe` + `resources/install-stamp.json` 的 `commit` / `builtAt` | 用户说“版本号还是旧的那个”，指的是这一层 |

`hermes --version` 报 `Could not resolve the stable source release: git ls-remote … timed out` 只是版本号解析拿不到 tag，不影响运行；网络恢复后再看一次即可。

## `hermes update` 在 Windows 上做了什么

顺序：git 拉取 → Python 依赖 → Node 依赖 → 建 TUI → 建 web UI → **建桌面 App**。

桌面这一步失败时的输出：

```
Desktop app build owed: desktop dependencies failed
⚠ Update follow-up 'build' did not finish: desktop dependencies: …
```

后续行为：会用**不含 desktop 的 workspaces 重试 Node 依赖**（TUI/web 能过），桌面壳被跳过 —— 于是后端是最新的、壳还是旧的。

**用户能直接感到的症状**：需要审批的命令全部被拒，返回

> the attached client cannot answer approval requests (update the Hermes app)

即壳太旧、连审批弹窗都送不到界面上。看到这句就不要再重试同类命令，直接修壳。

## 重建桌面壳的前提

必须**先完全退出 Hermes.exe**（多进程；文件锁定会导致覆盖失败）。用户关掉之后再跑更新/重建，否则只会再失败一次。告诉用户“关了 App 后告诉我”，不要自己在运行时硬推。

## 官方 Windows 安装包（语义容易误解）

- 下载页：`https://hermes-agent.nousresearch.com/desktop` → 按钮指向
  `https://hermes-assets.nousresearch.com/Hermes-Setup.exe?build=…`
- 验签（必须做）：`Get-AuthenticodeSignature` → `Signer: CN=Nous Research Inc., O=Nous Research Inc., L=Austin, S=Texas, C=US`，签发者 `Microsoft ID Verified CS EOC CA 03`。
- 体积约 7.9 MB，是 **WebView2 引导器**（`msedgewebview2.exe` 子进程 + `%TEMP%\hermes-git-bootstrap-<pid>\` 里下载 portable-git），不是成品 Electron 包。
- 它会在 `%LOCALAPPDATA%\hermes\installs\<install-id>\environments\<env-id>\workspace\` **新建一套受管安装**（Python 侧，如 `v0.21.5+…`），**不会产出 `Hermes.exe`**。所以：装完之后 `hermes --version` 会指向这个新 workspace，但桌面壳没变 —— 别把“版本号变了”当成壳修好了。
- GitHub Releases **没有 Windows 资产**（`api.github.com/.../releases/latest` 的 `assets` 为空）；文档提到的 `.appinstaller` / `.msixbundle` 在 assets 主机上全 404。

## 诊断顺序

```bash
hermes --version                                   # 后端层
cat "$LOCALAPPDATA/hermes/hermes-agent/apps/desktop/release/win-unpacked/resources/install-stamp.json"
ls -lt "$LOCALAPPDATA/hermes/update_v41.log"       # 上次 update 卡在哪一步
Get-Process | Where-Object {$_.ProcessName -match 'Hermes'} | Select-Object Id,Path
```

## 坑

- 更新日志写 `EXIT=` 之前都算没结束；Node 依赖在弱网下会反复 `SSL: UNEXPECTED_EOF_WHILE_READING` 重试，别当成死循环。
- `hermes update` 会先把工作区 `git stash`（自定义补丁被收走，日志里会给 `git stash apply <sha>`）；自己改过的核心文件要记住这条，或者干脆升级到已修版本。
- 更新会提示 “gateway 未重启，可能仍在跑旧模块”。本机没有常驻 gateway 时（`hermes cron status` 会直说 Gateway is not running），这条无实际影响，但**本机的 cron 任务也因此根本不会触发** —— 定时任务要么装 gateway，要么改用 Windows 计划任务。
- 升级完 `state.db` 里可能出现新 session 行（旧会话被 fork/重开）：用户问“为什么模型名变了/会话断了”，先查 `sessions` 表按 `last_activity_at` 排序，而不是猜。
