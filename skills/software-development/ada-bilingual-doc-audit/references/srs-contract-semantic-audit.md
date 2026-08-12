# SRS Contract-Semantic Audit (ZH source → EN translation, auditor side)

Session-proven recipe (项目 `docs/SRS.md` ↔ `docs/en/SRS.md`, 4985 vs 4971
lines, 150 REQ blocks). The audit treats the pair as a CONTRACT: strength
modals, failure semantics, AC condition boundaries, numeric constraints,
security promises, REQ ID/Actor/Priority invariants. Read-only: scripts in
OS temp (`hermes-verify-` prefix), repo `git status` frozen before/after,
temp cleaned at the end.

## Order of operations

1. **Freeze repo state** (`git status --short`, `git hash-object` the EN file,
   note untracked/new-file status as process context, not a defect).
2. **Load the translation glossary** (`.tmp/*-glossary.md`) — it defines the
   term mapping AND strength rules (必须→must, 应→should, 可以/允许→may) that
   the audit judges against.
3. **Mechanical battery** (scripted, one pass — every check below).
4. **Hand-read sampled block pairs** (paired dumps per section, ZH then EN).
5. **Re-freeze git status** — identical ⇒ read-only proof; clean up temp.

## Mechanical battery (all scripted)

1. **Heading inventory + sequence diff** — `^(#{1,4})\s+(.*)` both files,
   diff (level, normalized text) sequences. Catches duplicate headings (EN
   had `## 3.4 Editor Tab Management` at TWO consecutive lines: 59 vs 58
   headings — Low structural finding), dropped/renumbered sections. Map
   sections by number prefix (`^##\s+(\d+(?:\.\d+)*)`) — heading TEXT differs
   between languages, numbers don't.
2. **REQ block extraction**:
   `^\|?\s*`?(REQ-(?:F|NF)-\d+)`?\s*(🔴|🟡|🟢)?\s*\[Actor: ([^\]]+)\]` →
   compare the full (ID, marker, Actor) sequence positionally. 150/150
   identical = the strongest invariant check (covers all IDs, priorities,
   actors mechanically).
3. **Per-block AC label sequence** — match `^\s*(AC\d*)\s*[：:]` on
   label-shaped lines ONLY. NEVER search the whole block: a Description
   mentioning "REQ-F-140 AC2:" false-matches (this session's only "AC
   mismatch" was exactly that). Expected: preserved source quirks — duplicate
   labels (F-027 AC2/AC2), mislabeled sequences (F-017 AC4 then "AC2") — EN
   keeping them verbatim is CORRECT, not a defect.
4. **Numeric token set equality** — `\b\d+(?:\.\d+)?\b` on both files, diff
   the sets (385 vs 385 identical here). One line that catches port/date/
   count drift everywhere (30 FPS, 300ms, 500ms, 90+, 15+, `2.0`, 500ms,
   ≤20, 2026-07-31...).
5. **Backtick identifier parity** — strip fences first
   (`re.sub(r'```.*?```', 'FENCE', text, re.S)`), then diff `` `([^`]+)` ``
   sets; exclude CJK-containing tokens. Expected diff: template placeholders
   (`[Actor: 角色]` → `[Actor: role]` — translated by design).
6. **CJK residual in EN** — count lines with `[\u4e00-\u9fff]`, verify every
   hit is in the allowlist: §1.5 term-table Chinese column, §1.5.2 role
   definitions, first-occurrence parenthetical annotations in §1.7. Python
   counting only, never grep (multibyte).
7. **Marker-bounded appendix index rows** — rows between
   `<!-- docs:requirements-index:start/end -->`; compare ID sets AND
   positional (ID, priority marker) per row → zero diffs = pass. Row count
   may exceed the doc's official count (158 vs 150) because summary/extra
   rows contain REQ- tokens — expected, not a finding.
8. **Appendix table COLUMN parity** — compare column counts per table, not
   just rows. ZH Appendix B had 4 cols (编号|优先级|标题|推迟原因), EN 3 —
   the deferral-reason column was dropped (Medium: rationale loss; IDs/
   priorities/titles intact ⇒ non-blocking). Change-log tables: row order
   1:1 + spot-check descriptions (ADR numbers, dates must survive).
9. **Fence/mermaid/SVG counts** — ` ``` ` count, ` ```mermaid `, `<svg`
   (306/306, 2/2, 5/5 here). SVG: only `<text>` inner content may differ;
   node IDs/classes/geometry byte-identical.
10. **Terminology variant scan** — per-concept distinct spellings with
    counts: `Dock Region` 110 vs `Dock region` 6 → casing finding (Low);
    glossary `Tool Panel` 0 vs `tool window` 6 → glossary deviation in
    descriptive prose only (Nit). Zero-count glossary terms are NOT defects
    when the ZH source never uses them (变更集/分割基准/内容引用 were HLD-only;
    EN zeros correct) — grep ZH first before flagging an absence.

## Modal strength scan (must/should/may) — traps

Per REQ block: ZH must-class `必须|不得|禁止|不允许|不可` vs EN
`must|must not|shall`; ZH should `应...` vs EN `should`; ZH may
`可以|允许|可能` vs EN `may|allow(ed|s|ing)?`. Flag only class-absence
mismatches (ZH must>0 & EN must==0 etc.), then hand-verify each flag.

Every flag in this session resolved benign — the false positives:
- ZH 不可 not in must regex → F-078's correct "must not continue moving"
  flagged as EN strengthening. (Add 不可.)
- ZH 可能 not in may regex → NF-008 "may produce transition animations"
  flagged. (Add 可能.)
- EN bare `can` over-matches may (common word) — restrict to may/allow.
- Genuine-but-benign: F-071 应禁止 → "must forbid" in Description while all
  ACs use "should not" — Nit (strength deviation, testable contract
  unchanged), not a finding.
- Modal counts (13 vs 8 shoulds) are noise — only class absence + hand-read
  matter.

## Sampling plan (after the battery)

Hand-read ~45% of blocks (67/150 here), distributed per section, ALWAYS
including: all of the persistence section (§3.7), all of the non-functional
section (§4, incl. the security REQ e.g. NF-006 SandboxedFrame/
TrustedComponent — fail-closed semantics, no-uncaught-exception, crash
isolation), and every block flagged by any mechanical scan. Dump paired
blocks (ZH range then EN range) to per-section files and read them fully —
skimming is where semantic drift hides.

Verified-in-practice checks while reading: cross-REQ references (REQ-F-031
AC2 etc.) survive; "formerly F-004 AC3/AC4" annotations survive; deferred-
REQ status consistent between body block and Appendix B; change-log
descriptions carry ADR ids + dates; mermaid/SVG labels translated while
participant IDs (`User->>TB`) preserved; special strings (`contentId
"text-editor"`, `/src/a.md`) byte-identical.

## Report shape (this user's format)

- Verdict FIRST: APPROVE / NEEDS-FIX with one-line cutover implication.
  Mechanical correctness passing while findings are non-normative ⇒ APPROVE
  with Medium/Low/Nit listed, NOT needs-fix.
- Findings by severity (Blocking/High/Medium/Low/Nit), each with file:line
  on BOTH sides + suggested fix.
- Explicit PASS line for every check category.
- Coverage statement: N/150 blocks side-by-side, per-section breakdown,
  which sections read 100%.
- Process observations separate from defects (other workstreams' untracked
  files, modified validator).
- Close: "未创建或修改任何文件；未提交、未推送。" + git status identical
  before/after.
