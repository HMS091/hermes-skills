# Claude Code 权限模式与规则匹配（速查）

来源：`code.claude.com/docs/en/permissions`、`/permission-modes`。命令行合法值可由 `claude --help | grep -A4 "permission-mode <mode>"` 现场核对（v2.1.304 实测为 `acceptEdits, auto, bypassPermissions, manual, dontAsk, plan`）。

## 1. 模式对照（官方措辞）

| 模式 | 免问放行 | 定位 |
|---|---|---|
| `default`（CLI 里显示 Manual，`manual` 是别名） | 只放行读取 | 每个动作都要自己盯 |
| `acceptEdits` | 读取、文件编辑、常见文件系统命令（`mkdir`/`touch`/`mv`/`cp` 等，限工作目录或 `additionalDirectories`） | 边看边改代码 |
| `plan` | 读取 + 只读命令，不改源文件 | 先摸清代码再动手 |
| `auto` | 几乎一切，动作执行前后台分类器复核 | 长任务、减少弹窗 |
| `dontAsk` | 工作目录内读取 + 预批准工具；**会弹窗的一律拒绝** | 锁死的 CI / 脚本 |
| `bypassPermissions` | 一切（含受保护路径） | 只在容器/VM 里用 |

- `dontAsk` 常被读反。它最严，不是最宽。
- 受保护路径（`.git`、`.claude`）的写入在 `acceptEdits` 下**不会**自动通过 —— 所以 acceptEdits 模式里 Claude 改不到自己的权限文件，可以据此放宽心。
- `defaultMode` 只决定**新会话**的起始模式；运行中的会话不变。
- 想在策略上封死：`permissions.disableBypassPermissionsMode: "disable"` 或 `disableAutoMode: "disable"`（放 managed settings 才不可覆盖）。

## 2. 规则优先级与匹配

**`deny` > `ask` > `allow`**。顺序先于特异性：一条宽的 deny（`Bash(aws *)`）会挡住同时命中窄 allow（`Bash(aws s3 ls)`）的调用；allow 无法从 deny 里开例外。deny 在所有模式生效，含 `bypassPermissions`。

工具名写法：
- 裸名 `Read` / `Bash` / `WebFetch` = 匹配该工具**全部**调用；`Bash(*)` 等价于 `Bash`。
- 带括号 = 只匹配该 specifier。
- deny/ask 支持参数匹配 `Tool(param:value)`，但**不能**匹配主内容字段（Bash 的 `command`、Read/Edit/Write 的 `file_path`）—— `Bash(command:rm *)` 会被忽略并给启动警告，因为复合命令可绕过。

Bash 前缀匹配（`*` 代表任意文本，含空格）：

| 规则 | 命中 | 不命中 |
|---|---|---|
| `Bash(npm run build)` | `npm run build` | `npm run build --watch` |
| `Bash(npm run *)` | `npm run build`、`npm run test --watch`、`npm run` | `npm install` |
| `Bash(ls *)` | `ls -la`、`ls` | `lsof` |
| `Bash(ls*)` | `ls -la` | ——（还命中 `lsof`，危险） |
| `Bash(git log * main)` | `git log -5 main` | `git log main` |

- 尾部 ` *` 前的空格是规则的一部分，且「尾部单个 `*` 且前有空格」时也匹配裸命令。
- `:*` 是尾部通配的等价写法（`Bash(ls:*)`），只在结尾有效。
- 只读类工具（Read/Grep）在工作目录内本来就不需要批准 —— 往 allow 里加 `Read`/`Read(*)` 基本没有收益。
- Read 路径用 gitignore 风格 glob，递归示范写法是 `Read(./project/**)`；单星 `Read(*)` 只顶一层。

复合命令：Claude Code 认 `&&`、`||`、`;`、`|`、`|&`、`&`、换行。allow 规则必须**每个子命令各自命中**才放行；deny/ask 只要**任一**子命令命中就生效，包括 subshell、`$(...)`、`for` 循环体。所以 `cd /tmp && rm -rf x` 会被 deny 挡住，但 `bash -c 'rm -rf x'` 这种靠包装器的不一定。

## 3. deny 的绕过写法（配置放宽时必须主动说）

| 意图 | `Bash(rm -rf *)` 拦得住吗 |
|---|---|
| `rm -rf build` | 拦住 |
| `rm -fr build` | **不拦** |
| `rm -r -f build` / `rm --recursive --force build` | **不拦** |
| `sudo rm -rf /` | **不拦**（前缀是 sudo） |
| `cd tmp && rm -rf x` | 拦住（子命令命中） |
| `node -e "fs.rmSync('/x',{recursive:true})"` | **完全不相关**，只要 allow 有 `Bash(node *)` 就免确认执行 |

结论：deny 三条 `rm -rf` / `format` / `diskpart` 的真实作用是**防手滑**，不是防越权。真正的洞在 allow 里的 `Bash(rm *)`、`Bash(node *)`、`Bash(python *)`、`Bash(ssh *)`、`Bash(curl *)`。要堵就删/收窄这些，而不是继续往 deny 加变体。

## 4. 改动校验（两套解析器 + 编码 + 未变字段）

```bash
# 1) 结构：PowerShell
powershell.exe -NoProfile -Command '$j = Get-Content -Raw -Encoding UTF8 "C:\Users\<u>\.claude\settings.json" | ConvertFrom-Json; $j.permissions.defaultMode; $j.permissions.allow.Count; $j.permissions.deny.Count; $j.env.ANTHROPIC_AUTH_TOKEN.Length'

# 2) 结构：node
node -e 'const j=require("C:/Users/<u>/.claude/settings.json"); console.log(j.permissions.defaultMode, j.permissions.allow.length, j.permissions.deny.length)'

# 3) 无 BOM（首字节应是 7b = '{'）
head -c 3 "C:/Users/<u>/.claude/settings.json" | od -An -tx1

# 4) 备份一致性
md5sum settings.json settings.json.bak-<date>
```

`claude doctor` 可非交互运行，会列出「被跳过的无效规则」（如 `mcp__` 带括号、工具名 typo）。它说 `No installation issues found` 不等于逐条规则都合法，但**一条 invalid-settings 警告都没有**就说明写进去的 JSON 结构没被判错。完整的 `/doctor` 只能在会话内跑。

## 5. 与自定义网关的交互

`ANTHROPIC_BASE_URL` 指向第三方兼容端点时，`claude doctor` 会显示 `Managed settings (remote): not fetched` 与 `Organization policy: not fetched` —— 企业策略通道不走，本地 `settings.json` 就是唯一生效来源，`permissions.disableBypassPermissionsMode` 这类策略锁也就没人替你设。
