# Root Cause Analysis Patterns

> Extracted from ada-bugfix-architecture-root-cause SKILL.md for progressive disclosure.

## Root Cause Analysis Template

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

### Phase 5: Implement as One Coherent Change

Do NOT fix one symptom at a time. Implement all changes for the shared root cause in a single pass, then verify ALL symptoms are resolved.

## Detailed Pitfalls

- **Don't fix symptoms individually.** If three bugs share one root cause, three separate fixes = three wrong places + one remaining root cause.
- **Don't stop at the C# layer.** Blazor drag bugs often live in the TypeScript front-end (visual feedback) while the C# logic is correct. Read both layers.
- **Don't propose fixes before presenting the root cause.** The user may have domain knowledge that changes your understanding.
- **Don't conflate "works on my machine" with "bug is fixed."** After implementing, verify ALL original symptoms are gone, not just the one you were looking at.
- **Don't sacrifice architecture to fix UI bugs.** When a user says "fix this bug" and then adds "but don't reduce code quality", that is a second-order constraint: the fix must be principled even if the symptom seems small. Opening a direct coupling in one place to quickly fix a symptom is worse than leaving the symptom unfixed. If the fix would violate an existing abstraction boundary, extend the abstraction — never work around it. A "quick fix" that creates technical debt is a failed fix.
- **Don't assume `OnAfterRenderAsync` logic alone is sufficient for drag source re-registration.** Even with correct per-render comparison logic, Blazor can reuse component instances across parameter changes while preserving instance fields (like `_isFirstRender`, `_headerRegistered`). Always add `@key` to the component in the parent template to ensure Blazor creates fresh instances. Use string-comparison identity tracking instead of boolean `_registered` flags.
- **Don't skip the user's second-order constraints.** When the user adds a constraint like "covered SRS first" or "don't reduce code quality", that IS the main requirement. Present the SRS coverage table before the fix plan.
- **Don't split a shared-root-cause fix into multiple PRs.** If three bugs share one root cause, one fix resolves all three.
- **ToolBar drag sources have the same lifecycle problem as panel drag sources.** Use panel-ID hash detected in `OnAfterRenderAsync` to re-register drag handlers when the panel set changes, regardless of `firstRender`.
- **`ElementReference[]` array pattern for ToolBar loops.** Blazor `@ref` in `foreach` only captures the last element. Use a pre-allocated `ElementReference[MaxEntries]` + index counter + parallel `string?[]` for panel IDs.
- **Group ordering in ToolBars: Upper to Lower to Bottom (REQ-F-021 AC5).** Use GroupBy(RegionName) + OrderBy(RegionGroupOrder). Within each group, preserve insertion order — do NOT sort alphabetically.
- **`.OrderBy(p => p.Title)` silently violates SRS ordering.** REQ-F-021 AC5 requires group-internal ordering by add order.
- **CSS hr divider is invisible without explicit style.** Must define border, width, height, background, and flex-shrink. Without flex-shrink: 0 flexbox may collapse the divider.
- **@ref inside RenderFragment returned from a C# method silently breaks ElementReference capture.** `@ref` ONLY works directly in the component's main .razor template. See `references/blazor-ref-in-renderfragment-pitfall.md`.
- **Do not couple Dock Region visibility to droppability.** Separate normal space occupancy from drop scaffold rendering. See `references/dock-visibility-scaffold-pattern.md`.
