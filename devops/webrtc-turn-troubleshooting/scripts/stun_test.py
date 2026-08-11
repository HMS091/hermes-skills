#!/usr/bin/env python3
"""STUN/TURN UDP 可达性探测：发 STUN Binding Request，收到响应即端口通。
用法: python stun_test.py <host> [port1 port2 ...]   (默认端口 3478 80 443)
注意: 从局域网内测自家公网 IP 走 NAT hairpin，很多路由器不支持，测不通不代表端口转发没配好。
"""
import struct
import socket
import random
import sys


def stun_probe(host: str, port: int, timeout: float = 6.0) -> str:
    cookie = 0x2112A442  # STUN magic cookie
    txid = random.randbytes(12)
    # Binding Request: type=0x0001, len=0, magic cookie, 12B transaction id
    msg = struct.pack('>HHI', 0x0001, 0x0000, cookie) + txid
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(msg, (host, port))
        data, addr = s.recvfrom(2048)
        t = struct.unpack('>H', data[:2])[0]
        return f"UDP {port}: OK type=0x{t:04x} (0x0101=成功) from {addr[0]}"
    except Exception as e:
        return f"UDP {port}: FAIL {type(e).__name__}: {e}"
    finally:
        s.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    host = sys.argv[1]
    ports = [int(p) for p in sys.argv[2:]] or [3478, 80, 443]
    for port in ports:
        print(stun_probe(host, port))
