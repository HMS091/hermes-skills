---
name: hermes-mcp-tool-config
description: >
  Configure MCP servers and third-party tools for Hermes on Windows — install,
  register, troubleshoot, and verify external tool connections. Covers
  cua-driver, browser automation, and any stdio-based MCP server.
version: 1.0.0
platforms: [windows]
metadata:
  hermes:
    tags: [hermes, mcp, tools, setup, configuration, windows]
    category: autonomous-ai-agents
    related_skills: [computer-use, hermes-agent]
---

# Hermes MCP / Tool Configuration (Windows)

## When to use this skill

Load this skill when a user asks you to:
- Install or configure a new Hermes tool (computer-use, cua-driver, etc.)
- Add an MCP server to Hermes (`hermes mcp add`)
- Fix a broken MCP server connection
- Verify that a tool or MCP server is working
- Troubleshoot "tool not found" or "connection failed" errors

## Canonical workflow

### 1. Install the underlying binary first

Most MCP servers need a native binary or npm package. Install it before
registering it with Hermes:

```bash
# cua-driver (computer-use)
hermes computer-use install

# Generic MCP server via npm
npm install -g @some/mcp-server
```

### 2. Register with Hermes via `hermes mcp add`

Use the add command — NOT `hermes config set` — for MCP servers that need
arguments:

```bash
hermes mcp add <name> \
  --command "<full-path-to-binary>" \
  --args arg1 arg2
```

The `--args` flag MUST be the **last** option. It produces a proper YAML list
(`args: [arg1, arg2]`).

### 3. Verify the connection

```bash
hermes mcp test <name>         # connection + tool discovery
hermes mcp list                # should show as ✓ enabled
```

### 4. Start a new session

MCP tools only appear in the next session (`/reset` in chat, or start a new
`hermes` invocation). They do NOT appear mid-conversation.

## Known pitfalls

### `hermes config set` serialises lists as strings

```yaml
# ❌ WRONG — stored as a quoted string, connection fails silently
mcp_servers:
  my-server:
    command: "path\to\binary"
    args: '["mcp"]'    # string, not YAML list
```

**Fix:** remove and re-add with `hermes mcp add`:

```bash
hermes mcp remove <name>
hermes mcp add <name> --command "...<binary>" --args mcp
```

Do NOT use `hermes config set mcp_servers.<name>.args [...]` — the `config set`
command serialises array values as quoted YAML strings.

### `hermes mcp add` requires interactive approval

The tool discovery step prompts "Enable all N tools? [Y/n/select]". To make
it non-interactive, pipe `echo Y |` as a prefix.

### Full path required for Windows stdio servers

Always use the absolute path to the binary. Relative paths or bare names may
not resolve in the MCP server process's environment.

### New session needed after adding/removing tools

MCP server changes and toolset toggles only take effect after `/reset`. If
the user reports a tool is "missing" after configuration, the session hasn't
been restarted.

## Verification checklist

After any MCP tool setup, confirm each item:

- [ ] `hermes mcp list` — server shows as `✓ enabled`
- [ ] `hermes mcp test <name>` — connection succeeds
- [ ] Binary's own health check passes (if available)
- [ ] `/reset` was performed (or new session started)
- [ ] The tool appears in the available tool list
