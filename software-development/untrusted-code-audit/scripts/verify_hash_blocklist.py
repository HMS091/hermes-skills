#!/usr/bin/env python3
"""Verify a truncated-hash domain blocklist (sorted N-byte hashes in one file).

Checks structural integrity (entry width, ascending order, duplicates) and
membership of domains you name, in both directions: --block entries must be
present, --allow entries must be absent.

Usage:
  verify_hash_blocklist.py FILE [--hash-bytes 5] [--hash fnv|xxh] \
      [--block d1 d2 ...] [--allow d1 d2 ...]

Defaults match the ESP32 DNS-sinkhole family: FNV-1a 64-bit masked to 40 bits,
little-endian 5-byte entries.
"""
import argparse
import sys

FNV_OFFSET = 0xCBF29CE484222325
FNV_PRIME = 0x100000001B3
U64 = (1 << 64) - 1


def fnv(domain: str, mask: int) -> int:
    h = FNV_OFFSET
    for c in domain.lower().encode():
        h = ((h ^ c) * FNV_PRIME) & U64
    return h & mask


def load_entries(path: str, width: int):
    data = open(path, "rb").read()
    if len(data) == 0:
        sys.exit("FAIL: file is empty")
    if len(data) % width:
        sys.exit(f"FAIL: size {len(data)} is not a multiple of {width} (truncated/corrupt)")
    return data, [int.from_bytes(data[i:i + width], "little") for i in range(0, len(data), width)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--hash-bytes", type=int, default=5)
    ap.add_argument("--block", nargs="*", default=[], help="domains that MUST be present")
    ap.add_argument("--allow", nargs="*", default=[], help="domains that MUST be absent")
    a = ap.parse_args()

    width = a.hash_bytes
    mask = (1 << (width * 8)) - 1
    data, entries = load_entries(a.path, width)
    s = set(entries)

    print(f"file        : {a.path}")
    print(f"bytes       : {len(data):,}")
    print(f"entries     : {len(entries):,} x {width}B ({width * 8}-bit hashes)")
    ascending = all(entries[i] < entries[i + 1] for i in range(len(entries) - 1))
    print(f"sorted asc  : {ascending}")
    print(f"duplicates  : {len(entries) - len(s)}")
    print(f"min / max   : {entries[0]:#x} / {entries[-1]:#x}")

    bad = 0
    if not ascending:
        print("FAIL: not strictly ascending -> on-device binary search silently misses entries")
        bad += 1
    if len(s) != len(entries):
        print("WARN: duplicate entries waste space (harmless to lookup)")

    for d in a.block:
        hit = fnv(d, mask) in s
        print(f"  block {d:32s} {'PRESENT ok' if hit else 'MISSING  <-- list is not what it claims'}")
        bad += 0 if hit else 1
    for d in a.allow:
        hit = fnv(d, mask) in s
        print(f"  allow {d:32s} {'absent  ok' if not hit else 'PRESENT  <-- silent over-block of a real site'}")
        bad += 0 if not hit else 1

    print("RESULT:", "all checks passed" if bad == 0 else f"{bad} problem(s)")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
