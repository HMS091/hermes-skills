# Zipball IncompleteRead Failure Pattern

## Discovery (2026-06-04)
Rustchain-bounties zipball download failed with `IncompleteRead(3403071 bytes read)` during a routine cron run. The script had already been running stably for 8+ hours with Phase 1+2 fixes. Only the zipball download step failed.

## Error Signature
```
❌ 下载仓库失败: IncompleteRead(3403071 bytes read)
```
The number (~3.4MB) indicates partial data was received before the connection dropped.

## Root Cause
1. **`gh_request_raw()` reads entire response body at once** — `data = req.read()` has no streaming/buffering. If TCP connection drops mid-transfer, `read()` returns incomplete data. When the response is binary (zipball), `IncompleteRead` is raised by urllib because Content-Length doesn't match received bytes.

2. **Chunked transfer encoding sensitivity** — GitHub's zipball endpoint uses chunked transfer encoding. Under unstable network conditions (Docker overlay, NAT, proxy chains), individual chunks can be lost.

3. **No retry in the code path** — Unlike GitHub API calls which use `gh_request_retry()`, the zipball download code path (`gh_request_raw()`) has no retry logic.

## Affected Repositories (candidates)
Any repo where `size` field (in KB) from `GET /repos/{owner}/{repo}` exceeds ~3-5MB (~3000-5000 KB). The larger the repo, the more likely the zipball download fails.

Likely candidates based on observed git early EOF incidents:
- `tenstorrent/tt-metal` (GB-class, will always fail — should be caught by size check)
- `mohitkumhar/business-ai-agent` (~100MB+)
- `Scottcjn/rustchain-bounties` (confirmed failure ~3.4MB partial read)
- `zkldi/Tachi`, `CoralSwap-Finance/coralswap-sdk`
- Any repo with binaries (images, compiled artifacts, test fixtures) in git history

## Fix: Retry Wrapper + Pre-Check

### Pre-check: Skip repos that are too large
Add before zipball download in `do_bounty.py`:
```python
repo_data = gh_request(token, f"https://api.github.com/repos/{owner}/{repo}")
size_mb = repo_data.get("size", 0) / 1024
if size_mb > 10:  # conservative threshold
    print(f"   ⏭️ 仓库 {size_mb:.0f}MB > 10MB，zipball 下载风险过高 — 跳过")
    # Record to history so we don't retry next cycle
    return
```

### Retry wrapper for zipball download
Replace the direct `gh_request_raw()` call for zipball with:
```python
def download_zipball_with_retry(token, zip_url, max_retries=2):
    """Download zipball with retry on IncompleteRead / ConnectionReset."""
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(zip_url)
            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("Accept", "application/vnd.github.v3+json")
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            # Sanity check — tiny responses are error pages
            if len(data) < 1000:
                raise ValueError(f"Zipball too small ({len(data)} bytes): likely error response")
            return data
        except (urllib.error.IncompleteRead, ConnectionResetError, ValueError) as e:
            print(f"   ⚠️ Zipball download attempt {attempt + 1}/{max_retries + 1} failed: {e}")
            if attempt < max_retries:
                time.sleep(2)
                continue
            raise  # All retries exhausted
    return None  # Unreachable
```

## Verification
After fix:
- `curl -s "https://api.github.com/repos/Scottcjn/rustchain-bounties" | python3 -c "import json,sys;d=json.load(sys.stdin);print(f'{d[\"size\"]/1024:.0f}MB')"` → check repo size
- Run full script and verify rustchain-bounties no longer triggers IncompleteRead
- If it still fails, repo is simply too large for this network environment — add to auto-skip list
