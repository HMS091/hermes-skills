# cua-driver (computer-use) MCP Setup on Windows

Session-specific instructions for the most common Hermes MCP tool install:
setting up cua-driver for computer-use on Windows.

## Full install sequence

### 1. Install the binary

```bash
hermes computer-use install
```

This downloads cua-driver-rs 0.8.3 (or latest), extracts to
`%LOCALAPPDATA%\Programs\Cua\cua-driver\bin\`, updates PATH, and registers
an auto-start service.

### 2. Register the MCP server in Hermes

```bash
echo Y | hermes mcp add cua-driver --command "C:\Users\%USERNAME%\AppData\Local\Programs\Cua\cua-driver\bin\cua-driver.exe" --args mcp
```

`echo Y |` pipes "yes" to the "Enable all 39 tools?" prompt.

### 3. Verify

```bash
hermes mcp test cua-driver
hermes mcp list                                        # should show ✓ enabled
"$env:LOCALAPPDATA/Programs/Cua/cua-driver/bin/cua-driver.exe" health_report   # all ✓ pass
```

### 4. Start a new session

Type `/reset` in the chat, or close and reopen `hermes`. The `computer_use`
tool will be available.

## Result

After setup, the MCP server exposes 39 tools:

| Category | Tools |
|----------|-------|
| Window management | `list_apps`, `list_windows`, `get_window_state`, `launch_app`, `kill_app`, `bring_to_front` |
| Input | `click`, `double_click`, `right_click`, `drag`, `type_text`, `press_key`, `hotkey`, `scroll` |
| Vision | `get_desktop_state`, `get_screen_size`, `zoom`, `get_cursor_position` |
| UI tree | `get_accessibility_tree`, `set_value`, `get_window_state` |
| Agent cursor | `move_cursor`, `set_agent_cursor_*`, `get_agent_cursor_state` |
| Recording | `start_recording`, `stop_recording`, `get_recording_state`, `replay_trajectory` |
| Browser | `page` (CDP-driven web interaction) |
| Diagnostics | `health_report`, `get_config`, `check_permissions`, `debug_window_info` |
