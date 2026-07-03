# API-Only Git Workaround

## Problem
Some environments cannot reach `github.com:443` (connection timeout) but can reach `api.github.com:443`. All git CLI operations (clone, push, fetch) fail.

## Workaround: Use GitHub REST API

### Clone → Zipball Download
```
GET /repos/{owner}/{repo}/zipball/{ref}
```
Add retry for `IncompleteRead` errors (common on repos >3MB):
```python
def download_zipball(url, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={...})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            if len(data) > 1000:
                return data
        except (urllib.error.IncompleteRead, ConnectionResetError):
            if attempt < max_retries:
                time.sleep(2)
                continue
            raise
    return None
```

### Commit/Push → Git Data API
1. Get current tree: `GET /repos/{owner}/{repo}/git/trees/{branch_sha}`
2. Create blobs: `POST /repos/{owner}/{repo}/git/blobs` (for each new file)
3. Create tree: `POST /repos/{owner}/{repo}/git/trees` (base SHA + new entries)
4. Create commit: `POST /repos/{owner}/{repo}/git/commits`
5. Update ref: `PATCH /repos/{owner}/{repo}/git/refs/heads/{branch}`

### Pre-Check: Repo Size
Before any download, check repo size:
```python
repo_data = gh_request(token, f"https://api.github.com/repos/{owner}/{repo}")
size_mb = repo_data.get("size", 0) / 1024
if size_mb > 50:
    print(f"   ⏭️ Repo {size_mb:.0f}MB > 50MB — skip (zipball risk)")
    return
```
