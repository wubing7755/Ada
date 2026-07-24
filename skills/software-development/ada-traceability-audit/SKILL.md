---
name: ada-traceability-audit
description: Use when auditing requirements-traceability.md against actual source code to find status mismatches, missing REQs, stale line counts, or outdated appendixes. Code is primary evidence, docs are secondary.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [traceability, audit, srs, documentation, verification, discrepancy]
    related_skills: [ada-srs-review, ada-docs-revision, codebase-inspection]
---

# Traceability / Documentation Discrepancy Audit

Systematically compare `docs/requirements-traceability.md` against actual source
code to find and fix status mismatches, missing requirements, stale line counts,
outdated appendixes, and wrong summary statistics. Source code is the truth;
documentation is secondary. When they disagree, fix the documentation.

## When to Use

- After a major feature phase, before declaring done — verify traceability matches reality
- When traceability stats look suspicious (e.g. 199 tests pass but appendix says 93)
- When a requirement marked "Not Implemented" is actually found in code
- When document counts (151 vs 152) don't reconcile across files
- User says "核实", "审计文档", "traceability 是否准确", or "检查需求覆盖"

## Methodology

### Phase 1: Cross-reference REQ IDs

Find all unique REQ IDs in both SRS and traceability, then diff them.

```bash
# Extract REQ IDs from SRS
grep -oP 'REQ-[A-Z]+-\d+' docs/SRS.md | sort -u > /tmp/srs-reqs.txt

# Extract REQ IDs from traceability
grep -oP 'REQ-[A-Z]+-\d+' docs/requirements-traceability.md | sort -u > /tmp/trace-reqs.txt

# Find REQs in SRS but NOT in traceability (missing entries)
comm -23 /tmp/srs-reqs.txt /tmp/trace-reqs.txt
```

The SRS appendix may list "deleted" requirements. Those are legitimate exclusions
from traceability; only flag REQs that appear in the SRS body as real gaps.

### Phase 2: Verify status labels against code

For each REQ in the traceability, check if the status matches reality.

| Traceability says | Action |
|---|---|
| **Not Implemented** | Grep the codebase for the REQ number or feature keywords. If found, the status is wrong. |
| **Implemented** | Verify the implementation file(s) listed actually exist and contain relevant code. |
| **Tested** | Verify both implementation AND test files exist. Run `dotnet test --filter` for the REQ. |
| **Partial** | Read the notes column. Is the "partial" reason still accurate, or has code caught up? |

The most common failure: requirements implemented in a prior phase but traceability
never updated. Example: REQ-F-149 (ToolBar spatial layout) was fully implemented in
`ToolBar.razor:11-100` but traceability still said "Not Implemented". The only way
to catch this is to READ THE CODE.

### Phase 3: Verify appendix accuracy

**Appendix A (test files):**
```bash
find tests -type f -name "*.cs" ! -path "*/obj/*" | sort
```
Compare against traceability. Flag: files listed that don't exist, files NOT listed
that do exist, test method counts that don't match.

**Appendix B (source files):**
```bash
find src/Atlas -type f \( -name "*.cs" -o -name "*.razor" -o -name "*.ts" \) \
  ! -path "*/obj/*" ! -path "*/bin/*" ! -path "*/node_modules/*" | sort
```
Flag: files with "—" in the line count column, new files not listed, line counts
wrong after refactoring.

### Phase 4: Verify cross-document consistency

| Check | Method |
|-------|--------|
| SRS REQ count in README matches traceability | `grep "requirements" docs/README.md` |
| Traceability summary stats add up | Manually verify Tested + Implemented + Partial + Not Implemented = Total |
| Priority subtotals sum to total | P0 + P1 + P2 = Total |

### Phase 5: Verify design document statuses

Check `docs/refactoring/*.md` files:
- Phase status labels ("已完成", "待确认") match actual git history
- "独立审查待完成" flags resolved or escalated
- Design doc claims about file counts / test counts match current state

## Planning Workflow: Investigate Before Committing

When the user asks for a development plan, do NOT jump to writing a plan based on
assumptions. Instead:

1. **Read the traceability** to see what's claimed as not implemented
2. **Read the actual source code** to verify those claims
3. **Cross-reference** — find mismatches between docs and code
4. **Report findings** — present what's actually done vs what docs say
5. **Then write the plan** — based on verified reality, not stale docs

This avoids the most common planning failure: proposing to implement something
that's already done.

## Common Discrepancy Patterns

| Pattern | Symptom | Root cause |
|---------|---------|------------|
| **Status lag** | "Not Implemented" but code exists | Phase completed, traceability not updated |
| **Snapshot drift** | Appendix counts stale | Copied from old coverage matrix without refresh |
| **Phantom files** | Files listed that don't exist | Refactored/moved since last audit |
| **Missing REQs** | SRS has REQ, traceability doesn't | New requirement added to SRS but matrix not regenerated |
| **Wrong status tier** | "Tested" but no test file listed | Status changed without updating file columns |

## Pitfalls

- **Trusting the traceability at face value.** Always verify with grep and code reading.
- **Not checking the SRS appendix for deleted requirements.** REQ IDs that appear only
  in the deleted-appendix table are legitimate exclusions, not gaps.
- **Confusing unique ID count with requirement count.** `grep -oP | sort -u | wc -l`
  counts unique IDs, but a REQ may appear in multiple places. Distinguish "in body"
  from "in appendix only".
- **Updating stats without updating the underlying rows.** If you change a status
  label, the summary statistics, priority subtotals, and coverage percentages all
  need recalculation.
- **Forgetting to check design docs.** Phase statuses in `docs/refactoring/` often
  lag behind reality.

## Verification Checklist

- [ ] All unique REQ IDs in SRS body present in traceability
- [ ] All traceability status labels verified against actual code
- [ ] Appendix A lists all real test files with accurate method counts
- [ ] Appendix B lists all real source files with accurate line counts (no "—")
- [ ] Summary statistics (Tested + Implemented + Partial + Not Implemented = Total) correct
- [ ] Priority subtotals sum to Total
- [ ] Cross-document REQ count references consistent (README, traceability header, SRS)
- [ ] Design doc phase statuses match git history
- [ ] `dotnet build && dotnet test` confirms no regressions after doc changes
