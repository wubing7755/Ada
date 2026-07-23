---
name: ada-srs-review
description: Systematic SRS (Software Requirements Specification) review — find dead requirements, stale references, concept confusion, scope violations, and implementation-detail leaks
version: 1.1.0
platforms: [linux, macos, windows]
author: Hermes Agent
metadata:
  hermes:
    related_skills: [ada-srs-lifecycle]
---

# SRS Review Methodology

Systematically audit a Software Requirements Specification document to identify structural and logical flaws before the document drives design and implementation.

## Triggers

- User asks to "review", "audit", or "check" an SRS document
- User says "这个需求是否合理" or "检查这个 SRS"
- Two SRS documents are compared for cross-learning
- User challenges a single requirement and you need to scale the check across the whole document

## Workflow

### 1. Map the document structure

Read the full document first. Build a mental map of:
- Chapter/section hierarchy
- Requirement numbering scheme (REQ-F-XXX, NFR-XXX, etc.)
- Priority/actor notation
- Cross-reference patterns

### 2. Run the audit passes

#### Pass A — Dead Requirements (physically impossible scenarios)

For each requirement describing a user interaction or system behavior, ask: **"Can this actually happen?"**

Signals:
- A splitter dragged between two panels — can both sides hit minimum simultaneously? (No: one shrinks, one grows)
- Two panels claiming the same region name at runtime — can this happen? (Depends on whether panels can move between regions)
- Edge cases that are mathematically unreachable

**Action**: Remove or merge into a covering requirement. Add a deletion note with reasoning.

**Examples from practice:**
- REQ-F-086 (分割条双向锁定): Dragging a splitter shrinks one side while the other grows. Both sides cannot simultaneously hit their minimums — it's physically impossible. Single-side constraint already covered by REQ-F-085. → Delete.
- REQ-F-004 AC3 (运行时重复区域名称检测): No runtime operation creates duplicate region names. After initialization, panels move but don't claim region names. → Delete the AC.
- REQ-F-110 "若目标面板处于折叠或自动隐藏状态": Editor Area tabs don't fold/auto-hide — that's a Dock Panel feature. The AC describes an impossible scenario for Editor Tabs. → Remove the fold/auto-hide clauses.

#### Pass B — Stale Cross-References

Search for references to requirements that have been:
- Merged (e.g., REQ-F-028 → REQ-F-027)
- Deleted (e.g., REQ-F-086, REQ-F-063)
- Renamed or renumbered

Use `search_files(pattern='REQ-F-XXX')` to find all references to a known-merged ID. Replace with the current requirement ID.

#### Pass C — Concept Confusion & Terminology Audit

The most common SRS defect. Check whether the document uses the same word to mean different things, or different words to mean the same thing.

**Detection** — see `references/tab-panel-confusion.md` for the detection checklist and red-flag patterns. Core technique: define the entity model FIRST, then audit every requirement against those definitions.

**Execution** — when the audit reveals systemic terminology drift (multiple term families for the same concept, legacy model remnants), follow the full execution methodology in `references/terminology-audit-execution.md`. Key steps: inventory → classify → propose bilingual glossary → replace most-specific-first → manual rewrite of heavy sections → SVG fix → statistics update → verification script.

**Bilingual rule**: User preference is `English（中文）` format. Glossary entries lead with English, Chinese follows in parentheses. In narrative text, the English form is sufficient after the glossary establishes the mapping. Region names (like `Left Dock Upper`) stay in English throughout — they map to code identifiers.

For dock-layout systems, the **four-concept model** (Region / DockPanel / EditorView / EditorTab) must be explicitly defined before auditing:

| Concept | Location | Role |
|---------|----------|------|
| Region | Layout tree | Spatial slot, no content lifecycle |
| DockPanel | Dock regions | Tool window, LT/RT switching, no Editor Tabs |
| EditorView | Editor Area | Split-view subcontainer, owns Editor Tabs |
| EditorTab | EditorView | Content switching unit |

