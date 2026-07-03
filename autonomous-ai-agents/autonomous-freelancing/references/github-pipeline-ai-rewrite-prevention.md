# AI Destructive Rewrite Prevention

## Problem
The AI code-generation step in auto-bounty scripts frequently produces complete file rewrites instead of targeted patches. A ~10-line change becomes 842L deleted + 153L added, stripping unrelated functionality.

## Detection (Pre-Commit Check)

```python
def check_destructive_rewrite(files, repo_size_kb):
    """Flag destructive rewrites before committing."""
    for f in files:
        if f["action"] in ("create", "modify"):
            old_lines = count_lines_in_repo(f["path"])
            new_lines = f["content"].count("\n") + 1
            if old_lines > 50 and new_lines < old_lines * 0.3:
                print(f"  ⚠️ DESTRUCTIVE REWRITE: {f['path']} ~{old_lines}→{new_lines} lines")
                return False  # abort
    return True
```

## Prevention (Prompt Engineering)

Add to the AI system prompt:
```
CRITICAL RULE: Make the MINIMAL change to fix the described issue.
Do NOT rewrite entire files unless the issue explicitly asks for it.
A 10-line patch is 10x better than a 500-line rewrite.
Only modify the specific function(s) or line(s) that the issue references.
Preserve ALL existing functionality — features not mentioned in the issue
must remain untouched.
```

## Red Flags Before Submission
- Single-file change with deletions/additions ratio > 3x
- File size reduced >50%
- Commit message says "simplified", "rewritten", "refactored" for a bugfix
