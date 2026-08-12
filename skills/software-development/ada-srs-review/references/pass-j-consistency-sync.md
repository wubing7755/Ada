# Pass J — Post-Edit Consistency Sync

Run after ANY add/delete/renumber operation on the SRS document.

Requirement deletions/additions silently rot the document's self-descriptions. Audit ALL of:

1. **Section index headers** (`本节需求索引 (N 条)`): N must match actual count; ranges must enumerate around gaps (`REQ-F-073~078、REQ-F-080~082`), never span deleted IDs.
2. **§5 statistics table**: recount per-section totals AND P0/P1/P2 split from genuine headers — don't trust the old table.
3. **Doc-stated totals**: `合计 N 条` appears in multiple places (§5 table, appendix index footer) — fix all.
4. **§1.6 numbering rules**: ID range + explicit gap list; kill any stale "连续无跳号" claim.
5. **Deferred-requirements appendix**: #1 stale-ID hotspot — entries often cite pre-renumber IDs whose numbers now belong to DIFFERENT requirements (e.g. "REQ-F-138 布局缩放适配" when current F-138 is 右键菜单; real target was F-136). Match by TITLE, then fix ID+title+priority to current body.
6. **Change-log appendix**: every fix session appends rows (user convention: 编号 | 需求名称 | 变更类型 | 变更说明; use 变更类型=勘误 for editorial fixes).
7. **Missing chapter numbers** (§3.2 gap): user chose keep-number + one-line note over renumbering — ask, don't assume (see srs-renumbering "When NOT to Renumber").
8. **Hardcoded ID ranges inside requirement BODIES** (not just indexes/statistics): NFRs love phrasing like "所有功能需求（REQ-F-001 至 REQ-F-139）应正常工作" (browser-compat, performance NFRs). The range rots on ANY add/delete and silently spans gap IDs. Grep `REQ-F-\d{3}\s*(至|~|到)\s*REQ-F-\d{3}` outside index tables; replace with unbound phrasing: "所有功能需求（§3 全部 REQ-F 需求）". Caught in Lib REQ-NF-002 AC1 only on a SECOND verification pass — the range read plausibly and slipped the first review.
9. **New-REQ cascade checklist**: adding a single new requirement touches N locations — every one must be updated:
   - Section index header (`本节需求索引 (N 条)`) — increment count + extend range
   - §5 statistics row — increment section count + adjust P0/P1/P2 split
   - §5 totals row — increment totals (count, P0-2)
   - §1.6 numbering rules — extend ID range
   - Appendix index table — insert row at correct physical-order position
   - Appendix footer total — increment F count and overall total
   - Appendix C changelog — add row (变更类型=新增)
   *Proven in Lib session: adding REQ-F-141 touched all 7. When adding MULTIPLE new REQs (e.g., B3-B11 = 6 REQs + scope/docs fixes), batch the work: insert ALL requirements first, then sync ALL indices/stats/changelog/appendix in ONE pass. This turns N×7 touch-points into 1×7 — critical at scale.*

**Re-verification after user self-fix**: when the user fixes reported issues themselves and asks you to re-read, do three things — (a) verify EACH previously-reported item against the new text (report per-item ✅/❌ in a table), (b) independently recompute the statistics table (per-section counts AND P0/P1/P2 split) from genuine requirement headers — never diff against your memory of the old table, (c) run one FRESH residual scan for patterns adjacent to the fixed ones (that's how the hardcoded-range leftover in item 8 was found). Also check the change-log appendix gained rows covering the fixes; when you then make a follow-up edit, append your own change-log row in the same commit.

**Bulk-replace damage patterns** — after any terminology pass, grep for:
- Duplicated words: `Editor Editor Tab` (from Tab→Editor Tab replace hitting "Editor Tab")
- Suffix collisions: `Dock Region（Dock 区域）域` (replace target was substring of a longer word)
- Nested annotations: `Panel Header（Dock Panel（Dock 面板）标题栏）`
- Self-referential annotations: `Focus（键盘 Focus）`
- Broken Given/When/Then: AC with `When ...` followed by `And ...` but no `Then` (replace ate the Then line)
- Stray-space orphans: `不属于 面板`, `恢复 面板位置` (word deleted, space left)

**Annotation density rule** (user convention): `English（中文）` annotation appears ONCE per Title / Description / each-AC segment; later occurrences in the same segment use bare English. Enforce by script over requirement blocks only — mermaid/SVG labels are standalone (leave them); appendix index tables annotate per row (leave them).

**Verification**: run `scripts/verify_srs_consistency.py <SRS.md>` — counts genuine headers per section, lists ID gaps, flags index-header mismatches and same-segment duplicate annotations. Uses the strict header regex (emoji + `[Actor:`) — a loose `^REQ-F-\d{3}` also matches line-initial cross-refs like `REQ-F-017 所述的...` and corrupts segment state (bit us once; encoded in script). NOTE: the script reports per-SUBSECTION counts (§3.3 / §3.3.1 / §3.3.2 separately) while the doc's §5 statistics table aggregates at the §3.x level — sum subsections manually before comparing (e.g. 19+8+1=28 vs "§3.3: 28"). The "<-- index claims N!" warnings for parent sections are expected noise, not defects.
