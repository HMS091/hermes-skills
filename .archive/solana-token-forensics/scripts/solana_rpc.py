#!/usr/bin/env python3
"""Minimal Solana RPC helpers for token forensics. No API key, public mainnet RPC.

Usage:
    from solana_rpc import rpc, sigs, all_sigs, tx, sol_delta, token_delta, b58

Keep concurrency at 2-3 threads; the public endpoint 429s above that.
"""
import json
import time
import urllib.request

RPC_URL = "https://api.mainnet-beta.solana.com"
_id = [0]
_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58(raw: bytes) -> str:
    n = int.from_bytes(raw, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = _ALPHABET[r] + out
    return "1" * (len(raw) - len(raw.lstrip(b"\x00"))) + out


def rpc(method: str, params: list, tries: int = 5, url: str = RPC_URL):
    """JSON-RPC call with backoff. Raises after `tries` attempts."""
    last = None
    for attempt in range(tries):
        _id[0] += 1
        body = json.dumps({"jsonrpc": "2.0", "id": _id[0], "method": method,
                           "params": params}).encode()
        try:
            req = urllib.request.Request(url, data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as resp:
                payload = json.loads(resp.read())
            if "result" in payload:
                return payload["result"]
            last = payload
        except Exception as exc:  # 429, timeout, truncated body
            last = exc
        time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"rpc {method} failed: {last}")


def sigs(address: str, limit: int = 1000, before: str | None = None,
         until: str | None = None) -> list:
    """Newest-first signatures (no reverse cursor: -1 is the oldest in the page)."""
    opts: dict = {"limit": limit}
    if before:
        opts["before"] = before
    if until:
        opts["until"] = until
    return rpc("getSignaturesForAddress", [address, opts])


def all_sigs(address: str, cap: int = 20000) -> list:
    """Page back to wallet creation. Fine for wallets; never for a live mint (50k tx/day)."""
    out, before = [], None
    while len(out) < cap:
        page = sigs(address, 1000, before)
        if not page:
            break
        out.extend(page)
        before = page[-1]["signature"]
        if len(page) < 1000:
            break
    return out


def tx(signature: str):
    """Parsed tx. maxSupportedTransactionVersion=1 is mandatory: version-1 txs error with -32015."""
    return rpc("getTransaction", [signature, {
        "encoding": "jsonParsed",
        "maxSupportedTransactionVersion": 1,
        "commitment": "confirmed",
    }])


def sol_delta(t: dict, account: str) -> float:
    """SOL change for `account` inside one tx (fee included, as the chain sees it)."""
    keys = [k["pubkey"] for k in t["transaction"]["message"]["accountKeys"]]
    if account not in keys:
        return 0.0
    i = keys.index(account)
    return (t["meta"]["postBalances"][i] - t["meta"]["preBalances"][i]) / 1e9


def token_delta(t: dict, owner: str, mint: str) -> float:
    """UI-amount change of `mint` for `owner` inside one tx."""
    delta = 0.0
    for b in t["meta"].get("postTokenBalances", []):
        if b.get("owner") == owner and b.get("mint") == mint:
            delta += b["uiTokenAmount"]["uiAmount"] or 0.0
    for b in t["meta"].get("preTokenBalances", []):
        if b.get("owner") == owner and b.get("mint") == mint:
            delta -= b["uiTokenAmount"]["uiAmount"] or 0.0
    return delta


def instruction_names(t: dict) -> list:
    """Anchor programs leave parsed=null; the log lines are the classifier."""
    return [line.split("Instruction: ")[-1]
            for line in (t["meta"].get("logMessages") or [])
            if "Instruction: " in line]


def token_deltas_by_owner(t: dict, mint: str) -> dict:
    """Every owner's net change of `mint` in one tx — used to spot same-slot bundles."""
    out: dict = {}
    for side, sign in (("postTokenBalances", 1), ("preTokenBalances", -1)):
        for b in t["meta"].get(side, []):
            if b.get("mint") == mint:
                out[b["owner"]] = out.get(b["owner"], 0.0) + sign * (b["uiTokenAmount"]["uiAmount"] or 0.0)
    return {k: v for k, v in out.items() if abs(v) > 0.01}


if __name__ == "__main__":
    import sys
    target = sys.argv[1]
    page = sigs(target, 10)
    print(json.dumps(page, indent=2)[:2000])
    print("balance/lamports:", rpc("getBalance", [target])["value"])
