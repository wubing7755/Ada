---
name: ada-bugfix-architecture-root-cause
description: "Use when fixing multiple UI or behavior bugs that may share a common root cause — trace symptoms to architecture-level issues before patching. Covers Blazor interop patterns, dock panel lifecycles, toolbar grouping, and RenderFragment pitfalls."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, refactoring, architecture, root-cause, blazor, interop]
    related_skills: [ada-systematic-debugging]
---

# Architecture Root Cause Analysis for Bug Fixes

## Overview

When multiple UI/behavior bugs present simultaneously — especially in cross-cutting infrastructure like drag-and-drop, interop registration, event wiring, or layout computation — they rarely stem from independent causes. This skill defines a five-phase methodology to trace symptom clusters to a single architecture-level root cause before writing any fix: (1) map symptoms to code paths, (2) find the shared design pattern, (3) perform a mandatory full SRS coverage audit, (4) present the root cause with evidence before fixing, and (5) implement all fixes as one coherent change. The approach prevents the common failure mode where fixing symptom A exposes symptom B, triggering an iterative cycle that never addresses the underlying design flaw.

The skill also captures recurring architectural anti-patterns specific to Blazor drag/interop systems: infrastructure coupled to content, lifecycle tied to `firstRender`, front-end/back-end semantic gaps, and wrong abstraction boundaries. Each includes a signature, real-world example, and the fix principle.

## When to Use

- User reports **multiple UI/behavior bugs** (2–5 symptoms) that could share a root cause
- The bugs span **cross-cutting infrastructure** (drag targets, interop registration, event wiring, layout computation)
- A fix for symptom A causes symptom B to appear — strong signal of a shared root cause
- User adds a quality constraint ("不要为了解Bug而忽视了代码质量、项目架构") — treat this as a mandatory second-order constraint, not a nice-to-have

**Do NOT use for:** single isolated bugs (use `systematic-debugging`), pure refactoring from an existing deviation analysis document (use `deviation-analysis-refactoring`).

## Core Principle

**When 3+ symptoms exist, look for ONE architecture-level root cause before fixing any of them.**
Fixing symptoms individually is wasteful and often impossible without addressing the underlying design flaw first.

## Test: Are the Bugs Surface-Level or Architecture-Level?

| Scenario | Likely nature | Approach |
|---|---|---|
| Bugs touch different features of one component | Surface-level | Fix independently |
| Bug A = "Bottom Dock can't receive drops", Bug B = "Panel shows wrong visual feedback", Bug C = "Panel can't be moved again after first drop" | **Architecture-level** | All three trace to ONE infrastructure design flaw |
| Each fix reveals a new problem in a different place | Architecture-level | The infrastructure layer is wrong |
| Fixing requires changes across 3+ files and both C# and TypeScript | Architecture-level | The boundary between front-end and back-end is drawn wrong |

## Workflow

### Phase 1: Map Symptoms to Code Paths

For each reported symptom:

