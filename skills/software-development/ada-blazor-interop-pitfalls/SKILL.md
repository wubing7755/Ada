---
name: ada-blazor-interop-pitfalls
description: "Use when debugging Blazor JS interop issues, adding mouse/hover/keyboard event handlers in Razor components, or diagnosing silently-ignored Blazor event directives. Covers IJSRuntime patterns, DotNetObjectReference lifecycle, invisible drop targets, mouseenter/mouseleave fixes, and WeakMap memory management."
version: 1.3.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, interop, js, events, pitfalls, wasm]
    related_skills: [ada-blazor-component-library, ada-dotnet-blazor-library, ada-blazor-interaction-pitfalls]
---

# Blazor JS Interop Pitfalls

## Overview

Covers the most common Blazor .NET 6 JS interop failures encountered in production — non-bubbling DOM events, `IJSRuntime` patterns, `DotNetObjectReference` lifecycle management, drag-and-drop memory leaks, and invisible drop targets. Each pitfall is a standalone troubleshooting guide with verified fixes. Documented failures and fixes for Blazor .NET 6 JS interop event handling.

For lifecycle and rendering pitfalls (`StateHasChanged`, `OnAfterRender`, `@ref` in `RenderFragment`), see `ada-blazor-interaction-pitfalls`.

## When to Use

- A Blazor Razor event directive compiles but never fires at runtime
- Adding mouseenter/mouseleave, focus/blur, or other non-bubbling DOM event handlers
- Replacing `@on{event}` directives with JS interop for unsupported events
- Debugging silent event failures in Blazor WASM
- `DotNetObjectReference` disposal errors or memory leaks
- Drag-and-drop targets disappearing after Blazor re-renders


Don't use for: lifecycle or rendering issues — load `ada-blazor-interaction-pitfalls`. General Blazor component architecture — load `ada-blazor-component-library`.

## Supported Mouse Events (.NET 6)

Blazor .NET 6 supports these mouse event directives out of the box:

```
@onclick, @ondblclick, @onmousedown, @onmouseup,
@onmousemove, @onmouseover, @onmouseout, @onmousewheel, @oncontextmenu
```

Any directive NOT in this list **compiles without error but is silently ignored** at runtime. Razor does not validate event attribute names against a whitelist — the handler becomes unreachable dead code.

## Non-Bubbling Events Must Use JS Interop

Events that do not bubble (mouseenter, mouseleave, focus, blur, load, unload) cannot be handled by Blazor's event delegation system (which listens at the document level and relies on event propagation). For these, register native listeners via JS interop.

### Fix Pattern

See `references/mouseenter-mouseleave-fix.md` for the complete three-layer pattern (TypeScript → C# interop → Razor component integration) used to fix this in Atlas.

### Why not `@onmouseover`/`@onmouseout`?

They fire when entering/leaving child elements, causing flicker for flyout UIs. `mouseenter`/`mouseleave` only fire when crossing the target element boundary.

## JS Interop: `IJSObjectReference` Pattern

### Avoid `eval` + `import()`

Using `js.InvokeVoidAsync("eval", $"...import('...').then(...)")` for ES module loading is brittle and hard to debug. Use the `IJSObjectReference` pattern instead.

### Initialize once at startup

```csharp
private static IJSObjectReference? _module;
public static async ValueTask InitializeAsync(IJSRuntime js)
{
    _module = await js.InvokeAsync<IJSObjectReference>("import", "./xdocker/xdocker.js");
}

// Then call module methods directly
await _module!.InvokeVoidAsync("attachDragHandlers", element, dragType, dragData, callback);
```

### TypeScript side

Export plain functions (no default export needed):

```typescript
export function attachDragHandlers(
  element: HTMLElement,
  dragType: string,
  dragData: string,
  dotNetHelper: DotNet.DotNetObject
): void { ... }
```

### C# → JS callback pattern

Use `DotNetObjectReference<T>` with `[JSInvokable]` methods. Pass to JS via `DotNetObjectReference.Create(callback)` — the runtime handles reference counting automatically.

### Drag type: pass explicitly from JS to C#

**Wrong** — infer drag type on the C# side:
```csharp
_dragType = _context.State.FindTab(dragData) is not null ? DragType.Tab : DragType.Panel;
```

**Right** — include it as a parameter in the JS → C# callback:
```typescript
dotNet.invokeMethodAsync('OnDragStarted', dragData, dragType, clientX, clientY);
```

## JS Interop Callback Lifecycle

When registering JS event listeners that call back to .NET via `DotNetObjectReference`:

1. **Guard against re-registration**: Use string identity comparison (`_lastRegisteredPanelId`) — avoids DOTNET object create/dispose on every render.
2. **try/catch on registration**: `JSException` can occur if the DOM element was removed between renders.
3. **Unregister before dispose**: Always call `UnregisterHoverEvents` BEFORE `DisposeAsync` — prevents stale DOTNET references in JS closures.
4. **DisposeAsync cleanup**: Both `DisposeAsync` and the re-registration path must pair `UnregisterHoverEvents` + `DisposeAsync`.

## dropTargets Map Memory Leak

**Pitfall**: `dragHandlers` uses `WeakMap<HTMLElement, ...>` (auto-cleanup). `dropTargets` uses `Map<HTMLElement, ...>` (no cleanup). Blazor DOM recreation causes unbounded growth.

**Impact**: Low. `findDropTarget` hit-tests with `getBoundingClientRect()` — removed elements return zero-area, never match. Memory growth proportional to panel count changes, not drags.

**Fix**: Deferred. WeakMap is non-iterable, so `findDropTarget` would break. Proper fix: periodic purge after drag ends or migration to a cleanable structure.

## Verification

After switching from `@on{event}` to JS interop:
- [ ] `npm run build:js` succeeds and output contains the new TS functions
- [ ] `dotnet build` 0 errors
- [ ] `dotnet test` full suite passes
- [ ] Browser console shows 0 JS errors after page load
- [ ] Manual browser test confirms the event fires (e.g., hover triggers flyout)
- [ ] No `DisposeAsync` / `DotNetObjectReference` leaks

## Related

- `ada-blazor-component-library` — general Blazor component library patterns
- `ada-dotnet-blazor-library` — RCL setup, naming conventions, NuGet packaging
- `ada-blazor-interaction-pitfalls` — lifecycle and rendering pitfalls
- `references/mouseenter-mouseleave-fix.md` — complete three-layer fix pattern with render guard and try/catch
- `references/invisible-drop-targets.md` — JS dynamic element creation for drop targets that survive Blazor conditional rendering
- `references/lifecycle-pitfalls.md` — delegated to `ada-blazor-interaction-pitfalls`
- `references/dom-lifetime-pitfalls.md` — delegated to `ada-blazor-interaction-pitfalls`
