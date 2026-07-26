---
name: ada-srs-review
description: "Use when reviewing an SRS for quality: dead requirements, stale cross-references, concept confusion, scope leaks, implementation details, missing ACs, or terminology drift. For source code quality, use ada-code-quality-analysis; for large edits after findings, use ada-srs-revision."
version: 1.1.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [srs, review, requirements, quality]
    related_skills: [ada-srs-lifecycle]
---

# SRS Review Methodology

Systematically audit a Software Requirements Specification document to identify structural and logical flaws before the document drives design and implementation.

## Agent Execution Contract

Inputs to identify first:
- SRS path and any linked terminology, architecture, traceability, or source-code references.
- Review scope: full document, specific section, post-edit sync, framework gap analysis, or code coverage audit.
- Requirement ID format and priority/actor conventions.

Default workflow:
1. Map the document structure before judging individual requirements.
2. Choose the relevant passes instead of blindly running all passes for small scopes.
3. Search cross-references globally before deleting, merging, or renumbering requirements.
4. Separate findings from edits unless the user asked for direct revision.
5. Route large-scale fixes to `ada-srs-revision`.

Stop conditions:
- A contradiction requires product/architecture intent, not editorial judgment.
- Source documents or referenced sections are missing.
- The requested fix would change requirement semantics without user approval.

Output contract:
- Review scope and passes run.
- Findings with location, issue, risk, and recommended action.
- Required user decisions.
- Suggested next revision order.
- Consistency checks performed.

## Overview

`ada-srs-review` is a systematic audit methodology for Software Requirements Specification documents. It runs 12 structured passes (Pass A–K plus Pass J for post-edit consistency sync) that collectively catch: dead requirements describing physically impossible scenarios (Pass A), stale cross-references to merged or deleted requirements (Pass B), concept confusion and terminology drift (Pass C), implementation-detail leaks (Pass D), scope boundary violations (Pass E), missing behaviors exposed by corrections (Pass F), framework coverage gaps against reference implementations (Pass G), SRS-to-code coverage mismatches (Pass K), and silent post-edit rot in indexes, statistics, and cross-references (Pass J). Developed and hardened on the Atlas/xDocker SRS — a 4700+ line dock-layout specification — each pass includes detection signals, fix procedures, and real-world examples of the defect class it targets.

## When to Use

Use when:
- User asks to "review", "audit", or "check" an SRS document for quality
- User questions a single requirement's validity ("这个需求合理吗？") and you need to scale the check across the whole document
- After any large-scale revision — run Pass J (post-edit consistency sync) to catch silently rotted indexes, statistics, numbering rules, deferred-requirements appendix entries, change log, and hardcoded ID ranges
- Comparing an SRS against a reference implementation's full capability set (Pass G — framework coverage / gap analysis)
- Comparing SRS requirements against actual source code implementation (Pass K — SRS-to-code coverage analysis)
- Before handing off an SRS to design or implementation — a pre-handoff quality gate
- Auditing an existing coverage report for accuracy (Pass K — "复核 SRS 覆盖率报告的准确性")

Don't use for:
- Writing new requirements — use direct authoring or lightweight requirement writing
- Deriving SRS from a TP — use protocol-to-SRS derivation
- Executing fixes found during review — use large-scale revision for global changes or surgical authoring for targeted edits

## Workflow

The review follows a 4-step process with 12 structured audit passes (Pass A–K plus Pass J for post-edit consistency sync). **Full methodology with detection signals, fix procedures, and real-world examples**: `references/srs-review-workflow.md`.

### Quick Reference — The 12 Passes

| Pass | Focus | Detailed Reference |
|------|-------|--------------------|
| **A** | Dead Requirements — physically impossible scenarios | workflow |
| **B** | Stale Cross-References to merged/deleted/renumbered REQs | workflow |
| **C** | Concept Confusion & Terminology Audit | `tab-panel-confusion.md`, `terminology-audit-execution.md` |
| **D** | Implementation Details Leaking into Requirements | workflow |
| **E** | Scope Boundary Violations | workflow |
| **F** | Missing Behaviors exposed by corrections | workflow |
| **G** | Framework Coverage / Gap Analysis vs reference implementations | `gap-analysis-methodology.md` |
| **H** | Add Clarifying Diagrams (SVG, Mermaid) | workflow |
| **I** | Renumbering Requirements (with ripple-effect checklist) | workflow |
| **J** | Post-Edit Consistency Sync (indexes, stats, rules, appendix, change log) | `pass-j-consistency-sync.md` |
| **K** | SRS-to-Code Coverage Analysis | `srs-to-code-coverage.md` |

### The 4 Workflow Steps

1. **Map the document structure** — read the full document, build a mental map of hierarchy, numbering scheme, notation, and cross-reference patterns before any audit pass.
2. **Run the audit passes** — execute Pass A through K in order. Each pass has detection signals, fix procedures, and verification steps detailed in `references/srs-review-workflow.md`.
3. **Add Section Scope Notes** — after concept clarification, add scope notes at the top of each major section to prevent future concept confusion.
4. **Update Change Log** — record every deletion, merge, and concept shift in an appendix change log with date, change type, and author.

