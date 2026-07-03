# PlakarKorp Bounty Ecosystem

Researched: June 2, 2026 — Live target found: $1,500 GitLab CE integration

## Overview

PlakarKorp runs a real-cash bounty program for integration plugins. Unlike most GitHub "bounty" labels, these are genuine USD payouts emailed after PR merge.

**Policy:** https://plakar.io/legal-notice/bounty-policy/

## Two-Repo Structure

Bounties require work on **both** repos:

### 1. `PlakarKorp/hub` — Recipe Index
Contains only `recipe.yaml` files that point to actual code.

**Layout:**
```
{tier}/{kloset-compat-version}/{plugin}/recipe.yaml
```

**recipe.yaml format:**
```yaml
name: ftp
version: v1.1.1
repository: https://github.com/PlakarKorp/integrations
```

**Tiers:**
- `community/` — open-source plugin set
- `enterprise/` — internal-only, requires special access

**Version branches:**
- `v1.0.0/` — legacy per-plugin repos (e.g., `PlakarKorp/integration-ftp`), flat tags
- `v1.1.0/` — mono-repos, prefixed tags `<name>/<version>`

### 2. `PlakarKorp/integrations` — Go Plugin Code
Mono-repo with actual plugin implementations. Prefixed tags like `ftp/v1.1.1`.

## Bounty Tiers

| Label | Payout | Scope |
|-------|--------|-------|
| `bounty:tier1` | $1,500 | Advanced: distributed systems, remote orchestration, complex restore |
| `bounty:tier2` | $750 | Standard: auth support, filter options, well-documented tooling |
| `bounty:tier3` | $500 | Basic: straightforward dump/restore with single data source |

## Claiming Process

1. **Ask questions first** — comment on the issue to align scope
2. **Comment to claim** — one active claim at a time, 2-week completion window
3. **Submit PR to `PlakarKorp/integrations`** — reference the issue
4. **First merged PR wins** — then email `bounty@plakar.io` for payment (not automatic)
5. **Payment:** bank wire within 30 days after invoice/certificate validation

## Competition Dynamics Observed (June 2-3, 2026)

Plakar bounties attract rapid claimers. When the GitLab CE bounty ($1500, issue #9) was posted on June 2:
- **@Asobu01** claimed within ~1 hour: "ETA: first reviewable PR in about 8h"
- **@tinyopsstudio** (TinyOps Studio LLC) claimed shortly after: "local prototype started"
- Both claimed within the first ~3 hours of a 14-day window

**Implication:** PlakarKorp bounties on hub/ are NOT uncontested even at 1-2 comments. By the time a cron cycle detects them, at least one person has likely claimed with a head start. The "first merged PR wins" policy rewards speed, not order of claiming.

**Go/No-Go decision for Plakar bounties:**
- If 0 comments and < 12h old → GO (first mover advantage possible)
- If 1+ comments and any contain "prototype", "ETA", "started", "PR" → SKIP (competitor has meaningful head start on a feature-complex integration)
- If 1+ comments and all are just "interested" / questions about scope → YELLOW (proceed with fast investigation only)

## Existing Community Plugins (v1.1.0)

azblob, etcd, ftp, gcs, grpc, imap, k8s, mysql, notion, oci, postgresql, proxmox, rclone, s3, sftp, sqlite

**Proxmox is the SSH-pattern reference** — use it as a template for remote-orchestration integrations.

## GitLab CE Bounty #9 — $1,500

**Issue:** https://github.com/PlakarKorp/hub/issues/9  
**Status:** Labeled `status:wip`, 2 comments (very low competition)  
**Opened:** June 2, 2026 (~45 min before discovery)

**Requirements:**
- Invoke `gitlab-backup create` on local/remote GitLab CE instance
- Ingest backup archive + config files into a Plakar snapshot
- Restore: extract snapshot → `gitlab-backup restore`
- Support remote SSH operation (like Proxmox)
- Reference: https://docs.gitlab.com/ee/administration/backup_restore/

## Blocked by Token

When scanning Plakar bounties, note: fine-grained PATs cannot fork repos (403 error). A classic PAT (`ghp_...` with `repo` scope) is required for the fork → PR pipeline. See `references/classic-vs-finegrained-tokens.md` for setup.
