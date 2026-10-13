#!/usr/bin/env python3
"""Enumerate the real tool catalog of a stdio MCP server, before registering it.

Usage:
    python3 mcp_stdio_probe.py -- npx -y some-pkg@1.2.3 mcp
    python3 mcp_stdio_probe.py --json /tmp/catalog.json -- node server.js mcp

Performs the minimum valid handshake (initialize -> notifications/initialized ->
tools/list) and prints the authoritative tool count plus each tool's name and
description. Exits 1 if the server never answers, printing the stderr tail so a
crash-on-startup is distinguishable from a slow one.

Why: vendor READMEs and marketing pages quote stale counts (a repo advertising
68 tools served 170). Enumerate the catalog you are about to register - a wrong
number discredits the rest of the report, and a blind registration costs a
client restart plus a tool table full of calls that only return errors.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

PROTOCOL_VERSION = "2025-06-18"


def probe(argv, timeout):
    """Return (tools_list_result, fatal, stderr_tail) for a stdio server command."""
    proc = subprocess.Popen(
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def send(payload):
        proc.stdin.write(json.dumps(payload) + "\n")
        proc.stdin.flush()

    try:
        send({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "catalog-probe", "version": "1"},
            },
        })
        send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    except (BrokenPipeError, OSError) as exc:
        proc.kill()
        return None, f"could not write to server stdin: {exc}", ""

    catalog, fatal = None, None
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            break  # server exited before answering
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue  # server logging on stdout instead of stderr; harmless
        if msg.get("id") == 1 and "error" in msg:
            fatal = f"initialize -> {msg['error']}"
            break
        if msg.get("id") == 2:
            if "error" in msg:
                fatal = f"tools/list -> {msg['error']}"
            else:
                catalog = msg.get("result") or {}
            break

    proc.kill()
    stderr_tail = (proc.stderr.read() or "").strip()
    return catalog, fatal, stderr_tail


def main():
    ap = argparse.ArgumentParser(description="Enumerate a stdio MCP server's tool catalog.")
    ap.add_argument("--json", dest="json_path", help="also write the raw tools/list result here")
    ap.add_argument("--timeout", type=float, default=90.0, help="seconds to wait for tools/list")
    ap.add_argument("command", nargs=argparse.REMAINDER, help="server command, after --")
    args = ap.parse_args()

    argv = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not argv:
        ap.error("give the server command after --")

    catalog, fatal, stderr_tail = probe(argv, args.timeout)
    if catalog is None:
        print(
            f"FAILED: no tools/list response ({fatal or 'timeout or server exited'})",
            file=sys.stderr,
        )
        if stderr_tail:
            print("stderr tail:", file=sys.stderr)
            for line in stderr_tail.splitlines()[-15:]:
                print("  " + line, file=sys.stderr)
        return 1

    tools = catalog.get("tools", [])
    print(f"TOOL COUNT: {len(tools)}")
    for tool in tools:
        desc = " ".join((tool.get("description") or "").split())[:90]
        print(f"{tool.get('name')}: {desc}")

    if catalog.get("nextCursor"):
        print(
            f"NOTE: paginated - nextCursor={catalog['nextCursor']!r}; "
            "re-query tools/list with params.cursor to see the rest"
        )

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(catalog, handle, indent=2)
        print(f"raw catalog -> {args.json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
