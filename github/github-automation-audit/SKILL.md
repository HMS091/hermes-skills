---
name: github-automation-audit
description: "Use when auditing GitHub automation and email sources."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Actions, Audit, Notifications, Automation]
    related_skills: [github-repo-management, github-auth, github-issues, cron-data-workflows]
---

# GitHub Automation Audit

Answers two questions with API evidence: **"which of my scripts are still running?"** and
**"why do I keep getting these GitHub emails?"** — covering GitHub Actions/bots and the local
Hermes cron jobs. The trap is answering from the file tree: a workflow YAML existing proves
nothing about whether it runs.

## When to Use

- The user asks which of their scripts/jobs are still running, or "how many are left" — on GitHub
  or in Hermes cron.
- The user reports a flood of GitHub notification email and wants the source identified.
- Before telling the user something is off (or accepting that it is on), and before touching any
  workflow, PR, or scheduled job.

## Ground truth (read this before reporting anything)

1. **Registered workflows + actual runs are the only evidence of live automation.**
   `GET /repos/{o}/{r}/actions/workflows` returning `total_count: 0`, or
   `GET /repos/{o}/{r}/actions/runs` returning empty, means that repo is NOT running anything —
   regardless of how many `.github/workflows/*.yml` files (with hourly `cron:` schedules) are
   committed. Never describe a repo as "running a scheduled script" because the YAML exists.
2. **Fork repos keep Actions disabled.** A fork can carry 20 workflows with `cron: '0 * * * *'`
   and never execute one of them. So a content search (`search_files`) across workflow files for
   `cron:` produces a mostly-false list — always cross-check each candidate against `/actions/runs`.
3. **`/actions/permissions` returning `enabled: true` is the repo setting, not proof of execution.**
   It reads `true` on dormant forks too. Do not quote it as evidence that things run.
4. **Zero runs is ambiguous.** Run history is truncated (~90 days), and GitHub auto-disables
   scheduled workflows after a long stretch of repository inactivity. "0 runs" can mean
   never-enabled OR ran-long-ago-then-pruned/auto-disabled. Confirm with commit history
   (`/repos/{o}/{r}/commits?since=...`) — a repo whose last bot commit is months old is dormant.
5. **The commits endpoint defaults to the default branch.** Work pushed to another branch
   (`?sha=BRANCH`) is invisible to a plain `/commits?since=` scan; if counts look too low,
   enumerate `/branches` before concluding nothing is happening.

## Procedure

1. **Auth.** `gh` is frequently absent; the whole audit works over REST with a token. Source it
   without printing it: from `$GH_TOKEN`/`$GITHUB_TOKEN`, or extract it once from an existing
   remote — `git -C <repo> config --get remote.origin.url` → the `user:token@` segment — and
   keep it in a `chmod 600` file under the scratch dir that scripts read.
2. **Run the probe:** `scripts/github-automation-probe.py` prints registered workflows + states,
   per-repo runs in the last N days, authored open PRs by repo, `involves:LOGIN` recency, and
   stored notifications by reason/repo/date. Prefer this one script over a long chain of inline
   `curl | python3 -c` — a single file is re-runnable, survives tool timeouts, and re-reads the
   token instead of re-embedding it.
3. **Classify each candidate** into `running` (registered workflow AND runs in the window) vs
   `dormant` (files present, zero runs). Report the two lists separately; the user's mental model
   is usually "everything I forked still runs".
4. **Attribute the emails.** `GET /notifications?all=true` is the closest proxy for what GitHub
   is mailing: group by `reason` (`author`, `mention`, `review_requested`, …), by repo, and by
   date. Cross-check with `search/issues?q=involves:LOGIN+updated:>=YYYY-MM-DD` for recent
   activity and `q=author:LOGIN+type:pr+state:open` for the outstanding-PR backlog.
5. **Check the local side too.** "Auto-executing scripts" usually spans Hermes cron, not just
   GitHub: read `$HERMES_HOME/cron/jobs.json` (`enabled`, `state`, `paused_reason`, `schedule`,
   `repeat.completed`, `last_status`, `deliver`) and group `$HERMES_HOME/cron/executions.db`
   (table `executions`) by `job_id` and by day to get real run volume. Paused jobs still count as
   "configured" — list them with their paused reason.
6. **Offer zero-risk fixes before destructive ones.** Self-serve: GitHub notification settings
   (https://github.com/settings/notifications — turn off email for the categories you don't want)
   plus a mailbox filter on `notifications@github.com` / `noreply@github.com`. Structural:
   disable Actions on the noisy repos, or close the stale auto-generated PRs.

## Pitfalls

- **Do not assert an email source you cannot see.** If account activity over the last 7/30 days is
  ~0, say that plainly and ask for one sample email (sender + subject) — do not pick the loudest
  historical candidate and present it as the current cause. Evidence first, hypothesis labelled as such.
- **`/user/emails` needs the `user:email` scope and 404s without it**; `/user` returns `email: null`
  when the address is private. Do not assume you can discover the account's mailbox from the API.
- **A big backlog is not authorization.** Closing PRs, disabling workflows, or deleting anything
  are irreversible external writes — they need explicit consent in the current conversation, even
  when the cleanup is obviously the user's intent. Report, recommend, then wait.
- **Distinguish "never enabled" from "enabled then auto-disabled"** for fork workflows; the user
  may have received a burst of mail months ago that has already stopped. Say which it is.
- **Counts must come from the API, not from memory of the file list.** Report the number of
  repos/runs/PRs you actually queried, and reconcile any total you state against the enumerated list.

## Report shape (this user)

Chinese, conclusion first, then numbers. Two explicit tables/lists — **在跑** vs **已停** — with
concrete counts (runs in window, open PRs, jobs `completed`). State plainly what is NOT happening
and which conclusion is unverified; never frame dormant automation as active to look thorough.
Close with the exact next actions the user can approve, and the self-serve steps they can do now.

## Files

- `scripts/github-automation-probe.py` — read-only inventory probe (registered workflows, runs,
  open PRs, `involves:` recency, notifications). Run it first; it produces the raw table for step 3.
