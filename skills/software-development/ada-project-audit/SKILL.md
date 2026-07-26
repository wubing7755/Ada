---
name: ada-project-audit
description: "Use when auditing a software project for implementation status, documentation accuracy, and traceability drift — before planning, before releases, or after major refactoring phases. Covers parallel source-code audit, doc cross-check, and traceability correction.  Broader scope than pre-implementation audit — covers full project health including docs, traceability, and code status. For focused plan-validation, use pre-implementation auditing."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [audit, verification, traceability, documentation, planning, code-review]
    related_skills: [ada-blazor-component-library, plan, ada-requesting-code-review]
---

## Overview

A comprehensive audit protocol for detecting drift between source code, traceability matrices, requirement specifications, and status reports. Runs parallel source-code audits, cross-checks documentation claims, and produces a delta report that corrects traceability before planning begins.

# Project Audit: Code ↔ Documentation Verification

Systematic methodology for auditing a project to detect drift between
source code, traceability matrices, requirement specs, and status reports.
Use BEFORE drafting any implementation plan that assumes traceability
status is accurate.

## When to Use

- Before drafting a multi-phase implementation plan from traceability data
- After major refactoring phases to confirm traceability is current
- User asks "核实功能实现" or "audit the project" or "检查文档是否准确"
- Preparing for a release — verify all "Not Implemented" items are genuinely missing

**Skip for:** single-file changes, bug fixes that don't touch traceability,
greenfield projects with no secondary documentation.

## Core Principle

**Secondary documents drift.** Traceability matrices, coverage reports,
deviation analyses — all are manually maintained and can be stale within
hours. A "Not Implemented" row may be fully implemented; a "Completed"
checkbox may be aspirational. The source code is the only source of truth.

## The Protocol

### Phase 1: Source Audit

Use parallel subagents to read every source file. Split by module:

```
delegate_task(tasks=[
  {goal: "Audit Domain + Results + Interop — read every .cs/.ts file"},
  {goal: "Audit Services + Commands + Dto — read every .cs file"},
  {goal: "Audit Components + CSS — read every .razor/.css file"},
])
```

Each subagent reports per-file:
- What the file implements (key classes, methods, behavior)
- Any SRS requirement references (`REQ-F-XXX` in comments)
- Any TODOs, FIXMEs, or incomplete markers
- Test coverage status

### Phase 2: Document Cross-Check

Against source audit findings, verify:

| Document | Check |
|----------|-------|
| `docs/requirements-traceability.md` | Every REQ with "Not Implemented" — does code say otherwise? |
| `docs/requirements-traceability.md` | Appendices — are source/test file lists complete? Line counts accurate? |
| `docs/README.md` | Requirement counts, file links — all point to existing files? |
| `docs/SRS.md` | Any REQ IDs not in traceability? Any "deleted" REQs still in active sections? |
| Status documents | "Completed" checkboxes — verified against code or aspirational? |

### Phase 3: Delta Report

Output a table of discrepancies:

```markdown
| REQ | Traceability Says | Code Says | Action |
|-----|------------------|-----------|--------|
| F-149 | Not Implemented | Implemented (ToolBar.razor:11-100) | Correct traceability |
| F-023 | Not Implemented | Tested (flyout + AutoHidden toggle) | Correct traceability |
```

### Phase 4: Correct

Apply corrections to traceability/docs BEFORE drafting any implementation
plan. A plan built on stale data wastes implementation time.

## Common Pitfalls

- **Trusting traceability without verification.** The most common failure
  mode. Always read the actual source files before concluding a feature
  is missing.
- **Counting REQ IDs from grep without deduplication.** SRS documents
  contain REQ IDs in cross-references, appendix tables, and "deleted"
  lists. Use `sort -u` and diff against traceability.
- **Missing new REQs.** New requirements added to SRS after traceability
  was generated won't appear in the matrix. Run `comm -23` between SRS
  and traceability REQ ID sets.
- **Component file line counts.** Razor files are often left as `—` in
  appendices. Count them with `wc -l`.
- **Test method counts vs runner output.** `[Theory]` with `[MemberData]`
  produces more runner-discovered tests than `[Fact]`/`[Theory]` attribute
  counts. Document the discrepancy explicitly.

## Verification Checklist

- [ ] All source files read (via parallel subagents or direct reading)
- [ ] Every "Not Implemented" REQ verified against actual code
- [ ] SRS REQ IDs diffed against traceability REQ IDs — no orphans
- [ ] Traceability appendix file lists match actual `find` output
- [ ] Line counts updated (especially for components previously marked `—`)
- [ ] Phase 3 delta report produced
- [ ] Corrections applied before any implementation plan is drafted

## Reference

See `references/atlas-audit-example.md` for the concrete audit that
discovered F-149 and F-023 were already implemented, cutting the planned
Phase 21 scope by half.
