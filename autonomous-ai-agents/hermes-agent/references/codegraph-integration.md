# CodeGraph + Hermes Agent 集成指南

## 概述

[CodeGraph](https://github.com/colbymchenry/codegraph)（colbymchenry/codegraph）是一个 57K+ stars 的开源工具，为 AI 编程助手预建代码知识图谱。它自动索引项目中的符号、调用关系和依赖到 SQLite 数据库，使 AI 助手**一次调用就能获得精确的代码上下文**，无需逐文件 grep/read。

Hermes Agent 原生支持 CodeGraph（MCP 协议），`codegraph install --target=hermes` 会自动配置。

## 核心优势

| 指标 | 效果 |
|---|---|
| 工具调用次数 | 减少 40-81% |
| 响应速度 | 快 11-33% |
| 文件读取 | 趋近于 0（一次定位） |
| Token 消耗 | 减少 23-64% |

## 安装（Docker 环境 / 受限网络）

### 问题：install.sh 和 npm 直连失败

在容器内运行 `curl -fsSL ... install.sh | sh` 可能因 SSL/TLS 错误失败，npm 默认也可能因代理/网络超时。

### 解决方案：先清除代理，再用 npm

```bash
# 1. 检查是否有全局代理阻塞
env | grep -i proxy

# 2. 清除代理环境变量
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# 3. 用 npm 全局安装（自带 Node.js 运行时，无需本地装 Node）
npm i -g @colbymchenry/codegraph

# 4. 验证
codegraph version
# 应输出类似 "1.2.0"
```

> **注意：** CodeGraph 打包了自己的 Node.js 运行时，所以即使系统没有 Node 也能工作。`npm install` 方式需要系统有 node，但如果 install.sh 因网络失败，npm 是可靠备选。

## 配置到 Hermes Agent

```bash
codegraph install --target=hermes --yes
```

这会自动：
- 更新 `/opt/data/config.yaml`（或其他 Hermes 配置路径），添加 `mcp_servers.codegraph` 配置项
- 在 `platform_toolsets` 中添加 `mcp-codegraph`
- 设置 auto-allow 权限

### 写入的配置示例

```yaml
mcp_servers:
  codegraph:
    command: codegraph
    args:
      - serve
      - --mcp
    timeout: 120
    connect_timeout: 60
    enabled: true

platform_toolsets:
  cli:
    - hermes-cli
    - mcp-codegraph
```

### 无需重启当前会话

**CodeGraph 的 MCP 服务器在 Hermes Agent 启动时自动加载。** 如果安装时已经在会话中，新会话（`/reset` 或重启 hermes）才会加载。但有趣的是 — 当前会话的工具列表里 **已经出现** `mcp_codegraph_codegraph_explore`，说明 Hermes 在配置写入后动态发现了 MCP 工具。

## 初始化项目索引

```bash
cd your-project
codegraph init
```

这会：
1. 扫描所有源文件（支持 20+ 语言）
2. 用 tree-sitter 解析 AST，提取符号和关系
3. 写入 `.codegraph/codegraph.db`（SQLite）
4. 自动启动文件监听（inotify/FSEvents），后续修改自动增量同步

### 索引示例（Hermes 项目自身）

```
Files:     1,468
Nodes:     37,023
Edges:     45,468
DB Size:   101.96 MB

Nodes by Kind:
  function    12,661
  import       7,857
  method       6,345
  variable     5,013
  file         1,354
  class          938
  ...

Files by Language:
  python         852
  typescript     377
  yaml           114
  tsx            104
  javascript      18
```

## 验证

```bash
# 查看索引状态
codegraph status

# 搜索符号
codegraph query "config" --limit 5

# 探索式查询（核心功能）
codegraph explore "agent loop"

# CLI 方式（等价于 MCP 工具的 codegraph_explore）
codegraph explore <query>
```

## 升级

```bash
codegraph upgrade
# 或
codegraph upgrade --check   # 只检查不升级
```

## 卸载

```bash
codegraph uninstall        # 从所有 agent 移除配置
codegraph uninit           # 删除项目索引文件
```

## Pitfalls

1. **代理阻塞 npm/github** — 在 Docker 容器内，容器级别的 `http_proxy` 环境变量可能指向外部不可达的代理（如 192.168.1.88的Clash端口）。必须 `unset http_proxy https_proxy` 后才可直连。
2. **install.sh 可能因 SSL 错误失败** — `OpenSSL SSL_read: unexpected eof`。npm 方式更可靠。
3. **首次索引大型项目较慢** — 1,500 文件的项目需要约 2 分钟完整解析。索引后自动监听，后续增量更新很快。
4. **索引状态需手动 sync** — 如果看到 "Pending Changes: Added: 1 files"，运行 `codegraph sync`。
5. **不同版本重建告警** — "Index was built by an earlier version; re-index to pick up this engine's improvements" — 运行 `codegraph index --force` 重建。

## 参考资料

- 项目主页：https://github.com/colbymchenry/codegraph
- 文档：https://colbymchenry.github.io/codegraph/
- 作者 X：https://x.com/getcodegraph
