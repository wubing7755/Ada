# Blazor Lifecycle Pitfalls

> Extracted from ada-blazor-interop-pitfalls SKILL.md per agentskills.io progressive disclosure guidelines.

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
since `ShouldRender` handles it unconditionally.

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
    var ordered = _upperGroups.SelectMany(g => g)
        .Concat(_lowerGroups.SelectMany(g => g)).ToList();

    _panelIndexCache.Clear();
    for (int i = 0; i < ordered.Count; i++)
        _panelIndexCache[ordered[i].Id] = i;

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
```

### Side benefit: caches the grouped results

```csharp
private IReadOnlyList<IGrouping<string, DockPanelModel>> _upperGroups = Array.Empty<...>();
private IReadOnlyList<IGrouping<string, DockPanelModel>> _lowerGroups = Array.Empty<...>();

// In OnParametersSet:
_upperGroups = panels.Where(IsUpper).GroupBy(...).OrderBy(...).ToList();
_lowerGroups = panels.Where(IsBottom).GroupBy(...).ToList();
```

### When to use

- Panel/entry count ≤ ~50 (pre-compute allocation is amortized)
- Correctness preferred over minimal per-render allocation
- Template uses nested `@foreach` across multiple sections with a shared index

### When to keep ShouldRender

- High-frequency renders (animation, real-time data) where a `List.Clear() + rebuild` per render is wasteful
