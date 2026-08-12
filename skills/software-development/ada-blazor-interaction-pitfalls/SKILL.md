---
name: ada-blazor-interaction-pitfalls
description: "Use when a Blazor/Razor bug involves lifecycle or rendering behavior: StateHasChanged not updating UI, OnParametersSet/OnAfterRender ordering, ShouldRender state reset, @ref in RenderFragment, or BuildRenderTree IndexOutOfRange. Prefer ada-blazor-interop-pitfalls for JS/DOM event interop."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, wasm, lifecycle, rendering, pitfalls]
    related_skills: [ada-blazor-component-library, ada-blazor-interop-pitfalls, ada-blazor-ui-audit]
    trigger_keywords: ['Blazor WASM', 'ShouldRender', 'OnParametersSet', 'StateHasChanged', 'IndexOutOfRange', 'BuildRenderTree', 'OnAfterRender', 'OnAfterRenderAsync', '@ref', 'RenderFragment']
---

# Blazor Lifecycle & Rendering Pitfalls

## Overview

A catalog of silent Blazor WASM lifecycle and rendering failures — `StateHasChanged()` skipping `OnParametersSet`, `OnAfterRender` vs `OnAfterRenderAsync` ordering traps, `@ref` inside `RenderFragment` silently breaking, paired-list `IndexOutOfRange`, and render-state reset strategies. Each pitfall includes the root cause, why the obvious fix doesn't work, and a verified solution with code examples.

For JS interop-specific pitfalls (`@onmouseenter`/`@onmouseleave`, `DotNetObjectReference`, `IJSRuntime`, `WeakMap` leaks), see JS interop debugging patterns.

## Agent Execution Contract

Inputs to identify first:
- The Razor component(s), render fragments, and state fields involved.
- The lifecycle method sequence relevant to the symptom.
- Whether the symptom requires JS/DOM interop or pure Blazor rendering reasoning.

Default workflow:
1. Classify the issue: lifecycle ordering, render-state reset, `@ref`, paired collections, or re-registration.
2. Inspect component state mutation and render-trigger path before editing.
3. Prefer deterministic render data structures over mutable per-render counters when possible.
4. Add or run a focused test/repro for the failing render behavior.
5. Route to `ada-blazor-interop-pitfalls` if DOM event delegation or JS module code is involved.

Stop conditions:
- Browser behavior or component tree state cannot be observed enough to classify the issue.
- The fix requires component architecture changes beyond the failing lifecycle path.
- The symptom is actually JS interop, not Blazor rendering.

Output contract:
- Lifecycle path analyzed.
- Root cause category.
- Fix pattern used.
- Verification steps and remaining render risks.

## When to Use

Use when:
- `StateHasChanged()` triggers `IndexOutOfRange` or stale render-state bugs
- `@ref` assignments work in `.razor` templates but silently fail inside `RenderFragment`
- Adding hover/flyout behavior to Blazor components (for JS interop, use JS interop debugging patterns instead)
- Debugging lifecycle order issues (parent-first vs child rendering order)
- Paired lists (`List<T>`) with assumed-equal `.Count` diverge between renders


Don't use for: JS interop event handling — use JS interop debugging patterns. General Blazor component design — use component library design patterns instead. Simple compile errors — these are lifecycle issues, not syntax errors.

## Pitfall 1: `StateHasChanged()` Skips `OnParametersSet`

`OnParametersSet` is ONLY called when the parent component passes parameters. `StateHasChanged()` triggered internally (e.g., after `TogglePanel` → `InvokeAsync(StateHasChanged)`) **skips** `OnParametersSet`.

If `BuildRenderTree` relies on per-render state reset (like `_renderIndex = 0` for array indexing in loops), putting the reset in `OnParametersSet` is NOT sufficient.

### Fix: Use `ShouldRender()` for per-render state reset

`ShouldRender()` fires BEFORE `BuildRenderTree` on **every** render, regardless of trigger:

```csharp
protected override bool ShouldRender()
{
    _renderIndex = 0;  // Guaranteed before every BuildRenderTree
    return true;
}
```

## Pitfall 2: `OnAfterRender` vs `OnAfterRenderAsync` Ordering

Blazor lifecycle runs parent-first, depth-first:
1. ALL components' `OnAfterRender(bool)` — sync, parent-first
2. ALL components' `OnAfterRenderAsync(bool)` — async, parent-first

If child components register `ElementReference` callbacks in sync `OnAfterRender` and the parent reads those refs in its `OnAfterRenderAsync`, this is correct. Moving the child's ref registration into `OnAfterRenderAsync` breaks this — the parent runs its async lifecycle before the child's async lifecycle populates the refs.

**Rule**: Keep `RegisterElementRef` in sync `OnAfterRender`. Keep JS interop registration in `OnAfterRenderAsync` with a `_lastRegisteredPanelId` guard.

### Alternative: Pre-compute render order, eliminate mutable state

For complex render trees with shared state across nested loops (e.g., ToolBar rendering three panel sections), mutable render-state fields (`_renderIndex`) are fragile. The lifecycle-safe alternative: pre-compute a flat ordered list and an index cache in `OnParametersSet`, then use `Dictionary<PanelId, int>` lookups during render.

