# Phase-Scoped Bilingual Migration Audit — Session-Proven Recipe

Validated auditing a P1 migration: 7 doc pairs `git mv`'d from
`docs/{guides,security}/` into `docs/zh/`, English canonicals created under
`docs/en/`, plus a documentation manifest with integrity blobs and a
translation-status table. All snippets below are the actual working checks.

## 1. Rename history (history preservation)

```bash
git status --short                       # RM rows = rename staged, edits unstaged
git diff --cached --name-status -M       # MUST show R100 for every move
git diff --name-status -M                # unstaged edits on top of renames
```

- `R100` = 100% similarity, history preserved. `D`+`A` pairs = broken.
- Renames staged + modifications unstaged is valid mid-work state: report as
  process note (`git add -A` before commit), not a defect.
- Old directories left behind on disk are harmless if empty and untracked:
  `ls docs/guides docs/security` then `git ls-files docs/guides docs/security`
  (must be empty).

## 2. Manifest blob integrity (never trust the manifest)

```bash
# Original (pre-move) content of a renamed file = STAGED blob:
git ls-files -s docs/zh/guides/testing-guide.md     # -> 100644 <blob> 0 ...
# Current EN canonical = worktree blob:
git hash-object docs/en/guides/testing-guide.md
```

- `translatedFromBlob` must equal the staged blob of the ZH file
  (i.e. the original content at HEAD).
- `reviewedCandidateBlob` and `canonicalBlob` must both equal the worktree
  blob of the EN file (canonical is only filled after cutover and must equal
  the reviewed candidate).
- Check every entry of the phase in the manifest; also verify
  `authority.path`, `language`, `state` (e.g. `English Canonical`) and
  `chineseState` (e.g. `Chinese Synchronized`).
- Status table (`docs/translation-status.md`) rows must mirror the manifest:
  authority path, state labels, and all three blobs.
- `mirrorExceptions` must still list the control files (language selector,
  manifest, status table, plan) with lifetime + removal condition.

## 3. Structural parity per pair

```python
import io, re, os
root = "."  # repo root
pairs = [  # (en_path, zh_path)
    ("docs/en/guides/architecture-overview.md", "docs/zh/guides/architecture-overview.md"),
    # ... all pairs incl. root README.md / README.zh.md
]
def headings(p):
    return [(ln, l) for ln, l in enumerate(io.open(os.path.join(root, p), encoding="utf-8").read().splitlines(), 1)
            if re.match(r'^#{1,6} ', l)]
for en, zh in pairs:
    he, hz = headings(en), headings(zh)
    print(en, "OK" if [h for _, h in he] == [h for _, h in hz] else "HEADING MISMATCH")
    # plus: table rows (lines starting with '|') count equality
    # plus: fenced blocks count equality: len(re.findall(r'^```', text, re.M))
```

## 4. Fact parity: numbers + identifiers

```python
def nums(t): return set(re.findall(r'\d+(?:\.\d+)?', t))
# for each pair: only_zh = nums(zh) - nums(en); only_en = nums(en) - nums(zh)
# both must be empty (catches test counts, ports 8765, dates, versions)

# Identifier parity: every backticked token + camelCase identifier in ZH must
# appear in EN (code identifiers are never translated):
backtick = set(re.findall(r'`([^`]+)`', zh_text))
camel = set(re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+\b', zh_text))
missing = [t for t in (backtick | camel) if t not in en_text
           and not re.search(r'[\u4e00-\u9fff]', t) and len(t) > 2]
```

Spot-check domain facts present in BOTH: fixture filenames
(`p5-drag-fixture.html`), magic strings (`0.0.0-dev`, `127.0.0.1`),
DOM attributes (`appReady`, `parentDomBlocked`), security tokens
(`allow-scripts`, `event.source`, `contentWindow`).

## 5. Link resolvability walk + old-path sweep

```python
pat = re.compile(r'\[[^\]]*\]\(([^)#]+)')
# for every .md under docs/en and docs/zh (and every changed file):
#   strip '#anchor', skip http(s)/mailto/empty, resolve relative to file dir,
#   assert os.path.exists(resolved)  -> zero broken links required
```

Old-path sweep (legacy prefixes before their phase's cutover):

```bash
grep -rn -E "docs/(guides|security)/" . 2>/dev/null | \
  grep -v "^./.git/" | grep -v "\.packages" | grep -v node_modules | \
  grep -v "docs/en/" | grep -v "docs/zh/" | \
  grep -v "documentation-manifest.json" | grep -v "translation-status.md" | \
  grep -v "multilingual-documentation-plan.md"
# also scan future-phase target paths used as LINKS (docs/en/SRS.md):
# allowed ONLY in the manifest as declared targets, not in markdown links
```

## 6. Gates

```bash
python scripts/validate-docs.py --phase P1 --repo .   # must PASS at the phase
git diff --check                                      # must be clean
```

## 7. Findings patterns seen in the wild

- **Medium**: EN-only prose sentence claiming legacy files are "compatibility
  pointers to the canonical English documents" — wrong mid-migration (they
  are the current Legacy Canonical docs; compat pointers appear only at the
  plan's cutover phase, e.g. P5d). Also an EN/ZH asymmetry (no ZH
  counterpart). Fix: remove or reword to reflect current state.
- **Nit**: language selector wording ("canonical after cutover") slightly
  stale after the cutover already happened in the same phase.
- **Nit**: EN doc keeping a ZH heading anchor (`#8-错误处理与质量属性`) — legal
  while the legacy doc stays ZH; informational only.
- **PASS patterns to state explicitly**: R100 renames; 1:1 heading trees;
  identical table/fence counts; empty number-diff sets; zero broken links;
  empty old-path sweep; validator PASS; diff --check clean; no product
  code/CI files touched.
