# ADR / Contract-Pair Tuple Audit — session-proven recipe

Validated on the 项目 P3 ADR migration (18 zh/en ADR pairs, git mv +
English translations + manifest/status updates). All snippets are read-only
Python; run from the repo root. This recipe complements the general
migration checks in SKILL.md §6; the numbered checks below mirror the
review checklist.

## 0. Read the plan first

Extract the migration plan's requirements for the phase: file mapping,
header format, link depth, state machine, and — critically — what the plan
says the *validator must check* (§11-style "auto validation" list). The
plan is the yardstick for findings like "validator no-ops" and "blob
completeness for canonical rows".

## 1. Rename history (staged)

```bash
git diff --cached --name-status -M   # every move must print R100
git diff --cached -M --summary
```

All R100 ⇒ content moved untouched; unstaged edits on top are the zh
header/link fixes. Prove zh is header-only per file:

```python
import subprocess
# list-args; shell=True on Windows mangles single quotes (cmd.exe)
out = subprocess.run(['git','diff', f'HEAD:docs/adr/{f}', f'docs/zh/adr/{f}'],
                     capture_output=True, text=True, encoding='utf-8').stdout
added   = [l for l in out.splitlines() if l.startswith('+') and not l.startswith('+++')]
removed = [l for l in out.splitlines() if l.startswith('-') and not l.startswith('---')]
# expect: removed == [], len(added) == header line count (e.g. 5)
```

## 2. Tuple extraction with continuation lines

`- **Related**:` values wrap onto 2-space-indented next lines. A
line-based regex reports false truncation mismatches. Join continuations;
both zh `：` and en `:` field separators occur.

```python
def extract_tuple_full(text):
    lines = text.split('\n'); fields = {}; i = 0
    while i < len(lines):
        m = re.match(r'^-\s+\*\*([^*]+)\*\*[：:]\s*(.*)$', lines[i])
        if m:
            key = m.group(1).strip(); val = m.group(2).strip(); i += 1
            while i < len(lines) and lines[i].startswith('  '):
                val += ' ' + lines[i].strip(); i += 1
            fields[key] = val
        else:
            i += 1
    return fields
```

Field-name map (zh → en): `状态→Status`, `日期→Date`, `决策者→Decision
maker`, `关联→Related`. Diff with two normalizations that are NOT defects:
- `、` vs `,` enumeration separators
- translated parentheticals (e.g. `项目 Maintainer（2026-07-31 批准继续）`
  vs `项目 Maintainer (approved continuation on 2026-07-31)`)

## 3. Fence-stripped token/number parity

Strip fenced blocks BEFORE comparing inline backticks (otherwise fence
content produces giant garbage tokens):

```python
def strip_fences(text): return re.sub(r'```.*?```', 'FENCE', text, flags=re.S)
def backticks(text):    return sorted(set(re.findall(r'`([^`]+)`', strip_fences(text))))
def numbers(text):      return sorted(set(re.findall(r'\b\d+(?:\.\d+)?\b', text)))
```

- Backtick diffs: only line-wrapping artifacts of the same token and
  cosmetic backtick additions (`Changed` bare in zh vs `` `Changed` `` in
  en) should remain — both Nit-level.
- Number-set diff is the authoritative numeric check (catches test counts,
  enum values, dates, versions). It subsumes ad-hoc per-file grep hunches —
  don't trust grep counts over the set diff.
- Heading sequences: if section headings are language-neutral (this repo's
  zh ADRs used English headings `## Context`, `## Decision`, …) compare
  `re.findall(r'^##?\s+(.+)$', text, re.M)` directly; only the H1 title
  differs (translated).

## 4. Supersession / cross-link parity

```python
links = sorted(set(re.findall(r'\]\(((?:\./)?00\d\d-[^)]+\.md)[^)]*\)', text)))
```

- Link SETS must be identical between zh and en; every target must exist in
  BOTH `docs/en/adr/` and `docs/zh/adr/`.
- Supersession may also be prose-only (no link) — verify the prose mentions
  match (`Supersedes ADR-0008's …` in both) even when no link exists.
- Header cross-links: en `English (canonical) | [简体中文](../../zh/adr/<f>.md)`,
  zh `[English](../../en/adr/<f>.md) | 简体中文` + `Chinese Synchronized`
  status line; `../../` depth correct for docs/en|zh/adr (two levels below
  repo root).

## 5. Bullet-structure parity (no-space-dash trap)

```python
def bullets(text):
    out = []
    for line in strip_fences(text).split('\n'):
        m = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', line)
        if m: out.append((len(m.group(1)), m.group(2), m.group(3)[:60]))
    return out
```

Count mismatches: check for `-成功`-style items (dash + CJK, NO space) —
invalid Markdown bullets that render as plain text and escape the `[-*]\s+`
regex. When en fixed the spacing and zh kept the original, confirm
pre-existing with `git show HEAD:<old-path>` (Low finding, "preserved
verbatim" context — never a regression accusation).

## 6. CJK / placeholder scan on en side

```python
cjk = re.findall(r'[\u4e00-\u9fff]+', en_text)   # only '简体中文' (header label) allowed
grep -rniE "TODO|TBD|FIXME|lorem" docs/en/adr/   # placeholders
```

## 7. Manifest blob integrity (triplets)

```python
orig  = subprocess.run(['git','rev-parse', f'HEAD:docs/adr/{name}'], ...).stdout.strip()
enb   = subprocess.run(['git','hash-object', f'docs/en/adr/{name}'], ...).stdout.strip()
# expect: translatedFromBlob == orig; reviewedCandidateBlob == canonicalBlob == enb
```

Pattern to flag: entries declaring `English Canonical` + `Chinese
Synchronized` + review-approval columns, but with EMPTY
`reviewedCandidateBlob`/`canonicalBlob` while sibling entries (and all
prior-phase rows) fill all three. Either fill both with `git hash-object
<en-path>` after approval, or downgrade state to `English In Review` — the
canonical claim is not backed by the record. Cross-check
`translation-status.md` table columns against the manifest JSON row by row.

## 8. Validator: prove the ADR check actually runs

```python
# read the validator source; look for the ADR function
#   if not (repo/'docs'/'adr').exists(): return   ← SILENT NO-OP after git mv
```

Also verify it compares the en/zh PAIR (cross-language tuple parity), not
just title/status presence in one directory. A green `--phase P3` run with
a no-op ADR check is a Medium gate-strength finding even when the manual
comparison passes.

## 9. Semantic spot-read (contract docs)

Structure cannot prove semantics. Full-read the contract-heaviest pairs
(supersession chains, security, protocol/API freeze ADRs) and check:
must/should/may strength preserved, failure semantics (returns/throws/
"does not save"/"no events published") unchanged, acceptance conditions and
verification numbers identical. In the session, full reads of ADR-0001 and
ADR-0016 plus structural checks on all 18 pairs were sufficient.
