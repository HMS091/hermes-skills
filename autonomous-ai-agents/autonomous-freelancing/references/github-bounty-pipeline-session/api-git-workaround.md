# API-Based Git Operations Workaround

## Problem

`github.com:443` is unreachable from this environment (TCP connection times out), but `api.github.com:443` and `raw.githubusercontent.com` work fine. All git CLI operations that connect to `github.com` (clone, push, fetch) fail.

| Domain | Status |
|--------|--------|
| `github.com:443` (git clone/push) | ❌ Connection timeout |
| `api.github.com:443` (REST API) | ✅ Works |
| `raw.githubusercontent.com` (raw content) | ✅ Works |

## Solution: Replace git CLI with GitHub API

### 1. Clone → API Zipball Download

```python
import zipfile, io

def api_clone_repo(token, fork_full, repo_path):
    """Download repo via API zipball endpoint, extract to repo_path."""
    # Get default branch and HEAD SHA
    repo_info = gh_request(token, f"https://api.github.com/repos/{fork_full}")
    default_branch = repo_info.get("default_branch", "main")
    branch_info = gh_request(token,
        f"https://api.github.com/repos/{fork_full}/branches/{default_branch}")
    head_sha = branch_info["commit"]["sha"]

    # Download zipball via API
    zip_url = f"https://api.github.com/repos/{fork_full}/zipball/{default_branch}"
    raw_data = gh_request_raw(token, zip_url)  # returns bytes

    # Extract (zipball has a top-level directory like "owner-repo-<sha>")
    os.makedirs(repo_path, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw_data)) as zf:
        members = zf.namelist()
        top_dir = members[0].split("/")[0] if "/" in members[0] else members[0].rstrip("/")
        for member in members:
            if member.startswith(top_dir + "/"):
                rel_path = member[len(top_dir)+1:]
            elif member == top_dir:
                continue
            else:
                rel_path = member
            if not rel_path:
                continue
            target = os.path.join(repo_path, rel_path)
            if member.endswith("/"):
                os.makedirs(target, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    dst.write(src.read())

    # Init local git repo for AI analysis
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, timeout=10)
    subprocess.run(["git", "checkout", "-b", default_branch], cwd=repo_path,
                   capture_output=True, timeout=10)

    return default_branch, head_sha
```

### 2. Push → Git Data API

Uses the GitHub Git Data API pipeline: **create blob → create tree → create commit → update ref**.

```python
def api_push_commit(token, fork_full, branch_name, base_sha, changed_files_data):
    """Push via API: creates commit and updates branch ref."""
    # Get base tree SHA
    base_tree = gh_request(token,
        f"https://api.github.com/repos/{fork_full}/git/commits/{base_sha}")
    base_tree_sha = base_tree["tree"]["sha"]

    # Create blobs for each changed file
    tree_items = []
    for change in changed_files_data:
        blob_data = {"content": change["content"], "encoding": "utf-8"}
        try:
            blob = gh_request(token,
                f"https://api.github.com/repos/{fork_full}/git/blobs", data=blob_data)
        except:
            # Fallback to base64 if utf-8 encoding fails
            content_b64 = base64.b64encode(change["content"].encode("utf-8")).decode("ascii")
            blob = gh_request(token,
                f"https://api.github.com/repos/{fork_full}/git/blobs",
                data={"content": content_b64, "encoding": "base64"})
        tree_items.append({
            "path": change["path"], "mode": "100644",
            "type": "blob", "sha": blob["sha"],
        })

    # Create new tree
    new_tree = gh_request(token,
        f"https://api.github.com/repos/{fork_full}/git/trees",
        data={"base_tree": base_tree_sha, "tree": tree_items})

    # Create commit
    commit = gh_request(token,
        f"https://api.github.com/repos/{fork_full}/git/commits",
        data={
            "message": f"fix: bounty submission",
            "author": {"name": "Bot Name", "email": "bot@users.noreply.github.com"},
            "parents": [base_sha],
            "tree": new_tree["sha"],
        })

    # Update ref (push)
    ref = f"refs/heads/{branch_name}"
    try:
        # Create new branch
        gh_request(token, f"https://api.github.com/repos/{fork_full}/git/refs",
                   data={"ref": ref, "sha": commit["sha"]})
    except urllib.error.HTTPError as e:
        if e.code == 422:
            # Update existing branch
            gh_request(token, f"https://api.github.com/repos/{fork_full}/git/{ref}",
                       data={"sha": commit["sha"], "force": True}, method="PATCH")
        else:
            raise

    return commit["sha"]
```

### 3. Verifying fork commit was pushed

After the API push succeeds, verify by fetching the branch:
```python
branch_info = gh_request(token,
    f"https://api.github.com/repos/{fork_full}/branches/{branch_name}")
assert branch_info["commit"]["sha"] == new_commit_sha
```

## Integration in do_bounty.py

The full replacement was applied to `/opt/data/scripts/do_bounty.py` on 2026-06-04:
- `git clone` removed → `api_clone_repo()` used instead
- `git add/commit/push` removed → `api_push_commit()` used instead
- git config (user.name/email) kept for local `git init` operations
- PR creation unchanged (already used API)
- `git fetch origin` removed (not needed with fresh zipball)

## When to revert to git CLI

Only if the network changes so that `github.com:443` becomes reachable. Check with:
```bash
curl -v --max-time 5 https://github.com 2>&1 | grep -c "Connection refused\|timed out"
# Returns 1 if still blocked, 0 if reachable
```
