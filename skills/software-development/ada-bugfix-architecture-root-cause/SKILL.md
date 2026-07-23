---
name: ada-bugfix-architecture-root-cause
description: >-
  When fixing multiple UI/behavior bugs, trace them to a shared architecture-level
  root cause before proposing fixes. Never fix symptoms in isolation.
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, refactoring, architecture, root-cause, blazor, interop]
    related_skills: [systematic-debugging, deviation-analysis-refactoring, blazor-component-development]
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

### Cluster: <shared pattern name>

**Symptoms:**
- Symptom A → <file:line> → <mechanism>
- Symptom B → <file:line> → <mechanism>
- Symptom C → <file:line> → <mechanism>

**Root cause:** One-sentence description of the design flaw.

**SRS evidence:** <SRS §X.Y> explicitly distinguishes these concepts.

**Fix principle:** <architectural principle, not code — e.g., "Region droppability is a Region attribute, not a Panel attribute">

### Fix plan

| File | Change | Principle |
|---|---|---|
| path/to/file.razor | <what to change> | <why> |
| path/to/index.ts | <what to change> | <why> |

**Risks:**
- <Risk 1> — <mitigation>
```

### Phase 5: Implement as One Coherent Change

Do NOT fix one symptom at a time. Implement all changes for the shared root cause in a single pass, then verify ALL symptoms are resolved.

## Common Pitfalls

- **Don't fix symptoms individually.** If three bugs share one root cause, three separate fixes = three wrong places + one remaining root cause.
- **Don't stop at the C# layer.** Blazor drag bugs often live in the TypeScript front-end (visual feedback) while the C# logic is correct. Read both layers.
- **Don't propose fixes before presenting the root cause.** The user may have domain knowledge that changes your understanding.
- **Don't conflate "works on my machine" with "bug is fixed."** After implementing, verify ALL original symptoms are gone, not just the one you were looking at.
- **Don't sacrifice architecture to fix UI bugs.** When a user says "fix this bug" and then adds "but don't reduce code quality", that is a second-order constraint: the fix must be principled even if the symptom seems small. Opening a direct coupling in one place (e.g., adding a special-case parameter) to quickly fix a symptom is _worse_ than leaving the symptom unfixed. If the fix would violate an existing abstraction boundary, extend the abstraction — never work around it. If the fix would make a class/component do two things, split the responsibility — never add a flag. A "quick fix" that creates technical debt is a failed fix.
- **Don't assume `OnAfterRenderAsync` logic alone is sufficient for drag source re-registration.** Even with correct per-render comparison logic, Blazor can reuse component instances across parameter changes while preserving instance fields (like `_isFirstRender`, `_headerRegistered`). The `_registered` bool flag may persist in its `true` state from a previous render cycle, preventing re-registration on a new DOM element. **Always add `@key` to the component in the parent template** (`@key="@RegionName"`) to ensure Blazor creates fresh instances when the logical identity changes. Use string-comparison identity tracking (e.g., `_lastHeaderPanelId`) instead of boolean `_registered` flags — strings automatically detect changes and don't require manual reset logic.
- **Don't skip the user's second-order constraints.** When the user adds a constraint like "covered SRS first" or "don't reduce code quality", that IS the main requirement — the bug fix is secondary. Present the SRS coverage table before the fix plan. If the user says "先出方案确认", produce the full root cause analysis + SRS table + fix plan for approval before writing any code.
- **Don't split a shared-root-cause fix into multiple PRs.** If three bugs share one root cause, one fix resolves all three. Splitting them into separate changes forces iterative testing and makes each individual change look incomplete.
- **ToolBar drag sources have the same lifecycle problem as panel drag sources.** `OnAfterRenderAsync(firstRender: true)` registration in ToolBar components suffers the same `firstRender` + boolean flag fragility as `DockPanel.razor`. After panels move between regions, the ToolBar re-renders but `firstRender` is already false. Fix: use a panel-ID hash (`string.Join(",", panels.Select(p => p.Id))`) detected in `OnAfterRenderAsync` to re-register drag handlers when the panel set changes, regardless of `firstRender`.
- **`ElementReference[]` array pattern for ToolBar loops.** Blazor `@ref` in `foreach` only captures the last element. For ToolBars with multiple entry buttons, use a pre-allocated `ElementReference[MaxEntries]` + index counter + parallel `string?[]` for panel IDs. Loop through the array in `OnAfterRenderAsync` to register JS handlers per entry.
- **Group ordering in ToolBars: Upper to Lower to Bottom (REQ-F-021 AC5).** Use GroupBy(RegionName) + OrderBy(RegionGroupOrder) where RegionGroupOrder maps region names containing Upper to 0, Lower to 1, Bottom to 2. Within each group, preserve the order from the DockPanels list (add order) - do NOT sort alphabetically by Title. Groups are separated by hr with class xd-toolbar-divider.
- **.OrderBy(p => p.Title) silently violates SRS ordering.** REQ-F-021 AC5 requires group-internal ordering by add order (insertion order in the DockPanels list). Alphabetical sort is a silent SRS violation. Always remove explicit OrderBy on groups unless the SRS specifies a different rule.
- **CSS hr divider is invisible without explicit style.** hr elements have no default visible style in most browsers. When using hr as a visual separator, you MUST define border: none, width, height, background, and flex-shrink: 0. Without border: none the default border-top renders inconsistently. Without flex-shrink: 0 flexbox may collapse the divider to zero. This is undetectable by HTML-only code review.
- **@ref in foreach only captures the last element.** Blazor @ref inside a loop overwrites each iteration. For ToolBars with multiple entry buttons, use a pre-allocated ElementReference[MaxEntries] + a parallel string?[MaxEntries] array for panel IDs + an int renderIndex counter. In OnAfterRenderAsync, iterate up to renderIndex to register JS handlers per entry. The Dictionary pattern fails because Razor @ref cannot bind to dictionary indexers.
- **@ref inside RenderFragment returned from a C# method silently breaks ElementReference capture.** Extracting repeated `@ref`-containing markup into a helper that returns `RenderFragment` compiles fine but at runtime `ElementReference` points to a stale/non-existent DOM element, causing `JSException: Cannot read properties of null (reading 'removeAttribute')` in JS interop calls. The `@ref` directive ONLY works when placed directly in the component's main .razor template — not inside a `__builder` lambda. **Fix**: keep `@ref` assignments inline (accept duplication), only extract display-only content (no `@ref`, no event handlers). Additionally, wrap `DetachDragHandlers` in `try-catch (JSException)` to tolerate stale references from Blazor diffing. See `references/blazor-ref-in-renderfragment-pitfall.md`.
- **Do not couple Dock Region visibility to droppability.** In Dock layouts, a logical Dock Region can be hidden in normal mode (no expanded panels) and still must be a valid target while a panel is being dragged. If you simply stop rendering empty regions, users cannot drag panels back into them. Fix by separating **normal space occupancy** from **drop scaffold** rendering: normal mode shows regions only when they contain expanded panels; panel-drag mode temporarily exposes hidden logical regions as lightweight drop scaffolds that register `dock-region` targets. See `references/atlas-dock-visibility-scaffold-pattern.md`.

## Common Pitfalls

- **Fixing symptoms individually when they share a root cause.** Three separate fixes for three symptoms that trace to one design flaw = three wrong places + one remaining root cause. Map all symptoms first, find the shared pattern, then fix once.
- **Stopping at the C# layer when bugs span C# and TypeScript.** Blazor drag/interop bugs often live in the TypeScript front-end (visual feedback, DOM registration) while the C# logic is correct. Read both layers before concluding.
- **Skipping the SRS coverage audit before proposing a fix.** A fix that passes tests but violates SRS acceptance criteria is incomplete. Every AC of every affected requirement must be individually checked — not just the happy-path AC.
- **Using boolean `_registered` flags for Blazor JS re-registration.** Blazor reuses component instances across parameter changes. A `_registered` bool stays `true` forever. Use `@key` on the parent template or string-comparison identity tracking.
- **Treating the user's second-order constraint as optional.** When the user says "fix this bug, but don't reduce code quality," the quality constraint IS the main requirement. A "quick fix" that creates technical debt is a failed fix.
- **Splitting a shared-root-cause fix into multiple PRs.** One root cause → one coherent change → one PR. Splitting forces iterative testing and makes each change look incomplete.
- **`@ref` inside `foreach` only captures the last element.** Use pre-allocated `ElementReference[N]` arrays with index counters, not dictionaries (Razor can't bind `@ref` to dictionary indexers).

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
- `references/atlas-dock-panel-move-pattern.md` — Atlas-specific root cause example (this session)
- `references/atlas-toolbar-grouping-pattern.md` — ToolBar region grouping (REQ-F-021 AC5), entry drag handler registration lifecycle, and icon display
- `references/atlas-dock-visibility-scaffold-pattern.md` — Dock Region visibility vs droppability: hide empty/auto-hidden regions in normal mode, expose hidden logical regions as drop scaffolds during panel drag
- `references/blazor-ref-in-renderfragment-pitfall.md` — @ref inside RenderFragment silently breaks ElementReference capture; inline-only rule + try-catch defense
