---
name: ada-pre-implementation-audit
description: "Use when creating implementation plans that reference existing code or documentation — verify traceability claims and implementation status against actual source code before proposing new work. Prevents building plans on stale or inaccurate docs."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [audit, investigation, planning, traceability, pre-implementation, code-review]
    related_skills: [plan, ada-blazor-component-library, ada-code-dedup-audit]
---

## Overview

A pre-planning audit that verifies traceability claims against actual source code before any implementation plan is written. Prevents building multi-phase plans on stale documentation by first dispatching parallel subagent auditors, cross-checking findings, and quantifying the delta between what docs claim and what code actually contains.

# Pre-Implementation Audit

Verify assumptions about existing code and documentation before writing an implementation plan. Documentation drifts — traceability matrices claim "Not Implemented" when code already exists, file counts go stale within days, and phase-plan statuses lag reality.

## When to Use

- Writing a plan that references traceability matrix statuses ("Not Implemented", "Partial")
- User asks for a development plan and you haven't read the relevant source files recently
- The traceability says "X not implemented" but the feature seems to work in the demo
- After docs have been through multiple revision cycles without corresponding code re-audit
- User explicitly says "先探知代码再出方案" / "先确认再计划"

## Core Principle

> **Traceability is a lagging indicator. Code is the source of truth.**

## Audit Workflow

### 1. Identify the claims to verify

From the requirements traceability matrix or SRS, extract the REQs relevant to the planned work. Note their claimed status (Implemented/Partial/Not Implemented), referenced files, and test files.

### 2. Dispatch parallel subagent auditors

Use `delegate_task` batch mode with 3 agents covering different modules:

```python
delegate_task(tasks=[
    {
        "goal": "Audit Domain/Results/Interop files...",
        "context": "Repo root: ... Read every file, report implementation status per REQ..."
    },
    {
        "goal": "Audit Services/Commands/Dto files...",
        "context": "Repo root: ... Read every file, report implementation status per REQ..."
    },
    {
        "goal": "Audit Components/Razor files...",
        "context": "Repo root: ... Read every file, report JS interop, TODOs, REQ references..."
    }
])
```

Each agent gets:
- Full file paths to read
- Instructions to note REQ references, TODOs, and actual implementation state
- Instructions to read corresponding test files

### 3. Cross-check findings against traceability

For each REQ in the planned scope:

| REQ | Traceability says | Code actually | Discrepancy? |
|-----|------------------|---------------|:---:|
| F-149 | Not Implemented | `ToolBar.razor:11-100` has full AC1–AC5 | ✅ YES |
| F-023 | Not Implemented | `PanelOperations.cs` + `ToolBar.razor` flyout complete | ✅ YES |

### 4. Quantify the delta

Before:
- Plan assumed 4 implementation phases
- Traceability said 31 Not Implemented

After:
- 2 phases already done → removed from plan
- 2 phases revised to reflect actual gaps
- Traceability corrected: 31 → 27 Not Implemented

### 5. Present findings before planning

Ask 5 specific technical questions to confirm the plan's assumptions against the discovered reality:

1. What's the actual scope boundary? (Phase 21b: API only vs API + UI)
2. Is the proposed sorting behavior sufficient for the SRS acceptance criteria?
3. Does the drag registration pattern match existing component patterns?
4. What specific test scenarios are needed?
5. What concrete verification commands prove each phase?

### 6. Revise the plan

Publish the revised plan with explicit "original assumption → actual finding" deltas. Include:
- Which phases were removed/merged
- Which phases' deliverable changed
- Updated traceability states

## Common Pitfalls

- **Trusting traceability over code.** The matrix is documentation, not a compiler. Always verify "Not Implemented" claims with `grep` or `read_file` before planning work.
- **Skipping the cross-check step.** Finding that F-149 is already implemented is more valuable than writing one more feature — it saves an entire phase of unnecessary work.
- **Presenting the delta insufficiently.** The user needs to see "I assumed X, but found Y" before approving the revised plan. Generic "plan updated" messages don't build trust.
- **Using a single auditor for a large codebase.** Fan out to 3 parallel subagents — one reading domain/services won't know about component state, and vice versa.
- **Auditing only the files mentioned in traceability.** Traceability file lists are often incomplete (missing new files like `DockVisibilityPlan.cs`, `ContentHost.razor`). Use `find` / `search_files` for the actual file list.

## Verification Checklist

- [ ] All REQs in the planned scope have been cross-checked against actual code
- [ ] At least one live `grep` or `read_file` confirmed each "Not Implemented" claim
- [ ] Discrepancies between docs and code were flagged before plan approval
- [ ] Revised plan includes explicit "assumption → reality" deltas per phase
- [ ] Traceability matrix was corrected for any stale statuses found
