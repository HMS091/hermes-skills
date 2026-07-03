# Open Source Customer Support Systems Survey (2026-06)

Survey of GitHub open-source helpdesk/ticketing systems evaluated for solopreneur/一人公司 use cases.

## Top Candidates

| Project | Stars | Tech | Last Push | License | Open Issues | Docker | Chinese |
|---------|-------|------|-----------|---------|-------------|--------|---------|
| **Chatwoot** | 33,688 | Ruby/Rails | 2026-06-29 | NOASSERTION | 1,223 | ✅ | ❌ |
| **UVdesk** | 19,211 | PHP/Symfony | 2025-10 | OSL-3.0 | 78 | ✅ | ❌ |
| **Zammad** | 5,726 | Ruby/Rails | 2026-06-28 | AGPL-3.0 | 456 | ✅ | ❌ |
| **Freescout** 🥇 | 4,382 | PHP/Laravel | 2026-06-28 | AGPL-3.0 | 21 | Community | ✅ |
| **osTicket** | 3,813 | PHP | 2026-06-17 | GPL-2.0 | 1,197 | ✅ | ❌ |
| **Trudesk** | 1,490 | Node.js+Mongo | 2026-05-11 | Apache-2.0 | 11 | ✅ | ❌ |
| **Bytedesk** | 441 | Java | 2026-06-27 | AGPL-3.0 | 1 | ✅ | ✅ |

## Solopreneur Recommendation

### 🥇 Freescout (freescout-help-desk/freescout)

**Why:** Pure PHP + MySQL, no external services needed. Email-to-ticket workflow means the operator replies from email — no dashboard login required. Built-in Chinese (simplified & traditional). Only 21 open issues. Extremely active (last push 2026-06-28). Runs on $5 VPS or shared hosting.

**Deployment:** https://github.com/freescout-help-desk/freescout
- Docker community images exist
- Web installer for easy setup
- Mobile apps (iOS + Android)

### Why not the others for solo ops
- **Chatwoot** ★33,688: Ruby+Rails+Redis+Postgres is heavy. 1,223 open issues is a maintenance burden for one person.
- **Zammad** ★5,726: Ruby architecture complex. 456 open issues.
- **Trudesk** ★1,490: Requires MongoDB 5.0+ and optional Elasticsearch 8. No Chinese.
- **Helpy** ★2,483: Abandoned since 2023.
- **Bytedesk** ★441: Java stack is heavy for deployment on limited hardware (NAS J3455).

## Key URLs

- Freescout: https://github.com/freescout-help-desk/freescout
- Freescout demo: https://demo.freescout.net
- Freescout website: https://freescout.net
- Chatwoot: https://github.com/chatwoot/chatwoot
- UVdesk: https://github.com/uvdesk/community-skeleton
- Zammad: https://github.com/zammad/zammad
- osTicket: https://github.com/osTicket/osTicket
- Trudesk: https://github.com/polonel/trudesk
- Bytedesk: https://github.com/Bytedesk/bytedesk
