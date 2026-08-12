---
name: ada-bilingual-doc-audit
description: 'Audit bilingual doc pairs: fact drift, broken commands.'
version: 1.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [audit, documentation, bilingual, translation, consistency, verification, readme]
    related_skills: [ada-doc-implementation-audit, ada-doc-comparison-analysis, ada-docs-revision]
---

# Bilingual Documentation-Pair Consistency Audit

Verify that two language versions of the same document (typically an
English-canonical `README.md` + synchronized `README.zh-CN.md`, or EN/CN SRS)
tell the same facts, carry byte-identical commands, and link to each other
correctly — and that the language switch was implemented within its approved
scope. This is a READ-ONLY review: no file edits, no commits, no pushes.

## When to Use

- User asks for an independent review of a README/文档 bilingual (中英文) transformation
- A repo switched to EN-canonical + translated README and you must verify the pair
- Verifying that translation did not corrupt commands, paths, versions, skill
  names, env vars, or migration steps (the plan's "must not be translated" list)
- Checking "英文为主" was actually implemented (root README is EN, language
  status declared, real markdown switch links both ways)
- Verifying the change stayed within the approved file scope
- Auditing a **multi-file, phase-scoped migration** (git mv renames into
  `docs/en/` + `docs/zh/`, a documentation manifest with integrity blobs, a
  translation-status table, inbound-link fixes) — see "Multi-Document
  Migration Audits" below
- **Producing** a translated part (ZH → EN spec section, README mirror, etc.)
  and needing verify-before-deliver structural parity — see "Producer-side
  verification (translation production)" below
- **Auditing an SRS translation pair as a CONTRACT** (ZH source → EN
  translation): must/should/may strength, failure semantics, AC boundary
  equivalence, REQ-ID/Actor/Priority invariants, security promises, numeric
  constraints — auditor-side mechanical battery + sampling plan + modal-scan
  traps in `references/srs-contract-semantic-audit.md`

**Skip for:** single-language doc edits, doc↔code consistency (use
ada-doc-implementation-audit), or merging two drafts (use ada-doc-comparison-analysis).

## The Method

### 1. Freeze repo state

```bash
git status --short        # column 1 = index, column 2 = worktree
git diff HEAD --stat
git diff HEAD -M -- <old> <new>    # rename-aware diff — see pitfall 1
```

### 2. Fact-token presence check (both languages)

Extract the "must not be translated" list from the plan (identifiers,
versions, commands, env vars, paths, CI check names, level labels, gateway
names, shell guards), then assert every token exists in BOTH files:

```python
en = open('README.md', encoding='utf-8').read()       # read via python:
zh = open('README.zh-CN.md', encoding='utf-8').read() # read_file may misjudge UTF-8+Chinese
for t in tokens:
    print(('OK ' if t in en else 'MISS'), ('OK ' if t in zh else 'MISS'), t)
```

Cross-check version label and skill catalog against the manifest
(`distribution.yaml`: `version` field; `skills:` list vs backticked
identifiers in both docs vs skill dirs on disk).

### 3. Byte-level code-block comparison

Commands must be byte-identical across languages; inline `#` comments may
differ (each language comments in its own language — not a defect). Content
`text` blocks (slogans, principles) are translated by design — not a defect.

```python
import re, difflib
def blocks(text, lang):
    return [m.group(2) for m in re.finditer(r'```' + lang + r'\n(.*?)```', text, re.S)]
for lang in ('bash', 'powershell', 'text'):
    eb, zb = blocks(en, lang), blocks(zh, lang)
    print(f'== {lang}: EN {len(eb)} / ZH {len(zb)} blocks')
    for i, (e, z) in enumerate(zip(eb, zb), 1):
        if e != z:
            print('\n'.join(difflib.unified_diff(z.splitlines(), e.splitlines(), lineterm='')))
```

Migration blocks deserve extra scrutiny: every guard (`test -f`, `test ! -e`,
`mkdir -p`, `mv`, re-verify both paths) must survive translation intact.

### 4. Language-residual and linkage checks

- EN doc must contain no CJK except the language-switch label itself
  (`[\u4e00-\u9fff]` scan with a context window; `简体中文` as the link label is intended).
- Language bar: REAL markdown relative links both ways, peer file exists on
  disk. Before claiming a gap, read the repo's validator — it may already
  enforce links/version/catalog; cite what the validator covers.
- All markdown link targets exist: `re.findall(r'\[[^\]]+\]\(([^)]+)\)', text)`.
- Section 1:1 mapping between language versions (same headings, same order) —
  the cheapest drift detector.

### 5. Re-run the repo's own quality gates — read-only

```bash
export PYTHONDONTWRITEBYTECODE=1    # no __pycache__ from unittest/validator
python -m unittest <test-file> -v
python <validator.py>
python -m compileall -q scripts     # only after confirming .gitignore covers __pycache__/
git diff --check
python <smoke-script>.py
```

Then re-freeze `git status --short` and confirm it is IDENTICAL to step 1 —
that is the read-only proof to cite in the report.

### 6. Multi-document migration audits (git mv + manifest + status table)

For phase-scoped migrations where N pairs move via `git mv` and a manifest
claims authority/blob state, add these checks (full scripts in
`references/migration-phase-blob-audit.md`):

1. **Rename history**: `git status --short` shows `RM` rows; then
   `git diff --cached --name-status -M` must list every move as `R100` —
   anything reported as delete+add means history is NOT preserved. Note:
   `-M` is required; plain `--name-status` can report `D`/`A` pairs.
   Renames staged + content edits unstaged is a valid intermediate state —
   report as a process note (`git add -A` needed), not a defect.
2. **Manifest blob integrity** (the highest-value check): for each P1-style
   document entry, independently verify all three integrity fields:
   - `translatedFromBlob` == the ORIGINAL file blob: `git ls-files -s <zh-path>`
     (staged blob of the moved file; for a staged rename this is the old
     content, NOT the worktree content). Equivalent probe:
     `git rev-parse HEAD:<old-path>` — the pre-migration blob at the legacy
     path must equal `translatedFromBlob`. When the ZH file received
     post-rename edits (header/link-depth only), the CURRENT ZH worktree blob
     legitimately differs from `translatedFromBlob` — expected, not drift;
     confirm the diff is only headers + link-depth corrections.
   - `reviewedCandidateBlob` == `canonicalBlob` == the current EN file blob:
     `git hash-object <en-path>` (worktree blob)
   Do NOT trust the manifest — recompute every blob and diff the sets.
3. **Status table ↔ manifest consistency**: every row's authority path, state
   label, and three blobs must equal the manifest's document entry. Also
   check mirror-exception list still contains the control files (language
   selector, manifest, status table, plan) with lifetimes/removal conditions.
4. **Structural parity per pair**: heading trees (same headings, same order —
   cheapest drift detector), table row counts, and fenced-block counts must be
   identical between EN and ZH. Then number-set parity: extract all numeric
   tokens from both files and diff the sets (catches test counts, ports,
   dates, versions). Spot-check domain facts (fixture filenames, magic
   strings like `0.0.0-dev`, DOM attributes) present in BOTH.
5. **Identifier parity**: every backticked token and camelCase identifier in
   the ZH source must appear in the EN translation (code identifiers are
   never translated).
6. **Link resolvability walk**: resolve every relative link in every changed
   file against disk (strip `#anchor`, skip http/mailto) — zero broken links
   required. Dead-link sweep for old paths: grep the whole repo for
   `docs/(guides|security)/`-style legacy prefixes, excluding the new
   language dirs, manifest, status table, and plan file. Future-phase target
   paths (`docs/en/SRS.md`) appearing in the manifest are declarations, not
   broken links — only flag them if used in markdown links before their phase.
7. **Re-run the repo's phase validator** (`python scripts/validate-docs.py
   --phase P1 --repo .`) plus `git diff --check` — both must be clean.
8. **History-document fact audit** (remediations, work-packages, evidence):
   these docs are historical records, so the translation must preserve EVERY
   fact, not just structure — treat this as the highest-priority check for
   such pairs. Build a token list from the ZH source (dates, branch names,
   test counts like `264/264`, review/delegation IDs, file paths, code
   identifiers, timestamps like `11:46`, REQ/DES numbers, F1/F2/F3 labels)
   and assert each token appears in the EN translation. Then verify:
   - Section-number parity: extract `^#{2,3} (\d+(?:\.\d+)*)` headings from
     both files and diff the sequences — catches dropped/renumbered sections
     that heading-text comparison misses.
   - State-claim wording preservation: the translation must NOT upgrade
     historical status claims — ZH `尚未提交` / `等待用户复测确认` must read
     `not committed` / `waiting for user retest confirmation` in EN, and
     `Implemented, not Verified` must not become `Verified`.
   - Line-count asymmetry (EN much longer than ZH, e.g. 368 vs 240 lines) is
     normal English expansion, NOT truncation — never flag it; use heading
     and fact parity instead.
   Session-proven recipe: `references/history-doc-fact-audit.md`.
9. **ADR/contract-pair tuple audit** (ADRs, decision records, specs): these
   are domain contracts, so beyond structure verify the DECISION TUPLE:
   status/date/decision-maker/related-ID fields with continuation-line
   handling, supersession relationship parity (supersedes links + prose,
   both directions), modal-strength preservation (must/should/may, failure
   semantics, acceptance conditions — spot-read full pairs of the
   contract-heaviest docs rather than relying on structure alone), and
   same-dir ADR cross-link sets (e.g. `./0016-xxx.md`) identical in both
   languages with targets existing. Full session-proven recipe:
   `references/adr-pair-tuple-audit.md`.
10. **Structured table row-parity audit** (status/audit tables, e.g. a
    150-row requirement audit): row counts alone are NOT enough — parse
    every data row of the same table in BOTH files and compare
    positionally per column. For an audit table with columns
    `ID | Status | DES | Evidence`: assert (a) exact row count (e.g. 150),
    (b) ID uniqueness in both, (c) ID sets identical, (d) every
    non-translated column (ID/Status/DES) equal per row — only the free-text
    column (Evidence) may differ (as a translation), (e) every Status value
    inside the allowed set (e.g. In Progress/Verified/Implemented/Not
    Started/Deferred), (f) no forbidden values (`| Designed |`). Also print
    the distinct-value frequency of the translated column so you can
    spot-read every distinct translation once instead of 150 rows.
    Session-proven script: `references/table-row-parity-and-fake-translation.md`.
11. **Fake-translation detection (ZH copy that is not Chinese)**: a file in
    `docs/zh/` may claim `Chinese Synchronized` + "本文是英文主文档的翻译" in
    its header while its BODY is byte-identical English — the translation was
    never produced. This is the plan-violating case (plan says "再创建中文翻译"
    / "then create the Chinese translation"); the EN original is legitimately
    byte-identical to the legacy file, but the ZH mirror must actually BE
    Chinese. Detect with a CJK character COUNT, not `grep -c` lines:
    `python -c "import re;print(len(re.findall(r'[\u4e00-\u9fff]',open(f,encoding='utf-8').read())))"`
    — a header-only count (e.g. 28 CJK chars, all inside the `>` language bar)
    proves the body was never translated. Confirm the copy claim with
    `diff <(tail -n +8 <zh>) <en>` (header is 7 lines: title, blank, 3-line
    blockquote, 2 blanks) — identical ⇒ real finding (High: false
    translation-state claim + missing deliverable), even though tests and
    validators stay green.
12. **Special-case legacy-English docs**: when the plan marks one legacy doc
    as "already English", verify the EN authority file is byte-identical to
    the legacy original (`git show HEAD:<old-path> | diff - <en-file>` —
    empty diff) while the ZH file is a REAL translation of it. Checking only
    one side misses the defect (this session: EN == original ✓, ZH == original
    too ✗).
13. **Prose-summary vs table-number drift**: when a doc's prose summary
    contradicts its own table (e.g. "Verified 49, Implemented 16" vs table
    actually counting 48/17), run `git show HEAD:<legacy-path> | grep` on the
    same claim BEFORE blaming the translation — if the legacy original had
    the same numbers, the translation faithfully preserved a pre-existing
    inconsistency: report as Nit/Low with "preserved verbatim" context, not
    as a translation defect.
14. **SRS contract-semantic audit (auditor side, ZH → EN)**: for SRS pairs,
    run the mechanical battery FIRST (heading-seq diff — catches duplicate
    headings; REQ (ID, marker, Actor) tuple sequence; per-block AC labels
    matched on label-shaped lines ONLY; numeric-token set equality; backtick
    identifier parity; CJK residual with term-table/annotation allowlist;
    marker-bounded appendix index rows positionally; appendix table
    column-count parity; fence/mermaid/SVG counts; per-spelling terminology
    counts), then hand-read ~45% of REQ blocks including ALL of the
    persistence (§3.7) and non-functional (§4) sections. Modal-strength scan
    regexes MUST include 不可 and 可能 in the ZH must/may classes or every
    flag is a false positive; treat every flag as needing hand verification.
    Verdict: mechanical correctness + preserved source quirks ⇒ APPROVE with
    non-blocking findings listed, never NEEDS-FIX. Full session-proven
    recipe: `references/srs-contract-semantic-audit.md`.
15. **HLD contract-pair audit (auditor side, ZH → EN)**: HLD pairs are domain
    contracts — the contract is the DES block tuple (ID line, title, `Source:`
    footer), the OI table tuple, appendix matrix rows, backticked error-code
    identifiers, mermaid label preservation, and §10 must/should/may strength.
    Run the mechanical battery: heading-seq diff (an EN-only duplicate `## N`
    heading is the part-seam merge artifact — Low finding, delete one line);
    `DES-[A-Z]+-\d+` / `OI-\d+` / `REQ-[FN]-\d+` set parity; DES footer
    comparison AFTER stripping `(Source:|来源：)\s*`; Appendix D positional
    row parity on (REQ, status) columns with comma-space normalization on
    BOTH sides; bounded Appendix C/B extraction (never sweep Appendix D rows
    into Appendix C counts); numeric-token parity; zero-CJK incl. punctuation
    ranges; backtick identifier parity (ZH ⊆ EN; EN-only additions like
    `Source` are the footer label translation — expected); relative-link walk
    against the EN file's OWN directory (a preserved `./zh/...` link breaks
    from `docs/en/` and needs `../zh/...`). Then hand-read §10 in full:
    MUST/SHOULD/MAY legend, DEV-GATE rows (OI/ADR refs), API surface manifest,
    layer numbers (0/10/20/30/40), phase gates (P0–P8 + demo), work-package
    fields, stop conditions, status vocabulary. Verdict: parity + preserved
    quirks ⇒ APPROVE with Low merge-seam findings listed, never NEEDS-FIX.
    Full session-proven recipe: `references/hld-contract-pair-audit.md`.
