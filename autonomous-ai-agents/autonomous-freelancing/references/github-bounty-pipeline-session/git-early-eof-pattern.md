# Git Early EOF / Sideband Disconnect Pattern

## Symptom

```
unexpected disconnect while reading sideband packet
fatal: early EOF
fatal: fetch-pack: invalid index-pack output
```

Also manifests as git subprocess timeout when repos are large:
```
['git', 'clone', ..., 'rustchain-bounties']' timed out after 60 seconds
```

## ⚠️ False Fix Claim (2026-06-04 07:22)

The user claimed "脚本修好了git网络问题" (script fixed the git network issue) and "不会再超时了" (won't timeout anymore). **This was tested and proven false.** In the very next run, the script timed out at 300s, and history shows identical git failures ongoing:

- Issue #13071: `rustchain-bounties` — git clone timed out after 60s
- Issues continue to be marked FAILED with `early EOF` / `sideband` / `invalid index-pack` errors

The "fix" was not actually applied or was ineffective. The git early EOF problem remains the single largest source of execution failures.

## Occurrence Stats (as of 2026-06-04 07:22)

| Repository | Attempts | Outcome |
|-----------|---------|---------|
| `mohitkumhar/business-ai-agent` | 2 (issues #398, #395) | Both FAILED |
| `tenstorrent/tt-metal` | 1 (#46006) | FAILED |
| `redmushie/ss14-starlight` | 1 (#11) | FAILED |
| `zkldi/Tachi` | 1 (#1630) | FAILED |
| `CoralSwap-Finance/coralswap-sdk` | 1 (#193) | FAILED |
| `mowlsint/MagicPaws` | 1 (#1834) | FAILED |
| `Scottcjn/rustchain-bounties` | 1 (#13071) | FAILED (git clone timeout) |
| **Total** | **9+ failures** | **0 recovered** |

The rustchain-bounties failure suggests any repo over ~30MB on flaky network will hit this. The shallow clone `--depth 1` + `GIT_SSL_NO_VERIFY=1` mitigations may not have been applied to do_bounty.py, or they're insufficient for the network conditions.

## Root Causes

### 1. Repo size
Repos >50MB trigger sideband protocol issues in constrained Docker environments. `tenstorrent/tt-metal` is ~GB scale and should never be attempted.

### 2. Git packfile protocol
Git uses sideband multiplexing over HTTPS for large transfers. In Docker with limited memory (default 2GB), the packfile decompression buffer can be exhausted.

### 3. SSL termination
The `clean_env` dict unsets `HTTP_PROXY`/`HTTPS_PROXY` but doesn't set `GIT_SSL_NO_VERIFY`. If the Docker host has a TLS-intercepting proxy, git's HTTPS connection may be terminated mid-stream.

## Detection (pre-clone)

```python
repo_url = f"https://api.github.com/repos/{owner}/{name}"
data = gh_request(GH_BOT_TOKEN, repo_url)
size_mb = data.get("size", 0) / 1024  # GitHub size is KB
if size_mb > 50:
    print(f"   ⏭️ Repo {size_mb:.0f}MB > 50MB, skipping")
    return
```

## Mitigation (in clone step)

```python
clean_env.update({
    "GIT_SSL_NO_VERIFY": "1",
    "GIT_TERMINAL_PROMPT": "0",
})
result = subprocess.run(
    ["git", "clone", "--depth", "1", authed_url, repo_path],
    capture_output=True, text=True, timeout=60,
    env=clean_env,
)
if result.returncode != 0:
    stderr = result.stderr.strip()
    if "early EOF" in stderr or "sideband" in stderr:
        print(f"   ⚠️ Git clone failed (large repo): {stderr[:100]}")
    else:
        print(f"   ❌ Git clone failed: {stderr[:200]}")
    return
```
