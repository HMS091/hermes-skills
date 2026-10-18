#!/usr/bin/env python3
"""Ask a DNS resolver whether it actually blocks a domain.

Answers the only question that matters when someone says "I already run
AdGuard/Pi-hole": is this domain sinkholed, or is the filter doing nothing?

Usage:
  check_dns_blocking.py SERVER domain [domain ...] [--port 53] [--timeout 4]

Verdict per domain:
  BLOCKED   -> 0.0.0.0 / :: / NXDOMAIN / empty answer / REFUSED
  RESOLVED  -> one or more real A records (filter off, or list not enabled)
  NO-REPLY  -> timeout (NOT a block; retry before concluding)
"""
import argparse
import socket
import struct
import sys


def query(server: str, port: int, name: str, timeout: float, tid: int = 0x4242):
    q = struct.pack(">HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    q += b"".join(bytes([len(p)]) + p.encode() for p in name.rstrip(".").split("."))
    q += b"\x00" + struct.pack(">HH", 1, 1)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(q, (server, port))
        d, _ = s.recvfrom(2048)
    except socket.timeout:
        return None, None
    finally:
        s.close()
    if len(d) < 12 or struct.unpack(">H", d[0:2])[0] != tid:
        return None, None
    rcode = d[3] & 0x0F
    ancount = struct.unpack(">H", d[6:8])[0]
    i = 12
    while i < len(d) and d[i]:
        i += d[i] + 1
    i += 5  # zero byte + QTYPE + QCLASS
    ips = []
    for _ in range(ancount):
        if d[i] & 0xC0 == 0xC0:
            i += 2
        else:
            while d[i]:
                i += d[i] + 1
            i += 1
        typ, _cls, _ttl, rdlen = struct.unpack(">HHIH", d[i:i + 10])
        i += 10
        if typ == 1 and rdlen == 4:
            ips.append(".".join(str(b) for b in d[i:i + 4]))
        i += rdlen
    return rcode, ips


def verdict(rcode, ips):
    if rcode is None:
        return "NO-REPLY", "timeout — retry; a timeout is not a block"
    if rcode in (3, 5):
        return "BLOCKED", f"rcode={rcode} ({'NXDOMAIN' if rcode == 3 else 'REFUSED'})"
    if not ips:
        return "BLOCKED", "answered with no A record"
    sink = [ip for ip in ips if ip in ("0.0.0.0", "127.0.0.1")]
    if sink and len(sink) == len(ips):
        return "BLOCKED", f"sinkholed -> {sink[0]}"
    return "RESOLVED", f"real A records: {', '.join(ips[:3])}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("server")
    ap.add_argument("domains", nargs="+")
    ap.add_argument("--port", type=int, default=53)
    ap.add_argument("--timeout", type=float, default=4.0)
    a = ap.parse_args()
    for d in a.domains:
        try:
            rcode, ips = query(a.server, a.port, d, a.timeout)
        except OSError as e:
            print(f"{d:32s} ERROR {e}")
            continue
        state, why = verdict(rcode, ips)
        print(f"{d:32s} {state:9s} {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
