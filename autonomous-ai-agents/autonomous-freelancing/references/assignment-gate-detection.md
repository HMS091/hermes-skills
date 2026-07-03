# Hacktoberfest/Assignment-Gate Bounty Detection

## Overview
Some repos offer real USD bounties under the `hacktoberfest` label but require assignment before PR submission. The agent cannot auto-execute these, but should recognize and report them.

## Detection Signals
Issue body contains phrases like:
- "Ask to be assigned"
- "Wait to be assigned"
- "Request assignment"
- "Make sure to ask before working"
- Issue has the `hacktoberfest` label

## Known Repos with Real USD + Hacktoberfest
| Repo | Bounty Range | Notes |
|------|-------------|-------|
| aporthq/aport-integrations | $10-$50 | Python/LangGraph/CrewAI integrations with APort SDK |

## Agent Strategy
1. Detect assignment gate via issue body text
2. Classify as "near-miss" (not auto-executable)
3. Surface in cron report with bounty details and link
4. User can self-assign if interested, then agent proceeds with tech work

## Fallback: Check existing PRs
Even for assignment-gated issues, check if someone already submitted a PR:
```python
curl -s "https://api.github.com/repos/owner/repo/pulls?state=open&per_page=100" \
  | python3 -c "import sys,json; pulls=json.load(sys.stdin); \
  [print(f'#{p[\"number\"]}: {p[\"title\"]} by @{p[\"user\"][\"login\"]}') for p in pulls]"
```
If a PR already exists, the bounty is likely claimed — skip.
