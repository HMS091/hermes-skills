---
name: rea-mcp-setup
description: "Analyze binaries with the REA MCP server (rea-agents)."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [REA, Reverse-Engineering, MCP, Claude-Code, npm]
    related_skills: [claude-code, native-mcp, app-reverse-engineering]
---

# REA MCP server — install + verify (Claude Code)

REA (GitHub `morluto/rea`, npm `rea-agents`, MIT) is a 200+ tool binary/RE analysis MCP server. Unconfigured its tool schemas are ~830k tokens; the two schema-profile env vars below cut that to ~55k.

## Using REA from Hermes (no native MCP tools — do NOT register the full server)

On this box REA is installed globally and registered **only** in Claude Code's user config. Hermes' own `mcp_servers` deliberately excludes it: 207 tools would burn ~55k tokens of schema every turn. Call it on demand instead — zero schema cost, all 207 tools reachable:

```bash
node ~/.hermes/scripts/rea_call.mjs --list <keyword>      # search 207 tool names/descriptions
node ~/.hermes/scripts/rea_call.mjs --schema <tool>       # one tool's input schema
node ~/.hermes/scripts/rea_call.mjs <tool> '<json args>'  # call it (900 s timeout)
```

Verified: `open_binary` on an ELF returns `sha256` matching `sha256sum` in ~150 ms; cold start ~5 s per call. State does not persist between invocations (each call opens and closes a server), so open → analyze → close must happen inside ONE script call when state matters — extend `rea_call.mjs` with a `--script` mode rather than chaining separate CLI calls.

Only register it natively (Hermes `mcp_servers:` + `platform_toolsets`) if a long interactive RE session genuinely needs it, and expect a big per-turn schema bill.

## Install

```bash
node -v            # needs >= 20
npm install -g rea-agents
rea --version      # package bin {rea, rea-agents} -> scripts/rea.mjs
```

Resolve the two absolute paths (npm global bin is often not on PATH):

```bash
node -e "console.log(process.execPath)"    # real node binary, not a shim
npm root -g                                # <prefix>/lib/node_modules
ls $(npm root -g)/rea-agents/scripts/rea.mjs
```

If `<prefix>/bin` is not on PATH, symlink `rea` into `/usr/local/bin` and `chmod +x` the .mjs.

## Register with Claude Code

```bash
claude mcp add-json -s user rea '{"type":"stdio","command":"<ABS_NODE>","args":["<ABS>/rea-agents/scripts/rea.mjs","mcp"],"env":{"REA_MCP_INPUT_SCHEMA_PROFILE":"compact","REA_MCP_OUTPUT_SCHEMA_PROFILE":"off"},"timeout":900000}'
claude mcp get rea      # expect: Status: ✔ Connected
```

Rules:
- `timeout` is per tool call in **milliseconds** (900000 = 15 min hard cap).
- **Never** set `REA_MCP_MAX_RESPONSE_BYTES` below `10485760` — the server then fails at startup and the client only shows a misleading `CONNECTION_CLOSED`.
- Use the real node binary path: a `#!/usr/bin/env node` shim depends on PATH inside the MCP child, which is not guaranteed.

## Verify (machine-checkable)

1. `claude mcp get rea` → `Status: ✔ Connected`.
2. `claude -p "run sleep 14 then reply DONE" --output-format stream-json --verbose --debug-file /tmp/x.log`. Cold start is 5–12 s; at `init` the server is `"status":"pending"` and `mcp__rea__*` count is 0. The CLI's own log line `Dynamic tool loading: 0/N deferred tools included` is the count evidence: `11` before rea connects, `218` after ⇒ **207 rea tools**. `claude -p` never prints a tool list (tool search defers them).
3. End-to-end: prompt the session to `ToolSearch` with query `select:mcp__rea__open_binary`, then call `mcp__rea__open_binary` on a real ELF (`cp /bin/ls ./ls_elf`) and diff the returned `sha256` against `sha256sum`. Random/short byte files are rejected (`target_unavailable` / `unsupported binary format`) — use a well-formed ELF/PE/Mach-O.

Standalone server check without any client: spawn `node <rea.mjs> mcp` with the two env vars, send `initialize` → `notifications/initialized` → paginated `tools/list`, count tools. `initialize` takes ~5 s.

## Pitfalls

- **npm 12 blocks install scripts** (`install-scripts` warning). `@anthropic-ai/claude-code` installs a `claude` symlink that points at `claude.exe` — a 290 MB *Linux* binary in the package, the name is just odd. If the CLI misbehaves, reinstall with `npm install -g --allow-scripts=<pkg> <pkg>`.
- `rea-agents` ships `frida`; its postinstall is blocked the same way, so `require('frida')` throws *Could not locate the bindings file*. Reinstall with `npm install -g --allow-scripts=frida rea-agents`; check via `node -e "console.log(typeof require('frida').getLocalDevice)"` run from the package dir. Never `require('frida/package.json')` — its `exports` map forbids it.
- **`--dangerously-skip-permissions` is refused when running as root** (`cannot be used with root/sudo privileges`). In print mode use `--allowedTools "Bash,ToolSearch,mcp__rea__<tool>"`; that auto-approves exactly those tools.
- Claude Code truncates MCP tool descriptions to 4096 chars (`description truncated from N to 4096`) — harmless.
- No Anthropic login on a headless box? Verification sessions can run against an Anthropic-compatible endpoint, e.g. DeepSeek: `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`, `ANTHROPIC_AUTH_TOKEN=<key>`, `ANTHROPIC_MODEL=deepseek-chat`. The CLI warns `unrecognized_model` (assumes 200k window) but works. Real fix for the user: `claude auth login`.
