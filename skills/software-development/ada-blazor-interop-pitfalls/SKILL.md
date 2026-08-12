---
name: ada-blazor-interop-pitfalls
description: "Use when a Blazor/Razor task involves JS interop, DOM events, hover/mouseenter handlers, DotNetObjectReference disposal, WeakMap/Map leaks, C#-invokable module exports missing from the shipped bundle, JS preview vs commit render timing, or drag/drop targets that disappear after render. Prefer ada-blazor-interaction-pitfalls for pure Blazor lifecycle/rendering issues."
version: 1.3.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, interop, js, events, pitfalls, wasm]
    related_skills: [ada-blazor-component-library, ada-dotnet-blazor-library, ada-blazor-interaction-pitfalls, ada-blazor-ui-audit, ada-ui-interaction-protocol-contracts]
---

# Blazor JS Interop Pitfalls

## Overview

Covers the most common Blazor .NET 6 JS interop failures encountered in production — non-bubbling DOM events, `IJSRuntime` patterns, `DotNetObjectReference` lifecycle management, drag-and-drop memory leaks, and invisible drop targets. Each pitfall is a standalone troubleshooting guide with verified fixes. Documented failures and fixes for Blazor .NET 6 JS interop event handling.

For lifecycle and rendering pitfalls (`StateHasChanged`, `OnAfterRender`, `@ref` in `RenderFragment`), see lifecycle debugging patterns.

## Agent Execution Contract

Inputs to identify first:
- Razor component, TypeScript/JavaScript module, and interop service files involved.
- The event or interop call that fails, including browser console errors if available.
- Whether the symptom is DOM event delegation, module loading, callback lifetime, or render-lifetime target loss.

Default workflow:
1. Confirm whether the event bubbles and is supported by Blazor directives.
2. Inspect both Razor and JS/TS sides of the interop boundary.
3. Verify `DotNetObjectReference` ownership and disposal lifetime.
4. Prefer `IJSObjectReference` module imports over `eval` or dynamic string imports.
5. For disappearing targets, check Blazor re-render lifecycle and re-registration.

Stop conditions:
- The symptom is pure Blazor rendering/lifecycle rather than JS interop; route to `ada-blazor-interaction-pitfalls`.
- Browser/runtime evidence is needed but unavailable.
- Fixing requires changing public component API or architecture beyond the local interop path.

Output contract:
- Interop boundary map: Razor -> C# service -> JS/TS.
- Root cause category.
- Fix pattern used.
- Verification steps, including browser/event behavior when applicable.

## When to Use

- A Blazor Razor event directive compiles but never fires at runtime
- Adding mouseenter/mouseleave, focus/blur, or other non-bubbling DOM event handlers
- Replacing `@on{event}` directives with JS interop for unsupported events
- Debugging silent event failures in Blazor WASM
- `DotNetObjectReference` disposal errors or memory leaks
- Drag-and-drop targets disappearing after Blazor re-renders


Don't use for: lifecycle or rendering issues — use lifecycle debugging patterns instead. General Blazor component architecture — use component library design patterns instead.

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