## Common Pitfalls

- **Don't review in isolation**: Cross-reference every requirement against the architecture section (§1.x) and concept definitions. A requirement that looks fine in isolation may be nonsense when checked against the data model.
- **Don't be shy about deleting**: Dead requirements should be removed, not marked "future" or "low priority". They confuse implementers.
- **Stale references propagate**: When you merge/delete a requirement, search the ENTIRE document for references — not just obvious cross-references, but casual mentions in descriptions and change logs.
- **User intuition is a signal**: When the user questions "这个需求合理吗？", they've likely spotted a real issue. Scale that check across the section.
- **Concept definitions must come first**: Define the concepts in a dedicated section (e.g., §1.7), then audit against those definitions — don't rename individual requirements in isolation.
- **Section headers are part of the audit**: "内容渲染与页签管理" doesn't tell the reader what kind of tabs. Rename to "Editor 标签页管理".
- **Swap → Stack is a cascade, not a rename**: Changing from swap to move+stack affects requirements, ToolBar sync, error codes, splitter logic, and constraint tables. Verify every "互换" occurrence — it may become "移动", "堆叠", "镜像互换" (RTL), or be deleted.
- **Batch priority symbols with replace_all**: When migrating `[P0]`/`[P1]`/`[P2]` to 🔴🟡🟢, use three `replace_all=True` calls. Verify statistics table uses unbracketed `P0` (unaffected).
- **Markdown fences after tables**: Stray ``` fences after plain markdown tables break rendering. Check the entire document for empty ``` pairs.
- **AC extension over new requirement**: When a behavior naturally follows from an existing requirement, add an Acceptance Criterion (AC) rather than creating a new REQ. A new REQ fragments related concerns.
- **Missing behavior detection**: After fixing a concept (e.g., panels move rather than swap), reverse-engineer the consequences: "What happens when the last panel in a region is hidden? Does the region collapse?" Fill gaps proactively.
- **SVG sizing for markdown preview**: Use landscape-proportioned viewBox with ~2:1 aspect ratio. Full-layout: `760×390`; single-panel zone: `440×270`; before/after: `680×290`. Color-code with CSS: gray (#f5f5f5) fixed, blue (#e3f2fd) navigation, green (#e8f5e9) workspace, light blue (#f8fbff) dockable. Include legend box.
- **Stacking diagrams must show the XDocker model correctly**: Only ONE panel is visible in a Dock region at a time; others collapse to LT/RT ToolBar entries — NOT stacked content rectangles. Include LT/RT sidebars with entry badges, before/after states with toolbar migration, and never show two panels with a separator line. Use "同区域其余面板收起为 LT/RT 条目", not "更多面板可堆叠". Use `viewBox="0 0 760 300"`.
- **Requirements matrix vs traceability matrix**: Without design docs or test suites, a traceability matrix is empty scaffolding. Replace it with a "需求矩阵" — a flat table of every requirement by section (ID, priority, actor, title). Extract programmatically with `grep + python3`.
- **Contradiction resolution needs user decision**: When §1.3 and a requirement AC disagree, present both as 方案 A/B with industry reference + recommendation. Don't pick silently. After user picks, trace the cascade for companion gaps.
- **Batch-insert-then-sync for multi-REQ additions**: Insert ALL REQ bodies first, then update indices/stats/changelog/appendix in ONE pass. Avoids N×7 edits per REQ.

## Verification Checklist

- [ ] Full document read and section hierarchy mapped before starting any audit pass
- [ ] Pass A complete: all dead requirements (physically impossible scenarios) identified, flagged, and rationale documented
- [ ] Pass B complete: all stale cross-references to merged/deleted requirements found via `search_files` and updated to current IDs
- [ ] Pass C complete: concept confusion and terminology drift audited against explicit entity definitions (e.g., the four-concept model: Region / DockPanel / EditorView / EditorTab)
- [ ] Pass D complete: implementation details (pixel values, animation durations, API field names) flagged and either justified or removed
- [ ] Pass E complete: scope boundary violations corrected — requirements filed under their correct section
- [ ] Pass F complete: missing behaviors exposed by corrections identified and filled
- [ ] Pass G complete: framework coverage gaps against reference implementations identified, contradictions between §1.3 and requirement ACs resolved
- [ ] Pass K complete (if applicable): SRS-to-code coverage analysis done or existing report audited for accuracy
- [ ] Pass H complete: clarifying diagrams added for spatial, sequence, state, or decision concepts
- [ ] Pass I complete: numbering consistent, all cross-references updated, statistics regenerated
- [ ] Pass J complete: section indexes recount matches actual headers, §5 statistics recomputed from genuine requirement headers, numbering rules reflect current gaps, deferred-requirements appendix entries match by title not stale ID, change log appended, hardcoded ID ranges in NFR bodies replaced with unbound phrasing
- [ ] Section scope notes added after concept clarification
- [ ] Change log updated with all deletions, merges, and concept shifts
