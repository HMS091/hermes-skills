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

## Using REA from Hermes (registered natively — cheap, because of tool search)

REA is registered in BOTH clients on this box:

| Client | Where | Tools |
|---|---|---|
| Claude Code | `~/.claude.json` (user scope) | `mcp__rea__*`, 207 |
| Hermes | `config.yaml → mcp_servers.rea` + `platform_toolsets.cli` | `mcp__rea__*`, **209** (207 tools + `list_prompts` / `get_prompt` prompt accessors) |

Hermes' Tool Search assembly keeps only ~21 tools inline (~12k tokens) and defers the rest, so 209 REA tools cost **~0 tokens per turn** (raw would be ~70k). They are pulled on demand via `tool_search` → `tool_describe` → `tool_call`. In a Claude Code session the equivalent is `ToolSearch` + `select:mcp__rea__<tool>`.

Registering (Hermes) — the prompt is interactive, so pipe the answer:

```bash
cd /opt/data && export HERMES_HOME=/opt/data
printf 'Y\n' | /opt/hermes/.venv/bin/hermes mcp add rea \
  --command /opt/hermes/tools/node-26.7.0-linux-x64/bin/node \
  --connect-timeout 120 \
  --env REA_MCP_INPUT_SCHEMA_PROFILE=compact REA_MCP_OUTPUT_SCHEMA_PROFILE=off \
  --args /opt/hermes/tools/node-26.7.0-linux-x64/lib/node_modules/rea-agents/scripts/rea.mjs mcp
/opt/hermes/.venv/bin/hermes config set mcp_servers.rea.timeout 900   # add sets no timeout (default 120 s!)
```

`hermes mcp add` writes `207/207 tools enabled` and needs a **new session** (or `/reload-mcp`) to go live. Verify without a model call:

```bash
HERMES_HOME=/opt/data /opt/hermes/.venv/bin/python -c "
import os,sys; sys.path.insert(0,'/opt/hermes')
from tools.mcp_tool_discovery import discover_mcp_tools
n=discover_mcp_tools(); print(len([x for x in n if x.startswith('mcp__rea__')]))"   # -> 209
```

On-demand single call, no session needed (all 209 reachable, zero schema cost):

```bash
node ~/.hermes/scripts/rea_call.mjs --list <keyword>      # search tool names/descriptions
node ~/.hermes/scripts/rea_call.mjs --schema <tool>       # one tool's input schema
node ~/.hermes/scripts/rea_call.mjs <tool> '<json args>'  # call it
```

State does not persist between separate `rea_call.mjs` invocations (each spawns and drops a server); multi-step open→analyze→close belongs in one script. Native tools inside a live Hermes session do persist.

## Keeping it updated (cron)

`/opt/data/scripts/rea_update_apply.sh` (cron, `no_agent`, job id `1b71bc2f4ef2`, daily `0 1 * * *` = 09:00 Beijing, deliver=all) runs `rea_update_check.sh`:

1. compares `rea --version` against `npm view rea-agents version`;
2. if newer, `npm install -g --allow-scripts=frida rea-agents@<latest>`;
3. self-tests: version matches AND `rea_call.mjs --list` still reports ≥200 tools;
4. on any failure, re-installs the previous version (rollback);
5. on success, deletes `/opt/data/cache/mcp_schema_cache.json` so the next Hermes session re-discovers tools.

Run it by hand any time: `/opt/data/scripts/rea_update_apply.sh` (add nothing for a report-only pass: `/opt/data/scripts/rea_update_check.sh`). Log: `/opt/data/logs/rea-update.log`.

Cron scripts must live in `/opt/data/scripts/` (absolute paths are rejected); the wrapper exists because cron cannot pass arguments.

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
- **Claude Code truncates MCP tool descriptions** to 4096 chars (`description truncated from N to 4096`) — harmless.
- **The agent's `write_file`/`patch` refuse `config.yaml`** (`Refusing to write to Hermes config file`). Route every MCP/config change through `hermes mcp add|remove` and `hermes config set` — never hand-edit.
- **209 ≠ 207**: Hermes also registers the server's MCP *prompts* as `mcp__rea__list_prompts` / `get_prompt`. The Claude Code tool count stays 207.
- No Anthropic login on a headless box? Verification sessions can run against an Anthropic-compatible endpoint, e.g. DeepSeek: `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`, `ANTHROPIC_AUTH_TOKEN=<key>`, `ANTHROPIC_MODEL=deepseek-chat`. The CLI warns `unrecognized_model` (assumes 200k window) but works. Real fix for the user: `claude auth login`.
