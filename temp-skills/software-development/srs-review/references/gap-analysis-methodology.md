# SRS Gap Analysis — Reference Implementation Methodology

How to systematically identify missing requirements by comparing an SRS
against mature reference implementations (VS Code, Rider, etc.) and the
document's own scope declarations.

## When to Use

- User asks "这个 SRS 是否完整？", "还有需要补充的需求点吗？"
- After a major concept fix or model change, when you suspect behavioral gaps
- Before starting implementation — last-chance completeness check

## Workflow

### 1. Inventory what's covered

Build a capability matrix by scanning the SRS sections:

| Capability | § | Coverage |
|-----------|----|:--:|
| Layout declaration | §3.3 | ✅ Complete |
| Editor Tab lifecycle | §3.4 | ✅ 42 REQs |
| Dock Panel move | §3.5 | ✅ 4 REQs |
| ... | ... | ... |

### 2. Compare against reference implementations

Pick 2-3 mature dock-layout implementations (VS Code, Rider, Eclipse).
For each, list every user-facing capability. Cross-check against the SRS
inventory. Tag gaps with one of:

- **Missing**: capability absent from SRS entirely
- **Under-specified**: capability mentioned in prose (§1.7, §1.3) but no REQ
- **Contradiction**: two sections describe different behavior for the same
  interaction (e.g., §1.3 says "收起 Panel" but F-022 says "不关闭")

### 3. Check scope declarations against body

Read §1.2 (range table) and §2.2 (role navigation). For every capability
claimed in scope, verify at least one REQ exists in the body. Common
patterns:

- §1.2 says §3.8 covers "主题、国际化" → zero REQs in §3.8 → scope lie
- §3.1 mentions "后续扩展 Floating Window" → not in deferred list → implicit
  deferral should be explicit

### 4. Check data model fields against REQs

The ER diagram (§1.4) defines fields (e.g., `sizeRatio`, `autoHide`). For
each field, verify there is at least one REQ that:
- Sets it (declaration)
- Changes it (operation)
- Reads it (export/API)

Fields with no controlling REQ are dead columns.

### 5. Categorize gaps by priority

| Priority | Criteria | Example |
|:--------:|----------|---------|
| 🔴 P0 | Core framework completeness — missing renders the dock layout unfit for basic use. Also: model-level contradictions that must be resolved before implementation | Panel show/hide (B1), §1.3 vs F-022 contradiction (C1) |
| 🟡 P1 | Important feature present in all reference implementations. Missing significantly reduces competitiveness | Panel title/icon declaration (B3), initial size ratio (B4) |
| 🟢 P2 | Nice-to-have, documentation cleanup, future extensions | Error code appendix (B10), floating window deferral (B11) |

**Decision rule**: P0 = must-add-REQ, P1 = should-add-REQ, P2 = may-be-doc-fix-only.

### 6. Identify scope inconsistencies (B9 pattern)

When scope table claims a feature but no REQ exists:

- **If in current scope**: add the missing REQ(s)
- **If not in current scope**: remove from scope table + add to §1.2 范围外
  + add to 附录 B 延期需求

This is a documentation fix only, no new REQ.

### 7. Present findings

Structure the report as:
1. **A. 已覆盖良好的核心能力** — brief confirmation table
2. **B. 需补充的功能需求** — ranked B1-Bn list with gap description
3. **C. 需修正的矛盾** — C1-Cn list with conflicting locations quoted
4. **Priority recommendation table** — one-line per item

**Do NOT start editing** until the user confirms which items to proceed with.
The user may want to defer some P1/P2 items.

### 8. Execute in batch

When user says "继续，中间不用暂停" or similar, batch all remaining items
in one continuous edit pass:

1. Insert all new REQs (one patch call per insertion point)
2. Update ALL indices and statistics in one batch at the end:
   - Section index headers
   - §5 statistics table
   - §1.6.1 numbering rules
   - Appendix index tables
   - Appendix bottom totals
   - Appendix C changelog
3. Run `verify_srs_consistency.py` once at the end to catch any missed syncs

**Do NOT** update indices incrementally per-REQ — this risks accumulation
errors and wastes context. Insert all bodies first, then sync all numbers.

## Common Gap Categories for Dock Layout SRS

| Category | What to check |
|----------|--------------|
| Panel lifecycle | show/hide, close, reopen, header drag-reorder within region |
| Panel metadata | title, icon declaration; runtime update |
| Panel sizing | initial size ratio, min/max constraints |
| View lifecycle | type declaration (Template/Dynamic), symmetric to Panel |
| Editor events | open event (symmetry with activate/close) |
| Instance management | destroy API, cleanup, idempotency |
| Layout adaptation | container resize proportional scaling, constraint conflicts |
| Scope integrity | scope table vs requirements body consistency |
| Deferred features | explicit listing in 附录 B for all future extensions mentioned in prose |
| Error codes | consolidated appendix vs scattered ad-hoc definitions |

## Pitfalls

- **Don't re-invent each time**: the gap categories above are stable across
  dock-layout SRS documents. Start from this checklist, don't re-derive.
- **Reference implementations are not requirements**: VS Code has floating
  windows; that doesn't mean your SRS must have them. Judge each gap against
  the SRS's own scope statement and target use cases.
- **Document contradictions are P0**: a contradiction between §1.3 and F-022
  is more urgent than a missing feature — it means the spec can't be
  implemented as written.
- **Scope lies are cheap to fix**: when the scope table claims features not
  in the body, removing them from scope is faster and cleaner than adding
  20+ new REQs for a feature the team hasn't designed yet.
