# CodeGraph 安装、接线与验证

本文件是 `codegraph` 技能的细节附录：安装路径、Hermes 接线、网络/容器环境坑、验证清单、上游基准数据。

## 1. 安装

### 首选：npm 全局

```bash
# 受限网络 / 代理环境先清代理变量，再装
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
npm i -g @colbymchenry/codegraph
codegraph --version      # 期望形如 1.6.2
```

### 不推荐：官方一键脚本

```bash
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex
```

没有 checksum、没有可核对内容，等于 `curl | sh`。npm 路径有 provenance 可验，优先它。
（官方脚本的唯一优势是「本机完全没 Node」也能装；装了 Node 的机器没必要。）

### 容器 / 受限网络已知失败

| 现象 | 原因 | 处理 |
|---|---|---|
| `install.sh` 报 `OpenSSL SSL_read: unexpected eof` | 容器级 `http_proxy` 指向不可达代理 | `unset` 四个 proxy 变量后改用 npm |
| `npm i -g` 超时 | 同上（npm 走代理） | `unset` 代理，或 `npm i -g --noproxy '*'` |
| 升级后容器里的 MCP 二进制「消失」 | 重建镜像/重建容器把全局包丢了 | 重装一次即可；不需要时 `enabled: false` 摘掉，别反复折腾 |

## 2. 接线到 Hermes

`codegraph install --target=hermes --print-config hermes` 只打印计划、不写文件（**先看它想写什么**），
然后用 `hermes config set` 自己写，或者直接编辑 `config.yaml` 的 `mcp_servers` 段：

```yaml
mcp_servers:
  codegraph:
    command: C:/Users/<user>/AppData/Roaming/npm/codegraph.cmd   # Windows；Linux 用 codegraph
    args:
      - serve
      - --mcp
    enabled: true
    timeout: 120
    env:
      CODEGRAPH_TELEMETRY: '0'     # 必须带引号，见 SKILL.md 坑 2
```

- **绝不抄 `platform_toolsets`**：自带的 snippet 会往 `platform_toolsets.cli` 里塞 `mcp-codegraph`，
  抄进去等于只对 CLI 平台开放，别的 MCP 服务器会在其他平台「消失」。只认 `mcp_servers.<name>`。
- 交互式 `hermes mcp add` 在非 TTY 下必然 Cancelled —— 别指望 `printf 'Y\n' |`，直接写 config。
- `codegraph install` 若已手工写过同名条目会重复；写完回读 `grep -A9 "codegraph:" config.yaml` 确认只有一段。

## 3. 验证（三步都要过）

```bash
codegraph --version                    # 1. CLI 在 PATH
hermes mcp test codegraph              # 2. ✓ Connected + ✓ Tools discovered: 1
cd <repo> && codegraph status          # 3. 索引统计（Files/Nodes/Edges/DB Size）
```

**工具数与 schema 成本**：只有 1 个工具 `codegraph_explore`（3 个参数：query / maxFiles / projectPath），
工具描述约 580 字符 ⇒ 相对那些一次塞进上百个工具、几十万 token schema 的 MCP 服务器（如 REA），
它的常驻成本可以忽略。

**会话生效**：改完 config 需重启网关 / 开新会话；当前会话里不会凭空出现新工具。
CLI 方式（`codegraph explore`）不需要网关，随时可用。

## 4. 上游基准（作者自测，仅作量级参考）

在 VS Code / Django / Tokio / OkHttp 等 7 个真实项目、同一模型各跑 4 轮取中位数：

| 指标 | 平均改善 |
|---|---|
| 工具调用次数 | 少 40–81% |
| 响应速度 | 快 11–33% |
| 文件读取 | ≈0 次（无 CodeGraph 时 4–9 次） |
| Token 消耗 | 少 23–64% |
| 费用 | 省 0–40%（大项目 + 高频才显著） |

这是**上游厂商数据**，不是独立复现。判断它在本机值不值，看 `codegraph status` 的规模 +
一次 explore 的输出体量是否明显小于「读同等数量文件」的代价。

## 5. 上游信息（核实方式可复用）

```bash
npm view @colbymchenry/codegraph version time.created dist.attestations maintainers repository.url
curl -s https://api.github.com/repos/colbymchenry/codegraph | \
  python -c "import json,sys; d=json.load(sys.stdin); print(d['stargazers_count'], d['forks_count'], d['license']['spdx_id'], d['open_issues_count'])"
```

- 许可 MIT；npm 有 SLSA provenance；`scripts` 为空、无 postinstall、平台二进制走 `optionalDependencies`
  ⇒ 安装期不会执行奇怪代码。
- 文档站：`https://colbymchenry.github.io/codegraph/`；升级用 `codegraph upgrade`。
