#!/usr/bin/env python3
"""Verify a skills.external_dirs entry actually feeds Hermes skill discovery.

Usage:
  python verify-external-dirs.py <external_dir> [local_skills_dir]

Prints names from <external_dir> that are platform-compatible on this OS and
not shadowed by a same-name local skill (Hermes dedupes by name, local wins).
Then grep `hermes skills list` for a few of the printed names — presence in
the list proves the external dir is live. See hermes-skills-sync SKILL.md
step 4 for the `external_dirs: '[]'` string trap (looks empty, is a no-op).
"""
import os
import pathlib
import sys


def _parse_frontmatter(text):
    import re
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}, ""
    fm = {}
    for key, val in re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.MULTILINE):
        fm[key] = val.strip().strip('"').strip("'")
    return fm, ""


def _skill_matches_platform(fm):
    # Minimal fallback: missing platforms = compatible; honor explicit lists.
    raw = fm.get("platforms", "")
    if not raw:
        return True
    import platform
    names = [p.strip().lower() for p in raw.replace("[", "").replace("]", "").split(",") if p.strip()]
    if not names or "all" in names:
        return True
    sys_name = platform.system().lower()
    if sys_name == "darwin":
        sys_name = "macos"
    return sys_name in names


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    ext = pathlib.Path(sys.argv[1]).resolve()
    local_dir = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else _default_local_skills()

    # Prefer Hermes' own parsers when the source tree is available.
    src = pathlib.Path(os.environ.get("HERMES_HOME", "")) / "hermes-agent"
    parse_fm, matches_platform = _parse_frontmatter, _skill_matches_platform
    if src.exists():
        sys.path.insert(0, str(src))
        try:
            from tools.skills_tool import _parse_frontmatter as pf, skill_matches_platform as sp
            parse_fm, matches_platform = pf, sp
        except ImportError:
            pass

    local_names = set()
    for md in local_dir.rglob("SKILL.md"):
        try:
            fm, _ = parse_fm(md.read_text(encoding="utf-8", errors="replace"))
            local_names.add(fm.get("name", md.parent.name).lower())
        except Exception:
            pass

    hits = []
    for md in ext.rglob("SKILL.md"):
        if any(p in md.parts for p in (".git", ".github", ".hub", ".archive")):
            continue
        try:
            fm, _ = parse_fm(md.read_text(encoding="utf-8", errors="replace"))
            if not matches_platform(fm):
                continue  # e.g. macOS-only skills never show on Windows
            name = fm.get("name", md.parent.name)
            if name.lower() in local_names:
                continue  # local-before-external dedup
            hits.append(name)
        except Exception:
            continue

    print(f"external-only + platform-compatible skills: {len(hits)}")
    for n in sorted(hits):
        print(f"  {n}")
    print("Now: `hermes skills list | grep <one of the names above>` — if it appears, external_dirs is live.")


def _default_local_skills():
    home = pathlib.Path(os.environ.get("HERMES_HOME", ""))
    if home.exists():
        return home / "skills"
    if os.name == "nt":
        return pathlib.Path(os.environ.get("APPDATA", "")) / "hermes" / "skills"
    return pathlib.Path.home() / ".hermes" / "skills"


if __name__ == "__main__":
    main()
