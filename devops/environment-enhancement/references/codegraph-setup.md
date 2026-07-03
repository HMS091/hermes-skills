# CodeGraph (colbymchenry/codegraph) 安装与配置

## 项目简介

CodeGraph 是一个预建代码知识图谱工具，为 AI 编程助手（Claude Code / Cursor / Codex / Hermes Agent 等）提供精准代码上下文。一次查询返回精确符号源码 + 调用路径 + 影响范围，替代 AI 助手的 grep/find/Read 循环。

- GitHub: https://github.com/colbymchenry/codegraph
- Stars: 57K+, MIT 许可证
- 语言: TypeScript（自带 Node.js 运行时）
- 版本: v1.2.0+（每日发版）

## 安装

### 方法一：npm 全局安装（推荐）

```bash
# GFW 环境必须取消代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
npm i -g @colbymchenry/codegraph --noproxy '*'
```

### 方法二：独立安装脚本（无需 Node.js）

```bash
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
```

### 配置 Hermes Agent

```bash
codegraph install --target=hermes --yes
```

会自动修改 `/opt/data/config.yaml`，添加：

```yaml
mcpServers:
  codegraph:
    command: codegraph
    args:
      - serve
      - --mcp
    timeout: 120
    connect_timeout: 60
    enabled: true
```

以及 `platform_toolsets` 添加 `mcp-codegraph`。

### 初始化项目索引

```bash
cd your-project
codegraph init
```

一条命令完成：创建 `.codegraph/` 目录 + 建全量索引。之后文件修改会自动通过 OS 原生文件事件（inotify/FSEvents）增量同步。

### 验证

```bash
codegraph status
```

输出示例：
```
Files:     1,468
Nodes:     37,023
Edges:     45,468
DB Size:   101.96 MB
```

## 常用 CLI 命令

| 命令 | 用途 |
|------|------|
| `codegraph explore "query"` | 查询符号源码 + 调用路径 + 影响范围 |
| `codegraph node <symbol>` | 查看某个符号的源码 + 调用者 |
| `codegraph query <search>` | 搜索符号名 |
| `codegraph status` | 查看索引统计 |
| `codegraph sync` | 手动增量同步 |
| `codegraph init [path]` | 新建项目索引 |
| `codegraph upgrade` | 升级到最新版 |

## 效果基准测试

在 VS Code / Django / Tokio / OkHttp 等 7 个真实项目测试（Claude Opus 4.8，各跑 4 轮取中位数）：

| 指标 | 平均改善 |
|------|---------|
| 工具调用次数 | **少 40-81%** |
| 响应速度 | **快 11-33%** |
| 文件读取 | **≈0 次**（无 CodeGraph 时 4-9 次）|
| Token 消耗 | **少 23-64%** |
| 费用 | **省 0-40%**（大项目+高频才显著）|

## Pitfalls

1. **GFW 安装**：SSH 端口被封，SSH 方式 clone/push 不可用。必须用 HTTPS + Personal Access Token。npm install 时要 `unset proxy` + `--noproxy '*'`。
2. **首次索引耗时**：1,400+ 文件的项目约需 2-3 分钟（Parsec CPU 单核性能限制）。之后增量同步 <1 秒。
3. **索引约 100MB**：大项目的 `.codegraph/` 目录占用约 100MB 磁盘空间，计入 `.gitignore` 不要提交到 git。
4. **替换当前会话**：`codegraph install` 写入 config.yaml，但正在运行的 Hermes 会话需要代码中已有 MCP discovery。新启动的会话自动加载。
