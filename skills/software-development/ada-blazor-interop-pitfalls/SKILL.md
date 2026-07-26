---
name: ada-blazor-interop-pitfalls
description: "Use when debugging Blazor JS interop issues, adding mouse/hover/keyboard event handlers in Razor components, or diagnosing silently-ignored Blazor event directives. Covers IJSRuntime patterns, invisible drop targets, and mouseenter/mouseleave fixes."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, interop, js, events, pitfalls, wasm]
    related_skills: [ada-blazor-component-library, ada-dotnet-blazor-library]
---

# Blazor JS Interop Pitfalls

## Overview

Covers the most common Blazor .NET 6 JS interop failures encountered in production — non-bubbling DOM events, render-state lifecycle traps, JS interop callback lifecycle management, drag-and-drop memory leaks, and session-state file-editing hazards. Each pitfall is a standalone troubleshooting guide with verified fixes from Atlas PanelDrag (2026-07-24).

Documented failures and fixes for Blazor .NET 6 JS interop event handling.

## When to Use

- A Blazor Razor event directive compiles but never fires at runtime
- Adding mouseenter/mouseleave, focus/blur, or other non-bubbling DOM event handlers
- Replacing `@on{event}` directives with JS interop for unsupported events
- Debugging silent event failures in Blazor WASM

## Supported Mouse Events (.NET 6)

Blazor .NET 6 supports these mouse event directives out of the box:

```
@onclick, @ondblclick, @onmousedown, @onmouseup,
@onmousemove, @onmouseover, @onmouseout, @onmousewheel, @oncontextmenu
```

Any directive NOT in this list **compiles without error but is silently ignored** at runtime.
Razor does not validate event attribute names against a whitelist — the handler becomes
unreachable dead code.

## Non-Bubbling Events Must Use JS Interop

Events that do not bubble (mouseenter, mouseleave, focus, blur, load, unload) cannot be
handled by Blazor's event delegation system (which listens at the document level and
relies on event propagation). For these, register native listeners via JS interop.

### Fix Pattern

See `references/mouseenter-mouseleave-fix.md` for the complete three-layer pattern
(TypeScript → C# interop → Razor component integration) used to fix this in Atlas.

## Verification

After switching from `@on{event}` to JS interop:
- [ ] `npm run build:js` succeeds and output contains the new TS functions
- [ ] `dotnet build` 0 errors
- [ ] `dotnet test` full suite passes
- [ ] Browser console shows 0 JS errors after page load
- [ ] Manual browser test confirms the event fires (e.g., hover triggers flyout)

## Lifecycle & Render-State Pitfalls

Two deep-dive references cover the most common Blazor lifecycle issues that silently corrupt JS interop state:

- `skill_view(name="ada-blazor-interop-pitfalls", file_path="references/lifecycle-pitfalls.md")` — **StateHasChanged skipping OnParametersSet** (stale render-index → IndexOutOfRange), `ShouldRender()` as the only guaranteed reset point, and **pre-computation pattern** (eliminate mutable render state with dictionary caches)
- `skill_view(name="ada-blazor-interop-pitfalls", file_path="references/dom-lifetime-pitfalls.md")` — **Blazor @if removing JS-dependent DOM elements**, JS dynamic element creation fix, **OnAfterRenderAsync re-registration guards** (leaf vs parent), and **parent-first lifecycle ordering** (OnAfterRender sync vs OnAfterRenderAsync)

## Paired-List Defensive Iteration

**Pitfall**: When a parent component maintains multiple `List<T>` fields that should always
have the same `.Count` (e.g., `_entryPanelIds`, `_entryRefs`, `_entryWrapperRefs` — all
built in the same `ComputeGroupsAndIndex` loop), Blazor lifecycle timing can cause them to
diverge. Use `Math.Min` to prevent `IndexOutOfRange`.

```csharp
// WRONG
for (var i = 0; i < _entryWrapperRefs.Count; i++)
    var panelId = _entryPanelIds[i];  // ← 💥 if shorter

// RIGHT
var count = Math.Min(_entryWrapperRefs.Count, _entryPanelIds.Count);
for (var i = 0; i < count; i++)
    var panelId = _entryPanelIds[i];
```

## dropTargets Map Leak

**Pitfall**: `dragHandlers` uses `WeakMap<HTMLElement, ...>` (auto-cleanup). `dropTargets`
uses `Map<HTMLElement, ...>` (no cleanup). Blazor DOM recreation causes unbounded growth.

**Impact**: Low. `findDropTarget` hit-tests with `getBoundingClientRect()` — removed elements
return zero-area, never match. Memory growth proportional to panel count changes, not drags.

**Fix**: Deferred. WeakMap is non-iterable, so `findDropTarget` would break. Proper fix:
periodic purge after drag ends or migration to a cleanable structure.

## Related

- `ada-blazor-component-library` — general Blazor component library patterns
- `ada-dotnet-blazor-library` — RCL setup, naming conventions, NuGet packaging
- `references/mouseenter-mouseleave-fix.md` — complete three-layer fix pattern with render guard and try/catch (Atlas, 2026-07-24)
- `references/invisible-drop-targets.md` — JS dynamic element creation for drop targets that survive Blazor conditional rendering; **v2 corrected approach** replacing the failed v1 C#-rendered pattern (Atlas, 2026-07-24)

## Related