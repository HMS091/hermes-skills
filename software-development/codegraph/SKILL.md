---
name: codegraph
description: Use when a codebase question needs symbols/impact fast.
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [codegraph, code-intelligence, mcp, symbol-graph, impact-analysis, refactor]
    related_skills: [mcp-server-integration, native-mcp, ui-pixel-diff-and-ast-grep, rea-mcp-setup]
---

# CodeGraph — 本地代码知识图谱

把整个仓库预索引成 SQLite 符号图谱（函数 / 类 / 路由 / 边），对外只暴露**一个** MCP 工具 `codegraph_explore`：一次调用返回「相关符号的逐行源码 + 调用链 + 改动影响面（blast radius）」，替代「grep → 逐个 Read」的循环。

- 上游：`colbymchenry/codegraph`（MIT，npm `@colbymchenry/codegraph`，自带运行时，无需本地 Node 版本管理）
- 本机形态：CLI + MCP server + 每个仓库一份 `.codegraph/codegraph.db`
- 详细安装 / 接线 / 基准测试见 `references/install-and-wiring.md`

## When to Use

用：

- 「X 是怎么工作的 / X 在哪 / 这个 bug 涉及哪些文件」→ **一次 explore**，不要先 grep。
- **改代码之前**看影响面：谁调它、几个调用方、有没有测试覆盖（动高频 hook / 共享工具函数时必看）。
- 跨文件调用链：React 组件重渲染、JSX children、callback 动态派发这类 **grep 跟不上的边**。
- 找「某个流程从 A 到 B 经过谁」：把首尾两个符号名一起丢进去。

不用：

- 文本 / 配置 / 文档搜索 → `search_files`（快得多）。
- 二进制 / 反编译产物 → `rea-mcp-setup`（REA）。**反编译 bundle 不要建索引**，见下。
- 没索引过的仓库 → 先 `codegraph init .`。

## MCP 用法（Hermes）

工具名 `codegraph_explore`，参数：`query`（必填）、`maxFiles`、`projectPath`。

**坑 1 — 每次调用都要传 `projectPath`。** Hermes 起 MCP server 的 cwd 是用户家目录，那里没有 `.codegraph/`，服务启动就会打印 `No .codegraph/ at or above <home>: no default project, live sync disabled`。不传 `projectPath` 时它不知道自己该查哪个仓库：

```
codegraph_explore(query="<自然语言问题或符号名>", projectPath="C:/<abs>/<repo>")
```

**坑 2 — env 值必须是字符串。** `config.yaml` 里写 `CODEGRAPH_TELEMETRY: 0`（数字）会被 pydantic 拒绝：

```
ValidationError: 1 validation error for StdioServerParameters
env.CODEGRAPH_TELEMETRY  Input should be a valid string
```

后果很隐蔽：服务连续 3 次连不上后被 **park（挂起）**，工具在会话里彻底不出现，但**用户看不到任何报错**——只有 `logs/mcp-stderr.log` / `logs/gateway-stdio.log` 里有记录。写 `'0'`（带引号）即可。改完先 `hermes mcp test codegraph`（应输出 `✓ Connected` + `✓ Tools discovered: 1`），再重启网关生效。

**坑 3 — 别信它 instruction 里的「不要再 grep 验证」。** 它自述「你是预建索引，重复 grep 是浪费」——方向对，但对 Tamagui `styled()`、expo-router 动态路由这类**运行时拼装**的结构会有解析偏差。关键结论仍用 grep / 打开文件复核一次。

## CLI（不开 MCP 时直接用，通常更快）

```bash
cd <repo>
codegraph init .              # 首次建索引（数百文件量级 ≈ 5–20 秒）
codegraph sync                # 增量同步；有 daemon 时会自动 live sync
codegraph status              # 文件/节点/边/DB 大小 + 按语言、按 kind 分布
codegraph explore "<问题>"     # = MCP 的 codegraph_explore
codegraph node <符号>          # 单个符号源码 + caller/callee 轨迹
codegraph callers|callees <符号>
codegraph impact <符号>        # 改它的影响面（改共享函数前必看）
codegraph affected <文件...>   # 哪些测试文件受影响
codegraph query|context|files
codegraph upgrade             # 升级；upgrade 会自动 refresh 已接线 agent 的配置
codegraph uninstall / uninit  # 从 agent 摘除 / 删掉本仓库索引
```

## 实测效果（2026-10，本机）

| 指标 | 实测 |
|---|---|
| 一个 RN/Expo 前端仓库 | 487 文件 / 7,619 节点 / 16,456 边 / 21 MB |
| 一个 TS monorepo 后端 | 69 文件 / 927 节点 / 1,837 边（重建 6.8 秒） |
| 单次 explore 输出 | 18–26 k 字符（≈5–7 k token），含 26–44 个符号 + 调用方清单 |
| 单次 explore 的召回 | 一个高频自定义 hook 的 **96 个调用方**一次列全（跨 43 个文件） |

对比：同样的「这个符号被谁用、改了影响谁」问题，靠 grep + Read 需要十几轮往返，且**容易漏掉动态派发那几条边**。

上游自测基准（VS Code / Django / Tokio 等 7 个项目，各 4 轮取中位）：工具调用次数 −40~81%、响应快 11~33%、文件读取 ≈0、token −23~64%。**这是上游数据，非本机实测**，只能当量级参考。

## 索引维护

- `.codegraph/` 是**本地索引**（20 MB 起，大仓库可到 100 MB 以上）：**写进仓库根 `.gitignore`**，否则 `git status` 永远多一个未跟踪目录。
- 索引会过期：文件变了就 `codegraph sync`（秒级）。发现 `Pending Changes` 或版本升级后的 `built by an earlier version` 提示 → `codegraph index --force` 重建。
- **反编译 / 混淆产物不要当索引对象**：符号是一堆寄存器名（`r10 = r9.SomeSection`）、样式字面量全库 0 命中 ⇒ 建出来全是无语义节点，还要 GB 级空间。真要追调用链就切一小片源码再建。

## 安全 / 依赖

- MIT；npm 发布带 **SLSA provenance 证明**（`dist.attestations` → `slsa.dev/provenance/v1`），包名与仓库对得上。
- 装的姿势：`npm i -g @colbymchenry/codegraph`。**不要用它官网的 `install.sh` / `install.ps1`**（无 checksum，等于 `curl | sh`）。
- **遥测默认开**。关掉两处：`codegraph telemetry off` + `mcp_servers.codegraph.env.CODEGRAPH_TELEMETRY: '0'`。
- 100% 本地：SQLite 在项目里，查询不出网；除遥测外无外部依赖。
- `codegraph install --target=hermes --print-config hermes` 打出来的片段里会带 `platform_toolsets`，那条**别抄**（抄进去会让别的 MCP 服务器在 CLI 平台消失），只认 `mcp_servers.<name>` 段。
