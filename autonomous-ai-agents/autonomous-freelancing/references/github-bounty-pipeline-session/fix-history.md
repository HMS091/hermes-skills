# do_bounty.py 修复历史

## 2026-06-03: 三连 bug 修复

**背景**: xevrion-v2/agent-playground 的 $50 Bounty 自动执行卡在 fork 步骤。

### Bug 1: `data={}` 被当作 falsy → POST 变 GET

**症状**: 打印 `尝试用已有 fork: HMS091/agent-playground` 然后 404。

**根因**: Python 中空字典 `{}` 是 falsy。`gh_request()` 中用 `if data:` 判断是否 POST：
```python
body = json.dumps(data).encode() if data else None  # data={} → body=None
req = urllib.request.Request(url, data=body)
if data: req.method = "POST"  # data={} → False → 没设method
```
所以 `data={}` 传进去，请求变成 **GET** `/repos/{owner}/{repo}/forks`（返回 fork 列表第一页）。自己的 fork 不在那页里，代码就 fallback 去查硬编码的 fork 名 → 404。

**修复**: `if data` → `if data is not None`（第25、28行）

### Bug 2: `clean_env` 使用在定义之前

**症状**: `NameError: name 'clean_env' is not defined`（但实际运行被其他异常掩盖）

**根因**: 
```python
# 第259行使用
env=clean_env
# 第272行才定义
clean_env = {...}
```

**修复**: 将 clean_env 定义移到 fork 之后、clone 之前。

### Bug 3: git commit 静默失败

**症状**: 分支推上去了，但没有新提交。PR 创建失败："No commits between xevrion-v2:main and HMS091:fix/..."

**根因**: 容器没配 git user.name / user.email，git commit 返回非零但无人检查：
```python
subprocess.run(["git", "add"] + changed_files, capture_output=True, timeout=10)
subprocess.run(["git", "commit", "-m", msg], capture_output=True, timeout=10)
# 返回码被忽略！
```

**修复**: 
1. checkout 前设 git config
2. 所有 git 操作检查 returncode，失败立即 exit(1)

### 新增功能: gh_request_retry()

GitHub fork API 是异步的。POST 创建 fork 后立即 GET 可能 404。
新增 `gh_request_retry(url, retries=5, delay=3)` — 只重试 404，其他异常直接抛出。

### 新增功能: fork 等待逻辑

```python
# 旧: 试图解析 fork 列表 → 混乱
# 新: 
gh_request(token, f"/repos/{owner}/{repo}/forks", data={})  # 真 POST
time.sleep(3)
gh_request_retry(token, f"/repos/{my_login}/{repo}")       # 等待就绪
```

## ✅ 修复验证 (2026-06-03)

**全流程首次跑通**: xevrion-v2/agent-playground #15 "Implement infinite sequence iterator" ($50)

执行日志:
```
🎯 目标: xevrion-v2/agent-playground #15
📖 读取 Issue...  Title: Implement infinite sequence iterator
🍴 Fork 仓库...   Fork: HMS091/agent-playground  ✅
📦 Clone Fork...                                   ✅
✏️  AI 分析 Issue — 生成 7 个文件                   ✅
📤 Commit & Push...                                ✅
🔄 创建 PR... PR #100 已提交!                      ✅
```

PR: https://github.com/xevrion-v2/agent-playground/pull/100
状态: open, 7 files changed, 1 commit
验证人: 用户主动要求"要跑通，要你自主能赚钱"后执行

**关键验证点**:
- `data={}` 修复后 POST 正确创建 fork ✅
- gh_request_retry 成功处理异步 fork 延迟 ✅
- git config 后 commit 正常 ✅
- returncode 检查无异常触发 ✅
- do_bounty.py 写 .bounty_history.json 防重复 ✅

**复现步骤**:
```bash
cd /opt/data/scripts
# 清历史（如需重试）
python3 -c "import json; h=json.load(open('.bounty_history.json')); h.pop('ISSUE_URL',None); json.dump(h,open('.bounty_history.json','w'),indent=2)"
# 运行
/opt/hermes/.venv/bin/python do_bounty.py "https://github.com/OWNER/REPO/issues/NUM"
```

## 排查方法

```bash
# 检查远程分支是否包含新提交
git log origin/fix/bounty-XX-desc --oneline
git diff main..origin/fix/bounty-XX-desc --stat

# 验证 fork 存在
curl -H "Authorization: Bearer $GH_BOT_TOKEN" \
  https://api.github.com/repos/HMS091/agent-playground
```

