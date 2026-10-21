#!/usr/bin/env python3
"""Probe a Lightpanda MCP server over stdio: initialize + tools/list.

Run this instead of guessing from config.yaml whether the MCP tools are live.
Prints the tool count and names, then exits non-zero if the server did not
answer. Privacy env vars are forced on so the probe itself never phones home.

Usage: mcp_probe.py [/opt/lightpanda/lightpanda]
"""
import json
import os
import select
import subprocess
import sys

BIN = sys.argv[1] if len(sys.argv) > 1 else "/opt/lightpanda/lightpanda"

env = dict(os.environ)
env["LIGHTPANDA_DISABLE_TELEMETRY"] = "true"
env["LIGHTPANDA_DISABLE_CORE_DUMP"] = "1"

p = subprocess.Popen(
    [BIN, "mcp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
    env=env,
    bufsize=1,
)


def send(obj):
    p.stdin.write(json.dumps(obj) + "\n")
    p.stdin.flush()


def read_one(timeout=25):
    ready, _, _ = select.select([p.stdout], [], [], timeout)
    if not ready:
        return None
    line = p.stdout.readline()
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return {"raw": line[:200]}


send({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "hermes-probe", "version": "1.0"},
    },
})
init = read_one()
if not init or "result" not in init:
    print("FAIL initialize:", json.dumps(init)[:400] if init else "NO RESPONSE")
    p.terminate()
    sys.exit(1)

info = init["result"].get("serverInfo", {})
print(f"initialize OK: {info.get('name')} {info.get('version')} "
      f"proto={init['result'].get('protocolVersion')}")

send({"jsonrpc": "2.0", "method": "notifications/initialized"})
send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
tools = read_one()
if not tools or "result" not in tools:
    print("FAIL tools/list:", json.dumps(tools)[:400] if tools else "NO RESPONSE")
    p.terminate()
    sys.exit(1)

names = [t["name"] for t in tools["result"]["tools"]]
print(f"tools: {len(names)}")
print(", ".join(names))
p.terminate()
