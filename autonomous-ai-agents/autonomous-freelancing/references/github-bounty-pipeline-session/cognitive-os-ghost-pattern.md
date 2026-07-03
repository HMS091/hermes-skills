# Cognitive-OS Ghost Repo Pattern (2026-06-04)

## Overview

Cognitive-OS (aLexzzz430/Cognitive-OS) is an example of a "ghost bounty" — a repo that looks legitimate but where the maintainer never merges or pays out. It was flagged by `smart_bounty_search.py` with AI:⚠️ and $3000, but investigation revealed it's a dead target.

**Status**: Added to `BLOCKED_REPOS` in the skill on 2026-06-04 after confirmation.

## Red Flags

| Check | Finding | Verdict |
|-------|---------|---------|
| **Repo age** | Created 2026-04-22 (~6 weeks old) | 🟡 Young but not disqualifying |
| **Stars/Forks** | 3 stars / 21 forks (forks >> stars) | 🔴 **Suspicious** — indicates bounty hunters, not real users |
| **Commits** | Only 5 commits, all by maintainer, in 5 days | 🔴 No real development |
| **Last push** | April 30, 2026 (over a month ago) | 🔴 Dead repo |
| **Open Issues** | 14 issues, 10+ are the same bounty #5 | 🔴 Spammy |
| **Maintainer merged bounty PRs** | **ZERO** out of 10+ submitted over 2 weeks | 🔴 **Ghosting** — worst signal |
| **Users claiming** | Mixed real-looking and bot-like | 🟡 Normal for any bounty |
| **Script AI warning** | ⚠️ Flagged | ✅ Correct — alerted manual investigation |

## Key Metrics at Time of Investigation

**2026-06-04 initial investigation (~13 days since issue creation):**
- Bounty amount: $3,000 (AGI architecture research)
- 31 comments on the issue
- **10 open PRs** all submitting the same research packet
- **3 closed PRs** — none merged (maintainer never accepted any)
- Competitors had submitted within hours of the issue opening

**2026-06-04 afternoon follow-up:**
- **14 open PRs** (grew from 10 → 14 in ~6 hours)
- Still **ZERO merged** despite 14 submissions
- 22 forks vs 3 stars = **7.3x fork/star ratio** (detection threshold is 2x, confirmed accurate)
- Repo description still `None` — maintainer never fleshed out the project
- Only 5 commits total, all in first week (April 22-26)
- Last pushed_at: April 30 (over a month ago) — no code changes for 35+ days despite active issue discussion

**2026-06-04 22:06 cron scan confirmation:**
- Script correctly flagged with ⚠️ and skipped due to 31 comments > 25 threshold
- Manual investigation validated the skip was correct
- No new activity from maintainer since last check — ghost repo confirmed

**Critical insight**: The fork/star ratio grew worse over time (from 7x → 7.3x) while payout-to-zero correlation held. This validates the detection logic: an ever-growing fork/star ratio with zero payouts is a definitive ghost bounty signal. Even with 22 forks suggesting high interest, the maintainer pays zero.

## Lesson

A repo can pass all automated checks (has stars, has commits, owner looks like a real person) but still be a dead bounty if:
1. Forks >> stars (indicates bounty hunter activity, not real users)
2. Maintainer merged ZERO bounty submissions despite 10+ PRs over 2+ weeks
3. All commits were in the first week of repo creation — no sustained development

## Detection Code

```python
# Add to manual post-scan protocol:
# GET /repos/{owner}/{repo}/pulls?state=closed&per_page=5
# Then count merged vs unmerged:
def has_any_bounty_payouts(pulls_data):
    """Return True if maintainer has ever merged a non-infrastructure PR."""
    merged = [p for p in pulls_data if p.get("merged_at")]
    # Filter out the maintainer's own infra PRs (init, CI, docs)
    non_infra_merged = [p for p in merged 
                        if not any(kw in (p.get("title","") or "").lower() 
                                   for kw in ["initialize", "ci", "license", "contributing"])]
    return len(non_infra_merged) > 0

# Suspicious fork/star ratio
def is_fork_bombed(repo_data):
    stars = repo_data.get("stargazers_count", 0)
    forks = repo_data.get("forks_count", 0)
    if stars > 0 and forks > stars * 2:
        return True  # forked way more than starred → bounty hunter magnet
    return False
```

## BLOCKED_REPOS Entry

Added to `smart_bounty_search.py` BLOCKED_REPOS on 2026-06-04:
```python
BLOCKED_REPOS = [
    ...
    "aLexzzz430",  # Cognitive-OS ghost repo, 14+PRs zero merged, fork≈stars×7, $3000 never paid
]
```

This prevents future runs from wasting cycles investigating this repo's issues.
