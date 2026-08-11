# Session: CC Switch + Codex + DashScope Debugging

## Context

User wanted to use CC Switch to route Codex CLI requests to Qianwen (DashScope) instead of OpenAI. Codex CLI was returning 401 errors when trying to connect to OpenAI's WebSocket endpoint.

## Initial Symptoms

1. **Codex CLI error**:
   ```
   unexpected status 401 Unauthorized: Incorrect API key provided: sk-ws-H.***.NGGg
   url: wss://api.openai.com/v1/responses
   ```

2. **CC Switch logs**:
   ```
   [WARN][cc_switch_lib::proxy::forwarder] [codex] [FWD-003] Provider qianwen 请求失败: 上游 HTTP 404
   ```

## Investigation

### Step 1: Check Codex Config

```bash
cat ~/.codex/config.toml
```

Found:
```toml
model = "qwen3.7-plus"
base_url = "http://127.0.0.1:15721/v1"
wire_api = "responses"  # ← Problem!
```

### Step 2: Check CC Switch Database

```python
import sqlite3, json, os

db_path = os.path.expanduser('~/.cc-switch/cc-switch.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Check providers table
row = conn.execute('SELECT * FROM providers WHERE name = ?', ('qianwen',)).fetchone()
print(json.loads(row['settings_config']))

# Check proxy_live_backup table
row = conn.execute('SELECT * FROM proxy_live_backup WHERE app_type = ?', ('codex',)).fetchone()
print(json.loads(row['original_config']))
```

Both tables had `wire_api = "responses"` in the config.

### Step 3: Test DashScope Directly

```bash
curl -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer <api-key>" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.7-plus","messages":[{"role":"user","content":"hi"}]}'
```

**Result**: Success! DashScope supports `/v1/chat/completions` but NOT `/v1/responses`.

### Step 4: Test CC Switch Proxy

```bash
curl -X POST http://127.0.0.1:15721/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.7-plus","messages":[{"role":"user","content":"hi"}]}'
```

**Result**: 404 error from upstream.

## Root Cause

1. Codex CLI 0.145.0 uses WebSocket-first connection to `/v1/responses`
2. When `wire_api = "responses"`, CC Switch forwards to `/v1/responses` endpoint
3. DashScope doesn't support `/v1/responses`, returns 404
4. CC Switch passes the 404 back to Codex
5. Codex falls back to HTTPS, tries `wss://api.openai.com/v1/responses` directly
6. Uses the CC Switch proxy token (not a real OpenAI key) → 401 Unauthorized

## Fix

Updated `wire_api` from `"responses"` to `"chat"` in both database tables:

```python
import sqlite3, json, os

db_path = os.path.expanduser('~/.cc-switch/cc-switch.db')
conn = sqlite3.connect(db_path)

provider_id = '6bc4439a-69ad-494d-b00a-f8981c7ecef8'

# Update providers table
row = conn.execute('SELECT settings_config FROM providers WHERE id = ?', (provider_id,)).fetchone()
if row:
    config = json.loads(row[0])
    config['config'] = config['config'].replace('wire_api = "responses"', 'wire_api = "chat"')
    conn.execute('UPDATE providers SET settings_config = ? WHERE id = ?',
                (json.dumps(config), provider_id))

# Update proxy_live_backup table
row = conn.execute('SELECT original_config FROM proxy_live_backup WHERE app_type = ?', ('codex',)).fetchone()
if row:
    config = json.loads(row[0])
    config['config'] = config['config'].replace('wire_api = "responses"', 'wire_api = "chat"')
    conn.execute('UPDATE proxy_live_backup SET original_config = ? WHERE app_type = ?',
                (json.dumps(config), 'codex'))

conn.commit()
conn.close()
```

Then restarted CC Switch:
1. Killed the process: `taskkill /F /PID 12264`
2. Launched from Start menu
3. Waited 5 seconds for proxy to start
4. Verified: `netstat -ano | findstr 15721` showed the listener

## Verification

```bash
curl -X POST http://127.0.0.1:15721/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.7-plus","messages":[{"role":"user","content":"hi"}]}'
```

**Result**: Success! Response from Qianwen model.

## Key Learnings

1. **CC Switch has two config layers**: `providers` (source of truth) and `proxy_live_backup` (live config). Both must be updated.
2. **`wire_api` setting is critical**: Third-party providers (DashScope, DeepSeek, etc.) typically only support `/v1/chat/completions`, not OpenAI's `/v1/responses`.
3. **Always test the proxy directly with curl** before testing through Codex CLI.
4. **Always test the upstream directly** to verify it's reachable and supports the endpoint.
5. **Restart CC Switch after config changes** — the proxy loads config into memory on startup.

## Provider Compatibility

| Provider | Supports `/v1/responses`? | Supports `/v1/chat/completions`? | Recommended `wire_api` |
|----------|---------------------------|----------------------------------|------------------------|
| OpenAI | ✓ | ✓ | `"responses"` |
| DashScope (Qianwen) | ✗ | ✓ | `"chat"` |
| DeepSeek | ✓ (partial) | ✓ | `"chat"` (safer) |
| Kimi | ✗ | ✓ | `"chat"` |

## Files Modified

- `~/.cc-switch/cc-switch.db` — Updated `wire_api` in `providers` and `proxy_live_backup` tables
- CC Switch process — Restarted to apply config changes

## Time Spent

~30 minutes of debugging and testing.