16. **Phase-scoped contract revision audit**: when a phase changes only a
    bounded subset of an existing EN/ZH SRS/HLD/ADR set, split verification
    into global invariants (ID counts/sets, marker-bounded indexes, links,
    fences, repository baseline tests) and changed-scope parity (only touched
    REQ/DES/ADR tuples, AC labels, titles, modal strength, supersession, and
    gate state). Compare unrelated mismatches against `HEAD` before calling
    them regressions; pre-existing title drift is not a phase blocker. Before
    adding a new requirement ID, inspect baseline ADRs, exact-count tests, and
    one-row-per-ID audit tables, then prefer extending an existing owning
    requirement when the behavior is not independent. Full recipe:
    `references/phase-scoped-contract-revision-audit.md`.
17. **Cross-document contract-change closure audit**: after an SRS/ADR/HLD
    change freezes or replaces behavior, do not stop at EN↔ZH parity. Build a
    source/outcome matrix (registration source × missing/conflict/factory/
    renderer failure × detection phase × whole-Host/per-Kind/per-outlet
    scope), including the adversarial case of two Items using the same Kind,
    then compare SRS ACs, ADR decisions, and HLD execution semantics. Enforce
    four-way trace equality after range/separator normalization:
    `DES Source = Appendix C = reverse(Appendix D.2)` and each requirement's
    `Appendix D.2 DES set = current evidence-row DES set`. Scan both
    directions: a D.2 removal can leave an unchanged DES Source stale, while
    a D.2 addition can leave an unchanged evidence row stale. Validate row-
    derived status totals and per-row DES mappings independently—a correct
    histogram does not prove correct traceability. Compare current relations
    with `HEAD` to separate phase regressions from preserved baseline drift;
    compare the actual changed REQ set with change-log and gate-evidence ID
    sets. Map each failure to exactly one transport/namespace (construction
    exception, workspace error, or Host diagnostic), then inspect general
    error-code catalogs for stale competing triggers. For descriptors that
    capture objects, reconcile maximum owner lifetime, source replacement,
    retired-source collection, and final disposal; an absolute “retained
    until disposal” consequence must not contradict earlier replacement
    semantics. In shared/multi-agent worktrees, hash scoped files before the
    semantic pass and immediately before reporting; if hashes changed, reload
    and rerun affected checks so findings and line references describe one
    stable final snapshot. Revalidate previous `Verified` rows against newly
    added AC clauses; distinguish dated evidence snapshots from current
    status; reconcile gate summaries, status tables, remediation notes, and
    the normative public-API manifest even when outside the diff. Full
    recipe: `references/contract-change-cross-document-audit.md`.