```csharp
// In ComputeGroupsAndIndex() — called once per parameter change:
for (var i = 0; i < ordered.Count; i++)
    _panelIndexCache[ordered[i].Id] = i;  // O(1) lookup during render

// In BuildRenderTree:
var idx = _panelIndexCache[panel.Id];  // No mutable field needed
```

This eliminates `ShouldRender()` override, `_renderIndex` field, and all lifecycle ordering dependencies for render-state.

## Pitfall 3: `@ref` inside `RenderFragment` Silently Breaks

`@ref` only works in `.razor` templates, not inside `__builder` lambdas. Keep `@ref` inline; only extract display-only content to helper methods.

## Pitfall 4: Paired-List Defensive Iteration

**Pitfall**: When a parent component maintains multiple `List<T>` fields that should always have the same `.Count` (e.g., `_entryPanelIds`, `_entryRefs`, `_entryWrapperRefs` — all built in the same `ComputeGroupsAndIndex` loop), Blazor lifecycle timing can cause them to diverge. Use `Math.Min` to prevent `IndexOutOfRange`.

```csharp
// WRONG
for (var i = 0; i < _entryWrapperRefs.Count; i++)
    var panelId = _entryPanelIds[i];  // ← 💥 if shorter

// RIGHT
var count = Math.Min(_entryWrapperRefs.Count, _entryPanelIds.Count);
for (var i = 0; i < count; i++)
    var panelId = _entryPanelIds[i];
```

## Pitfall 5: `firstRender` Boolean Flags Preventing JS Re-registration

Blazor reuses component instances. Use string-identity comparison (`_lastHeaderPanelId`) instead of boolean flags, or add `@key` in the parent template.

## Pitfall 6: `SetKey` Sibling Swap Drops Attributes in Real-Browser DOM Application

**Symptom**: two `SetKey`-ed sibling elements (e.g. toolbar entries with `SetKey(item.Id)`) exchange positions after a reorder; the moved element's attributes (including `data-*` drag metadata and `onclick`) vanish in the real browser — it becomes a "naked element" with content (icon/title) but no attributes. Dragging/clicking behavior breaks (no drag source, click no-op), while the other sibling works.

**Root cause**: when keyed siblings swap positions, Blazor performs DOM-node move + attribute patch. The attribute patch fails in the **real browser DOM application layer**; the moved element's attribute frames are lost as a block (element frame + content survive, attributes gone).

**Why bUnit cannot catch it**: bUnit's AngleSharp DOM application differs from the real browser. `RenderComponent` from an empty tree renders the final state without the incremental diff; even an incremental sequence (render → operation → render) passes because AngleSharp applies the diff correctly.

**Fix pattern**: for elements without internal state (bare buttons, simple entries), remove the unnecessary `SetKey` — with no key, swaps are handled by position-matched attribute value updates (attribute values differ, so they update correctly). This is a correct simplification, not a hack. For stateful elements, evaluate alternatives (e.g. keep the key and decouple attribute sequence from position via a region wrapper) — unverified alternatives require real-browser confirmation.

**Check siblings**: every `SetKey(item.Id)` in a reorderable sibling list is a candidate (toolbar entries, document tab strips). Test the reorder path in the real browser and inspect the moved element's attributes.

## Verification Limitations (Browser DOM Application Layer)

- **bUnit/AngleSharp cannot reproduce real-browser DOM application failures** (e.g. Pitfall 6). Green bUnit render assertions prove the render-tree output is correct, not that the browser applies incremental diffs correctly. Final judgment for these bugs must come from a real browser.
- **bUnit incremental sequence**: to even approximate a re-render path, use render → operation → render (not render-from-final-state), but do not treat a green result as proof against real-browser-only failures.
- **Synthetic PointerEvent in headless/CDP eval cannot simulate real drags**: in some headless environments `composedPath()` returns empty for synthetic `PointerEvent` (click works, pointerdown does not), so the interaction controller never receives the event. Do not rely on synthetic pointer sequences to reproduce drag bugs; use real-browser manual verification (or trusted CDP input) instead.

## Common Pitfalls

- **`@ref` in `foreach` loop only captures the last element**: Use a pre-allocated `ElementReference[]` array with an index counter, not a `Dictionary` (which Razor cannot bind to).
- **`write_file` overwrites prior patches within a session**: When editing the same file across multiple phases, `write_file` silently discards all changes made by prior `patch` calls. Use `patch` (not `write_file`) for follow-up edits. If a full rewrite is needed mid-session, read the current state with `read_file` first, then merge.

## Verification

- [ ] Browser console shows 0 JS errors after page load
- [ ] No `DisposeAsync` / `DotNetObjectReference` leaks (check for "disposed reference" errors)
- [ ] Drag-and-drop still works after Blazor re-renders (toggle panels, re-drag)
- [ ] `OnAfterRenderAsync` guards verified: leaf components have guards, parent components do not
- [ ] All `@ref` assignments are inline in `.razor` templates — no `@ref` inside extracted `RenderFragment` helper methods

## Reference Files

- `references/hover-interop-full-pattern.md` — Complete three-layer pattern for mouseenter/mouseleave: TypeScript addEventListener → DotNetObjectReference callback → Razor component integration with render guard and try/catch
