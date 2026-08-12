# HLD Contract-Pair Audit (auditor side, ZH → EN)

Session-proven recipe (2026-08: 项目 HLD, 2781 ZH lines → 3041 EN lines,
verdict APPROVE with two Low findings). HLD pairs are domain contracts: the
DES/OI tuples, appendix matrixes, §10 execution-contract modal strength,
error-code values, and code-identifier invariants ARE the contract — verify
them beyond heading/structure parity.

## Mechanical battery (run in this order)

1. **Freeze repo state**: `git status --short` before and after. The audit is
   read-only; the identical status is the proof to cite.
2. **Heading-seq diff**: extract `^#{2,3} ` lines from both files, compare
   counts and sequences. An EN-only DUPLICATE heading (`## 5 Interaction
   Architecture` at lines N and N+2) is the parallel-part seam merge artifact
   (see producer-side part-seam rule) — Low finding, delete one line, never
   content loss. ZH duplicate headings = source quirk, preserve.
3. **ID-set parity**: `DES-[A-Z]+-\d+`, `OI-\d+`, `REQ-[FN]-\d+` sets must be
   equal both ways (this session 57/57 DES, OI and REQ clean).
4. **DES block tuple extraction**: fenced blocks whose first content line is
   `DES-XXX-###`. Tuple = (ID line, title line, Source footer). Compare
   footers AFTER `re.sub(r'^(Source:|来源：)\s*', '', s)` — the `\s*` matters:
   EN `Source: X` has a space after the ASCII colon, ZH `来源：X` does not.
   Also normalize `、`→`,`. Only the footer label (`来源：`→`Source:`) and SRS
   section titles inside footers (`§1.7 空间概念`→`§1.7 Spatial Concepts`)
   may translate; the ID lists must match exactly. One legitimate mismatch of
   this kind ⇒ PASS with note.
5. **Appendix C (design index)**: bound extraction between the `## Appendix C`
   and `## Appendix D` headings — a naive `| DES-` row sweep overflows into
   Appendix D and inflates counts (174 vs 167 observed before bounding; real
   counts 57/57). Compare DES ID sequences positionally (must be identical),
   titles legitimately differ (translation), source column must match after
   `、`/`, ` normalization.
6. **Appendix D traceability matrix**: parse data rows between `### D.2 …`
   markers (header + separator skipped); compare per row on the REQ column
   and status column with `re.sub(r'\s*,\s*', ',')` + `、`→`,` on BOTH sides.
   `、`→`,` alone produces `A,B` vs EN `A, B` and false-flags every multi-ID
   row. Status VALUE SETS must be identical (87 Designed / 2 Deferred in both
   this session). D.1 status-exception rows likewise (26/26). The `—` cells
   (REQ-F-152 Deferred) must survive verbatim.
7. **Appendix B error codes**: codes are backticked snake_case identifiers
   (`LAYOUT_VERSION_INCOMPATIBLE`, `STALE_OPERATION`), NOT `ERR-\d+`.
   Extract `` `([A-Z][A-Z_]+)` `` tokens from the region between the
   `## Appendix B` and `## Appendix C` headings; compare sets (16/16) and the
   basis column (`F-xxx` / `DES-xxx` refs) per row. Blockquote notes after
   the table (e.g. "F-030 and F-121 uniformly return `ITEM_NOT_FOUND`…") must
   translate faithfully.
8. **OI table (§1.2 Known Open Issues)**: per-row parity on (ID, SRS basis,
   status, resolution). Basis IDs (`F-069、F-140…`) and ADR numbers
   (`ADR-0007`, `ADR-0012`, `ADR-0014`, `ADR-0013`, `ADR-0001/0016/0017`) must
   match; only issue/handling prose translates.
9. **Mermaid/state diagrams**: block count parity (7/7) and per-block label
   comparison — extract transition lines, check SAME line count, SAME node
   pairs (`[*] --> Declared`, `Expanded --> Collapsed`), REQ refs and numeric
   thresholds preserved (`4px`, `REQ-F-054~056`), only the human label after
   the colon translates. `stateDiagram-v2` keyword and state names
   (`Declared`, `PendingThreshold`, `DirectionDetected`) byte-identical.
10. **CJK residual**: HLD output is FULL-English — zero-CJK scan must include
    `\u3000-\u303f` and `\uff00-\uffef` ranges (this session: 0).
11. **Backtick identifier parity** (strip ``` fences first with
    `re.sub(r'```.*?```', 'FENCE', t, flags=re.S)`): ZH set ⊆ EN set. EN-only
    additions limited to expected artifacts — `Source` is the footer label
    translation, not drift.
12. **Numeric-token parity**: `\b\d{2,4}\b` outside fences (layer numbers
    0/10/20/30/40, `4px`, `30fps`, `150`, `9-region` all matched).
13. **Link-resolution walk**: resolve every relative markdown link of the EN
    file against the EN file's OWN directory (`os.path.join(repo, 'docs',
    'en', target)`), and the ZH file's against its own. A preserved
    `./zh/security/content-threat-model.md` link from the ZH original breaks
    from `docs/en/` — the translation must rewrite it to `../zh/...`. This is
    the one link class translation introduces; everything else is inherited
    intact.
14. **§10 development-execution-contract modal read (full, both sides)**:
    MUST/SHOULD/MAY legend; DEV-GATE-001~006 rows (OI/ADR refs, "Closed"
    claims); API Surface Manifest symbol families (`IWorkspace`,
    `WorkspaceResult<T>`…) incl. Forbidden columns; initialization-mode
    matrix; cross-boundary artifacts (`ClientScripts/protocol.ts`,
    `项目-workspace-v2.xsd`, `WorkspaceErrorCode`); lifecycle sequences
    (mermaid byte-identical — only prose around them translates); DOM
    metadata attrs (`data-项目-host-id`, `data-项目-split-id`…);
    项目-v2-* classes; layer table; P0–P8 + Consumer Demo phase rows
    (entry/exit gates); work-package fields; 5 stop conditions; status
    vocabulary. Modal mapping per glossary: 必须→must, 应→should, 可以/允许→may,
    不得/不能→must not (不能 also maps to "may not"/"cannot" in may-class
    contexts — hand-verify each).

## Verdict

Mechanical parity + preserved source quirks ⇒ **APPROVE** with findings
listed, never NEEDS-FIX. Typical findings at this quality bar are Low
merge-seam artifacts: (a) duplicate part-seam heading, (b) `./zh/` link not
rewritten for the `docs/en/` location. Both are one-line fixes recommended in
the same PR. Everything else (57/57 DES tuples, 89+26 matrix rows, 16 error
codes, 6 OI rows, §10 modal strength) passing is the APPROVE basis — cite
the exact counts in the report.

## Report shape

- Verdict first: APPROVE / NEEDS-FIX with the English Ready for Cutover
  implication.
- Findings by severity with `file:line`, problem, fix.
- PASS line for every check category with no findings (DES tuples, OI table,
  Appendix D, Appendix B, Appendix C, mermaid, §10, terminology, CJK).
- Read-only proof: git status frozen identical.
- Closing line: "未创建或修改任何文件；未提交、未推送。"