## 2026-06-03: 新陷阱 — Bot Issue 被自动执行

**背景**: relayhop/ClaudeEarnSelf-runtime/issues/102 通过所有过滤条件（金额 $50、AI-friendly、评论 0、刚创建、仓库活跃），被自动 fork 并提交 PR #103。

**真相**: Issue 作者是 `github-actions[bot]`，label 为 `radar` + `demand`。这是一个自动生成的内部需求信号，不是真实 Bounty。Issue body 为空，AI 只改了 README。

**教训**: Bot 创建的 Issue 必须过滤。body 过短的 Issue 也必须过滤。需在 smart_bounty_search.py 和 do_bounty.py 中增加 `user.type != "Bot"` 和 `len(body) > 50` 检查。同时加入生态黑名单防止自引用。

## 2026-06-03 (第四波): smart_bounty_search 差距确认

**背景**: 修复 do_bounty.py 的 fork/commit bug 后，全流程跑通（PR #100）。用户要求批量执行其余 10 个 $50 目标。审查后发现全部已有 PR，被其他 bot 抢了。

### 关键发现: 搜索脚本的最大差距

`smart_bounty_search.py` **报告目标时只检查评论数**，不检查该 Issue 是否已有 open PR。而 xevrion-v2 的所有竞品 PR 在我们搜索后的 2-3 分钟内就已经存在。

### 已更新但不影响当前搜索

- `references/bot-farm-detection.md` — 补充了 xevrion-v2 的完整实战数据表、[agent] PR 前缀检测函数、is_agent_bot_farm() 函数
- SKILL.md — 增加「关键实施缺口」警告章节，说明 PR 竞争检查、Bot 农场检测、代币面值验证三块代码尚未实现
- Cron 频率: Bounty 搜索从 2h → 30m → **5m**，PR 检查从 360m → 30m

### 搜索频率变更历史

| 时间 | 频率 | 原因 |
|------|------|------|
| 初始 | 2h | 默认设置 |
| 用户要求 | 30m | "竞争激烈，要快" |
| 最终 | **5m** | "每5分钟一次，单子出来第一时间抢" |

**背景**: 管线跑通后，用户问"怎么收钱？" — 发现 xevrion-v2 是 bot 农场，不付真钱。需要瞄准真实支付平台。

### 真钱平台发现

1. **MergeOS** (`mergeos-bounties/mergeos`) — 付 **USDC (Stellar)** 或 MRG 代币
2. **MergeWork** (`ramimbo/mergework`) — 付 MRWK 代币 (Stellar)
3. **Stellar Bounty Board** (`ritik4ever/stellar-bounty-board` 等) — 付 XLM

全部用 **Stellar 网络**，一个钱包地址收所有。

### 用户需求变更

- 用户确认要设置 Stellar 钱包地址来收款
- 搜索频率从 2h → 30m → **5m**（"每5分钟一次，单子出来第一时间抢"）
- PR 检查也从 360m 改为 30m

### SKILL.md 更新

- 新增「Payment Pipeline」章节，说明真钱平台和 Stellar 钱包设置
- 更新架构图中 cron 频率为 every 5m
- 新增 Bot 农场识别特征清单
- 新增搜索策略权重表

**背景**: xevrion-v2/agent-playground 的 $50 Bounty 全部在几分钟内被其他 bot 抢占。搜索脚本报告 comments=0-1，但执行时已有 PR。

**新发现的缺陷**:
1. **PR 竞争没检查**: 所有 10 个候选 Issue 都已有 open PR，但 smart_bounty_search.py 只检查评论数，没检查 PR。
2. **Bot 农场识别**: 全是 [agent] 前缀 PR + KHHH2312/rebel117/vumgg 等 bot 名。整仓是 bot 对战平台。
3. **用户再次强调中文**: "怎么又变英文了，以后给我展现的全部是中文"

**修复 (skill v1.7.0)**:
- 新增 Auto-Execution Criteria #4: PR 竞争检查
- 新增 Pitfall #17: 先查 PR 再动手
- 新增 Pitfall #18: Bot 农场检测
- 新增 `references/bot-farm-detection.md` 提供代码实现
- 修复 criteria 编号重复 (两个 #5)
