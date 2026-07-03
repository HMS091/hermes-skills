# Bountysource — Platform Assessment

**Status: DEFUNCT** (shut down ~2023)

## Summary

Bountysource was a bounty platform that let users place cash bounties on GitHub issues. It shut down in 2023 and its systems no longer process payouts. However, thousands of old GitHub issues still contain `<bountysource-plugin>` HTML comments in their bodies referencing old bounties.

## Detection Signal

The GitHub issue body contains a hidden HTML comment block like:
```html
<!--
<bountysource-plugin>
---
There is a **[$40 open bounty](https://www.bountysource.com/issues/4376331-...)** on this issue.
</bountysource-plugin>
-->
```

## Why It's a Trap

1. **Stale issue age**: Most Bountysource-linked issues are from 2014-2018
2. **Repo abandonment**: The repos hosting these issues are often unmaintained (last push years ago)
3. **No payout possible**: Even if someone merges a PR, Bountysource cannot pay
4. **False positive in price scanning**: The `$40` shows up in the issue body, making it appear as a real paid bounty to automated scanners

## Example

- **limetext/lime #380** — "$40 — Figure out a way to test the frontends"
  - Created 2014, last comment 2015
  - Bountysource issue #4376331 (defunct)
  - Repo last pushed 2021
  - 7 comments, all design discussion, not coding
  - Verdict: DEAD — skip

## How to Handle

When a bounty scanner finds an issue with a `$` amount:
1. Check the body for `<bountysource-plugin>` — if present, mark as DEAD immediately
2. No need to further evaluate repo health or competition

## Recommendation

Do not scrape, monitor, or evaluate Bountysource-linked issues. They are historical artifacts, not active bounties.
