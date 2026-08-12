# SRS-Specific Optimization Patterns

Concrete patterns extracted from the 示例项目 ↔ Lib comparison
session (2026-07-15). These are the deliverable-level details that sit
below the general methodology in SKILL.md.

## 示例项目 → Lib: What Transfered

### Structural Elements to Add

1. **Architecture diagram in §1 (Introduction)**
   - 示例项目 has Mermaid `flowchart LR` showing main→router→commands→storage
   - Lib had the detailed ASCII tree + SVG in §3.1 — move a simplified
     high-level Mermaid graph to Introduction, keep detail in §3
   - The intro diagram answers "what are the major pieces?" before diving in

2. **Data model / ER diagram in §1 (Introduction)**
   - 示例项目 §1.4 has `erDiagram` with entities + cardinality table
   - Lib has no entity-relationship view — Panel/Tab/Content relationships
     are scattered across prose
   - Add: Layout→Panel→Tab, ContentIdentifier→ContentComponent, with a
     cardinality constraints table

3. **Quick-Finder / decision tree**
   - 示例项目 §3 opens with a Mermaid flowchart: "What do you want to do?"
     → Object? → Action?
   - Lib's 150+ requirements are a flat list — add a decision tree
     branching on role (Developer/End User/System) → feature area → section
   - Also add a simple "I want to... → go to §X.Y" table

4. **Per-section requirement index**
   - Each 示例项目 sub-command section starts with an Options table
   - For Lib: add a "本节需求索引" block at each §3.x heading:
     ```
     > **本节需求索引 (N 条):** REQ-F-xxx~yyy — topic summary
     > | 你想... | 看这条 |
     ```

5. **Design Rationale callouts**
   - 示例项目 uses `> **💡 Design Rationale:** ...` for non-obvious decisions
   - Lib has none — add for decisions like "why Bottom Dock is sibling
     to Main Area, not child of Editor Container"

### Appendix-Level Elements to Add

6. **Requirement summary by role** (appendix)
   - 示例项目 §7.2: table of Role → Requirement IDs → Count
   - Lib has role definitions (§1.3.2) but no per-role requirement index
   - Essential for stakeholder review: "I'm the Application Developer — which
     of the 156 requirements apply to me?"

7. **Planned/Deferred requirements** (appendix)
   - 示例项目 §7.3: table of deferred REQ IDs with titles
   - Lib has P2 priorities scattered but no centralized "these are deferred"
   - Prevents scope disputes: "it's in the SRS" → "yes, but see Appendix C"

8. **Traceability matrix** (appendix)
   - 示例项目 §7.4: links requirements → docs/code/tests
   - Lib has none — add a table mapping requirement groups → design docs,
     implementation modules, and test suites

## What Lib Already Does Better (Keep)

These are Lib strengths that should NOT be "fixed":

| Lib Strength | Why Keep |
|-----------------|----------|
| Chinese main text + English terminology | Team convention; bilingual strategy works |
| AC1/AC2/AC3 explicit numbering | More testable than bare Given/When/Then |
| Cross-references (`参见 REQ-F-xxx`) | Dependency clarity |
| Inline merge annotations (`已合并: REQ-F-x→y`) | Document evolution traceable |
| Error code summary table (§3.9.1) | Single source of truth for error contracts |
| ASCII tree + SVG dual rendering (§3.1) | Text searchability + visual clarity |
| Lifecycle state diagrams (Appendix A) | Panel/Tab/Drag state machines |

## Hierarchy Flattening: Align with Established Reference Designs

When an SRS defines a hierarchical structure with intermediate containers
that carry no functional semantics, the hierarchy can (and should) be
flattened by referencing an established design authority. This was the
key finding from the VS Code alignment pass on Lib.

### Pattern

**Before (3-layer nesting with Content Area / Main Area):**
```
Work Area → Content Area → Main Area → {Left Dock, Editor, Right Dock}
                            ↘ Bottom Dock
```

**After (VS Code model, 1-layer flat):**
```
Work Area → LT | Left Dock | Editor Area | Right Dock | Bottom Dock | RT
```

### Decision Criteria for Flattening

1. **Do intermediate containers carry unique behavior or constraints?**
   Content Area and Main Area were pure grouping — no requirements depended
   on their existence. All constraints were about Dock panels being siblings
   of each other.