18. **Consuming independent-review results (review-fix-reverify loop)**: when a
    phase freeze depends on an external review, (a) a delegation that reports
    `completed` may have NO verdict — subagents that hit an HTTP 429 rate limit
    return without findings; inspect the summary for an actual PASS/NEEDS-FIX
    verdict before treating it as a gate result, and re-dispatch after the rate
    window; (b) review line numbers describe the snapshot the reviewer SAW —
    after any fix they go stale, so verify every finding against the CURRENT
    file by search (`grep -n` the token), never by the reported line; (c) when
    re-dispatching, scope the re-review tightly (list the exact findings to
    verify, name the files) to cut API usage and 429 risk; (d) recompute status
    histograms from the actual table rows — never copy reviewer-suggested
 candidate counts (this session: reviewer proposed `Verified 47 /
 Implemented 16`, the table actually counts `46 / 17`); the table is the
 contract, and note the corrected totals explicitly in the fix.
 (e) removal-type findings ("X no longer cites Y") verify by
 ENUMERATED-LOCATION absence, not global absence: enumerate the named
 locations (DES body `Source:` footer, Appendix C row, Appendix D
 traceability row), grep Y repo-wide, then confirm every remaining Y hit
 is a legitimate citation in an unrelated row. A removal is fixed when
 the named locations are clean even if Y still appears elsewhere (e.g.
 F-122 legitimately remains in DES-RND-001/002/004 sources and in
 `CONTENT_ALREADY_REGISTERED`'s basis column after its removal from
 DES-OP-008). (f) Include `??` untracked files from `git status --short`
 in the verification surface — new ADR/docs added by the fix are part of
 the current working tree. (g) When a finding names a doc region by
 shorthand (e.g. "Source/AppC/D.2"), enumerate the candidate locations
 from the document structure (footer + appendix indexes + matrix) before
 checking, so no intended location is skipped. (h) Report PASS with
 per-finding evidence as CURRENT file:line pairs from your own greps,
 never reviewer line numbers.

