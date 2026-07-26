---
name: ada-blazor-interaction-pitfalls
description: "Use when debugging Blazor WASM interaction issues — non-bubbling event directives that silently fail, lifecycle timing traps, JS interop workarounds for native DOM events, and render-state reset patterns."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, wasm, interop, lifecycle, events, pitfalls]
    related_skills: [ada-blazor-component-library, ada-blazor-interop-pitfalls]
    trigger_keywords: ['Blazor WASM', 'onmouseenter', 'onmouseleave', 'hover', 'ShouldRender', 'OnParametersSet', 'StateHasChanged', 'IndexOutOfRange', 'BuildRenderTree', 'non-bubbling', 'DotNetObjectReference', 'HoverCallback']
---

## Overview

A catalog of silent Blazor WASM interaction failures — event directives that compile cleanly but never fire, lifecycle timing traps that corrupt render state, JS interop teardown patterns that leak memory, and render-index reset strategies. Each pitfall includes the root cause, why the obvious fix doesn't work, and a verified solution with code examples.

# Blazor Interaction Pitfalls

Silent failures in Blazor WASM component interaction that compile without error but don't work at runtime — non-bubbling event directives, lifecycle traps, and render-state bugs.

## When to Use

Use when:
- A Blazor Razor event directive compiles but never fires at runtime (`@onmouseenter`, `@onmouseleave`)
- `StateHasChanged()` triggers `IndexOutOfRange` or stale render-state bugs
- Adding hover/flyout behavior to Blazor components
- Debugging lifecycle order issues (parent-first vs child rendering order)
- Registering JS interop events that need per-render lifecycle management

## Pitfall 1: `@onmouseenter` / `@onmouseleave` Silently Ignored

`@onmouseenter` and `@onmouseleave` compile without error in Razor but are **never invoked**. These DOM events do not bubble — Blazor's event system relies on event delegation at the document level and cannot capture non-bubbling events.

**Supported Blazor mouse events (.NET 6):**
`@onclick`, `@ondblclick`, `@onmousedown`, `@onmouseup`, `@onmousemove`, `@onmouseover`, `@onmouseout`, `@onmousewheel`, `@oncontextmenu`

### Fix: JS Interop with native addEventListener

Register `mouseenter`/`mouseleave` directly via native DOM listeners, calling back to C# through `DotNetObjectReference`. See `references/hover-interop-full-pattern.md`.

**Why not `@onmouseover`/`@onmouseout`?** They fire when entering/leaving child elements, causing flicker for flyout UIs. `mouseenter`/`mouseleave` only fire when crossing the target element boundary.

## Pitfall 2: `StateHasChanged()` Skips `OnParametersSet`

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

## Pitfall 3: `OnAfterRender` vs `OnAfterRenderAsync` Ordering

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

## Pitfall 4: JS Interop Callback Lifecycle

When registering JS event listeners that call back to .NET via `DotNetObjectReference`:

1. **Guard against re-registration**: Use string identity comparison (`_lastRegisteredPanelId`) — avoids DOTNET object create/dispose on every render.
2. **try/catch on registration**: `JSException` can occur if the DOM element was removed between renders.
3. **Unregister before dispose**: Always call `UnregisterHoverEvents` BEFORE `DisposeAsync` — prevents stale DOTNET references in JS closures.
4. **DisposeAsync cleanup**: Both `DisposeAsync` and the re-registration path must pair `UnregisterHoverEvents` + `DisposeAsync`.

## Pitfall 5: `dropTargets` Map Memory Leak

When Blazor components register DOM elements as drop targets for drag-and-drop, the TS layer stores them in a `Map<HTMLElement, TargetData>`. Unlike `WeakMap<HTMLElement, Handler>` used for `dragHandlers`, a regular `Map` prevents garbage collection of removed DOM elements.

Blazor frequently recreates DOM elements during render cycles. Each re-render:
1. Old element removed from DOM → `data-xd-dropzone` attribute removed
2. New element created → `registerDropTarget(newElement, ...)` → new Map entry
3. Old Map entry still holds reference to removed element → **memory leak**

**Fix**: Use `WeakMap` for `dropTargets` to match the `dragHandlers` pattern. `findDropTarget` needs to switch from `Map.forEach` to iterating DOM-registered elements via attribute query.

## Pitfall 6: `write_file` Overwrites Prior Patches

When editing the same file across multiple phases within one session, `write_file` silently discards all changes made by prior `patch` calls. Use `patch` (not `write_file`) for follow-up edits to files already modified in the current session. If a file needs a full rewrite mid-session, read it first with `read_file` to capture the current state, then `write_file` the merged result.

## Common Pitfalls

The six pitfalls below cover the most frequent Blazor WASM interaction failures encountered in production: non-bubbling event directives (Pitfall 1), render-state lifecycle ordering (Pitfalls 2–3), JS interop callback lifecycle management (Pitfall 4), drag-and-drop memory leaks (Pitfall 5), and session-state file-editing hazards (Pitfall 6). Each entry is a standalone troubleshooting guide — match the symptom to the pitfall and apply the verified fix.

## Cross-Reference: Verification Pattern

After every Blazor JS interop or lifecycle change, run a focused ad-hoc verification script:

## Verification

- [ ] Browser console shows 0 JS errors after page load
- [ ] All event handlers fire correctly (manual browser test on each event type)
- [ ] No `DisposeAsync` / `DotNetObjectReference` leaks (check for "disposed reference" errors)
- [ ] Drag-and-drop still works after Blazor re-renders (toggle panels, re-drag)
- [ ] `write_file` used only for initial file creation; all follow-up edits use `patch`
- [ ] `OnAfterRenderAsync` guards verified: leaf components have guards, parent components do not
