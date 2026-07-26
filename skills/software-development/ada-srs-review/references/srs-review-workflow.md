# SRS Review — Full Workflow

The complete multi-pass audit methodology: 12 structured passes across 4 workflow steps, with detection signals, fix procedures, and real-world examples for each pass.

## Step 1: Map the Document Structure

Read the full document first. Build a mental map of:
- Chapter/section hierarchy
- Requirement numbering scheme (REQ-F-XXX, NFR-XXX, etc.)
- Priority/actor notation
- Cross-reference patterns

## Step 2: Run the Audit Passes

### Pass A — Dead Requirements (physically impossible scenarios)

For each requirement describing a user interaction or system behavior, ask: **"Can this actually happen?"**

Signals:
- A splitter dragged between two panels — can both sides hit minimum simultaneously? (No: one shrinks, one grows)
- Two panels claiming the same region name at runtime — can this happen? (Depends on whether panels can move between regions)
- Edge cases that are mathematically unreachable

**Action**: Remove or merge into a covering requirement. Add a deletion note with reasoning.

**Example**: REQ-F-086 (分割条双向锁定): Dragging a splitter shrinks one side while the other grows. Both sides cannot simultaneously hit their minimums — it's physically impossible. Single-side constraint already covered by REQ-F-085. → Delete.

### Pass B — Stale Cross-References

Search for references to requirements that have been merged, deleted, or renumbered. Use `search_files(pattern='REQ-F-XXX')` to find all references to a known-merged ID. Replace with the current requirement ID.

### Pass C — Concept Confusion & Terminology Audit

The most common SRS defect. Check whether the document uses the same word to mean different things, or different words to mean the same thing.

**Detection** — see `references/tab-panel-confusion.md` for the detection checklist and red-flag patterns. Core technique: define the entity model FIRST, then audit every requirement against those definitions.

**Execution** — when the audit reveals systemic terminology drift, follow the full execution methodology in `references/terminology-audit-execution.md`. Key steps: inventory → classify → propose bilingual glossary → replace most-specific-first → manual rewrite of heavy sections → SVG fix → statistics update → verification script.

**Bilingual rule**: User preference is `English（中文）` format. Glossary entries lead with English, Chinese follows in parentheses. In narrative text, the English form is sufficient after the glossary establishes the mapping. Region names (like `Left Dock Upper`) stay in English throughout — they map to code identifiers.

For dock-layout systems, the **four-concept model** (Region / DockPanel / EditorView / EditorTab) must be explicitly defined before auditing:

| Concept | Location | Role |
|---------|----------|------|
| Region | Layout tree | Spatial slot, no content lifecycle |
| DockPanel | Dock regions | Tool window, LT/RT switching, no Editor Tabs |
| EditorView | Editor Area | Split-view subcontainer, owns Editor Tabs |
| EditorTab | EditorView | Content switching unit |

Patterns to look for:
- "面板" used for both DockPanels AND EditorViews → each must be audited against its section context
- "最后一个标签页被移除" triggering DockPanel removal → DockPanel doesn't carry EditorTabs; triggers should be "面板内容被清空"
- Tab lifecycle rules (dynamic/template) belonging to DockPanel → they belong to EditorView
- Mixed interaction models conflated (e.g., "互换" vs "移动")

**Fix**: Define the concepts in a dedicated section (§1.7), then audit every requirement against those definitions. Move wrongly-placed requirements to their correct section. When a Dock Panel AC mentions "标签页", change it to "面板内容". When an Editor View AC mentions "面板", change it to "视图".

### Pass D — Implementation Details Leaking into Requirements

SRS defines **what**, not **how**. Scan for:

| Leak type | Example | Fix |
|-----------|---------|-----|
| Pixel values | "默认值为 36px" | "折叠至最小显示尺寸（如仅保留标题栏高度），具体数值由详细设计确定" |
| Animation durations | "300ms 延迟" | Keep if it's a UX behavior parameter; remove if purely visual |
| API field names | "IsNew 字段为 false" | Debatable — may be acceptable if it's part of the contract |
| Implementation notes | "使用 write-to-temp-then-rename" | Remove — belongs in design doc |

