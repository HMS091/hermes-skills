# Project Organization for Online Earning

## When to Create a Separate Project Directory

The user may have multiple businesses or projects running. This reference documents the pattern for keeping "网上接单赚钱" (online freelancing/earning) isolated from other operations.

## Dedicated Directory Structure

```
/opt/data/projects/online-earning/
├── config/         # Platform credentials, API keys, wallet addresses
│   ├── platforms.yaml    # Registered platform list + credentials
│   └── profiles.yaml     # Profile text per platform
├── scripts/        # Monitoring and automation scripts
│   ├── monitor.py        # Task monitoring script
│   └── deploy.sh         # Environment setup
├── tasks/          # Individual task records
│   ├── 2026-05/         # Monthly subdirectories
│   │   └── task-001.md  # Bid → acceptance → deliver → payment
│   └── 2026-06/
├── logs/           # Execution logs
│   ├── monitor.log
│   └── tasks.log
└── output/         # Deliverables for clients (per project)
    ├── project-name-001/
    └── project-name-002/
```

## Why Separate

| Reason | Example |
|:-------|:--------|
| **No cross-contamination** | User's computer repair business ("排雷数码港") has its own files, client data, scripts. Freelancing work stays in its own sandbox. |
| **Clean deliverables** | Each client gets a self-contained zip from `output/` — no stray files from other projects. |
| **Isolated config** | Different platforms need different proxy settings, wallets, API keys. |
| **Predictable paths** | All monitoring scripts can hardcode `/opt/data/projects/online-earning/` paths without guessing. |

## Session History in This Directory

When working on a task in this project:
1. `cd /opt/data/projects/online-earning/`
2. Create `tasks/YYYY-MM/task-NNN.md` with: platform name, task description, price, timeline, deliverables
3. Write code in `scripts/` 
4. Package output files in `output/task-name/`
5. Log execution in `logs/`
