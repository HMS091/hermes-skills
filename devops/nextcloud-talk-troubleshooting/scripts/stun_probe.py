#!/usr/bin/env python3
"""UDP STUN reachability probe — verify a TURN/STUN server port is reachable from the current network.

Usage: python stun_probe.py <host> [port]
Exit 0 + prints STUN type on success; exit 1 on timeout/error; exit 2 on bad args.
Run from a machine OUTSIDE the LAN to test public reachability.
"""
import struct
import socket
import random
import sys


def probe(host, port=3478, timeout=6):
    cookie = 0x2112A442
    txid = random.randbytes(12)
    # STUN Binding request: type=0x0001, len=0x0000, magic cookie, 12-byte txid
    msg = struct.pack('>HHI', 0x0001, 0x0000, cookie) + txid
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(msg, (host, port))
        data, _ = s.recvfrom(2048)
        mtype = struct.unpack('>H', data[:2])[0]
        return True, mtype  # 0x0101 = binding success response
    except socket.timeout:
        return False, None
    finally:
        s.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 3478
    ok, mtype = probe(host, port)
    if ok:
        print(f"STUN OK host={host} port={port} type=0x{mtype:04x}")
        sys.exit(0)
    print(f"STUN FAILED host={host} port={port} (timeout — likely blocked/filtered)")
    sys.exit(1)
