---
name: ada-doc-implementation-audit
description: 'Use when verifying that project documentation or one change record accurately reflects source code, tests, architecture decisions, and the current Git diff. Supports full-project parallel audits and a targeted read-only document↔diff mode; use ada-srs-review for requirements quality rather than implementation truth.'
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [audit, documentation, traceability, consistency, verification, srs]
    related_skills: [ada-srs-review, ada-code-quality-analysis, ada-srs-lifecycle]
---

# Documentation-Implementation Consistency Audit

Verify that all project documentation accurately reflects the current state of
the source code, tests, and architectural decisions. This is NOT a code quality
audit and NOT an SRS review — it answers one question: **"Do the docs tell the
truth about what the code actually does?"**

## Overview

This skill provides a systematic methodology for auditing documentation-implementation
consistency across an entire project. It uses parallel subagents to read all source
code and test files across modules (Domain, Services, Components, Interop), then
cross-references findings against all documentation layers: SRS, traceability
matrix, design documents, README, ADRs, and quality reports. The output is a
structured gap report with priority-ranked findings and a concrete fix plan.

The core innovation is the **parallel 3-subagent dispatch pattern**: rather than
reading 50+ source files sequentially (which blows context), three subagents read
simultaneously — one per module cluster — and return structured summaries. The
orchestrator reads documentation in parallel, then synthesizes findings.

## When to Use

- User asks to "核实文档是否正确", "verify docs match code", or "audit documentation"
- After a major refactoring phase — verify traceability still holds
- Before a release — ensure README counts, statuses, and links are accurate
- When a new requirement was added to SRS but traceability wasn't updated
- Periodic project maintenance — monthly documentation health check
- User says "阅读最新项目代码，核实功能实现状态，核实文档是否正确"

**Skip for:** code-only reviews, adding new documentation from scratch, or a
single prose edit with no checkable implementation claims.

## Targeted Change-Record Mode

When one remediation note, fix record, release note, or implementation report
must be checked against one working-tree/commit diff, do not run the full-project
parallel audit:

1. Read the document fully and extract every checkable claim, named file, test,
   count, status, and explicit review question.
2. Freeze `git status`, changed-file list, diff stat, branch, and commit range.
3. Map each claim to current `file:line` evidence and the exact test/artifact
   evidence; do not cite only diff line numbers.
4. Reconcile every changed hunk to some document or explicitly classify it as
   pre-existing/out of scope.
5. Re-freeze the live diff before verdict; concurrent changes invalidate stale
   file counts and test claims.
6. Return PASS or severity-ranked mismatches in the output shape requested by
   the user. The audit remains read-only unless correction was explicitly asked.

Numerically identical formulas are not sufficient evidence when two paths use
different state models or index domains. Trace the claim through the owning
operation and assert its side effects.

## The Audit Workflow

### Phase 1 — File Discovery and Scoping

Get complete file listings for all layers:

```bash
# Source files (excluding build artifacts)
find src/ -type f \( -name "*.cs" -o -name "*.razor" -o -name "*.ts" -o -name "*.css" \) ! -path "*/obj/*" ! -path "*/bin/*" | sort

# Test files
find tests/ -type f -name "*.cs" ! -path "*/obj/*" ! -path "*/bin/*" | sort

# Documentation files
find docs/ -type f -name "*.md" | sort
```

Note the total counts — these are the first numbers you'll cross-check against
documentation claims.

### Phase 2 — Parallel Subagent Source Reading

Dispatch 3 subagents in parallel via `delegate_task` batch mode, splitting the
codebase by module cluster (Domain + Results + Interop, Services + Commands +
Dto, Components + Demo). See `references/parallel-audit-pattern.md` for the
complete dispatch template, subagent prompt format, and pitfall guidance.

Each subagent must report per file: path and line count, key types, REQ
references, TODOs/FIXMEs, and test coverage.

### Phase 3 — Documentation Reading (Orchestrator)

While subagents work, read all documentation:

1. **SRS.md** — Note total requirement count, check for REQ IDs not in traceability
2. **requirements-traceability.md** — Note claimed counts, appendix file lists, statuses
3. **All design docs** in `docs/refactoring/` — Note phase statuses, dates
4. **README.md** — Note claimed counts, verify all links resolve
5. **Deviation analysis** — Note baseline dates, compare to current state
6. **Code quality reports** — Note test counts, compare to current `dotnet test` output
7. **ADR directory** — Verify records match project decisions

