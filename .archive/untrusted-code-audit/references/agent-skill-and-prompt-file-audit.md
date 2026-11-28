# Auditing a markdown-only "skill" / prompt-rule pack before installing it

A repo whose entire payload is `SKILL.md` files has **no binaries and no scripts**, so the
firmware playbook (strings triage, binary dating, artifact integrity) is wasted work. The risk
surface moves entirely into text:

| Surface | What it looks like | Why it bites |
|---|---|---|
| 提示词劫持 | "ignore previous", "you are now", a remote URL the agent is told to fetch, priority declarations | the file becomes part of the agent's instructions; a hostile line can redirect every later turn |
| 可执行片段 | fenced `bash`/`python` blocks the doc expects the agent to run | code review never happens — the agent reads a doc and types the command |
| 隐藏字符 | zero-width / bidi overrides wrapping a phrase | invisible in a diff and in the user's editor |
| 强规则覆盖 | "never use Inter", "this file wins over framework defaults" | not malicious, but it silently rewrites your defaults — say so before installing |
| 授权链 | copied sections without credit, missing LICENSE | matters when the user ships the output commercially |

## Command set (one pass, ~30 s)

```bash
cd $BH_AGENT_WORKSPACE && rm -rf <name> && git clone --depth 1 <url> <name> && cd <name>
find . -type f -not -path '*/.git/*' | sort            # expect only .md/.txt/LICENSE — no payload = small surface
du -a . --exclude=.git | sort -k2                      # sizes tell you if it is 1 file or a real pack
git log -1 --format='last commit: %ci | %an'; head -3 LICENSE
```

```bash
# behavioural grep — keep the destructive-command literals OUT of the pattern
grep -nEi 'curl|wget|bash -c|eval\(|exec\(|base64 -d|nc -|/dev/tcp|chmod \+x|sudo |rm -rf|ssh-rsa|BEGIN .*PRIVATE|api[_-]?key|token|password|ignore (previous|all)|system prompt|exfiltrat|\.env|npm i -g|pip install|npx ' <files>

# invisible / bidi characters — empty output is the pass condition
grep -nP '[\x{200B}-\x{200F}\x{202A}-\x{202E}\x{2060}]' <files>
```

Repo-level credibility, never as security evidence:

```bash
curl -s https://api.github.com/repos/<owner>/<repo> | python3 -c "import sys,json;d=json.load(sys.stdin);print('stars',d.get('stargazers_count'),'| forks',d.get('forks_count'),'| created',d.get('created_at'),'| pushed',d.get('pushed_at'),'| license',(d.get('license') or {}).get('spdx_id'))"
curl -s "https://api.github.com/repos/<owner>/<repo>/commits?per_page=5" | python3 -c "import sys,json;[print(c['commit']['author']['date'],'|',c['commit']['message'].split(chr(10))[0][:70]) for c in json.load(sys.stdin)]"
```

A young repo with thousands of stars and only a handful of commits is normal for a viral design
skill; a *huge* star count with no commits and no press is the scam signal. Stars answer "is anyone
using it", never "is it safe".

## Reading the hits — three false positives that come up every time

- `curl -o .cursor/rules/<skill>.md ...` in the README is an **install example for the user's
  editor**, not something the skill executes. Say that, do not report it as a network channel.
- `token` hits inside rules like "read the PAT from an environment variable, never print it, never
  paste it into chat, never commit it" are **anti-leak instructions** — credit them.
- "When the user's explicit prompt conflicts with a rule, the user wins" is a sane priority
  declaration. Only a doc that puts itself *above* the user is a finding.

## Dedupe check before installing

Grep the local library for the same territory and compare by *purpose*, not by name:

```bash
grep -rli '<topic keyword>' /opt/data/skills/*/*/SKILL.md | head
grep -n '^#\{1,2\} ' /opt/data/skills/<cat>/<existing>/SKILL.md | head -14   # what it actually covers
```

A newcomer can be a **complement** rather than a duplicate: one skill supplies a style catalog,
another supplies hard numeric rules, a third supplies the build workflow. Report the split
("X 管交付形态，新 skill 管设计判断") instead of a keep/delete verdict, and name the genuine local
gap in one line when there is one.

## Install (markdown skill, no code)

1. **Keep the body byte-for-byte.** Only the frontmatter's `name`/`description` may be rewritten:
   upstream descriptions run 700+ chars and bloat the always-loaded skill list. Add one HTML
   comment with source URL, licence, and the synced commit so a later sync is diffable.
2. **Strip and re-add the frontmatter with a single-shot anchored match** (see the pitfall in
   `hermes-skills-sync` — a global regex eats every `---` horizontal rule in the body).
3. Write to `/opt/data/skills/<category>/<slug>/SKILL.md`, then **prove discovery**: `skill_view`
   the skill and `skills_list(category=...)` both return it.
4. **Prove the body survived**: upstream body substring present in the installed file, and
   `\n## ` / `|---` counts identical upstream vs installed.
5. **Check runtime deps the skill assumes** (`ffmpeg`, `playwright`, a Figma token, a CLI) and list
   the missing ones as a follow-up in the report. Do not silently install a heavy dependency
   (browser bundles, model weights) as part of "安装一个文档".

## Report shape for this user

Chinese, 结论先行, tables, then the verdict:

1. **仓库画像** — stars/forks/licence/created/last-push/size/文件数/更新频率, and the one-line "它其实是什么" (e.g. "就是 2 个 markdown 文件，没有代码").
2. **对做这件事有没有帮助** — 2–3 条具体的、能在以后的工作里兑现的用处, not praise.
3. **同类对比表** — 现有 skill | 定位 | 与新件的关系 (重叠/互补/空缺). State the real local gap if any.
4. **安全审计表** — 检查项 | 结果, one row per surface above, plus 风险等级 and the false positives you cleared.
5. **安装位置** + 完整性校验结果 + 待办依赖.

Never let "6千星" stand in for the security verdict, and never present a rule-strong skill as
neutral tooling — tell the user it will override your default taste and that one line changes it.
