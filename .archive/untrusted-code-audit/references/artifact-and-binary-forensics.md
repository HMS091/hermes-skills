# Artifact & Binary Forensics

Recipes for the parts of an audit that need more than grep: dating a committed binary, proving what an opaque data artifact contains, and checking whether a resolver actually blocks.

## 1. Dating a committed binary (stale-build detection)

The pattern:

```bash
# a) how often is the shipped binary rebuilt?
git log --pretty='%h %ad %s' --date=short -- docs/firmware.bin
# b) when did the security fix land?
git log --pretty='%h %ad %s' --date=short -S "<marker>" -- src/
# c) is the marker inside the binary?
python3 - <<'EOF'
d=open('docs/firmware.bin','rb').read()
for k in ['X-Requested-With','missing CSRF header','CHANGE_ME_WEB_PASSWORD']:
    print(f'{k:26s}', d.count(k.encode()))
EOF
```

Choose markers that are **string literals in the newest code** — header names, error messages, warning text, route paths, default credentials. Compiled-out constants are not reliable markers: an unused `static const char*` may be dropped entirely, so a zero count can mean "optimized away" rather than "absent". Cross-check with a path that is definitely referenced (`web.on("/pause")`, a log line) to distinguish the two.

Positive control: send the same scan at a string you *know* the old build has (boot banner, filename, HTML from the dashboard). If the positive control hits and the new-fix markers miss, the staleness conclusion is solid.

Placeholder check (was it built with real secrets?):

```bash
python3 -c "d=open('fw.bin','rb').read(); [print(k, d.count(k.encode())) for k in ['YOUR_WIFI_SSID','YOUR_API_KEY','CHANGE_ME']]"
```

Placeholder present = built with the example header = no leaked credentials. Placeholder absent *and* no warn-string = either an old build or genuinely baked credentials; resolve which with the git-log date.

## 2. Strings triage

```bash
strings -n 8 fw.bin | grep -iE 'http|\.com|\.net|\.ru|\.xyz|token|webhook|telegram|discord|api' | sort -u
strings -n 6 fw.bin | grep -oE '[a-z0-9][a-z0-9.-]{3,60}\.(com|net|org|io|cn|ru|xyz|top|info|me|cc|dev|app|site|tk|pw|club|link|vip)(:[0-9]+)?' | sort | uniq -c | sort -rn
```

Expected noise: framework source paths (`/home/<user>/.platformio/packages/...`, `//IDF/components/...`) — these also date and fingerprint the build environment. Unexpected: any hostname that is not in the source, especially a bare domain or `*.workers.dev` / `*.duckdns.org` / ngrok host.

Raw-byte scan for IP constants (a 4-byte `IPAddress` literal does not appear as text):

```bash
python3 -c "d=open('fw.bin','rb').read(); [print(s, d.count(s)) for s in (b'\x09\x09\x09\x09', b'\x01\x01\x01\x01', b'\x08\x08\x08\x08')]"
```

Empty byte-scan results are weak evidence (alignment, endianness, merged constants). Report it as "未发现" and lean on the source-level inventory for the actual claim.

## 3. Truncated-hash blocklist verification

Format family: sorted N-byte hashes of domains (FNV-1a truncated, xxhash truncated, …). Checkable properties:

| Check | How | What failure means |
|---|---|---|
| entry width | `size % N == 0` | corrupt/truncated download |
| sorted ascending | walk and compare | binary search on the device silently misses entries |
| duplicates | `len(list) - len(set)` | bloated list, wasted flash |
| true positives | reimplement the hash, check known ad domains | list is not what it claims |
| false positives | check popular benign domains (google, whatsapp, github, local CDNs) | silent over-block of real sites |
| provenance | rebuild from the same upstream lists, intersect | very low overlap = different (or doctored) source |

```bash
python3 scripts/verify_hash_blocklist.py published_blocklist.bin \
  --block doubleclick.net googlesyndication.com criteo.com \
  --allow google.com whatsapp.com github.com apple.com
```

For the FNV-1a/40-bit variant used by ESP32 DNS sinkholes: 64-bit FNV-1a over the lowercase domain, then `& ((1<<40)-1)`, serialized **little-endian, 5 bytes**; matching walks every parent suffix and strips a leading `www.`. Reimplement exactly that before concluding a domain is missing — a byte-order mistake looks exactly like tampering.

Collision math worth quoting instead of hand-waving: birthday bound ≈ n²/2^(b+1); at 40 bits and 537k entries that is ~1 over-blocked domain, at 32 bits and 250k it is ~7. Compare against the alternative design (strings in RAM) rather than against perfection.

## 4. Does the resolver actually block?

```bash
python3 scripts/check_dns_blocking.py 192.168.1.88 doubleclick.net googlesyndication.com google.com github.com
# BLOCKED  = 0.0.0.0 / :: / NXDOMAIN / REFUSED
# RESOLVED = a real A record  -> the filter is off or its lists are not enabled
```

Parsing notes: `ANCOUNT` is bytes 6:8; skip the question by walking labels to the zero byte, then +4 for QTYPE/QCLASS; each answer is `NAME (0xC0 pointer or labels) | TYPE(2) CLASS(2) TTL(4) RDLEN(2) RDATA`. Only TYPE 1 with RDLEN 4 is an A record. A CNAME chain yields several answers — read the *last* A record, and treat an empty answer with RCODE 3 as blocked-by-NXDOMAIN.

Flaky UDP makes spot checks noisy: a timeout is not a block. Retry once, and query 3–5 domains rather than one.

## 5. Severity ranking for findings

| Rank | Class | What the attacker gets |
|---|---|---|
| 🔴 | unauthenticated firmware/OTA write, unverified remote update of executable content | full device takeover |
| 🟠 | default credentials in-repo, TLS verification disabled on a data fetch | LAN attacker swaps/pushes data; MITM |
| 🟡 | plaintext admin + Basic Auth, unauthenticated info endpoints, open provisioning AP, open resolver on :53 | credential sniffing, enumeration, bandwidth abuse |
| ⚪ | unpinned CI actions, floating CDN JS, weak upload validation | supply-chain and silent-failure risk, no immediate takeover |
