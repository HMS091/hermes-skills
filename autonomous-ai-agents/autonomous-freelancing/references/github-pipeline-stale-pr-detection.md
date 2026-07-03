# Stale PR Detection — Not All Open PRs Block New Submissions

## Problem
The script's `check_existing_pr()` treated ALL open PRs as valid competition. In Warpspeed bounties, old PRs (#17, #11, #14, #15) were submitted 5+ days ago, never merged, and had no review activity — but blocked new submissions for the same issue.

## Solution: Viable PR Check

Check whether an open PR is actually active competition:

```python
def has_viable_pr(token, owner, repo, issue_num):
    """Check if there's a MERGEABLE open PR, not just any open PR."""
    q = f"repo:{owner}/{repo}+type:pr+%23{issue_num}+state:open"
    results = gh_search(token, q).get("items", [])
    for pr in results:
        updated = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
        age_days = (NOW - updated).days
        is_mergeable = pr.get("mergeable", False)
        has_review = pr.get("requested_reviewers") or pr.get("requested_teams")
        
        # Stale PR (7+ days, no review, unmergeable) → ignore
        if age_days > 7 and not is_mergeable and not has_review:
            continue  # abandoned
        
        # Recent PR or has review → block new submission
        return True  # active competition exists
    
    return False  # No viable PR found
```

## Rules
- PR 7+ days old AND no review AND not mergeable → abandoned, allow new submission
- PR ≤ 7 days OR has review activity → active competition, block
