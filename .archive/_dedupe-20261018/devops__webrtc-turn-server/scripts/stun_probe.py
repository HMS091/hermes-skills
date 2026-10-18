#!/usr/bin/env python3
"""UDP STUN binding probe — 验证 TURN/STUN 服务器端口是否真的响应协议。

用法:
    python stun_probe.py <host> <port> [port ...]
示例:
    python stun_probe.py 192.168.1.200 3478          # 局域网内验证 coturn 监听
    python stun_probe.py turn.example.com 3478 443   # 多端口
    python stun_probe.py 61.157.253.46 3478           # 公网 IP 可达性（注意 NAT hairpin 限制）

输出 type=0x0101 表示 STUN binding success response，服务正常。
端口开着但无响应（timeout）= 服务可能已停摆（如 Metered Open Relay 2026 实测）。
"""
import struct
import socket
import random
import sys


def stun_bind(host: str, port: int, timeout: float = 6) -> str:
    cookie = 0x2112A442
    txid = random.randbytes(12)
    # STUN Binding Request: type=0x0001, len=0, magic cookie, 12-byte txid
    msg = struct.pack('>HHI', 0x0001, 0x0000, cookie) + txid
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(msg, (host, port))
        data, addr = s.recvfrom(2048)
        t = struct.unpack('>H', data[:2])[0]
        return f"OK type=0x{t:04x} from {addr[0]}"  # 0x0101 = success
    except Exception as e:
        return f"FAIL {type(e).__name__}: {e}"
    finally:
        s.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    host = sys.argv[1]
    for port in map(int, sys.argv[2:]):
        print(f"UDP {host}:{port} -> {stun_bind(host, port)}")
