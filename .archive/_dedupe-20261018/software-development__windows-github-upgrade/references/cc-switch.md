# CC Switch Upgrade Quick Reference

## Install location

```
C:\Users\Administrator\AppData\Local\Programs\CC Switch\cc-switch.exe
```

Portable build — no installer, just replace `cc-switch.exe` and `portable.ini`.

## GitHub repo

- Repo: `farion1231/cc-switch`
- Releases: `https://github.com/farion1231/cc-switch/releases`
- Release API: `https://api.github.com/repos/farion1231/cc-switch/releases/tags/vX.Y.Z`

## Asset naming pattern

| Architecture | Asset name |
|---|---|
| Windows x86_64 | `CC-Switch-vX.Y.Z-Windows-Portable.zip` |
| Windows arm64 | `CC-Switch-vX.Y.Z-Windows-arm64-Portable.zip` |

Download URL template:
```
https://github.com/farion1231/cc-switch/releases/download/vX.Y.Z/CC-Switch-vX.Y.Z-Windows-Portable.zip
```

## Files in Portable zip

- `cc-switch.exe` — main executable (~31-33 MB)
- `portable.ini` — contains `portable=true` marker

## Upgrade checklist

1. Kill running CC Switch: `powershell "Stop-Process -Name cc-switch -Force"`
2. Download right asset for architecture (this machine is x86_64)
3. Backup: copy `cc-switch.exe` → `cc-switch.exe.bak`
4. Extract zip into `C:\Users\Administrator\AppData\Local\Programs\CC Switch\`
5. New `portable.ini` is harmless — only contains `portable=true`
6. Clean up downloaded zip

## Version history (observed)

| Version | Date | Exe size |
|---------|------|----------|
| v3.16.5 | 2026-07-01 | ~30.7 MB |
| v3.19.1 | 2026-07-31 | ~31.2 MB |