1. Identify the exact files involved (read ALL of them, don't zoom in on one)
2. Trace the data flow: user action → JS event → C# callback → state mutation → re-render
3. Note which file/layer each symptom "breaks" in

### Phase 2: Find the Shared Pattern

Look for these common cross-cutting design flaws in Blazor drag/interop systems:

| Pattern | Signature | Example from this session |
|---|---|---|
| **Infrastructure coupled to content** | JS registration inside `firstRender` guard that depends on content count (`Panels.Count > 0`) | Drop target registration only fired when panels existed — empty regions were invisible to drag |
| **Lifecycle tied to firstRender** | `OnAfterRenderAsync(firstRender)` with one-shot registration that never re-fires | After panel moved away, new DOM element was never registered as drop target |
| **Front-end/back-end semantic gap** | JS computes visual feedback (direction zones) without knowing the drag type | Dock panels showed split directions (left/right/up/down) even though SRS says panel drops are directionless |
| **Wrong abstraction boundary** | A Region-level property (droppability) lives inside a Panel-content component | `DockPanel.razor` owned the drop target for its Region, not a `Region.razor` component |

### Phase 3: Full SRS Coverage Audit (Mandatory)

**Before proposing any fix, produce a formal SRS requirement table mapping all affected symptoms.** This catches scope violations that symptoms alone don't reveal, and is a prerequisite to Phase 4.

1. **Collect every SRS requirement** touching the affected features. Group into:
   - **Group A: Directly broken** — symptom clearly violates this req
   - **Group B: Indirectly affected** — reqs sharing the same code path
   - **Group C: Regression guard** — reqs that must keep working post-fix

2. **For each requirement, check AC fidelity:** Does the AC say something the code does differently? E.g., AC says "the entire Region highlights with a border" but code shows directional zone indicators — that is a SRS violation even if drop logic works.

3. **Check concept conflation:** Does the SRS distinguish concepts that the code treats identically? Common examples:
   - `dock-region` vs `editor-view` drop targets (SRS §3.5 says panels have no direction; SRS §3.4.1 says tabs have 5-zone direction)
   - Region droppability vs Panel content presence (an empty Region must still be a valid drop target)

4. **Verify fix scope covers ALL ACs of each affected requirement.** It's not enough to make a test pass — each Acceptance Criterion in SRS must be individually checked. Common failure: fixing the "happy path" AC but missing edge-case ACs (e.g., "move to empty region" works but "move to region that already has panels" breaks).

5. **Document the coverage table** in your root cause analysis. Format:

```
| Req | Prio | Status | Violation |
|-----|------|--------|-----------|
| REQ-F-069 AC5 | 🔴 | ❌ | SRS "region highlights" ↔ code shows direction zones |
| REQ-F-052 | 🔴 | ✅ | Unchanged (tab drags only) |
```

6. **Do NOT proceed to Phase 4** until you know every requirement that must be satisfied and can articulate the priority trade-offs. If the user pushes back on quality, this table is your evidence that the fix is principled, not expedient.

### Phase 4: Present the Root Cause Before Fixing

Format:

```
## Root Cause Analysis

Use the template in `skill_view(name="ada-bugfix-architecture-root-cause", file_path="references/bugfix-analysis-patterns.md")` — cluster symptoms by shared pattern, identify the design flaw, cite SRS evidence, and produce a principled fix plan (not a symptom-level patch).

**Fix principle:** <architectural principle, not code — e.g., "Region droppability is a Region attribute, not a Panel attribute">

### Fix plan template

| File | Change | Principle |
|---|---|---|
| path/to/file.razor | <what to change> | <why> |
| path/to/index.ts | <what to change> | <why> |

Implement all changes for the shared root cause in a single pass — do NOT fix symptoms one at a time.

## Common Pitfalls

- **Don't fix symptoms individually.** If three bugs share one root cause, one fix resolves all three.
- **Don't stop at the C# layer.** Blazor drag bugs often live in TypeScript. Read both layers.
- **Use `@key` for Blazor component identity, not boolean `_registered` flags.** String-comparison tracking auto-detects changes.
- **The user's second-order constraint IS the main requirement.** A "quick fix" that creates technical debt is a failed fix.
- **`@ref` inside `foreach` or C#-returned `RenderFragment` breaks.** Keep `@ref` inline; use pre-allocated arrays with index counters.

Full pitfall catalog and root cause template: `skill_view(name="ada-bugfix-architecture-root-cause", file_path="references/bugfix-analysis-patterns.md")`

## Verification Checklist

- [ ] Full SRS coverage audit completed with requirement table (Group A: directly broken, Group B: indirectly affected, Group C: regression guard)
- [ ] Root cause analysis presented to user with: symptom cluster mapping, shared pattern identification, SRS evidence, fix principle, and risk assessment
- [ ] User explicitly approved the root cause analysis before any code was written
- [ ] All original symptoms verified as resolved after the fix (not just the one most visible)
- [ ] No new symptoms introduced — regression tests pass for unaffected features
- [ ] Each SRS acceptance criterion for affected requirements individually verified (not just happy-path ACs)
- [ ] `@key` attributes added to Blazor components that need fresh instances on identity change
- [ ] Boolean `_registered` flags replaced with string-identity comparison or eliminated entirely

## References

- `systematic-debugging` — For single-bug root cause analysis
- `deviation-analysis-refactoring` — For refactoring from an existing analysis document
- `references/drop-target-lifecycle-patterns.md` — Blazor drop target registration lifecycle: the corrected pattern (always register infrastructure, re-register on identity change, visual feedback by drag type)
- `references/dock-panel-move-pattern.md` — Lib-specific root cause example (this session)
- `references/toolbar-grouping-pattern.md` — ToolBar region grouping (REQ-F-021 AC5), entry drag handler registration lifecycle, and icon display
- `references/dock-visibility-scaffold-pattern.md` — Dock Region visibility vs droppability: hide empty/auto-hidden regions in normal mode, expose hidden logical regions as drop scaffolds during panel drag
- `references/blazor-ref-in-renderfragment-pitfall.md` — @ref inside RenderFragment silently breaks ElementReference capture; inline-only rule + try-catch defense
