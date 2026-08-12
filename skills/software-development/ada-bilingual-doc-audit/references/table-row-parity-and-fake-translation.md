# Structured table row-parity + fake-translation detection (evidence-phase audits)

Session-proven during the P4 evidence-migration review of the 项目 repo
(EN/ZH `docs/evidence/` pairs, manifest authority cutover). Read-only.

## 1. Positional row comparison of a translated audit table

For a 150-row table `| Requirement | Status | DES | Evidence |` where only
the Evidence column is translated (ID/Status/DES are shared identifiers):

```python
import re, collections

def parse(path):
    rows, in_table = [], False
    with open(path, encoding='utf-8') as f:
        for line in f:
            s = line.rstrip('\n')
            if s.startswith('| Requirement | Status | DES |'):
                in_table = True; continue
            if in_table:
                if s.startswith('|') and not re.match(r'^\|[\s\-|]+\|$', s):
                    c = [x.strip() for x in s.strip().strip('|').split('|')]
                    if len(c) == 4: rows.append((c[0], c[1], c[2], c[3]))
                elif s.startswith('##'): break
    return rows

en = parse('docs/en/evidence/p8-requirement-audit.md')
zh = parse('docs/zh/evidence/p8-requirement-audit.md')
assert len(en) == len(zh) == 150
assert len({r[0] for r in en}) == 150 and len({r[0] for r in zh}) == 150   # unique IDs
assert {r[0] for r in en} == {r[0] for r in zh}                            # same ID set
mism = [(i+1, e[0], col) for i,(e,z) in enumerate(zip(en,zh))
        for col in (0,1,2) if e[col] != z[col]]                            # ID/Status/DES
assert not mism
ALLOWED = {"In Progress","Verified","Implemented","Not Started","Deferred"}
assert all(r[1] in ALLOWED for r in en)                                    # status set
assert '| Designed |' not in open('...', encoding='utf-8').read()
print(collections.Counter(r[1] for r in en))                               # status distribution
# distinct Evidence translations, most frequent first — spot-read each once:
for k, v in sorted(collections.Counter(r[3] for r in en).items(), key=lambda x:-x[1]):
    print(f'x{v}: {k[:150]}')
```

Key checks: exact row count, ID uniqueness both sides, ID sets equal,
positional ID/Status/DES equality (0 mismatches), statuses inside the allowed
set, no forbidden marker values. The distinct-value frequency list is how you
review 150 rows of translation in ~12 spot-reads. `|` cells with embedded
pipes (e.g. `aria-hidden="true"`) are fine unless the cell count breaks.

## 2. Fake-translation detection (zh file that is still English)

A `docs/zh/...` file with a "Chinese Synchronized" header whose BODY is the
untranslated English original. The header block is 7 lines (title, blank,
3-line `>` blockquote, 2 blanks), so body comparison is `tail -n +8`.

```bash
# CJK char COUNT (not line count): header-only values (~20-30) prove no body
# translation; a real zh translation of a 70-line doc scores in the hundreds.
python -c "import re;print(len(re.findall(r'[\u4e00-\u9fff]',open('docs/zh/evidence/x.md',encoding='utf-8').read())))"
# body byte-compare vs the EN file (both directions):
diff <(tail -n +8 docs/zh/evidence/x.md) docs/en/evidence/x.md   # identical => FAKE
# EN authority file must equal the legacy original:
git show HEAD:docs/evidence/x.md | diff - docs/en/evidence/x.md  # empty => EN is the original
```

Interpretation: the plan typically REQUIRES a Chinese translation for this
file ("以现有英文 consumer evidence 为英文起点，再创建中文翻译"). If the zh
body equals the en body, the translation deliverable is missing and the
header/status claim ("本文是英文主文档的翻译", Chinese Synchronized) is false.
Severity High (needs-fix): no test or validator catches it — only the CJK
count and body diff do.

## 3. Manifest blob integrity (independent recompute)

```bash
for f in README 项目-demo-consumer-verification p5-drag-and-dock; do
  echo "== $f =="
  git hash-object docs/en/evidence/$f.md          # must equal manifest canonicalBlob/reviewedCandidateBlob
  git hash-object docs/zh/evidence/$f.md          # post-header zh blob (may differ from translatedFromBlob)
  git show HEAD:docs/evidence/$f.md | git hash-object --stdin   # must equal translatedFromBlob
done
```

- `translatedFromBlob` == legacy HEAD blob (pre-header content); zh worktree
  blob legitimately differs when header-only edits were applied.
- `canonicalBlob` == `reviewedCandidateBlob` == en worktree blob.
- `git cat-file -p <manifest-blob>` may fail "Not a valid object name" — the
  hash was computed with `git hash-object` (no `-w`), so no object exists in
  the DB; compare against `git hash-object` of the actual file instead.
- The repo's phase validator may only type-check these fields (null-or-string)
  — a stale canonicalBlob passes validation. Cite the validator gap explicitly.

## 4. Pre-existing prose-vs-table drift

If prose claims counts that contradict the table (e.g. "Verified 49,
Implemented 16" vs table 48/17), check the legacy original FIRST:

```bash
git show HEAD:docs/evidence/p8-system-hardening.md | grep -n "Verified 49"
```

If the legacy file carries the same numbers, the translation preserved a
pre-existing inconsistency — Nit/Low "preserved verbatim", NOT a translation
defect. Only flag as a translation defect when the numbers differ between
the legacy original and the translation.

## 5. Findings worth reporting even when everything is green

- Renames staged as R100 but zh header edits unstaged (`RM` rows): process
  note (`git add -A` needed), not a defect.
- In-bound link counts: spec may say "8 处" while the diff touches 9 links /
  8 lines — count links, not lines; report the actual count.
- Status-summary rows of evidence docs: spot-check the summary claim against
  the test gate it describes (e.g. RequirementsBaselineTests asserting 150
  rows + no "| Designed |" via manifest authority path, not hardcoded paths).