Pattern to look for:
- "面板" used for both DockPanels AND EditorViews → each must be audited against its section context
- "最后一个标签页被移除" triggering DockPanel removal → DockPanel doesn't carry EditorTabs; triggers should be "面板内容被清空"
- Tab lifecycle rules (dynamic/template) belonging to DockPanel → they belong to EditorView
- Mixed interaction models conflated (e.g., "互换" vs "移动")

**Fix**: Define the concepts in a dedicated section (§1.7), then audit every requirement against those definitions. Move wrongly-placed requirements to their correct section. When a Dock Panel AC mentions "标签页", change it to "面板内容". When an Editor View AC mentions "面板", change it to "视图".

#### Pass D — Implementation Details Leaking into Requirements

SRS defines **what**, not **how**. Scan for:

| Leak type | Example | Fix |
|-----------|---------|-----|
| Pixel values | "默认值为 36px" | "折叠至最小显示尺寸（如仅保留标题栏高度），具体数值由详细设计确定" |
| Animation durations | "300ms 延迟" | Keep if it's a UX behavior parameter; remove if purely visual |
| API field names | "IsNew 字段为 false" | Debatable — may be acceptable if it's part of the contract |
| Implementation notes | "使用 write-to-temp-then-rename" | Remove — belongs in design doc |

**When a numeric value IS acceptable**: 4px drag threshold (defines click-vs-drag), 200ms performance target (measurable NFR), 300ms auto-hide delay (user-perceived behavior). The test: "Would a designer change this value independently of engineering decisions?"

#### Pass E — Scope Boundary Violations

Check that each section's requirements belong there. After establishing the four-concept model (Region vs DockPanel vs EditorView vs EditorTab):
- Tab-specific requirements (overflow, dedup, pin) should be in the Editor section, not the Dock section
- Panel move requirements should not be mixed with tab drag requirements
- Event requirements should not contain API signature details

#### Pass F — Missing Behaviors

After fixing the above, check for behavioral gaps exposed by the corrections:
- If panels can move between regions (not swap), what happens when two panels occupy the same region? (stacking)
- If Bottom Dock can be hidden, what happens to the space? (upper areas expand)
- If a region has no visible panels, does it collapse?

#### Pass G — Framework Coverage / Gap Analysis

Triggered by questions like "这份文档把 X 类框架的需求统计全了吗？还缺什么？" or "还有需要补充的需求点吗？". Run a systematic framework-completeness audit comparing the SRS against the full capability set of mature reference implementations (the ones the doc itself cites as 设计参照: VS Code, Rider).

**Six detection techniques**, each cross-references a different document layer:

1. **Scope-table promises vs actual body**: §1.2 scope table and §2.2 role-navigation table promise capabilities per section. Verify each keyword has backing REQs. *Atlas case*: "§3.8 主题、国际化" was promised in two places; §3.8 had zero requirements. Either add REQs or remove from scope table.

2. **Concept-section mentions without backing REQ**: Terminology (§1.5) and concept (§1.7) tables describe behaviors that read like requirements — grep each behavioral claim for a covering REQ. *Atlas case*: "关闭 | 通过 Panel Header 关闭按钮" and "拖拽 Header 在同一区域内排序" were both described, neither had a REQ.

3. **Data-model fields without requirements**: Each ER-diagram field must be settable/observable via at least one REQ. *Atlas case*: `sizeRatio` existed in the data model and was restored on import (F-086), but no REQ let developers declare initial ratios.

4. **Event/API symmetry**: List all lifecycle events side by side, check for missing pairs. *Atlas case*: Tab had activate (F-111) and close (F-112) but no open event; Panel had create (F-113) and remove (F-114) but no visibility-change event. Also scan for referenced-but-undefined APIs: F-109 AC3 said "开发者调用销毁接口" but no REQ defined destroy.

5. **Type-declaration parity**: If entity A has a type-declaration REQ, entity B using the same taxonomy must have one too. *Atlas case*: Panel had Template/Dynamic declaration via F-019; Editor View used Template/Dynamic View in F-031/032 but had no declaration REQ.

