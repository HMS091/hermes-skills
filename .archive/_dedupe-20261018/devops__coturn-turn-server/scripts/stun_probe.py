#!/usr/bin/env python3
"""STUN binding request 探测脚本 — 验证 TURN/STUN 服务器 UDP 端口是否可达。

用法:
    python stun_probe.py <host> [port]

- port 默认 3478
- 收到 type=0x0101 (binding success response) 即服务器正常响应
- 用于：局域网内验证 coturn 监听正常；公网验证端口转发是否生效
  （注意 NAT hairpin：从局域网测公网 IP 不通≠转发失败，需从真公网测）
"""
import struct
import socket
import random
import sys

host = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
port = int(sys.argv[2]) if len(sys.argv) > 2 else 3478

# STUN binding request: type=0x0001, len=0, magic cookie, 12-byte txid
cookie = 0x2112A442
txid = random.randbytes(12)
msg = struct.pack('>HHI', 0x0001, 0x0000, cookie) + txid

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(8)
try:
    s.sendto(msg, (host, port))
    data, addr = s.recvfrom(2048)
    t = struct.unpack('>H', data[:2])[0]
    if t == 0x0101:
        print(f'OK: STUN success response (0x0101) from {addr[0]}:{addr[1]}')
    else:
        print(f'RESPONSE: type=0x{t:04x} from {addr[0]}:{addr[1]} (非成功响应, 见协议定义)')
    sys.exit(0)
except socket.timeout:
    print(f'TIMEOUT: {host}:{port} 无响应 (UDP 不可达或被防火墙丢弃)')
    sys.exit(1)
except Exception as e:
    print(f'FAILED: {type(e).__name__}: {e}')
    sys.exit(1)