**When a numeric value IS acceptable**: 4px drag threshold (defines click-vs-drag), 200ms performance target (measurable NFR), 300ms auto-hide delay (user-perceived behavior). The test: "Would a designer change this value independently of engineering decisions?"

### Pass E — Scope Boundary Violations

Check that each section's requirements belong there. After establishing the four-concept model (Region vs DockPanel vs EditorView vs EditorTab):
- Tab-specific requirements (overflow, dedup, pin) should be in the Editor section, not the Dock section
- Panel move requirements should not be mixed with tab drag requirements
- Event requirements should not contain API signature details

### Pass F — Missing Behaviors

After fixing the above, check for behavioral gaps exposed by the corrections:
- If panels can move between regions (not swap), what happens when two panels occupy the same region? (stacking)
- If Bottom Dock can be hidden, what happens to the space? (upper areas expand)
- If a region has no visible panels, does it collapse?

### Pass G — Framework Coverage / Gap Analysis

Triggered by questions like "这份文档把 X 类框架的需求统计全了吗？还缺什么？". Run a systematic framework-completeness audit comparing the SRS against the full capability set of mature reference implementations (the ones the doc itself cites as 设计参照: VS Code, Rider).

**Six detection techniques** (detailed methodology in `references/gap-analysis-methodology.md`):

1. **Scope-table promises vs actual body**: §1.2 scope table and §2.2 role-navigation table promise capabilities per section. Verify each keyword has backing REQs.
2. **Concept-section mentions without backing REQ**: Terminology (§1.5) and concept (§1.7) tables describe behaviors that read like requirements — grep each behavioral claim for a covering REQ.
3. **Data-model fields without requirements**: Each ER-diagram field must be settable/observable via at least one REQ.
4. **Event/API symmetry**: List all lifecycle events side by side, check for missing pairs. Scan for referenced-but-undefined APIs.
5. **Type-declaration parity**: If entity A has a type-declaration REQ, entity B using the same taxonomy must have one too.
6. **Reference-framework capability diff**: Compare against the full capability set of cited reference implementations (VS Code/Rider). Missing capabilities that are standard in the industry go into either new REQs or the deferred-requirements appendix (explicit deferral beats silent absence).

**Contradiction detection**: cross-check the architecture section (§1.3 constraint table) against individual requirement ACs. Two valid sections prescribing conflicting behaviors for the same scenario. Resolution pattern: present both as 方案 A/B with an industry reference table, recommend the architecture's version. After user picks, fix the requirement + flowchart, and check whether the chosen model exposes a companion gap.

**Presentation format** (user preference): three blocks — A) Covered well (capability-domain × ✅ table), B) Gaps (numbered list with 现状/缺口/优先级 🔴🟡🟢 + suggested fix), C) Contradictions (location × 原文 side-by-side table with recommendation). End with a priority-ordered action table and a single question asking where to start. Do NOT edit the document during the gap-analysis reply — the user decides priorities first.

### Pass K — SRS-to-Code Coverage Analysis

When comparing SRS requirements against actual source code implementation (not against a reference product), use the workflow documented in `references/srs-to-code-coverage.md`. This is distinct from Pass G (SRS vs reference product): Pass K compares SRS against *actual code*, producing a coverage matrix with ✅/⚠️/❌/— status per requirement plus infrastructure deviation and base-class optimization documents.

