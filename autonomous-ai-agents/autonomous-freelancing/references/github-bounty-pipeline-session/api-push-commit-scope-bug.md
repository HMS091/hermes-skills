# `api_push_commit()` 中未定义 `issue_num` 变量的作用域 Bug

## 发现时间
2026-06-04 07:09 (cron tick)

## 症状

`do_bounty.py` 在 API 推送 commit 时崩溃，错误：

```
NameError: name 'issue_num' is not defined
```

发生在第 299 行 `f"fix: bounty submission for #{issue_num}"`。

## 根因

`api_push_commit()` 函数的签名是：

```python
def api_push_commit(token, fork_full, branch_name, base_sha, changed_files_data):
```

该函数在 `main()` 中被调用（`main()` 中有 `issue_num` 变量），但函数本身**未接收 `issue_num` 参数**。第 299 行的默认 commit message 模板引用了不存在的局部变量。

此外，在线 306-309 处，如果 `changed_files_data` 中有元素包含 `commit_msg` 键，该消息会被覆盖。所以这个 bug 仅影响**没有自定义 commit message** 的提交（通常是直接提交 claim 文件的 PR）。

## 修复

### 1. 修改函数签名，添加 `issue_num=None` 参数

```python
def api_push_commit(token, fork_full, branch_name, base_sha, changed_files_data, issue_num=None):
```

### 2. 修改默认 commit message 使用安全回退

```python
"message": f"fix: bounty submission for #{issue_num if issue_num is not None else 'unknown'}",
```

### 3. 更新调用站点传入 `issue_num`

```python
commit_sha, commit_url = api_push_commit(token, fork_full, branch_name, head_sha, changed_files, issue_num)
```

## 受影响的 Issue

- `Scottcjn/rustchain-bounties#13080` — Claim: Multi-Round PR Reviews (43.00 RTC)
- 所有通过 API 推送且无自定义 `commit_msg` 的未来提交均受影响
