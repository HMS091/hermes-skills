#!/opt/hermes/.venv/bin/python3
"""检查 smart_bounty_search.py 和 do_bounty.py 的关键修复状态。
用于 cron agent 快速验证修复是否到位。"""
import sys
import os

SCRIPT = "/opt/data/scripts/smart_bounty_search.py"
DO_BOUNTY = "/opt/data/scripts/do_bounty.py"

checks = []

# 1. AUTO_EXEC_MIN_USD
with open(SCRIPT) as f:
   content = f.read()

checks.append(("AUTO_EXEC_MIN_USD = 50", "AUTO_EXEC_MIN_USD = 50" in content))
checks.append(("AUTO_EXEC_MIN_USD = 10 (旧值)", "AUTO_EXEC_MIN_USD = 10" not in content))
checks.append(("MAX_CANDIDATES_PER_TICK", "MAX_CANDIDATES_PER_TICK" in content))
checks.append(("try/except subprocess.TimeoutExpired", 
               "except subprocess.TimeoutExpired" in content or "except Exception" in content))

# 2. do_bounty.py DeepSeek timeout
with open(DO_BOUNTY) as f:
   do_content = f.read()

import re
for m in re.finditer(r'urlopen\(.*?timeout=(\d+)', do_content):
    timeout_val = int(m.group(1))
    checks.append((f"DeepSeek API timeout (do_bounty.py)", timeout_val <= 60))
    checks.append((f"  → actual value: {timeout_val}s", True))
    break

# 3. Temp dirs
import subprocess
result = subprocess.run(
    ["find", "/tmp", "-name", "bounty_*", "-type", "d"],
    capture_output=True, text=True, timeout=5
)
temp_count = len([l for l in result.stdout.strip().split("\n") if l])
checks.append((f"Residual temp dirs (/tmp/bounty_*)", temp_count == 0))
checks.append((f"  → Found {temp_count} dirs", True))

# Print summary
print("=== Fix Status Check ===")
all_pass = True
for name, passed in checks:
    status = "✅" if passed else "❌"
    print(f"  {status} {name}")
    if not passed:
        all_pass = False

print(f"\nResult: {'ALL FIXES APPLIED' if all_pass else 'FIXES STILL NEEDED'}")