2. **Is there an established reference design?**
   VS Code Workbench is the most widely-used dock layout implementation.
   Aligning with it means developers already understand the mental model.

3. **Does flattening simplify downstream requirements?**
   - Dock swap logic: no more "跨 Main Area / Bottom Dock" special case — 
     all six Dock panels swap at the same level.
   - Splitter placement: no distinction between "Main Area internal" and
     "Main Area/Bottom Dock" splitters — all are same-level sibling splits.
   - Drag-drop target detection: no need to check if a drop crosses
     intermediate container boundaries.

4. **Does it enable future extensions?**
   VS Code allows the Panel (Bottom Dock) to be repositioned to Left, Right,
   or Bottom via a single toggle. A flat hierarchy makes this trivial.

### What to Update When Flattening

This is a non-trivial refactor affecting 10+ locations. Work top-down:

| Location | Change |
|----------|--------|
| §1.3 Architecture Mermaid | Remove intermediate subgraphs; flatten to 2 levels |
| §1.3 Constraint table | Remove "Bottom Dock is sibling of Main Area"; add "all Dock areas are Work Area direct children" |
| §1.5 Terminology | Delete Content Area, Main Area entries; update Editor Area, Work Area, Bottom Dock definitions |
| §3.1 ASCII tree | Flatten: all Dock areas move to Work Area's direct children list |
| §3.1 SVG | Redraw: no nested boxes for removed containers |
| §3.2 Characteristics table | "位置" column: change all "Main Area xxx" to "Work Area xxx" |
| REQ-F-002 Description + ACs | Rewrite bullet list and ACs with flat structure |
| REQ-F-025 Bottom Dock declaration | "Content Area中声明" → "Work Area中声明" |
| REQ-F-026 sibling constraint | Rename: "Bottom Dock与Main Area兄弟关系" → "Dock区域同级约束" |
| REQ-F-020 ToolBar structure | "Main Area+Bottom Dock" → enumerate all Dock areas |
| REQ-F-061, REQ-F-063 dock swap | "跨Main Area/Bottom Dock" → "跨区域" |
| REQ-F-078 docking target | "Content Area底部" → "Work Area底部" |
| REQ-F-093 layout restore | "Main Area与Bottom Dock之间" → "上部区域与Bottom Dock之间" |
| Global name change | "Editor Container" → "Editor Area" (34 occurrences) |

### Naming: Container vs Area

"Editor Container" was renamed to "Editor Area" to match VS Code's
terminology and to avoid implying it's a parent of other Dock panels.
"Area" signals it's a peer workspace, not a nesting container.

### Verification After Flattening

```sh
# Zero remaining references to deleted concepts
search_files(pattern='Content Area|Main Area')
# Expected: 0 functional references (2 explanatory "no longer exists" notes are OK)
```

Before proposing any addition to an SRS, verify:
- [ ] Is this about WHAT the system must do, not HOW?
- [ ] Would a non-technical stakeholder understand this?
- [ ] Is the diagram at "boxes and arrows" level, not "protocol and format"?
- [ ] Does the data model show entities and relationships, not columns and types?
- [ ] Would this same element appear in a Design Document? If yes, it doesn't belong here.

## Design Rationale Placement

Design Rationale callouts (`> **💡 Design Rationale:**`) should go at
non-obvious decision points only. Target 3-5 per document. Good locations:

- After an entity-relationship definition that has a non-obvious cardinality
- After an architectural constraint that a newcomer would question
- After a type/strategy choice (template vs dynamic, fixed vs swappable)
- After an error-handling strategy that could have been designed differently

Place AFTER the requirement or table that states the decision, BEFORE the
next section heading or `---` separator. Keep each rationale to 2-3 sentences:
what was chosen + why + what alternative was rejected.

## Execution Mechanics

When implementing changes via `patch()`:

1. **Read the target area immediately before patching.** File content shifts
   after previous edits — a string read 10 turns ago may not match anymore.
2. **Anchor on section headers** (e.g. `## 3.3 布局模板`), not line numbers.
3. **One logical change per `patch()` call** for clean diff history.
4. **Verify incrementally** with `search_files` after each major phase.
5. **Batch independent renames** — renumbering §2.3→§2.4 and §2.4→§2.5
   in separate but consecutive calls is safe because each targets a unique string.
6. **Use a `todo()` list** for changes spanning 10+ tool calls.
