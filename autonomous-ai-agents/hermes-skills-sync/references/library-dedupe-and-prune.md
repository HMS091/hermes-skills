# Skills Library Dedupe & Prune — Recipes

Operational depth for the `Identity Duplicates` and `Pruning a Whole Pack` sections of SKILL.md.
Everything here is stdlib Python run against the live skills dir (`$HERMES_HOME/skills`, here `/opt/data/skills`).

## 0. Read the library's real shape first

- `$HERMES_HOME/skills` is the **live** dir; `/opt/hermes/skills` is the bundled **seed** that `hermes update`
  reinstalls from. Same-name pairs across the two are *not* duplicates to delete — the live copy shadows the seed.
  A live copy whose version is *older* than its seed is stale: refresh it from the seed (see §5).
- Usage truth lives in `$HERMES_HOME/skills/.usage.json` (`skills.<name>.use_count`). Zero-use is the strongest
  signal for pruning; mutual cross-references are the strongest signal *against* deduping.
- Nested `SKILL.md` (e.g. `computer-use/desktop-investigation/`) is a legitimately separate skill — count it, don't
  treat the nesting as a duplicate.

## 1. Find candidate pairs (Jaccard over bodies)

`scripts/skills_library_audit.py` does this; the core loop strips frontmatter so tags don't inflate overlap:

```python
import glob, re, itertools
D = "/opt/data/skills"
docs = {}
for p in glob.glob(D + "/**/SKILL.md", recursive=True):
    if "/.archive/" in p: continue
    t = open(p, encoding="utf-8", errors="replace").read()
    if t.startswith("---"):
        e = t.find("\n---", 3); t = t[e+4:] if e > 0 else t
    docs[p[len(D)+1:-9]] = set(re.findall(r"[a-z\u4e00-\u9fff]{4,}", t.lower()))
for a, b in itertools.combinations(sorted(docs), 2):
    j = len(docs[a] & docs[b]) / len(docs[a] | docs[b])
    if j > 0.30: print(round(j, 2), a, b)
```

Read the scores against their baseline, not against zero:

| Score | Meaning |
|---|---|
| 1.00 | literal copy (nested-dir accident) → archive the variant with fewer support files |
| 0.6–0.9 | same content, two rewrites → keep one, fold unique files in |
| 0.33–0.45 | **usually shared template, not duplication** — one author's pack boilerplate scores here for unrelated skills |

## 2. Separate "layered" from "duplicate" with the cross-reference test

```bash
for s in A B; do echo -n "$s: "; grep -c '<other-name>' $HERMES_HOME/skills/<cat>/$s/SKILL.md; done
```

- Mutual (1..8 each way) → router + component by design (`pol-probe-advisor` → `pol-probe`, `lifecycle-play-advisor`
  → `product-lifecycle-plays`, `user-story-mapping-workshop` → `user-story-mapping`). **Keep both.**
- One-way or zero, same output artifact → duplicate. Archive.
- Descriptions overlapping is not evidence; only the bodies and the reference direction are.

## 3. Archive (never `rm`), preserving unique support files

```python
import os, shutil, datetime
D, ARC = "/opt/data/skills", "/opt/data/skills/.archive/_dedupe-" + datetime.date.today().isoformat()
os.makedirs(ARC, exist_ok=True)
def archive(rel, reason):
    src, dst = os.path.join(D, rel), os.path.join(ARC, rel.replace("/", "__"))
    if os.path.exists(dst): shutil.rmtree(dst)
    shutil.move(src, dst)
    open(os.path.join(dst, "MERGED-INTO.txt"), "w").write(
        f"Archived {datetime.date.today()}: {reason}\nRestore: mv '{dst}' '{src}'\n")
```

Before moving, copy any `references/*.md` / `scripts/*` that the survivor lacks (name them `legacy-*` when
superseded) and add one line per file to the survivor's `## References` list — a survivor that silently loses a
sibling's data is worse than two overlapping skills.

Whole-pack pruning uses the same helper with bucket `.archive/_<pack>-prune-<date>/` and `ARCHIVED.txt`.

## 4. Fix the references you just broke

```python
import glob, os, re
D = "/opt/data/skills"
live = {re.search(r'^name:\s*(.+)$', open(p, encoding='utf-8').read(3000), re.M).group(1).strip().strip('"\'')
        for p in glob.glob(D + "/**/SKILL.md", recursive=True) if "/.archive/" not in p}
ALIAS = {"vllm": "serving-llms-vllm", "gguf": "llama-cpp",
         "huggingface-tokenizers": "huggingface-hub", "audiocraft": "audiocraft-audio-generation"}
for p in glob.glob(D + "/**/SKILL.md", recursive=True):
    if "/.archive/" in p: continue
    t = open(p, encoding="utf-8").read()
    m = re.search(r"related_skills:\s*\[([^\]]*)\]", t)      # UNANCHORED — the key is indented
    if not m: continue
    items = [x.strip().strip('"\'') for x in m.group(1).split(",") if x.strip()]
    new = [ALIAS.get(i, i) for i in items if ALIAS.get(i, i) in live]
    if new != items:
        open(p, "w", encoding="utf-8").write(t[:m.start()] + "related_skills: [" + ", ".join(new) + "]" + t[m.end():])
```

Then `grep -rn '<dead-name>' $HERMES_HOME/skills --include='*.md' | grep -v '/.archive/'` for prose hits and decide
one by one: repoint (`see the github umbrella's references/auth.md`), keep as history (a sync transcript), or drop.
**Hardcoded `skills/<cat>/<skill>/scripts/...` paths break silently** when the skill moved — rewrite them to the
surviving path in the same pass.

## 5. Refresh a stale live copy from the seed

Only when the seed's `version:` is strictly higher AND `difflib.SequenceMatcher(...).ratio() > 0.9` (pure upstream
drift, no local edits): `shutil.copy2(seed/SKILL.md, live/SKILL.md)`. Below ~0.7 the live copy has diverged on purpose
— merge sections or leave it; never blind-overwrite a long local build with a shorter upstream rewrite.

## 6. Verify (all four must hold)

```bash
find $HERMES_HOME/skills -name SKILL.md -not -path '*/.archive/*' | wc -l   # matches archived-count arithmetic
hermes skills list 2>&1 | tail -2        # "N enabled, 0 disabled"; N drops by exactly what you archived
hermes skills list 2>&1 | grep -icE 'warn|ambig|error|invalid'   # must be 0
```

Plus the dangling-`related_skills` scan from §4 returning an empty list, and `skill_view` on one survivor
(confirm `linked_files` still lists every reference you folded in).

## 7. Report shape this user expects

Conclusion first, then a table per duplicate group (keep / archive / why), then what was deliberately **not**
touched (layered pairs, with their reference counts as proof), then the remaining decision items, then restore
commands. State the count delta, the bytes/`~tokens` freed from the skill index, and the backup tarball path
(`tar -czf $TMPDIR/skills-backup-<date>.tar.gz --exclude='.archive' skills` before touching anything).
