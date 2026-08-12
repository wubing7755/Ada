# Bilingual / Translation-Pair README Audit — Concrete Recipe

Session provenance: independent read-only review of a repo switching from a
single Chinese README to an English-canonical `README.md` + synchronized
`README.zh-CN.md`, including a validator and regression-test change. Report was
delivered as a severity-ranked findings list with file:line evidence; the audit
modified nothing.

## 1. Freeze repo state (and re-freeze at the end)

```bash
git status --short          # first column = index state, second = worktree
git diff HEAD --stat
git diff HEAD -M -- <old> <new>   # rename-aware diff; see pitfall below
```

Pitfall: `git diff HEAD -- <new-name>` shows a renamed file as an untracked
"new file" with full content. Always use `-M` and both paths to see the REAL
content delta (e.g. "similarity index 98%, 7 changed lines"). This is how you
prove a rename+small-edit stayed within its intended scope. A `RM` status row
means the rename is staged but the worktree edits are NOT — note it as a
process observation (commit will need `git add -A`).

## 2. Fact-token presence check (both language versions)

Build a token list of everything the plan says must not be translated, then
assert each token exists in BOTH files. Proven token categories:

- version strings (`V1.1.1`, `V1.1.0`, `v1.0.0`)
- install/update commands and their full argument lines
- env var names, ports, platform names
- runtime/config paths (`local/...`, `skills/.../references/...`)
- CI check names, local gate commands, `HERMES_HOME`, `.gitignore`, `.env`
- skill identifiers (backticked), authorization-level labels, gateway names
- migration shell guards (`test -f "$OLD"`, `test ! -e "$NEW"`, `mkdir -p`, `mv`)

```python
en = open('README.md', encoding='utf-8').read()
zh = open('README.zh-CN.md', encoding='utf-8').read()
for t in tokens:
    print(('OK ' if t in en else 'MISS'), ('OK ' if t in zh else 'MISS'), t)
```

## 3. Byte-level code-block comparison

Commands must be byte-identical across languages; inline `#` comments are
allowed to differ (each language comments in its own language). Content
`text` blocks (slogans, privacy principles) are translated by design — do not
flag them.

```python
import re, difflib
def blocks(text, lang):
    return [m.group(2) for m in re.finditer(r'```' + lang + r'\n(.*?)```', text, re.S)]
for lang in ('bash', 'powershell', 'text'):
    eb, zb = blocks(en, lang), blocks(zh, lang)
    print(f'== {lang}: EN {len(eb)} / ZH {len(zb)} blocks')
    for i, (e, z) in enumerate(zip(eb, zb), 1):
        if e != z:
            print(f'!! block {i} differs:')
            print('\n'.join(difflib.unified_diff(z.splitlines(), e.splitlines(), lineterm='', n=1)))
        else:
            print(f'  block {i}: IDENTICAL ({len(e.splitlines())} lines)')
```

Report block counts per language and mark each block identical/differing —
this is the strongest evidence that "commands were not broken by translation".

## 4. Language-residual and linkage checks

- EN doc must contain no CJK except the language-switch label itself
  (`[\u4e00-\u9fff]` scan with a context window; `简体中文` in the switch bar is intended).
- Language bar must be REAL markdown relative links both ways; verify the peer
  file exists on disk (and read the repo's validator — it may already enforce
  the link/version/catalog rules; cite what it covers before claiming gaps).
- All markdown link targets must exist: `re.findall(r'\[[^\]]+\]\(([^)]+)\)', text)`.
- Section 1:1 mapping between the two language versions (same headings, same
  order) — the cheapest drift detector for translation pairs.
- Version label and skill catalog must match the manifest
  (`distribution.yaml`): manifest `version` vs `V1.1.1` in both docs; skill
  dirs on disk vs manifest `skills:` list vs backticked names in both docs.

## 5. Re-run the repo's own quality gates — read-only

The repo's gates are the strongest verification and prove the change is
CI-green. Keep the audit read-only:

```bash
export PYTHONDONTWRITEBYTECODE=1          # unittest/validator: no __pycache__
python -m unittest scripts/tests/test_validate_profile_distribution.py -v
python scripts/validate_profile_distribution.py
python -m compileall -q scripts           # check .gitignore covers __pycache__/ first
git diff --check
python scripts/smoke_profile_distribution.py
```

Then re-freeze `git status --short` and confirm it is IDENTICAL to step 1 —
that is the proof of read-only compliance to put in the report.

## 6. Report shape (as requested by the parent)

- Overall verdict up front (passed / findings only, by severity)
- Findings table: `# | 严重度 | 位置 (file:line) | 问题 | 建议`
- Explicit verdict per review point (translation quality, fact drift, command
  integrity, canonical-language implementation, scope control)
- Process observations separate from defects (staging state, untracked plan file)
- Closing line: "未创建或修改任何文件；未提交、未推送。"

This session's outcome: all gates green (22 unit tests incl. 4 new bilingual
failure cases, validator passed, compileall, diff --check, smoke), zero
medium+ findings, 3 minor English style suggestions — evidence that the method
produces a defensible "通过" verdict with only nit-level findings.