6. **Reference-framework capability diff**: Compare against the full capability set of the cited reference implementations (VS Code/Rider). Missing capabilities that are standard in the industry go into either new REQs or the deferred-requirements appendix (explicit deferral beats silent absence). *Atlas case*: floating windows, panel maximize, panel title/icon declaration, container-resize adaptation, in-region reorder — most were absent or underspecified. Floating Window was mentioned three times in body text as "future extension" but had no appendix-B deferred entry.

**Contradiction detection (supplemental to gap analysis)**: cross-check the architecture section (§1.3 constraint table) against individual requirement ACs. This is a distinct defect class from Pass A (physically impossible) and Pass C (concept confusion) — it's two valid sections prescribing conflicting behaviors for the same scenario. *Atlas case*: §1.3 said "再次点击收起 Dock Panel" (toggle model), F-022 AC2 said "不关闭任何面板" (no-op model). The architecture wording usually reflects design intent; the requirement drifted. Resolution pattern: present both options as 方案 A/B with a comparison table of how VS Code/Rider handle it, and recommend the architecture's version. After user picks, fix the requirement + flowchart, and check whether the chosen model exposes a companion gap.

**Presentation format** (user preference, proven in Atlas session): three blocks —
- **A) Covered well**: table of capability-domain × ✅, confirming what's solid
- **B) Gaps**: numbered list, each with 现状/缺口/优先级 🔴🟡🟢 + suggested fix
- **C) Contradictions**: location × 原文 side-by-side table, with a recommendation

End with a priority-ordered action table and a single question asking where to start. Do NOT edit the document during the gap-analysis reply — the user decides priorities first.

#### Pass K — SRS-to-Code Coverage Analysis

When the user asks to compare SRS requirements against actual source code
implementation (not against a reference product), use the workflow documented
in `references/srs-to-code-coverage.md`. This is distinct from Pass G
(SRS vs reference product): Pass K compares SRS against *actual code*,
producing a coverage matrix with ✅/⚠️/❌/— status per requirement plus
infrastructure deviation and base-class optimization documents.

When the user instead asks to **audit** an existing coverage report for
accuracy — i.e. "复核 SRS 覆盖率报告的准确性" — use the "Auditing an
Existing Coverage Report" workflow in the same reference. It prescribes
spot-check sampling (10 Tested + 8 Not Implemented + 5 Partial) with
**mandatory full-repo search across all source layers** (C#, TypeScript,
.razor) to catch the common blind spot where C#-only scans miss TS/razor
implementations.

#### Pass H — Add Clarifying Diagrams

Requirements that are hard to understand from text alone need visual support.

**When to add a diagram:**
- Spatial zone divisions (5-zone docking direction) → SVG with colored regions
- Interaction sequences (auto-hide hover/expand/collapse) → Mermaid sequence diagram
- Before/after comparisons (panel stacking after move) → SVG with before/after panels
- Decision flows (ToolBar entry click logic) → Mermaid flowchart
- State transitions (panel lifecycle, tab lifecycle, drag state machine) → Mermaid stateDiagram-v2

