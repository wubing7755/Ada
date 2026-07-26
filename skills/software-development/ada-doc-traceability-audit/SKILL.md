---
name: ada-doc-traceability-audit
description: "Use when auditing a project's documentation against its SRS and codebase — find missing requirements, stale traceability entries, outdated status markers, and incomplete appendices. Covers the full doc cleanup decision tree: delete vs archive vs keep."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [documentation, audit, srs, traceability, cleanup, maintenance]
    related_skills: [ada-blazor-component-library, ada-srs-documentation, ada-srs-review]
---

## Overview

A systematic audit process for verifying that project documentation — SRS, traceability matrix, status reports, and appendices — accurately reflects the current source code. Designed to catch drift between documentation claims and implementation reality before they mislead planning or release decisions.

# Documentation & Traceability Audit

Systematic audit of project documentation against source code and SRS. Verify
that traceability matrices are accurate, document references resolve, status
markers match reality, and obsolete files are cleaned up.

## When to Use

- After a major implementation phase completes (3+ source files changed)
- When user asks "is the documentation accurate?" / "核实文档是否正确"
- Before a release or public API freeze
- When traceability counts don't match expectations (e.g., SRS says 151 but
  traceability says 152)

## Audit Workflow

### Phase 1: Parallel Source Reading

Use `delegate_task` batch mode to fan out 2-3 subagents, each reading one
module. Every subagent gets the full file list for its module plus matching
test files, and reports:

- File path, line count
- Key types/classes defined
- SRS requirement references (REQ-F-XXX comments)
- TODOs, FIXMEs, incomplete markers
- Test coverage per class

### Phase 2: Cross-Reference SRS vs Traceability

```bash
# Find REQ IDs in SRS but not in traceability
grep -oP 'REQ-[A-Z]+-\d+' docs/SRS.md | sort -u > /tmp/srs.txt
grep -oP 'REQ-[A-Z]+-\d+' docs/requirements-traceability.md | sort -u > /tmp/trace.txt
comm -23 /tmp/srs.txt /tmp/trace.txt
```

For each missing REQ:
- Check if it's **deleted** (listed in SRS appendix as "删除") → no action
- If it's a **genuine requirement** → add row to traceability, update all counts

### Phase 3: Appendix Verification

```bash
# Actual test files vs appendix A
find tests -name '*Tests.cs' | wc -l

# Actual source files vs appendix B
find src -name '*.cs' -o -name '*.razor' | grep -v '/obj/' | grep -v '/bin/' | wc -l
```

Common gaps:
- Test files missing from appendix (new tests added after last update)
- Source files missing from appendix (new classes/components not listed)
- Component files have `—` for line counts (never measured)
- Line count total is stale (sum of individual entries doesn't match reality)

### Phase 4: Doc Consistency Check

```bash
# Find stale status markers
grep -rn "待确认\|pending\|TBD\|未完成" docs/ --include="*.md"

# Verify cross-document links from README
grep -oP '\[.*?\]\(.*?\.md\)' docs/README.md | while read link; do
  target=$(echo "$link" | grep -oP '(?<=\().*\.md(?=\))')
  [ -f "docs/$target" ] || echo "BROKEN: $target"
done
```

## Doc Cleanup Decision Tree

For every file in `docs/`, classify by answering these questions in order:

```
1. Is the file currently referenced from docs/README.md?
   ├── YES → Is it still accurate?
   │   ├── YES → KEEP ACTIVE
   │   └── NO  → FIX, then keep active
   └── NO  → Does it have decision-traceability value?
       ├── YES → MOVE to docs/archive/ (preserve subdirectory structure)
       └── NO  → DELETE
```

### Delete (no value)

- Intermediate draft superseded by a final version
- Single-line redirect or empty shell file
- Duplicate content with no additional info

### Archive to `docs/archive/` (historical value)

- Baseline snapshots documenting "before" state of a refactoring
- Coverage matrices superseded by formal traceability
- Completed refactoring plans that document design rationale
- Optimization action plans with P0/P1 tracking

### Keep Active

- SRS and traceability (always active)
- Current refactoring design driving implementation
- Active design documents with pending review
- Most recent final quality report
- Architecture Decision Records (ADRs)

### Archive Directory Convention

```
docs/archive/
├── deviation-analysis/    # Historical SRS deviation reports
├── refactoring/            # Completed refactoring plans
└── reports/                # Superseded quality reports
```

Preserve original subdirectory structure so file provenance is clear.

## Post-Audit Fixes

Once gaps are found, fix in priority order:

1. **SRS count mismatch** — update traceability stats table and `docs/README.md`
2. **Missing REQ row** — add to traceability with correct status
3. **Missing appendix entries** — add test files and source files with counts
4. **Stale component line counts** — `wc -l` each file, fill in `—` entries
5. **Stale status markers** — update to actual status with date
6. **Stale test counts in quality reports** — add historical snapshot note

### Update README After Cleanup

After moving files to `docs/archive/`, update `docs/README.md`:
- Remove entries for deleted files
- Add an "Archive" section linking archived files with one-line descriptions
- Verify all remaining links resolve

## Common Pitfalls

- **Stale line counts** — `wc -l` output in traceability docs rots on every code change. Always recount, never trust the doc.
- **Deleted files still referenced** — cross-document links (README → traceability → SRS) break silently when files move. Verify every link resolves.
- **Status markers out of sync** — "✅ Implemented" markers may be months stale. Code is the source of truth, not the status column.
- **Appendix totals don't match** — after cleanup, appendix totals (REQ count, file count) must be recalculated from scratch, not decremented.

## Verification Checklist

- [ ] SRS unique REQ count matches traceability claimed count (accounting for deleted/inactive)
- [ ] All traceability appendix files verified present on disk
- [ ] Cross-document links (README → traceability → SRS) resolve correctly
- [ ] No stale status markers on completed work
- [ ] `dotnet build && dotnet test` passes (docs-only changes should not break build)
- [ ] Empty directories removed after file moves
