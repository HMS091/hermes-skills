# Bug Bounty Platforms — Full Automation Research

Researched: June 1, 2026

## Why Bug Bounty for AI Automation

Bug bounty platforms are the best fit for "I do nothing, you auto-complete" because:
- ❌ No bidding (unlike Freelancer)
- ❌ No client communication
- ✅ AI scans code → finds bugs → writes report → submits
- ✅ Payout on results, not on winning proposals
- ✅ Crypto options available (Immunefi/Sherlock pay in crypto)

## Platform Overview

| Platform | Focus Areas | Min Payout | Auto-Report? | Code Audit Access |
|:---------|:-----------|:----------:|:------------:|:-----------------:|
| **HackerOne** | Web, mobile, API, infrastructure | $500 | ✅ Submit via API | Public + Private programs |
| **Immunefi** | Smart contracts, blockchain | $1,000 | ⚠️ Manual submission | Public programs visible |
| **Bugcrowd** | Web, mobile, API | $250 | ✅ Submit via API | Public programs |
| **Intigriti** | Web applications (EU focus) | $500 | ✅ Submit via API | Public programs |
| **YesWeHack** | Web, mobile, infrastructure | $500 | ✅ Submit via API | Public programs |
| **Sherlock** | Solana/DeFi audit contests | $1,000 | ⚠️ Contest-specific | Code available during contests |

## Key Considerations

1. **Registration:** All require KYC (Know Your Customer) for payouts. User must register.
2. **API access:** HackerOne and Bugcrowd have public APIs for vulnerability submission.
3. **Scope:** Private programs (invite-only) are more lucrative but harder to access.
4. **AI strengths:** Logic bugs, race conditions, input validation, SSRF, IDOR, auth bypass.
5. **AI weaknesses:** Complex business logic chains, physical security, social engineering.

## Recommended First Steps

1. User registers on **HackerOne** (most accessible, best API)
2. Agent analyzes public programs' scopes and attack surfaces
3. Agent runs automated analysis tools on in-scope targets
4. Agent submits findings with proof-of-concept
