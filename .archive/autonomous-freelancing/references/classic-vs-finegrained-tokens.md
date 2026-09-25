# GitHub Token Types for Bounty Automation

## Fine-Grained PAT (ghu_... / github_pat_...)

| Capability | Works? | Notes |
|:-----------|:------:|:------|
| Search Issues | ✅ | Works |
| Read repo contents | ✅ | Works |
| Write files (Contents) | ✅ | Works |
| Create/comment Issues | ✅ | Works |
| Create Pull Requests | ✅ | Works |
| **Fork a repository** | **❌** | **403 Resource not accessible** |

**Conclusion:** Fine-grained PATs cannot fork. They CAN do everything else (write to repos, create branches, push commits, open PRs), but fork/create-a-fork always returns 403. This is a GitHub platform restriction, not a permission misconfiguration.

## Classic PAT (ghp_...)

| Capability | Works? | Notes |
|:-----------|:------:|:------|
| Search Issues | ✅ | Works |
| Read repo contents | ✅ | Works |
| Write files (Contents) | ✅ | Works |
| Create/comment Issues | ✅ | Works |
| Create Pull Requests | ✅ | Works |
| **Fork a repository** | **✅** | Works |
| All repo operations | ✅ | With `repo` scope |

## How to Generate a Classic PAT

1. Go to https://github.com/settings/tokens
2. Click **Generate new token → Generate new token (classic)**
3. Name: any recognizable name
4. Expiration: **No expiration** (for ongoing automation)
5. Scopes: check **`repo`** (all sub-items auto-check)
6. Click **Generate token**
7. Copy the `ghp_...` string immediately — it won't be shown again

## Workflow Comparison

| Step | Fine-Grained | Classic (`repo`) |
|:-----|:------------:|:----------------:|
| Search bounties | ✅ | ✅ |
| Fork repo | ❌ Fork fails | ✅ Fork works |
| Clone fork | ✅ | ✅ |
| Create branch | ✅ | ✅ |
| Write code | ✅ | ✅ |
| Push branch | ✅ | ✅ |
| Open PR | ✅ | ✅ |

## The One Workaround (for fine-grained tokens)

The user manually forks the target repo once. After that, the machine account's existing fork can be used for all subsequent PRs (git clone → branch → write → push → PR). This is a one-time fix per repo but is friction for fully automated workflows.

## Verified (June 1, 2026)

- Fine-grained PAT: fork returns `403 Resource not accessible by personal access token`
- Classic PAT (`repo` scope): fork succeeds immediately
- PR creation from fork (classic PAT): works end-to-end
- PR link example: https://github.com/tommycet/proofworks-genlayer/pull/35