See `references/mouseenter-mouseleave-fix.md` for the complete three-layer pattern (TypeScript → C# interop → Razor component integration) used to fix this in a real component library project.

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
    _module = await js.InvokeAsync<IJSObjectReference>("import", "./lib/lib.js");
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

## Public API Re-Export Trap (C#-invokable module functions)

**Pitfall**: C# calls bundled JS module functions by name via `module.InvokeVoidAsync("fnName", ...)`. When the JS bundle has an entry surface (e.g. `public-api.ts`) that re-exports functions from implementation modules (`controller.ts`), a function exported from the implementation but NOT re-exported in the entry surface is missing from the shipped bundle, and a real browser fails with `Error: Could not find 'fnName' ('fnName' was undefined)`.

**Why tests miss it**: bUnit's `JSRuntimeMode.Loose` does not validate the target function exists — every `InvokeVoidAsync` is recorded and returns success. Node tests import the implementation module directly and never load the entry surface. Both layers stay green while the real browser breaks.

**Fix pattern**:
1. Add the new export to the `export { ... }` re-export block in the entry surface.
2. Rebuild the bundle and confirm the function is present: `grep -c "fnName" wwwroot/<bundle>.js`.
3. Add a Node regression test that imports the **entry surface** and asserts `typeof` each C#-invokable entry point is `"function"`.
4. If the library ships as a NuGet package, re-pack it and clear+restore the consumer sample's local package cache so the real-browser consumer actually gets the rebuilt bundle.

**Check** every C# `InvokeVoidAsync`/`InvokeAsync` call site against the entry-surface exports when adding or renaming a controller entry point.

**Browser-only attach failures (diagnostics)**: when a feature works under `dotnet run` but attach/interop fails only in the real browser after a rebuild, verify what the browser actually receives — `fetch('/<bundle>.js').then(r => r.text()).then(t => ({ len: t.length, hasFix: t.includes('fnName') }))`. The bundle is often a gitignored build artifact regenerated by a build step, and the browser caches the old bundle — hard refresh or restart the dev server before treating it as a code bug. A protocol-version or attach handshake that bUnit's loose mode cannot exercise is the same class: prove the shipped artifact contains the expected symbols.

## JS Render-Timing: Preview vs Commit Cycle

**Overview**: a class of Blazor WASM bugs where the **JS interaction controller** holds visual state (inline styles, drag previews, resize previews) that must stay in sync with the **Blazor commit/render cycle**. The JS side previews the gesture with inline styles; the commit is a separate async round trip (JS→.NET invoke → operation → `Changed` event → `StateHasChanged` → render batch → DOM apply). Any JS code that clears or reads preview state between the terminal gesture and the render batch observes a DOM that still holds the *old* Blazor-rendered value — producing visible bounce, snap-back, or stale-state bugs.

**When to use**: a drag/resize gesture "bounces" or snaps back on release before settling at the final position; JS clears an inline preview style and the layout visibly reverts for a frame or two; JS state (preview, overlay, hover) must be removed exactly when Blazor's re-render applies — not before, not never; you need deterministic tests for rAF/timer-based deferred JS logic against a fake DOM.

**Preview-Before-Commit Bounce**: on pointerup the controller cleared the JS inline preview style synchronously, then sent the commit message. The DOM fell back to the last Blazor-rendered value (a) until the async commit round trip completed (b). The gap between `clearPreview` and the render batch application is the bounce.

Why the obvious fixes don't work:
- Moving `clearPreview` after the `send` still runs synchronously before the render batch.
- `setTimeout(0)` also fires before the interop round trip lands.
- The commit can be **rejected** (stale base revision, constraint failure, no-change), in which case no re-render ever arrives — so "just wait for the render" needs a bounded fallback.

**Fix Pattern: Keep Preview Until the Commit's Re-Render Applies**
1. **Keep the preview inline style on the terminal gesture** when a commit is sent; only clear immediately when nothing changed (no commit).
2. **Rely on Blazor's style-attribute replacement to self-clean**: the re-render calls `setAttribute("style", ...)`, which wipes ALL inline preview styles. A successful commit removes the preview without JS doing anything.
3. **Detect the applied render via a revision attribute**: poll the element's `data-revision` at rAF cadence; when it advances past the `baseRevision` captured at gesture start, the render applied. Clear as an idempotent no-op safety net.
4. **Bounded fallback for rejected commits**: if no re-render arrives within a cap (e.g. 120 rAF frames ≈ 2 s), clear the preview so the layout reverts to the committed ratio instead of freezing at the preview position.
5. **Cancel on re-grab**: a new pointerdown on the same element must cancel the pending clear, otherwise the earlier commit's deferred clear wipes the new gesture's preview mid-drag.
6. **Cancel on dispose / generation change** so no timer/frame leaks.

**Testability: deterministic rAF tests** — rAF-based deferred logic is testable without real timers:
- Give the controller fixture a fake `Window` that records animation frames and exposes `flushAnimationFrames()` (runs one frame per call; re-registered frames run on the next flush).
- The fixture MUST set `root.ownerDocument` + `document.defaultView`, otherwise the controller takes the `setTimeout` fallback branch and tests become slow/flaky.
- Regression test shape: drag → release → assert preview STILL present (fails on the old clear-immediately code) → advance `data-revision` → flush one frame → assert preview cleared.
- Rejected-commit test: release → flush past the frame cap → assert preview cleared (reverted).
- Re-grab test: release → pointerdown again on the same element → move → flush → assert the new preview is untouched.

**Verification**: `tsc --noEmit`; Node controller tests green; solution build/test green (the JS bundle is a gitignored build artifact; CI regenerates it); real-browser manual acceptance for interaction bugs — bUnit/headless cannot reproduce render-batch timing; state this as a blocker rather than faking evidence.

## Verification

After switching from `@on{event}` to JS interop:
- [ ] `npm run build:js` succeeds and output contains the new TS functions
- [ ] `dotnet build` 0 errors
- [ ] `dotnet test` full suite passes
- [ ] Browser console shows 0 JS errors after page load
- [ ] Manual browser test confirms the event fires (e.g., hover triggers flyout)
- [ ] No `DisposeAsync` / `DotNetObjectReference` leaks

## Related

- Blazor component library design patterns — general Blazor component library patterns
- .NET Blazor library setup patterns — RCL setup, naming conventions, NuGet packaging
- Lifecycle and rendering debugging patterns
- `references/mouseenter-mouseleave-fix.md` — complete three-layer fix pattern with render guard and try/catch
- `references/invisible-drop-targets.md` — JS dynamic element creation for drop targets that survive Blazor conditional rendering
- `references/lifecycle-pitfalls.md` — see lifecycle and rendering debugging documentation (StateHasChanged timing, OnAfterRender ordering, @ref in RenderFragment, paired-list IndexOutOfRange)
- `references/dom-lifetime-pitfalls.md` — see lifecycle and rendering debugging documentation (StateHasChanged timing, OnAfterRender ordering, @ref in RenderFragment, paired-list IndexOutOfRange)
