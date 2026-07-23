# Example: Atlas Staged Diff Efficiency Review (2026-07-20)

Real output from a `code-efficiency-review` run on a Blazor WASM docking layout
(`Atlas`) staged diff covering TypeScript drag cleanup, C# auto-hide flyout,
JSON DTO extraction, and async disposal patterns.

---

## Findings (ordered by confidence/severity)

### 🔴 Finding 1: ToolBar.razor — CTS leak on every hover-leave
**File**: `src/Atlas/Components/ToolBar.razor:148-149`
**Problem**: `StartFlyoutHideDelay()` calls `_flyoutDelayCts?.Cancel()` then
immediately `_flyoutDelayCts = new CancellationTokenSource()` — the
old CTS is orphaned, never disposed. Under rapid mouse movement, many
CTS objects pile up waiting for finalizer/GC. `Dispose()` only cleans
the *last* assigned CTS.
**Fix**: `_flyoutDelayCts?.Dispose()` before reassignment:
```csharp
_flyoutDelayCts?.Cancel();
_flyoutDelayCts?.Dispose();
_flyoutDelayCts = new CancellationTokenSource();
```
**Confidence**: HIGH | **Risk**: SAFE — one-line add, no behavioral change.

### 🔴 Finding 2: AtlasLayout.razor — Event handler leak pins GC
**File**: `src/Atlas/Components/AtlasLayout.razor:164-166, 178-185`
**Problem**: `OnInitialized` subscribes three lambdas to
`_layoutContext.Events.*` that capture `this`. `DisposeAsync` never
unsubscribes them. When an external `Context` is injected (param
non-null), `DisposeAsync` is a no-op — the EventDispatcher's delegate
chain keeps AtlasLayout alive after disposal.
**Fix**: Lift handlers to named methods, unsubscribe in DisposeAsync:
```csharp
private void OnLayoutChanged(object? _, LayoutChangedEventArgs __) => InvokeAsync(StateHasChanged);
// In DisposeAsync:
_layoutContext.Events.LayoutChanged -= OnLayoutChanged;
_layoutContext.Events.TabClosed -= OnTabClosed;
_layoutContext.Events.TabActivated -= OnTabActivated;
```
**Confidence**: HIGH | **Risk**: SAFE — standard Blazor dispose pattern.

### 🟡 Finding 3: AtlasLayout.razor — 6 × `.ToList()` per render
**File**: `src/Atlas/Components/AtlasLayout.razor:92-98`
**Problem**: `PanelsIn(string)` is called 6 times from markup, each
allocating a new `List<>` via `.Where().ToList()`. For N=20 panels,
that's 6×20=120 iterations + 7 list allocations per render.
**Fix**: Pre-compute with `ToLookup` on state change:
```csharp
_panelsByRegion = State.DockPanels.ToLookup(p => p.RegionName, StringComparer.OrdinalIgnoreCase);
// Then: _panelsByRegion[regionName] instead of .Where().ToList()
```
**Confidence**: MEDIUM | **Risk**: SAFE.

### 🟡 Finding 4: LayoutContext.cs — `_recentTabIds` not cleared on reset
**File**: `src/Atlas/Services/LayoutContext.cs:455`
**Problem**: `ResetLayout()` clears `_history` but not `_recentTabIds`.
After reset, zombie tab IDs persist in the MRU list. `PickNextTab()`
passes `_recentTabIds.ToArray()` to the activation strategy, which may
reference deleted tabs.
**Fix**: Add `_recentTabIds.Clear()` alongside `_history.Clear()`.
**Confidence**: MEDIUM | **Risk**: SAFE.

### 🟢 Finding 5: ToolBar.razor — N serial JS interop calls on first render
**File**: `src/Atlas/Components/ToolBar.razor:178-191`
**Problem**: `OnAfterRenderAsync(firstRender: true)` iterates ALL panels
and calls `DragInterop.AttachDragHandlers` for each — one JS interop
call per panel.
**Fix**: Batch into a single JS invocation accepting an array.
**Confidence**: LOW | **Risk**: CAREFUL — significant JS refactoring;
acceptable for typical panel counts (< 50).

### 🟢 Finding 6: LayoutDto.cs — `.ToDictionary()` copies on export
**File**: `src/Atlas/Services/LayoutDto.cs:315`
**Problem**: `TabDto.FromModel()` copies the entire `Parameters`
dictionary with `.ToDictionary()` on every layout serialization (auto-save).
**Fix**: Shallow copy if immutability not required. Micro-optimization.
**Confidence**: LOW | **Risk**: SAFE.

---

## Positives (confirmed-correct changes in the diff)

- **DragInterop.cs**: `lock` → `SemaphoreSlim` — correct and necessary;
  synchronous `lock` cannot span `await`.
- **PersistenceService.cs**: `catch (Exception)` narrowed to `JSException`
  + `TaskCanceledException` — fails fast on unexpected errors instead of
  silently swallowing them.
- **index.ts**: `cleanupDragListeners()` deduplication — clean DRY extract.
- **TabContent.razor**: `else if (ActiveTab is not null)` — fixes a null-ref
  path the old code missed.

## Key Pitfalls Discovered

1. **CTS replace-without-dispose**: When debounce/delay patterns use a
   `CancellationTokenSource` field that gets reassigned (`_cts = new()`),
   the old CTS must be disposed first. Cancelling alone isn't enough —
   CTS implements `IDisposable` and holds timer resources.
   *Lesson: grep for `= new CancellationTokenSource()` on fields — each
   reassignment without a prior `.Dispose()` is a leak.*

2. **Event handler leak via captured-this lambdas**: In Blazor components,
   event subscriptions (`+=`) with lambdas that capture `this` in
   `OnInitialized` must be unsubscribed (`-=`) in `Dispose`. When the
   event source is an externally-injected service/context, the component
   leaks even after disposal. *Lesson: always pair `+=` with `-=` in Blazor
   lifecycle; named methods make this auditable.*

3. **`.ToList()` in Blazor computed properties**: Properties called from
   Razor markup run on every render cycle. If they allocate (`ToList`,
   `new List`, `Select`) and the markup calls them multiple times, the
   allocation cost multiplies. *Lesson: use `ToLookup` or `ToDictionary`
   for grouped access, and cache results in `OnParametersSet`.*
