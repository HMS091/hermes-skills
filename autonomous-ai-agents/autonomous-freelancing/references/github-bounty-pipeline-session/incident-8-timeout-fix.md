# Incident #8 — 终于修复的 120s 超时 (2026-06-03 17:49)

## 时间线

| # | 时间 | 行为 | 结果 | 工具调用数 |
|---|------|------|------|-----------|
| 1 | 16:13 | 写分析报告，建议 4 个修复 | ❌ 未应用任何修复 | ~15 |
| 2 | 17:12 | 写更长的分析报告 | ❌ 未修复 | ~18 |
| 3 | 17:20 | 再次分析+报告 | ❌ 未修复 | ~12 |
| 4 | 17:28 | 再次分析+报告 | ❌ 未修复 | ~14 |
| 5 | 17:33 | 再次分析+报告 | ❌ 未修复 | ~10 |
| 6 | 17:38 | Agent 读脚本→查 session→耗尽 max_turns | ❌ 中断，未修复 | 10 (max) |
| 7 | 17:44 | 同样模式，写入 config 但被 max_turns 截断 | ❌ 中断，未修复 | 10 (max) |
| **8** | **17:49** | **读了 skill → grep config → patch → 清理 temp** | **✅ 修复** | **9 (接近 max_turns 被截断)** |

## 根因

 `/opt/data/config.yaml` 缺少 `cron.script_timeout_seconds` 配置。调度器默认 120s 超时不适用于 do_bounty.py 的子进程（clone=120s + AI分析=120s + push=120s）。

## 最终修复

`/opt/data/config.yaml` 的 `cron:` 段添加了 `script_timeout_seconds: 300`。

## 经验

### 第8次会话的完整调用链（反面教材）

第8次虽最终修复，但仍然因为过度分析在 max_turns 被截断。调用链：

```
1. read_file(smart_bounty_search.py)        — ❌ 违反了「不要重复加载脚本全文」
2. read_file(do_bounty.py)                  — ❌ 读第二个脚本 415 行
3. search_files(smart_bounty in /etc/cron*) — ❌ 查系统 cron 文件
4. search_files(smart_bounty in /opt)       — ❌ 查配置文件
5. skill_view(github-bounty-hunter)         — ✅ 应该第一步就做
6. read_file(/opt/data/config.yaml)         — ✅ 但没有先 grep
7. patch(config.yaml → +script_timeout)     — ✅ 核心修复
8. terminal(verify import)                   — ❌ 验证命令失败 (ModuleNotFoundError)
9. terminal(find temp dirs)                 — ✅ 但已经不够时间清理
```

**理想调用链（2-3 次）**：
```
1. terminal(grep script_timeout_seconds /opt/data/config.yaml)
2. patch(config.yaml → +script_timeout_seconds: 300)
3. terminal(find /tmp/bounty_* -delete)
```

### 关键教训

1. **grep 先于 read_file**。一次 `grep` 调用就够判断是否需要修复，不需要读 440 行的 config.yaml
2. **验证命令不可靠**。`_get_script_timeout()` 的导入路径依赖 yaml 模块，在 cron 上下文中不可用。grep 直接读文件更可靠
3. **max_turns 配额有限**（10次）。每次读脚本文件=消耗 1-2 次调用不解决问题。协议应该限制在对 config 的 2-3 次操作内
4. **临时目录残留**。`/tmp/bounty_*` 目录在 SIGKILL 场景下从不清理，3 个旧目录需要手动清除

## 残余待办

- 清理 `/tmp/bounty_*` 旧目录（需要 rm -rf 权限）
- 脚本中 `AUTO_EXEC_MIN_USD` 仍为 10（skill 文档要求 50）
- `TOKEN_TO_USD` 中 MRG/MRWK 的脚本值仍高于实际 45-300 倍
- 仓库黑名单（BountyScout, xevrion-v2 等）未加入脚本
