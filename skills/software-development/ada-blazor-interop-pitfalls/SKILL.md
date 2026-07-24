---
name: ada-blazor-interop-pitfalls
description: Use when debugging Blazor JS interop issues, adding mouse/hover/keyboard event handlers in Razor components, or diagnosing silently-ignored Blazor event directives.
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

## StateHasChanged Lifecycle Pitfall

When a Blazor component calls `StateHasChanged()` internally (e.g., from a click handler),
Blazor re-renders the component **without** invoking `OnParametersSet()`. Any mutable
field used as a render-loop counter (like `_renderIndex` in `BuildRenderTree`) that was
reset only in `OnParametersSet` will retain its stale value, causing `IndexOutOfRange`.

### Root Cause

```text
User click → OnEntryClick → Context.TogglePanel → InvokeAsync(StateHasChanged)
                                                         ↓
                                              Blazor re-renders component
                                              WITHOUT calling OnParametersSet()
                                                         ↓
                                              _renderIndex still = Panels.Count
                                              _entryPanelIds[Panels.Count] → 💥
```

### Fix: reset in ShouldRender() — the only lifecycle method guaranteed before every render

The simplest approach — moving the reset into `SyncEntryCollections` (called by both
`OnParametersSet` and `OnAfterRenderAsync`) — **can still fail** when `OnAfterRenderAsync`
has a hash guard that skips `SyncEntryCollections`:

```csharp
// OnAfterRenderAsync with hash guard — SyncEntryCollections may be SKIPPED
if (!firstRender && _lastPanelIdHash == currentHash)
    return;  // ← GUARD! SyncEntryCollections() NOT called, _renderIndex NOT reset
```

The only Blazor lifecycle method that fires before **every** `BuildRenderTree`, including
`StateHasChanged()`-only renders, is `ShouldRender()`:

```csharp
/// <summary>
/// Reset the render-time panel index before every render pass.
/// OnParametersSet is NOT called for StateHasChanged()-only re-renders,
/// and OnAfterRenderAsync hash guards may skip collection sync.
/// ShouldRender fires before BuildRenderTree regardless of trigger.
/// </summary>
protected override bool ShouldRender()
{
    _renderIndex = 0;
    return true;
}
```

After adding `ShouldRender()`, `_renderIndex` can be removed from `SyncEntryCollections`
since `ShouldRender` handles it unconditionally. `SyncEntryCollections` is only responsible
for list sizing, not index management.

### Also applies to

- Any `_renderIndex` / `_counter` / `_position` field used in `BuildRenderTree`
- Components using pre-allocated `ElementReference[]` arrays with index-based assignment
- `foreach` loops in Razor markup that write to indexed collections

## Pre-Computation: Eliminate Mutable Render State Entirely

After stabilizing with `ShouldRender()`, the cleaner long-term solution is to
**eliminate the mutable render-time field entirely** by pre-computing in
`OnParametersSet`. Replace `_renderIndex` with a `Dictionary<PanelId, int>` cache
built once per parameter change.

### Before (mutable field + ShouldRender guard)

```csharp
private int _renderIndex;

protected override bool ShouldRender()
{
    _renderIndex = 0;
    return true;
}

// In BuildRenderTree:
var currentIndex = _renderIndex;
_entryPanelIds[currentIndex] = panel.Id.Value;
_renderIndex = currentIndex + 1;
```

### After (pre-computed cache, no mutable render state)

```csharp
private readonly Dictionary<PanelId, int> _panelIndexCache = new();

protected override void OnParametersSet()
{
    // Compute flat order once — same GroupBy/OrderBy as the template
    var ordered = _upperGroups.SelectMany(g => g)
        .Concat(_lowerGroups.SelectMany(g => g)).ToList();

    _panelIndexCache.Clear();
    for (int i = 0; i < ordered.Count; i++)
        _panelIndexCache[ordered[i].Id] = i;

    // Pre-fill indexed arrays — no render-time writes needed
    _entryPanelIds.Clear();
    _entryRefs.Clear();
    foreach (var p in ordered)
    {
        _entryPanelIds.Add(p.Id.Value);
        _entryRefs.Add(default);
    }
}

// In BuildRenderTree — pure immutable lookup:
var idx = _panelIndexCache[panel.Id];
// No write to _entryPanelIds (already pre-filled)
// No mutable counter to increment
```

### Side benefit: caches the grouped results

Once you pre-compute the flat order, you can also **cache the `GroupBy`/`OrderBy`
results** that the template recomputed on every render:

```csharp
private IReadOnlyList<IGrouping<string, DockPanelModel>> _upperGroups = Array.Empty<...>();
private IReadOnlyList<IGrouping<string, DockPanelModel>> _lowerGroups = Array.Empty<...>();

// In OnParametersSet:
_upperGroups = panels.Where(IsUpper).GroupBy(...).OrderBy(...).ToList();
_lowerGroups = panels.Where(IsBottom).GroupBy(...).ToList();
```

The template reads from the cached fields instead of recomputing LINQ queries.
This eliminates all render-time allocations from the grouping logic.

### When to use

- Panel/entry count ≤ ~50 (pre-compute allocation is amortized)
- Correctness preferred over minimal per-render allocation
- Template uses nested `@foreach` across multiple sections with a shared index

### When to keep ShouldRender

- High-frequency renders (animation, real-time data) where a `List.Clear() + rebuild`
  per render is wasteful
- Merging the two lifecycle methods seems like a clean-up (one less override) but silently breaks

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

## Blazor @if Removes DOM Elements Needed by JS Interop

**Pitfall**: Placing DOM elements that JS interop depends on inside Blazor
`@if` conditional blocks means they vanish from the DOM when the condition
is false. JS-side operations that iterate registered drop targets
(`findDropTarget`, indicator rendering) have zero elements to hit-test,
even though the logical region should still be a valid drop zone.

### Real-machine failure symptoms (Atlas PanelDrag, 2026-07-24)

| Symptom | Root cause |
|---------|-----------|
| Only 2-4 drop zones instead of 6 | `@if (ShowLeftColumn)` removed entire `.xd-left-dock` subtree |
| Highlight indicator wrong size/position | `position: absolute; inset: 0` inside `0fr` CSS grid track → zero-area bounding rect |
| ToolBar indicator always on RT | Missing `data-xd-region` attribute on invisible divs; `getRegionSideFromElement` defaulted to `'right'` |
| Layout changed during drag | `position: relative` on dock container + visible scaffolds took real space |

### Why C#-rendered divs fail

```razor
<!-- AtlasLayout.razor: the drop target container is inside @if -->
@if (_visibility.ShowLeftColumn)      // ← FALSE when no expanded left panels
{
    <div class="xd-left-dock">        // ← NOT RENDERED → drop targets don't exist
        ...
        <div class="xd-hidden-drop-targets-left">  // ← unreachable
            @if (DragSvc.IsPanelDragging)
            {
                <div data-xd-dropzone="dock-region" ...></div>  // ← never created
            }
        </div>
    </div>
}
```

Even when the `@if` condition IS true, if the CSS grid track has `0fr`
(because no expanded panels in child regions), `position: absolute` children
get bounding rects of zero, making indicator positioning fail.

### Fix: JS Dynamic Element Creation

Create drop-target divs from JavaScript using `document.createElement` with
`position: fixed`, anchored to **always-visible** DOM elements (ToolBars).
These are entirely outside Blazor's render tree — they exist whenever the
drag is active, regardless of what Blazor's `@if` blocks have rendered.

See `references/invisible-drop-targets.md` for the complete corrected
implementation (v3) with three-tier rect resolution.

**Indicator sizing**: The highlight indicator must use the drop target's
full `getBoundingClientRect()` dimensions, not hardcoded constants like
180×120. Since the JS drop target is already positioned at the correct
dock region bounds, mirroring its rect ensures the indicator covers the
right area at the right size.

### Design principle

When a DOM element must exist for JS interop **regardless of Blazor component
visibility**:

1. **Do NOT** render it in Razor markup (Blazor `@if` will kill it)
2. **Do** create it from JS with `document.createElement`
3. **Do** anchor it to always-visible DOM elements for positioning
4. **Do** set `position: fixed` so it doesn't depend on parent container sizing
5. **Do** include all required `data-xd-*` attributes — missing attributes
   can cause silent fallback to wrong defaults in JS

## JS Interop Re-Registration on Every Render

**Pitfall**: `OnAfterRenderAsync` (without a guard) runs on every Blazor render cycle.
JS interop operations inside it — `RegisterHoverEvents`, `AttachDragHandlers`, etc. —
fire even when nothing changed, causing unnecessary JS calls and `DotNetObjectReference`
allocate/dispose churn.

### Fix: string-equality guard matching existing patterns

The existing patterns in DockPanel (`RegisterDragSourceIfChanged`) and TabBar
(hash comparison) use a `_lastXxxId` field to skip re-registration when the target
hasn't changed:

```csharp
private string? _lastRegisteredPanelId;

protected override async Task OnAfterRenderAsync(bool firstRender)
{
    var currentId = Panel.Id.Value;

    // Guard: skip if nothing changed
    if (!firstRender && string.Equals(_lastRegisteredPanelId, currentId, StringComparison.Ordinal))
        return;

    // Unregister old
    if (_hoverCallback is not null)
    {
        try { await DragInterop.UnregisterHoverEvents(JS, elRef); }
        catch (JSException) { /* DOM removed */ }
        await _hoverCallback.DisposeAsync();
    }

    // Register new
    _hoverCallback = new HoverCallback(...);
    await DragInterop.RegisterHoverEvents(JS, elRef, _hoverCallback.Reference, currentId);
    _lastRegisteredPanelId = currentId;
}
```

The guard also prevents `DotNetObjectReference` dispose-then-call races: without it,
a mouse event already queued in the JS→.NET pipeline could fire on a disposed reference.
See `references/mouseenter-mouseleave-fix.md` for the complete pattern including
try/catch on JS interop calls and `DisposeAsync` cleanup.

### When NOT to use this guard: parent components managing child refs

The string-equality guard assumes the child component's own data hasn't changed.
For a **parent** component (like ToolBar) that manages `ElementReference[]` arrays
populated by children's `OnAfterRender`, the guard is BACKWARDS:

```csharp
// WRONG for parents managing child refs:
var hash = PanelIdHash(Panels);
if (!firstRender && _lastHash == hash) return;  // ← GUARD
await DetachAll();
// ... re-register drag handlers ...
```

The problem: `StateHasChanged()` triggers a re-render. Children's `OnAfterRender`
(sync) populates `_entryRefs[i]` with NEW ElementReferences (Blazor may recreate DOM).
Then parent's `OnAfterRenderAsync` checks hash → matches → returns.
The NEW ElementReferences never get drag handlers attached. User can no longer drag.

**Fix**: Remove the hash guard. Always detach old + re-attach:

```csharp
var hash = PanelIdHash(Panels);
if (firstRender || _lastHash != hash)
    _lastHash = hash;  // Track hash but don't return

await DetachAll();  // Always cleanup old handlers
// Always re-attach — _entryRefs may have new ElementReferences
for (var i = 0; i < _entryRefs.Count; i++) { ... }
```

`AttachDragHandlers` is idempotent (calls `detachDragHandlers` internally).
Re-registering every render is a small cost for correctness.

**Rule of thumb**:
- **Leaf component** (ToolBarEntry, DockPanel header) → use string/hash guard to skip redundant re-registration
- **Parent managing child refs** (ToolBar, TabBar) → NO guard; always detach + re-attach

## Parent-First Lifecycle Order (OnAfterRender vs OnAfterRenderAsync)

**Pitfall**: Merging `OnAfterRender(bool)` (synchronous) into `OnAfterRenderAsync(bool)` (async)
breaks parent-to-child communication when the parent depends on child `@ref` values being
populated before its own `OnAfterRenderAsync` runs.

### Blazor lifecycle order

```
1. OnAfterRender(bool)      — sync, parent → children depth-first
2. OnAfterRenderAsync(bool) — async, parent → children depth-first
```

If a child component uses `OnAfterRender` to register its `ElementReference` with a parent
collection (e.g., `RegisterElementRef?.Invoke(_elRef)`), the parent's `OnAfterRenderAsync`
can safely read the collection — the children have already populated it.

If `OnAfterRender` is removed and the registration is moved to `OnAfterRenderAsync`,
the parent's `OnAfterRenderAsync` runs BEFORE the child's, so the collection is empty.

### DO NOT merge

```csharp
// WRONG — parent reads _entryRefs before child has populated them
// (removed OnAfterRender, moved everything to OnAfterRenderAsync)
protected override async Task OnAfterRenderAsync(bool firstRender)
{
    RegisterElementRef?.Invoke(_elRef);   // runs AFTER parent's OnAfterRenderAsync
    // ... hover registration ...
}
```

### Keep separate

```csharp
// RIGHT — synchronous registration in OnAfterRender, async hover in OnAfterRenderAsync
protected override void OnAfterRender(bool firstRender)
{
    RegisterElementRef?.Invoke(_elRef);   // runs BEFORE parent's OnAfterRenderAsync
}

protected override async Task OnAfterRenderAsync(bool firstRender)
{
    // hover registration — doesn't affect parent's drag handler setup
}
```

### When this matters

- Parent collects child `ElementReference[]` for JS interop (drag handlers, focus management)
- Parent's `OnAfterRenderAsync` iterates over children's refs
- Merging the two lifecycle methods seems like a clean-up (one less override) but silently breaks