When the user instead asks to **audit** an existing coverage report for accuracy — i.e. "复核 SRS 覆盖率报告的准确性" — use the "Auditing an Existing Coverage Report" workflow in the same reference. It prescribes spot-check sampling (10 Tested + 8 Not Implemented + 5 Partial) with **mandatory full-repo search across all source layers** (C#, TypeScript, .razor) to catch the common blind spot where C#-only scans miss TS/razor implementations.

### Pass H — Add Clarifying Diagrams

Requirements that are hard to understand from text alone need visual support.

**When to add a diagram:**
- Spatial zone divisions (5-zone docking direction) → SVG with colored regions
- Interaction sequences (auto-hide hover/expand/collapse) → Mermaid sequence diagram
- Before/after comparisons (panel stacking after move) → SVG with before/after panels
- Decision flows (ToolBar entry click logic) → Mermaid flowchart
- State transitions (panel lifecycle, tab lifecycle, drag state machine) → Mermaid stateDiagram-v2

**SVG conventions** (match the document's existing SVG style):
- `viewBox="0 0 W H"` — use landscape aspect ratios (1.5:1 to 2.5:1). Avoid tall/narrow or nearly-square SVGs.
- Color-code regions with CSS classes in `<defs><style>`: Fixed regions: gray (#f5f5f5), Navigation: blue (#e3f2fd), Dock: light blue (#f8fbff), Editor: green (#e8f5e9), Bottom: orange (#fff3e0)

### Pass I — Renumbering Requirements

When requirements need sequential renumbering (document is in draft, gaps from deletions):

1. Extract all current REQ IDs, sort by document appearance order, build an old→new mapping table
2. Use Python with word-boundary regex to replace all references:
   ```python
   pattern = r'(?<![0-9])' + re.escape(old_id) + r'(?![0-9])'
   ```
3. Sort replacements by key length (longest first) to prevent partial matches
4. After replacement, update: all section indexes, §1.6 numbering rules, §5 statistics table, appendix requirement matrix, error code table references
5. Verify: `grep -c "REQ-F-"` — all remaining IDs should be in the valid range
6. Old deleted-ID references in "已删除" notes should remain as-is (they're historical)

When the SRS references an external design model (e.g., VS Code Workbench), verify architectural and interaction concept alignment:

1. **Hierarchy depth**: Does the SRS have unnecessary intermediate containers? Flatten to match the reference.
2. **Interaction model**: Swap vs Move+Stack? Fix the model first, then rewrite every requirement to match.
3. **Naming**: "Editor Container" → "Editor Area"? "互换" → "移动"? Global replace_all first, then audit each occurrence for context-correctness.
4. **Ripple effects**: Swap→Stack makes splitter-adaptation requirements dead, changes ToolBar sync wording, may obsolete DUPLICATE_REGION_NAME error code.

**Action checklist after model change**:
- [ ] Delete dead splitter-adaptation requirements
- [ ] Rewrite swap ACs as move+stack ACs
- [ ] Update ToolBar sync requirements
- [ ] Remove obsolete error codes
- [ ] Update terminology table ("可互换" → "可停靠/堆叠")
- [ ] Update constraint table and section indexes
- [ ] Global search for residual "互换" references

### Pass J — Post-Edit Consistency Sync

Run after ANY add/delete/renumber. Audits section indexes, §5 statistics, numbering rules, deferred-requirements appendix, change log, hardcoded ID ranges in NFR bodies, and the new-REQ cascade checklist (7 touch-points per new requirement). Also includes bulk-replace damage pattern detection and annotation density enforcement.

**Full methodology**: see `references/pass-j-consistency-sync.md`.

## Step 3: Add Section Scope Notes

After concept clarification, add a scope note at the top of each major section:

```markdown
> **适用范围：** 本章全部需求仅针对 **Editor Area** 内的标签页（Editor Tab）。
> Dock 面板的切换通过 LT/RT 完成，不涉及 Tab 栏操作。
> 关于区域、Dock 面板、Editor View 与 Editor Tab 的区别，参见 [§1.7 空间概念](#17-空间概念)。
```

This prevents future readers (and future reviews) from re-confusing the concepts.

## Step 4: Update Change Log

Record every deletion, merge, and concept shift in an appendix change log. Format:

```markdown
| 日期 | 变更 | 作者 |
|------|------|:----:|
| YYYY-MM-DD | **变更类型**: 具体描述 | — |
```
