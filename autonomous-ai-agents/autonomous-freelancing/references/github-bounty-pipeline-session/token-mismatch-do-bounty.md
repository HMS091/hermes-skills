# Token 跨脚本不一致 — do_bounty.py 找不到 GITHUB_TOKEN

## 修复状态

### 2026-06-04 06:58 — 方案 A 已应用 ✅

**操作**: 修改 `/opt/data/scripts/do_bounty.py` 的 `load_env()` 函数，添加从 `/opt/data/.env_bot` 回退读取 `GH_BOT_TOKEN` → `GITHUB_TOKEN` 的逻辑。

**验证**:
```bash
$ python3 -c "
import os
os.environ.pop('GITHUB_TOKEN', None)
from do_bounty import load_env
load_env()
token = os.environ.get('GITHUB_TOKEN', '')
print(f'GITHUB_TOKEN: {\"SET (len=\" + str(len(token)) + \")\" if token else \"MISSING\"}')
"
GITHUB_TOKEN: SET (len=40)  ✅
```

**修复代码** 已在 `load_env()` 末尾添加：

```python
# 回退: 从 .env_bot 读取 GH_BOT_TOKEN → GITHUB_TOKEN
if not os.environ.get("GITHUB_TOKEN"):
    for p in ["/opt/data/.env_bot", os.path.expanduser("~/.env_bot")]:
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if "GH_BOT_TOKEN" in line and "=" in line:
                        token = line.split("=", 1)[1].strip().strip('"').strip("'").replace("export ", "")
                        if token:
                            os.environ["GITHUB_TOKEN"] = token
                        break
```

**影响**: 下次 cron tick 运行时，`do_bounty.py` 能够正确认证 GitHub，不再阻塞于 "❌ 未设置 GITHUB_TOKEN 环境变量"。

## 问题

`do_bounty.py` 的 `load_env()` 读取 `/opt/data/.env` 寻找 `GITHUB_TOKEN` 环境变量。但 GitHub token 实际存储在 `/opt/data/.env_bot` 中，变量名为 `GH_BOT_TOKEN`。

## 影响范围

所有通过 `smart_bounty_search.py` → `subprocess.run(["python3", "do_bounty.py", url])` 调用的自动执行均失败。

`smart_bounty_search.py` 本身工作正常（它的 `load_env()` 读取 `.env_bot` → `GH_BOT_TOKEN`），但子进程 `do_bounty.py` 在启动时立即 `sys.exit(1)` 并输出 "❌ 未设置 GITHUB_TOKEN 环境变量"。

## 文件现状

| 文件 | 内容 | 用于 |
|------|------|------|
| `/opt/data/.env` | `DEEPSEEK_API_KEY=xxx`, `OPENAI_API_KEY=xxx` | do_bounty.py 的 load_env() |
| `/opt/data/.env_bot` | `GH_BOT_TOKEN=ghp_xxx`, `STELLAR_WALLET=G...` | smart_bounty_search.py 的 load_env() |

**注意**: 两个文件对 GitHub token 用了不同变量名 (`GH_BOT_TOKEN` vs `GITHUB_TOKEN`)，且存储在不同路径中。

## 修复方案

### 方案 A: 修改 do_bounty.py 的 load_env()（推荐，自愈型）

在 `do_bounty.py` 的 `load_env()` 末尾添加从 `.env_bot` 读取并映射的逻辑：

```python
# Also load from .env_bot and map GH_BOT_TOKEN → GITHUB_TOKEN
env_bot_paths = ["/opt/data/.env_bot"]
for p in env_bot_paths:
    if os.path.exists(p):
        with open(p) as f:
            for line in f:
                line = line.strip()
                if "GH_BOT_TOKEN" in line and "=" in line:
                    token = line.split("=", 1)[1].strip().strip('"').strip("'").replace("export ", "")
                    if token and not os.environ.get("GITHUB_TOKEN"):
                        os.environ["GITHUB_TOKEN"] = token
                    break
```

如果 `os.environ["GITHUB_TOKEN"]` 已经在子进程环境中存在（如 `smart_bounty_search.py` 显式传递），这行代码不会覆盖它 — 只有为空时才从 `.env_bot` 回退读取。

### 方案 B: 统一凭证存储

将 GitHub token 从 `/opt/data/.env_bot` 移到 `/opt/data/.env`：

```bash
echo "GITHUB_TOKEN=ghp_xxx" >> /opt/data/.env
```

然后将 `smart_bounty_search.py` 的 `load_env()` 也改成读取 `/opt/data/.env`（或者同时读取两个文件）。这样两个脚本都在同一位置找同一个变量名，不存在分裂问题。

### 方案 C: 从父进程传递（smart_bounty_search.py 修复）

修改 `smart_bounty_search.py` 中调用 `do_bounty.py` 的 subprocess.run，显式传递环境变量：

```python
# 在 smart_bounty_search.py 中, 第 421 行附近
env = os.environ.copy()
if token:  # token 来自 load_env()
    env["GITHUB_TOKEN"] = token
result = subprocess.run(
    [sys.executable, "/opt/data/scripts/do_bounty.py", target["url"]],
    timeout=240, capture_output=True, text=True, env=env,
)
```

## 验证修复

```bash
# 测试 do_bounty.py 的 load_env 修复
cd /opt/data/scripts
python3 -c "
import os
os.environ.pop('GITHUB_TOKEN', None)
exec(open('do_bounty.py').read().split('def main')[0])
# 现在 check
token = os.environ.get('GITHUB_TOKEN', '')
print(f'GITHUB_TOKEN: {\"SET\" if token else \"MISSING\"}')
"
```

修复后应输出 "GITHUB_TOKEN: SET"。修复前输出 "GITHUB_TOKEN: MISSING"。
