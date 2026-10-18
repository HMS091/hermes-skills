---
name: untrusted-code-audit
description: "Vet third-party code/firmware for backdoors before use."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [security, audit, backdoor, firmware, supply-chain, github]
    related_skills: [open-source-discovery, requesting-code-review, app-reverse-engineering, systematic-debugging]
prerequisites:
  commands: [git, python3, strings]
---

# Untrusted Code / Firmware Audit

Someone hands you a repo, a release binary, or an "install this" gadget and asks: **这是什么、有没有后门、安不安全、我能不能用**. The job is not "does it look sketchy" — it is to inventory every outbound channel, date every committed binary, verify every artifact the project ships, and then separate three different questions the user is collapsing into one:

1. **作者有没有恶意** (backdoor / exfiltration / telemetry)
2. **能不能被攻破** (exploitable weakness in the shipped build)
3. **靠不靠得住** (fragility, single point of failure, silent failure modes)

Answering only #1 and calling it "safe" is the failure this skill exists to prevent.

## When to Use

- "帮我看看这个有没有后门 / 安不安全"
- User is about to flash firmware, run a stranger's binary, or add a stranger's container to their NAS
- User bought / is considering cheap source code and wants it vetted before deploy
- A repo ships prebuilt binaries (firmware.bin, docs/*.bin, releases) that you would be trusting

If the question is "is this project any good / still alive" → `open-source-discovery` (viability assessment). If it is "review my own diff" → `requesting-code-review`.

When the verdict is "safe, but the wrong layer for what they actually want" — a DNS sinkhole or an ESP32 box when the real goal is YouTube ads — hand off to `network-ad-blocking` instead of stretching this report into a buying/deployment recommendation.

## Procedure

### 1. Clone and size it up before reading

```bash
cd $BH_AGENT_WORKSPACE && git clone --depth 50 <url> && cd <repo>
find . -path ./.git -prune -o -type f -print | sort
wc -l src/* tools/* 2>/dev/null
git log --pretty='%h %ad %s' --date=short | head -30
```

A 600–1500 line codebase is readable end to end — **do read it whole**, in two or three `read_file` calls. Skimming and grepping only finds the backdoors the author did not hide well. Note every non-source artifact: `docs/*.bin`, `firmware.bin`, `.stl`, release assets, web-installer manifests.

### 2. Inventory every outbound channel

```bash
# URLs (drop docs/badge/CDN noise)
grep -rInE "https?://[^\"' )]+" --exclude-dir=.git . | grep -vE "w3.org|schema|shields.io|unpkg|badge"
# IPC / exec / encode primitives
grep -rInE "base64|atob\(|eval\(|fromCharCode|os\.system|subprocess|system\(" --exclude-dir=.git .
# network sinks in any language
grep -rInE "beginPacket|HTTPClient|http\.begin|requests\.(get|post)|fetch\(|net\.connect|socket\(" --exclude-dir=.git . | head -30
```

Present this as a table the user can check line by line: **出站行为 | 位置 file:line | 判定**. A backdoor hides as one more `http.begin()` among ten; the table is what makes "only three outbound channels exist" a claim you can defend. Zero external hostnames in the binary strings is a *strong negative finding* — state it as evidence, not as a feeling.

Do not put destructive-command literals (`rm -rf`, etc.) inside a grep pattern: the terminal hardline guard blocks the entire call and you lose the scan. Enumerate `os.system`/`subprocess`/`exec` instead.

### 3. Date every committed binary — the highest-yield check

Repos that ship a prebuilt binary for a "one-click install" almost never rebuild it. Compare the binary's last commit against the commits that added security fixes:

```bash
git log --oneline -- docs/firmware.bin docs/littlefs.bin    # how many commits touch it?
git log --oneline -S "<marker string from the newest security fix>" -- src/ | head
git log --oneline -S "<symbol from a feature added last month>" -- src/ | head
```

Then count those markers inside the binary:

```bash
python3 - <<'EOF'
d=open('docs/firmware.bin','rb').read()
for k in ['X-Requested-With','missing CSRF header','CHANGE_ME','<a string only the fixed code contains>']:
    print(f'{k:24s}', d.count(k.encode()))
EOF
```

All zeros = the shipped binary predates those commits. Cross-check dates: binary committed earlier than the auth fix ⇒ **the download users are told to flash has no authentication**, even though the source looks fixed. This is the finding that matters most to a non-coder user, and git-log-plus-marker-count is the only cheap way to prove it.

Also check whether the binary was built with real secrets: a placeholder like `YOUR_WIFI_SSID` still present is reassuring (no baked-in credentials); a *missing* placeholder plus no example value means credentials may be compiled in — flag it.

### 4. Strings triage of the binary

```bash
strings -n 6 fw.bin | grep -oE "[a-z0-9][a-z0-9.-]{3,60}\.(com|net|org|io|xyz|ru|cn|top|info|me|cc|dev|app|site|tk|pw|club|link|vip)(:[0-9]+)?" | sort | uniq -c | sort -rn | head -40
strings -n 7 fw.bin | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | sort | uniq -c
```

Any hostname/IP that does not appear in the source is a backdoor candidate — chase it. But IP constants may be compiled as four raw bytes (`IPAddress(9,9,9,9)` → `b'\x09\x09\x09\x09'`), so an empty literal scan is **not** proof of "no hardcoded IP"; say so rather than overclaiming.

**State the limit explicitly:** without rebuilding you cannot prove a prebuilt binary matches the source. Give the mitigation you can defend — 自己从源码编译，或对比重编产物的 sha256 — and rank "用官方一键刷机" below it.

### 5. Git history hygiene

```bash
git log --all --oneline --name-only -- '*secret*' '*env*' '*cred*' | head -20
git log --diff-filter=D --name-only --oneline | head -20      # deleted files hide history
git log --format='%an <%ae>' | sort | uniq -c | sort -rn      # single-author vs community
```

Gitignored secrets that were never committed is a good sign; say it in one line. Deleted-then-recommitted files are worth a diff read.

### 6. Verify the artifacts the project publishes

Anything the device pulls at runtime (blocklist, model, ruleset, config) is an attack surface and its integrity is checkable. Recipe collection: `references/artifact-and-binary-forensics.md`.

- **Sorted/truncated data (hash lists, bloom filters):** check file size is an exact multiple of the entry width, strictly ascending order, zero duplicates, then reimplement the key function and spot-check it.
- **Spot-check both directions:** known-bad entries must be present (true positives) *and* popular benign entries must be absent (no silent over-block). Run `scripts/verify_hash_blocklist.py`.
- **Overlap with the claimed sources:** rebuild from the same upstream lists and compare set intersection. High overlap (~80%+) confirms provenance; drift is expected because source lists change daily.
- **Note what the format hides:** a truncated hash list cannot be audited for *which* domains it contains, only for *how many* and *whether known ones match*. Say that instead of pretending you read the list.

### 7. Threat surface of the thing itself

| Surface | What to check | Why it matters |
|---|---|---|
| 状态变更接口 | auth + CSRF on every mutating route (`/update`, `/upload`, `/set*`, `/forget*`) | unauthenticated reflash = full device takeover, not a nuisance |
| 默认凭据 | placeholder password still in the example header | a password that lives in the repo is public |
| TLS on fetches | `setInsecure()`, `verify=False`, `CERT_NONE` | MITM can swap the data artifact; **impact is data-only unless the fetched blob is executed** — say which |
| 传输加密 | plaintext HTTP admin + Basic Auth | base64, sniffable on the LAN; LAN-trust only |
| 只读泄露 | unauthenticated `/stats`, `/health`, debug endpoints | client IP/MAC enumeration |
| 配网/首次开机窗口 | open AP, no password on the provisioning portal | nearby attacker can re-provision or capture the WiFi password |
| 开放解析器 | :53 answering from WAN | DNS amplification abuse |
| 输入校验 | upload accepts "size % N == 0" only | truncated/corrupt data silently accepted → silent partial function, no error |
| 单点故障 | does the whole LAN depend on this device's uptime? | one cheap dongle dies, house loses DNS |

### 8. Supply chain

- GitHub Actions pinned to `@v4` tags rather than SHAs — upstream tag can move; report once, low severity.
- A workflow with `contents: write` that publishes the artifact devices auto-pull: compromise of the maintainer account ships bad data to every device. Weight it by what the artifact can do (hashes → over-block only; code → RCE).
- Web installer / dashboard pulling JS from a CDN with a floating major (`esp-web-tools@10?module`): third-party JS gets to touch the flasher.
- Independent press (Tom's Hardware, XDA, ...) is legitimacy evidence for "is this a scam repo", **not** security evidence. Search for it when star count looks implausible; never cite it as an audit result.

### 9. Answer the deployment question with the user's real hardware

When the ask is "能不能用软路由/NAS 实现", do not answer from theory and do not recommend a purchase first:

```bash
curl -sI --max-time 6 http://<nas-ip>:<port>/ | head -5     # dashboards, redirects
# then prove the service actually does its job — a login page is not a working filter
python3 scripts/check_dns_blocking.py <resolver-ip> doubleclick.net googleadservices.com google.com github.com
```

A filter running but not blocking is the common case (lists not enabled), and it is worth more to the user than any hardware advice. Compare in a table: **他已有的 vs 要买的那台** — 成本(0 优先)、容量、是否支持正则/白名单/DoH/缓存/分设备策略、功耗、单点故障、有线还是 2.4G 单链路。Then state the ceiling of the whole approach (DNS filtering cannot block in-feed/video ads that share the content domain) so the recommendation does not read as a magic fix.

## Report Shape (this user)

Chinese, 结论先行, tables over prose, every claim carrying a number or a `path:line`:

1. **一、结论** — 4–6 row table: 有后门吗 / 代码质量 / 安全性 / 能否跑在我的设备上. Verdict words, not adjectives.
2. **二、它到底是什么** — the mechanism in ≤10 lines, plus the honest limitation of the approach.
3. **三、后门审计** — outbound channel table with file:line + what the binary strings showed + git history result + artifact integrity numbers.
4. **四、问题（按严重程度）** — 🔴/🟠/🟡, each with location, mechanism, blast radius, and the concrete fix. Rank by what an attacker gets (RCE > device takeover > MITM data swap > info leak > DoS).
5. **五、能不能用软路由/NAS 实现** — 实测结果 of their existing gear, then the comparison table, then "对你没有任何性价比" if that is the truth.
6. **六、建议** — one immediately executable next step (e.g. "don't use the web installer; build from source with real passwords").

Never soften a serious finding to be polite, and never inflate a low-severity one for drama. Both destroy the report's credibility with this user.

## Pitfalls

1. **"No backdoor found" ≠ "safe"** — report malicious intent, exploitable weakness, and fragility as three separate verdicts. A spotless source tree with an unauthenticated `/update` endpoint is still a device anyone on the LAN can own.
2. **Prebuilt binaries go stale silently** — the README's feature list describes `main`, the download is whatever commit last touched `docs/*.bin`. Date the binary first; it is a two-command check with the largest payoff.
3. **Rate the TLS finding honestly** — `setInsecure()` on a data fetch is MITM (over-block/DoS), not code execution. Calling it "后门" wastes your credibility on the finding that actually matters.
4. **A running service is not a working service** — probe it with a real blocked-domain query before telling the user "你已经有了，直接用". Their AdGuard can answer :53 all day and still return real IPs for doubleclick.net.
5. **Verify artifacts both ways** — only checking that ad domains are blocked hides a list that also kills `whatsapp.com`/`github.com`. Always run benign domains too.
6. **Don't put destructive-command literals in grep patterns** — the hardline guard blocks the whole call; scan for `eval`/`subprocess`/`os.system` instead.
7. **Cloning into the workspace and reading it whole beats clever greps** — for anything under ~2k lines, grep misses intent; comments in these repos often name the vulnerability they fixed, which is how you date the binary.
8. **Don't recommend hardware before checking what they already run** — probe NAS ports/containers and router first; a price-sensitive user will not thank you for a $20 dongle that duplicates a service they already own and never configured.

## References

- `references/artifact-and-binary-forensics.md` — strings/marker recipes, blocklist integrity verification, DNS reply parsing.
- `scripts/verify_hash_blocklist.py` — check a truncated-hash blocklist (sorted, dupes, membership spot-checks).
- `scripts/check_dns_blocking.py` — ask a resolver whether it really blocks a domain.