### 7. Report shape

- Overall verdict up front (passed / findings only, by severity)
- Findings table: `# | 严重度 | 位置 (file:line) | 问题 | 建议`
- Explicit verdict per review point (translation quality, fact drift, command
  integrity, canonical-language implementation, scope control)
- Process observations separate from defects (mixed staging state, untracked plan file)
- Closing line: "未创建或修改任何文件；未提交、未推送。"
- Requested format (when the user prescribes one, e.g. severity classes
  Blocking/High/Medium/Low/Nit): group findings by severity with
  `file:line`, problem description, and suggested fix; write **PASS**
  explicitly for every check category with no findings; end with an overall
  verdict (`approve` / `needs-fix`). Mechanical correctness passing while a
  prose claim is wrong = approve with the wording issue listed as
  Medium/Non-blocking, not needs-fix.

## Producer-side verification (translation production)

Twin workflow for the audit: you are the one WRITING the translated part
(contract documents: SRS/HLD sections, requirement blocks, index tables).
Proven recipe for a large range (this session: 1648-line SRS section →
1633-line English part, all checks green):

Complements living in `repository-documentation` →
翻译批次的切分约定（part-seam）见 `references/bilingual-doc-pair-audit.md` 与生产侧验证节。
(the inclusive end line is often the NEXT section's heading — exclude it and
verify against the sibling part file's first heading), SVG attribute-line
parity (only `<text>` inner content may differ), and the root cause of the
temp-path rule (git-bash `/tmp` is invisible to native Windows Python, so
shared bash/python scratch files must live repo-local in `.tmp/`).

1. **Load the translation glossary first** — repo-local `.tmp/*-glossary.md`
   usually defines term mapping AND strength rules (必须→must, 应→should,
   可以/允许→may). Follow it exactly; consistency across parallel parts
   (multiple agents translating 3.6/3.7/3.8 in one session) depends on it.
2. **Extract the exact line range with Python** when `read_file` reports
   "Binary file" on a large UTF-8 CJK doc: slice
   `readlines()[start-1:end]` → write a `.tmp/` copy → `read_file` works on
   the temp file. Never translate from a guessed range; verify the range's
   first line against the source headings first (`grep -n '^## '`).
3. **Write in chunks**: a 70KB+ output in one `write_file` risks truncation —
   write 4 chunks to `.tmp/` then `cat chunk1..4 > target`.
4. **Preserve source-internal inconsistencies verbatim**: contract translation
   keeps typos (`RE F-034`), Actor mismatches between a requirement block and
   its index row, and stats-vs-table number drift exactly as the source has
   them. Report them in the delivery summary; do not "fix".
5. **Verify before reporting** with
   `python scripts/verify-translation-parity.py <src> <start> <end> <out>`
   (block-header parity incl. `REQ-NF-*`, per-block AC/GWTA structure bounded
   by the `Acceptance Criteria` marker, marker-bounded index-table rows on
   (ID, priority, actor), emoji distribution, CJK residual). Read its
   docstring — it encodes the false-positive traps below.
   For SRS ranges WITHOUT index markers (plain REQ blocks in ``` fences),
   use `scripts/verify-srs-block-translation.py` instead — it checks the
   (ID, marker, Actor) tuple directly on each `REQ-F-xxx 🔴 [Actor: ...]`
   header line, AC label sequences (incl. preserved quirks such as a
   duplicated `AC2` label), fence balance, mermaid/SVG block counts,
   anchor-slug resolvability, token preservation, and CJK residual with an
   allowlist.
6. **Convert internal anchor links to English slugs — part of the contract**:
   `[§3.1 层级结构](#31-层级结构)` → `[§3.1 Hierarchy](#31-hierarchy)`.
   Slug rule: lowercase, spaces→hyphens, strip punctuation
   (`## 3.1 Hierarchy` → `31-hierarchy`). Keep a src-anchor → new-slug map
   while translating headings; afterwards verify every output anchor
   resolves to a translated heading slug (script does this).
7. **Tuple parity on header lines when the range has no index markers**: the
   REQ line itself (`REQ-F-XXX` + 🔴🟡🟢 + `[Actor: ...]`) is the contract
   tuple — compare the full (ID, marker, Actor) sequence, not just IDs.
8. **Bilingual-annotation convention for EN output**: an English translation
   of a Chinese spec deliberately KEEPS the source's parenthetical Chinese
   annotations (`Dock Panel (Dock 面板)`) and the term-definition table's
   Chinese column (`| Term | Chinese | Definition |`) — that Chinese is
   glossary DATA, not untranslated prose. Run the CJK-residual check with an
   allowlist of these locations (script `--cjk-allow`), never a bare
   zero-CJK rule, or you will "fix" legitimate annotations.
9. **HLD/DES-block ranges** (fenced `DES-XXX-###` blocks, no REQ headers):
   the contract tuple is (DES id line, title line, `Source:` footer, fence
   pair). Translate only the title, prose, `//` comments, ASCII-diagram
   human labels, and `来源：`→`Source:`; keep code/struct/XML/Razor/HTML/
   arrow samples byte-identical. Verify with the token-multiset diff
   (`grep -oP '(DES-…|F-…|NF-…|OI-…|ADR-…)'` on the SOURCE RANGE vs output,
   sort, diff — this session 157/157), fence balance (`grep -c '^```$'`
   even = 2×N blocks), and zero-CJK (HLD output is FULL-English — the SRS
   bilingual-annotation allowlist does NOT apply). Part-seam rule: check
   `tail -3 partN` / `head -3 partN+1`; if the next part already carries
   your range's final heading, exclude it; if both parts carry the same
   heading, keep yours and flag the 1-line duplicate for merge-time dedupe.
   Full recipe: `references/hld-des-block-translation.md`.
10. **Report the final line count** of the deliverable plus what was verified,
    and flag preserved source inconsistencies explicitly.

False-positive traps when hand-verifying (all encoded in the script):
- Source AC labels use full-width `：`, output uses ASCII `:` — normalize
  before comparing, or every AC "mismatches".
- English descriptions legitimately start with `When`/`And` — count
  Given/When/Then/And only after the `Acceptance Criteria` line.
- Block-ID regex must be `REQ-(F|NF)-\d+`; `REQ-[FN]` silently misses every
  `REQ-NF-xxx` (47-vs-47 while grep says 55).
- Naive `| REQ-` row scans sweep Appendix B/C rows into the index count
  (185 ≠ 150) — bound extraction by the `<!-- docs:requirements-index:... -->`
  markers, which the contract requires to stay byte-identical.
- Emoji distribution must be counted INSIDE the marker-bounded region only
  (Appendix B rows legitimately carry 🟢 too).

Full concrete recipe with session-proven snippets:
`references/bilingual-doc-pair-audit.md`

HLD/DES-block translation recipe (block anatomy, byte-identical sample
rules, token-multiset diff, fence balance, part-seam coordination):
`references/hld-des-block-translation.md`

Migration-audit scripts (blob verification, structural/number/identifier
parity, link walk, old-path sweep, findings patterns):
`references/migration-phase-blob-audit.md`

Structured-table row-parity script (positional ID/Status/DES comparison,
allowed-set + uniqueness checks), fake-translation CJK-count detector,
EN==legacy-original diff, and the evidence-phase verification recipe:
`references/table-row-parity-and-fake-translation.md`

Producer-side verify-before-deliver script (block-header parity incl.
REQ-NF-*, per-block AC/GWTA structure, marker-bounded index rows on
(ID, priority, actor), emoji distribution, CJK residual):
`scripts/verify-translation-parity.py`

Producer-side script for SRS ranges WITHOUT index markers — REQ-block tuple
parity on header lines, AC label sequences (quirks preserved), fence
balance, mermaid/SVG counts, anchor-slug resolvability, token preservation,
CJK residual with allowlist:
`scripts/verify-srs-block-translation.py`

## Common Pitfalls

完整陷阱清单（逐类审计的失败模式与对策）见 `references/common-pitfalls.md`。
## Verification Checklist

- [ ] git status frozen before and after; identical ⇒ read-only proof
- [ ] All fact tokens present in BOTH language versions
- [ ] Version + skill catalog match manifest and disk
- [ ] All code blocks byte-compared; commands identical, only comments differ
- [ ] Migration guards intact in every platform block
- [ ] No CJK residual in EN doc outside the switch label
- [ ] Language-switch links real, relative, mutual, targets exist
- [ ] Repo's own gates re-run green (unittest, validator, compileall, diff --check, smoke)
- [ ] Findings table with severity + file:line + suggestion; verdicts per review point
- [ ] (Migration audits) All moves report R100 with `-M`; never delete+add
- [ ] (Migration audits) Manifest blob triplets recomputed via git hash-object / ls-files -s and match
- [ ] (Migration audits) Status-table rows consistent with manifest (authority, state, blobs)
- [ ] (Migration audits) Heading trees / table rows / fence counts / number sets identical per pair
- [ ] (Migration audits) History docs: every historical fact token (dates, counts, deleg IDs, paths, timestamps, REQ numbers) present in EN; section-number sequences match; status claims (uncommitted / waiting for retest / Implemented-not-Verified) never upgraded
- [ ] (Migration audits) ADR/contract pairs: tuple fields match (continuation lines joined, 、 vs , normalized); supersession links/prose identical both directions; modal strength + failure semantics spot-read on contract-heavy pairs; validator's ADR check verified to actually run (not a silent no-op on the pre-move path)
- [ ] (Migration audits) Structured tables: row count exact (e.g. 150), IDs unique + same set both sides, non-translated columns equal per row, statuses inside allowed set, no forbidden marker rows (`| Designed |`); distinct translated-column values spot-read once each
- [ ] (Migration audits) No fake translations: every zh file's CJK character count indicates a real translated body (not header-only); zh body byte-diff vs en file shows real differences; en authority byte-identical to legacy original for originally-English docs
- [ ] (Migration audits) Prose summary vs table numbers: drift checked against `git show HEAD:<legacy>` before blaming the translation (pre-existing ⇒ Nit "preserved verbatim")
- [ ] (Migration audits) Zero broken relative links; old-path sweep clean; no premature canonical/compat-pointer claims
- [ ] (Producer-side) Glossary loaded and strength rules (must/should/may) applied; source range verified against headings before extraction
- [ ] (Producer-side) `scripts/verify-translation-parity.py` green: block headers, per-block AC/GWTA structure, marker-bounded index rows, emoji distribution, no CJK residual (use `scripts/verify-srs-block-translation.py` for plain-fence SRS ranges: block tuples, AC sequences, fences, mermaid/SVG, anchor slugs, tokens, CJK allowlist)
- [ ] (Producer-side) Anchor links converted to English github-slugger slugs and resolvable against output headings; preservation-check tokens grepped in the SOURCE first (memory-sourced tokens false-FAIL, e.g. `REQ-F-135` vs source `F-135`)
- [ ] (Producer-side) Source-internal inconsistencies (typo IDs, block-vs-index Actor mismatches) preserved verbatim and reported in the summary; final line count reported
- [ ] (Producer-side HLD/DES-block ranges) Token multiset identical vs SOURCE RANGE (grep -oP + sort + diff); fence count even (2×N); zero CJK; seam checked against sibling part files (tail/head), boundary decisions reported
- [ ] (Auditor-side HLD pairs) DES block tuples (ID/title/Source footer, footer compared after `(Source:|来源：)\s*` strip), OI table tuples, Appendix D positional rows (REQ/status cols, comma-space normalization on BOTH sides), Appendix B backticked snake_case error-code sets, mermaid label parity, numeric-token parity, relative-link walk against the EN file's own directory, §10 must/should/may hand-read — full recipe in `references/hld-contract-pair-audit.md`
