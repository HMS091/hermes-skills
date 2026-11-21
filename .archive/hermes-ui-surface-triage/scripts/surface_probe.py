#!/usr/bin/env python3
"""Identify which Hermes surface is live on this host.

Read-only. Safe to run while the user is chatting: it only reads /proc.

Prints, for every Hermes TUI / gateway / dashboard process:
  pid, ppid, tty, PTY grid the TUI believes it has (rows cols),
  the TCP ports that process listens on, and its parent's command line.

Reading the output:
  node .../ui-tui/dist/entry.js with the dashboard as parent -> the user is in
  the BROWSER dashboard (xterm.js over the PTY bridge), not a real terminal.
  A wide grid (e.g. '40 170') plus 'text is huge' points at pixel/zoom issues.
"""
import glob
import os
import re
import subprocess


def cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
    except OSError:
        return ""


def ppid_of(pid):
    try:
        with open(f"/proc/{pid}/stat") as f:
            return int(f.read().rsplit(")", 1)[1].split()[1])
    except (OSError, IndexError, ValueError):
        return 0


def fd0(pid):
    try:
        return os.readlink(f"/proc/{pid}/fd/0")
    except OSError:
        return "?"


def pty_size(dev):
    if not dev or dev == "?":
        return "-"
    try:
        out = subprocess.run(
            ["stty", "-F", dev, "size"], capture_output=True, text=True, timeout=3
        ).stdout.strip()
        return out or "-"
    except Exception:
        return "-"


def listening_ports(pid):
    inodes = set()
    for fd in glob.glob(f"/proc/{pid}/fd/*"):
        try:
            target = os.readlink(fd)
        except OSError:
            continue
        if target.startswith("socket:["):
            inodes.add(target[8:-1])
    ports = set()
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path) as f:
                lines = f.read().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            if len(fields) > 9 and fields[9] in inodes and fields[3] == "0A":
                ports.add(int(fields[1].split(":")[1], 16))
    return sorted(ports)


def is_hermes_ui(cl):
    return bool(
        "ui-tui/dist/entry.js" in cl
        or "tui_gateway.entry" in cl
        or re.search(r"\)\s+dashboard\b", cl)
    )


def main():
    found = False
    for entry in sorted(glob.glob("/proc/[0-9]*"), key=lambda p: int(p.rsplit("/", 1)[1])):
        pid = int(entry.rsplit("/", 1)[1])
        cl = cmdline(pid)
        if not cl or not is_hermes_ui(cl):
            continue
        found = True
        parent = ppid_of(pid)
        dev = fd0(pid)
        print(f"pid={pid} ppid={parent} tty={dev} pty[rows cols]={pty_size(dev)}")
        print(f"  cmd   : {cl[:150]}")
        print(f"  listen: {listening_ports(pid) or '-'}")
        if parent:
            print(f"  parent: {cmdline(parent)[:120] or '-'}")
        print()
    if not found:
        print("no Hermes TUI/gateway/dashboard process found (desktop app or messaging surface?)")


if __name__ == "__main__":
    main()