Key cross-reference commands to run:

```bash
# Find REQs in SRS but NOT in traceability
grep -oP 'REQ-[A-Z]+-\d+' docs/SRS.md | sort -u > /tmp/srs-reqs.txt
grep -oP 'REQ-[A-Z]+-\d+' docs/requirements-traceability.md | sort -u > /tmp/trace-reqs.txt
comm -23 /tmp/srs-reqs.txt /tmp/trace-reqs.txt

# Find REQs in traceability but NOT in SRS (reverse check)
comm -13 /tmp/srs-reqs.txt /tmp/trace-reqs.txt
```

### Phase 4 — Cross-Reference and Gap Analysis

When subagents return, synthesize findings into a structured gap report:

#### Gap Categories (in priority order)

| Priority | Category | Detection Method |
|:--------:|----------|-----------------|
| 🔴 | Missing requirements in traceability | `comm -23` SRS vs traceability REQ IDs; exclude intentionally deleted REQs |
| 🔴 | Wrong requirement counts | Compare docs claims vs `grep -c` on SRS |
| 🔴 | Stale phase/document statuses | Compare doc headers vs git log |
| 🟡 | Incomplete appendix file lists | Compare doc lists vs `find` output |
| 🟡 | Outdated test/file counts | Compare doc counts vs actual `dotnet test` / `wc -l` |
| 🟡 | Missing line counts (— markers) | Scan appendix tables for `—` entries |
| 🟢 | Historical report dates not marked | Older quality reports without "historical snapshot" note |
| 🟢 | Component test coverage gaps | Subagent reports show which Razor files lack tests |

#### Report Structure

```markdown
## 文档审计初步结果

### 🔴 需要修复的问题
| # | 文件 | 问题 | 建议 |

### 🟡 建议优化的项目
| # | 文件 | 问题 | 建议 |

### ✅ 已验证一致的项目
- bullet list of confirmed-correct items
```

### Phase 5 — Execute Fixes

Apply fixes in this order (each independently verifiable):

1. **Critical counts**: Update SRS requirement count everywhere it appears
2. **Missing entries**: Add missing REQ rows, test files, source files to traceability
3. **Stale statuses**: Update design doc status headers
4. **Appendix accuracy**: Replace incomplete file lists with full `find`-based lists
5. **Historical markers**: Add snapshot dates to older reports

After each batch of fixes, verify:
- `dotnet build` passes
- `dotnet test` passes
- `grep -c 'old_count'` returns 0 (old references purged)

## Common Pitfalls

- **Don't trust appendices**: The most common documentation bug across projects
  is appendices that were written once and never updated. Always cross-check
  appendix file lists against `find` output.
- **Deleted REQs still in SRS**: Some REQ IDs appear in SRS appendix tables
  (marked "已删除") but are correctly excluded from traceability. These are NOT
  gaps — they're intentional exclusions. Check the context before flagging.
- **Test count mismatch**: `dotnet test` reports total test cases including
  `[Theory]` data rows and `[MemberData]` parameterized tests. Appendix counts
  based on `[Fact]`/`[Theory]` method declarations will be lower. Note this
  discrepancy explicitly in the audit report.
- **Subagent output truncation**: Large subagent summaries may be truncated.
  Always use the full output file path provided in the subagent result for
  detailed review.
- **Line count drift**: Component `.razor` files are often missing from appendix
  line counts. Use `wc -l` on every source file, not just `.cs` files.
- **Don't audit half the files**: This pattern ONLY works when ALL source and
  test files are read. Partial audits produce incomplete findings. If a subagent
  times out, re-dispatch with a smaller file set.
- **Phase status headers**: Check both the status line AND the verification
  checkboxes. A doc that says "已完成" with 0 checked boxes is lying. A doc
  that says "待确认" but git log shows merged commits is stale.

## Verification Checklist

- [ ] All source and test files listed via `find` and counted
- [ ] 3 parallel subagents dispatched and returned structured reports for all modules
- [ ] All documentation files read: SRS, traceability, design docs, README, ADRs, quality reports
- [ ] SRS vs traceability REQ ID diff computed (`comm -23`)
- [ ] All gap categories (🔴🟡🟢) populated with concrete file:line evidence
- [ ] Fixes applied in priority order, each batch independently verified
- [ ] `dotnet build && dotnet test` pass after all fixes
- [ ] No stale counts, missing REQs, or `—` placeholder line counts remain