**SVG conventions (match the document's existing SVG style):**
- `viewBox="0 0 W H"` — W: 440~760, H: 270~390 for comfortable markdown preview
- Use landscape aspect ratios (1.5:1 to 2.5:1). Avoid tall/narrow or nearly-square SVGs.
- Color-code regions with CSS classes in `<defs><style>`:
  - Fixed regions: gray (#f5f5f5), Navigation: blue (#e3f2fd)
  - Dock: light blue (#f8fbff), Editor: green (#e8f5e9), Bottom: orange (#fff3e0)
- Include a legend box (bottom-right, 8×8 swatches, 8px font)
- Use header+body two-layer structure for panel regions (darker header bar, lighter content area)
- Add content hint lines in the Editor Area (gray horizontal bars suggesting code)

**Prefer SVG over ASCII art** when the diagram shows spatial layout, color-coded regions, or before/after states. ASCII is fine for simple trees and tables.

#### Pass I — Renumbering Requirements

When requirements need sequential renumbering (document is in draft, gaps from deletions):

1. Extract all current REQ IDs, sort by document appearance order
2. Build an old→new mapping table
3. Use Python with word-boundary regex to replace all references:
   ```python
   pattern = r'(?<![0-9])' + re.escape(old_id) + r'(?![0-9])'
   ```
4. Sort replacements by key length (longest first) to prevent partial matches
5. After replacement, update:
   - All section indexes (search for "本节需求索引")
   - §1.6 numbering rules
   - §5 statistics table (section names, counts, priority distribution)
   - Appendix requirement matrix (regenerate entirely)
   - Error code table references
6. Verify: `grep -c "REQ-F-" ` — all remaining IDs should be in the valid range
7. Old deleted-ID references in "已删除" notes should remain as-is (they're historical)

When the SRS references an external design model (e.g., VS Code Workbench), verify that every architectural and interaction concept aligns:

1. **Hierarchy depth**: Does the SRS have unnecessary intermediate containers (Content Area, Main Area) that the reference model doesn't? Flatten to match the reference.
2. **Interaction model**: Swap vs Move+Stack? The SRS may describe one model in §3.2 but use the other in §3.5's requirements. Fix the model first (in architecture/terminology sections), then rewrite every requirement to match.
3. **Naming**: "Editor Container" → "Editor Area"? "互换" → "移动"? Do a global replace_all first, then audit each occurrence for context-correctness.
4. **Ripple effects of model change**: When you change from swap to move+stack, requirements about "swap splitter adaptation" become dead; "panel swap" in ToolBar sync requirements becomes "panel move"; DUPLICATE_REGION_NAME error code may become obsolete.

**Action checklist after model change**:
- [ ] Delete dead splitter-adaptation requirements (REQ-F-063-like)
- [ ] Rewrite swap ACs as move+stack ACs
- [ ] Update ToolBar sync requirements (from "swap entries" to "move entry to target side")
- [ ] Remove obsolete error codes (DUPLICATE_REGION_NAME)
- [ ] Update terminology table ("可互换" → "可停靠/堆叠")
- [ ] Update constraint table in §1.x
- [ ] Update section indexes
- [ ] Global search for residual "互换" references

## Pass J — Post-Edit Consistency Sync (run after ANY add/delete/renumber)

Requirement deletions/additions silently rot the document's self-descriptions. Audit ALL of:

1. **Section index headers** (`本节需求索引 (N 条)`): N must match actual count; ranges must enumerate around gaps (`REQ-F-073~078、REQ-F-080~082`), never span deleted IDs.
2. **§5 statistics table**: recount per-section totals AND P0/P1/P2 split from genuine headers — don't trust the old table.
3. **Doc-stated totals**: `合计 N 条` appears in multiple places (§5 table, appendix index footer) — fix all.
4. **§1.6 numbering rules**: ID range + explicit gap list; kill any stale "连续无跳号" claim.
5. **Deferred-requirements appendix**: #1 stale-ID hotspot — entries often cite pre-renumber IDs whose numbers now belong to DIFFERENT requirements (e.g. "REQ-F-138 布局缩放适配" when current F-138 is 右键菜单; real target was F-136). Match by TITLE, then fix ID+title+priority to current body.
6. **Change-log appendix**: every fix session appends rows (user convention: 编号 | 需求名称 | 变更类型 | 变更说明; use 变更类型=勘误 for editorial fixes).
7. **Missing chapter numbers** (§3.2 gap): user chose keep-number + one-line note over renumbering — ask, don't assume (see srs-renumbering "When NOT to Renumber").
8. **Hardcoded ID ranges inside requirement BODIES** (not just indexes/statistics): NFRs love phrasing like "所有功能需求（REQ-F-001 至 REQ-F-139）应正常工作" (browser-compat, performance NFRs). The range rots on ANY add/delete and silently spans gap IDs. Grep `REQ-F-\\d{3}\\s*(至|~|到)\\s*REQ-F-\\d{3}` outside index tables; replace with unbound phrasing: "所有功能需求（§3 全部 REQ-F 需求）". Caught in Atlas REQ-NF-002 AC1 only on a SECOND verification pass — the range read plausibly and slipped the first review.
9. **New-REQ cascade checklist**: adding a single new requirement touches N locations — every one must be updated:
   - Section index header (`本节需求索引 (N 条)`) — increment count + extend range
   - §5 statistics row — increment section count + adjust P0/P1/P2 split
   - §5 totals row — increment totals (count, P0-2)
   - §1.6 numbering rules — extend ID range
   - Appendix index table — insert row at correct physical-order position
   - Appendix footer total — increment F count and overall total
   - Appendix C changelog — add row (变更类型=新增)
   *Proven in Atlas session: adding REQ-F-141 touched all 7. When adding MULTIPLE new REQs (e.g., B3-B11 = 6 REQs + scope/docs fixes), batch the work: insert ALL requirements first, then sync ALL indices/stats/changelog/appendix in ONE pass. This turns N×7 touch-points into 1×7 — critical at scale.*

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

### 3. Add Section Scope Notes

After concept clarification, add a scope note at the top of each major section:

```markdown
> **适用范围：** 本章全部需求仅针对 **Editor Area** 内的标签页（Editor Tab）。
> Dock 面板的切换通过 LT/RT 完成，不涉及 Tab 栏操作。
> 关于区域、Dock 面板、Editor View 与 Editor Tab 的区别，参见 [§1.7 空间概念](#17-空间概念)。
```

This prevents future readers (and future reviews) from re-confusing the concepts.

### 4. Update Change Log

Record every deletion, merge, and concept shift in an appendix change log. Format:

```markdown
| 日期 | 变更 | 作者 |
|------|------|:----:|
| YYYY-MM-DD | **变更类型**: 具体描述 | — |
```

## Pitfalls

- **Don't review in isolation**: Cross-reference every requirement against the architecture section (§1.x) and concept definitions. A requirement that looks fine in isolation may be nonsense when checked against the data model.
- **Don't be shy about deleting**: Dead requirements (physically impossible scenarios) should be removed, not marked "future" or "low priority". They confuse implementers.
- **Stale references propagate**: When you merge/delete a requirement, search the ENTIRE document for references to it — not just the obvious cross-references, but also casual mentions in descriptions and change logs.
- **User intuition is a signal**: When the user questions "这个需求合理吗？" or "这个能实现吗？", they've likely spotted a real issue. Scale that check across the section.
- **Concept definitions must come first**: Don't try to fix concept confusion by renaming individual requirements. Define the concepts in a dedicated section (e.g., §1.7), then audit against those definitions.
- **Section headers are part of the audit**: "内容渲染与页签管理" doesn't tell the reader what kind of content or what kind of tabs. Rename to be specific: "Editor 标签页管理".
- **Swap → Stack is a cascade, not a rename**: Changing from swap to move+stack affects requirements, ToolBar sync, error codes, splitter logic, constraint tables, and RTL镜像 descriptions. Don't just rename — verify every occurrence of "互换" in the document and decide whether it becomes "移动", "堆叠", "镜像互换" (RTL), or is deleted entirely.
- **Batch priority symbols with replace_all**: When §1.x defines 🔴🟡🟢 but requirements still use `[P0]`/`[P1]`/`[P2]`, use three `replace_all=True` calls: `[P0]`→`🔴`, `[P1]`→`🟡`, `[P2]`→`🟢`. This avoids editing 150+ requirements by hand. Verify that the statistics table uses unbracketed `P0` (it won't be affected).
- **Markdown fences after tables**: After an error code summary table (which is a plain markdown table, not a code block), stray ``` fences may appear. Remove them — they break the rendering of the next code block. Check the entire document for empty ``` pairs with nothing between them.

- **AC extension over new requirement**: When adding a behavior that naturally follows from an existing requirement, add an Acceptance Criterion (AC) rather than creating a new REQ. Example: Bottom Dock visibility when all panels are hidden (REQ-F-026 AC3) naturally extends REQ-F-026 AC2's space allocation model. A new REQ would fragment related concerns.

- **Missing behavior detection**: After fixing a concept (e.g., panels move rather than swap), reverse-engineer the consequences: "If panels can move to any region and stack, what happens when the last panel in a region is hidden? Does the region collapse?" Fill these gaps proactively.

- **SVG sizing for markdown preview**: SVGs embedded in SRS documents should use landscape-proportioned viewBox (e.g., 760×390, not 800×520 or 440×370). The aspect ratio should be roughly 2:1. Tall/narrow SVGs (1.2:1 or squarer) look wrong in wide markdown content areas. When creating SVGs for spatial concepts (docking zones, layout structure, stacking), use:
  - `viewBox="0 0 760 390"` for full-layout diagrams
  - `viewBox="0 0 440 270"` for single-panel zone diagrams
  - `viewBox="0 0 680 290"` for before/after comparisons
  - CSS classes in `<defs><style>` for consistent coloring across regions
  - A small legend box (bottom-right corner, 8×8 swatches with 8px labels)
  - Color coding: gray (#f5f5f5) for fixed areas, blue (#e3f2fd) for navigation, green (#e8f5e9) for workspace, light blue (#f8fbff) for dockable areas

- **Stacking diagrams must show the XDocker model correctly**: Before/after panel-move diagrams are the #1 place where the XDocker model gets misrepresented. The model rule is: only ONE panel is expanded/visible in a Dock region at a time; additional panels in the same region are collapsed to LT/RT ToolBar entries — they are NOT visible as stacked content rectangles. A correct stacking diagram must include:
  1. LT/RT thin vertical sidebars with ToolBar entry badges (highlighted = active, dim = collapsed)
  2. Before state: each visible panel has its entry on the correct side toolbar
  3. After state: the moved panel's entry migrates to the target side toolbar; the hidden panel's entry stays on its original side
  4. The target region shows ONLY the newly active panel (expanded to fill the area), NOT two panels one above another with a separator line
  5. Never use "更多面板可堆叠" or similar wording implying multiple simultaneously visible panels. Correct: "同区域其余面板收起为 LT/RT 条目"
  6. Use `viewBox="0 0 760 300"` for before/after stacking diagrams (need room for LT+Dock+Dock+RT on each half)

- **Requirements matrix vs traceability matrix**: When the project has no design docs, code modules, or test suites yet, a "traceability matrix" (linking requirements→design→code→tests) is empty scaffolding. Replace it with a "需求矩阵" — a flat table listing every requirement by section, with ID, priority, actor, and title. This is useful immediately and can be updated to a traceability matrix later. Use `grep + python3` to extract all REQ-F/NF headers and titles programmatically — the file may be too large for regex-only approaches.

- **Contradiction resolution needs user decision before edits**: When architecture (§1.3) and a requirement AC disagree on the same scenario, DON'T pick a side silently. Present both as 方案 A/B with an industry reference table (how VS Code/Rider do it) and a recommendation. *Atlas case*: §1.3 said toggle, F-022 said no-op; user chose toggle after seeing that both VS Code and Rider use toggle. Then the chosen model exposed a companion gap (header close button + API needed a separate REQ) — trace the cascade.

- **Batch-insert-then-sync for multi-REQ additions**: When adding 6+ new requirements across multiple sections, insert ALL REQ bodies first (insertion is cheap), then update all indices/stats/changelog/appendix in a single sync pass. This avoids N×7 cascading edits per REQ. *Atlas case*: B3-B11 produced 6 REQs + 3 doc fixes (scope table, appendix B, appendix D) — 9 insertions followed by 1 sync pass of ~20 patch calls, verified once with `verify_srs_consistency.py`.
