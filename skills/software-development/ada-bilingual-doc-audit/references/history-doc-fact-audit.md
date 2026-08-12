# History-Document Fact Audit (remediations / work-packages / evidence)

Session-proven recipe from an independent P2 review of a development-history
migration (ZH originals → EN translations, remediation + work-package docs,
项目 repo, Aug 2026). For bilingual pairs where the source is a HISTORICAL
record, fact preservation outranks prose quality: the EN translation must
not rewrite dates, counts, IDs, paths, timestamps, or status claims.

## 1. Build the fact-token list from the ZH source, assert each in EN

Extract from the ZH original (not from memory): dates, branch names, test
counts (`264/264`, `45/45`, `34×32`), review/delegation IDs (`deleg_*`),
file paths, code identifiers, REQ/DES/F numbers, timestamps (`11:46`),
process IDs (`5078`), section labels (`F1`/`F2`/`F3`, `AC3`/`AC4`).

```python
import re
en = open('docs/en/development/remediations/x.md', encoding='utf-8').read()
zh = open('docs/zh/development/remediations/x.md', encoding='utf-8').read()

facts = ['2026-08-01', 'feature/项目-demo', 'not committed', '264/264',
         '266/266', '22/22', '34×32', '119 to 101', 'deleg_4be9c86c',
         'deleg_5b9931ad', 'deleg_199d5898', 'deleg_6b9ac2dc', 'deleg_401a63b4',
         'src/项目.Blazor/Components/Workspace/WorkspaceHost.cs',
         'MoveToolOperation', 'ReorderToolBarEntryOperation', 'TryGetValue',
         'setPointerCapture', 'getBoundingClientRect', 'min-inline-size',
         'REQ-F-150', 'REQ-F-155', 'REQ-F-142', 'F1', 'F2', 'F3',
         '11:46', '10:50', '15:32', '5078', '5080']
missing = [f for f in facts if f not in en]
print("MISSING in EN:", missing if missing else "NONE — all facts present")
```

Notes:
- Normalize exact-value wording before listing (ZH `119 漂移到 101` appears in
  EN as `drifted from 119 to 101` — list the numeric pattern `119 to 101`,
  or regex-search numbers instead of literal phrases).
- The `×` in `34×32` is U+00D7 and survives verbatim — include it.
- `deleg_*` IDs and file paths must be byte-identical (never translated).

## 2. Section-number parity (cheap, catches dropped/renumbered sections)

```python
zh_nums = re.findall(r'^#{2,3} (\d+(?:\.\d+)*)', zh, re.M)
en_nums = re.findall(r'^#{2,3} (\d+(?:\.\d+)*)', en, re.M)
print("Parity:", zh_nums == en_nums, zh_nums, en_nums)
```

Heading-text comparison alone misses a renumbered section; the number
sequence catches it. ZH remediation `1,1.1..1.3,2,2.1..2.13,3,3.1..3.4,4`
must equal EN exactly.

## 3. State-claim wording preservation (the "must not upgrade" check)

Historical records declare their own status. The translation MUST NOT
upgrade it. Verified mappings in this class of doc:

| ZH source | EN must read | Never |
|---|---|---|
| `尚未提交` | `not committed` | "committed" |
| `等待用户复测确认` | `waiting for user retest confirmation` | "approved/closed" |
| `状态为 Implemented，不标记 Verified` | `Implemented, not Verified` | "Verified" |
| `该包早于 2.11 修复` | `predates the 2.11 fix` | "includes the fix" |

Assert the EN contains the negative form and does NOT contain the positive
form: `'not committed' in en.lower() and 'committed' not in <the same sentence>`.
Grep both files for the paired words (`尚未提交` / `未提交` vs `committed`).

## 4. translatedFromBlob via the legacy path (staged-rename case)

For a staged rename with post-rename worktree edits on the ZH file:

```bash
git rev-parse HEAD:docs/development/README.md          # must == manifest translatedFromBlob
git hash-object docs/en/development/README.md          # must == reviewedCandidateBlob == canonicalBlob
git hash-object docs/zh/development/README.md          # differs from translatedFromBlob — EXPECTED
git diff -- docs/zh/development/README.md              # verify diff is only header + link-depth lines
```

`translatedFromBlob` pins the exact content the EN was translated FROM (the
pre-migration ZH blob). The current ZH worktree blob differing is only
legitimate when the diff is header/status lines and link-depth corrections;
any content-line diff is drift.

## 5. Line-count asymmetry is a false-positive trap

EN remediation was 368 lines vs ZH 240, EN README 50 vs ZH 36 — normal
English expansion, and in the README case EN is legitimately longer because
it also carries content. NEVER flag "EN file is longer/shorter than ZH" as
truncation or padding; structure parity (§2 + table/fence counts) and fact
tokens are the real signals. Also check for placeholder markers in EN
(`TODO|TBD|lorem|FIXME|待翻译|未翻译`) — absence is expected.

## 6. Report shape for prescribed severity formats

When the user prescribes Blocking/High/Medium/Low/Nit: write **PASS**
explicitly under every check category with no findings (git mv history,
translation completeness, fact preservation, manifest integrity, link
updates, validation runs, no-code-change), then issues by severity with
file:line, description, suggested fix; end `approve` / `needs-fix`.
Process observations (untracked EN files, mixed staging) go under Low/Nit,
never Blocking/High.
