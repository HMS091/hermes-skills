#!/usr/bin/env python3
"""Audit a Hermes skills library: duplicate candidates, dangling related_skills, stale copies.

Read-only. Nothing is moved; this only prints evidence so a dedupe pass starts from data
instead of eyeballing 200 skill descriptions.

Usage:
    python3 skills_library_audit.py [SKILLS_DIR] [--seed SEED_DIR] [--threshold 0.45]

Defaults: SKILLS_DIR=$HERMES_HOME/skills (or /opt/data/skills), SEED_DIR=/opt/hermes/skills.

Sections
  1. counts           total live skills, nested ones, zero-use skills from .usage.json
  2. pairs            token-set Jaccard > threshold (frontmatter stripped; interpret against the
                      0.33-0.45 shared-template baseline before calling anything a duplicate)
  3. dangling         related_skills entries that resolve to no live skill (+ alias suggestions)
  4. drift            live-vs-seed same-name pairs whose version regressed or whose body diverged
"""
import argparse, difflib, glob, itertools, json, os, re, sys

ALIAS = {
    "vllm": "serving-llms-vllm",
    "gguf": "llama-cpp",
    "huggingface-tokenizers": "huggingface-hub",
    "audiocraft": "audiocraft-audio-generation",
}
TOKEN = re.compile(r"[a-z\u4e00-\u9fff]{4,}")

def read(p):
    return open(p, encoding="utf-8", errors="replace").read()

def front(t):
    m = re.match(r"^---\s*\n(.*?)\n---", t, re.S)
    return m.group(1) if m else ""

def body(t):
    e = t.find("\n---", 3) if t.startswith("---") else -1
    return t[e + 4:] if e > 0 else t

def field(t, key):
    m = re.search(r"^%s:\s*(.+)$" % key, front(t), re.M)
    return m.group(1).strip().strip('"\'') if m else ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skills_dir", nargs="?", default=os.environ.get("HERMES_SKILLS", "/opt/data/skills"))
    ap.add_argument("--seed", default="/opt/hermes/skills")
    ap.add_argument("--threshold", type=float, default=0.45)
    a = ap.parse_args()
    D = os.path.abspath(a.skills_dir)
    if not os.path.isdir(D):
        sys.exit("not a directory: %s" % D)

    paths = [p for p in glob.glob(D + "/**/SKILL.md", recursive=True) if "/.archive/" not in p]
    skills = {}
    nested = []
    for p in paths:
        rel = p[len(D) + 1:-len("/SKILL.md")]
        t = read(p)
        name = field(t, "name") or os.path.basename(os.path.dirname(p))
        skills[name] = {"rel": rel, "path": p, "text": t}
        parent = os.path.dirname(rel)
        if parent and os.path.exists(os.path.join(D, parent, "SKILL.md")):
            nested.append(rel)

    usage = {}
    up = os.path.join(D, ".usage.json")
    if os.path.exists(up):
        raw = json.load(open(up, encoding="utf-8"))
        usage = raw.get("skills", raw)

    print("== 1. counts ==")
    print("live skills: %d   nested (parent also a skill): %d" % (len(skills), len(nested)))
    for n in nested:
        print("   nested: %s" % n)
    zero = [n for n in skills if isinstance(usage.get(n), dict) and not usage[n].get("use_count")]
    print("zero-use in .usage.json: %d (prune candidates, strongest signal)" % len(zero))

    print("\n== 2. similar pairs (Jaccard > %.2f) ==" % a.threshold)
    docs = {n: set(TOKEN.findall(body(s["text"]).lower())) for n, s in skills.items()}
    pairs = []
    for x, y in itertools.combinations(sorted(docs), 2):
        if not docs[x] or not docs[y]:
            continue
        j = len(docs[x] & docs[y]) / len(docs[x] | docs[y])
        if j > a.threshold:
            pairs.append((round(j, 2), skills[x]["rel"], skills[y]["rel"]))
    for row in sorted(pairs, reverse=True):
        print("   %-5s %-55s %s" % row)
    if not pairs:
        print("   none")
    print("   (1.00 = literal copy; 0.6-0.9 = two rewrites; 0.33-0.45 = shared template, often NOT duplication)")

    print("\n== 3. dangling related_skills ==")
    bad = 0
    for n, s in sorted(skills.items()):
        m = re.search(r"related_skills:\s*\[([^\]]*)\]", s["text"])
        if not m:
            continue
        for r in [x.strip().strip('"\'') for x in m.group(1).split(",") if x.strip()]:
            if r in skills:
                continue
            bad += 1
            hint = ALIAS.get(r)
            print("   %-40s -> %-32s %s" % (n, r, ("alias -> " + hint) if hint else "drop"))
    print("   total dangling: %d" % bad)

    if os.path.isdir(a.seed):
        print("\n== 4. live-vs-seed drift ==")
        for p in glob.glob(a.seed + "/**/SKILL.md", recursive=True):
            t = read(p)
            name = field(t, "name")
            live = skills.get(name)
            if not live:
                continue
            v_seed, v_live = field(t, "version"), field(live["text"], "version")
            sim = difflib.SequenceMatcher(None, body(live["text"]), body(t)).ratio()
            if sim < 0.97 or (v_seed and v_live and v_seed != v_live):
                flag = "SEED NEWER" if (v_seed and v_live and v_seed > v_live) else ""
                print("   %-38s live v%-8s seed v%-8s sim=%.2f %s" % (name[:38], v_live or "?", v_seed or "?", sim, flag))
        print("   (refresh only when seed version is strictly higher AND sim > 0.90 = pure upstream drift)")

    print("\nnext: read the candidate pairs, run the cross-reference test in references/library-dedupe-and-prune.md §2,")
    print("      then archive (never rm) with a MERGED-INTO.txt and verify count delta via `hermes skills list`.")

if __name__ == "__main__":
    main()
