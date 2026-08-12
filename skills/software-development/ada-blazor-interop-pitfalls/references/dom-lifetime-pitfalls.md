# Blazor DOM Lifetime & JS Interop Patterns

> Extracted from ada-blazor-interop-pitfalls SKILL.md per agentskills.io progressive disclosure guidelines.

## Blazor @if Removes DOM Elements Needed by JS Interop

**Pitfall**: Placing DOM elements that JS interop depends on inside Blazor
`@if` conditional blocks means they vanish from the DOM when the condition
is false. JS-side operations that iterate registered drop targets
(`findDropTarget`, indicator rendering) have zero elements to hit-test,
even though the logical region should still be a valid drop zone.

### Real-machine failure symptoms (Lib PanelDrag, 2026-07-24)

| Symptom | Root cause |
|---------|-----------|
| Only 2-4 drop zones instead of 6 | `@if (ShowLeftColumn)` removed entire `.xd-left-dock` subtree |
| Highlight indicator wrong size/position | `position: absolute; inset: 0` inside `0fr` CSS grid track → zero-area bounding rect |
| ToolBar indicator always on RT | Missing `data-xd-region` attribute on invisible divs; `getRegionSideFromElement` defaulted to `'right'` |
| Layout changed during drag | `position: relative` on dock container + visible scaffolds took real space |

### Why C#-rendered divs fail

```razor
<!-- LibLayout.razor: the drop target container is inside @if -->
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

### Fix: string-equality guard

```csharp
private string? _lastRegisteredPanelId;

protected override async Task OnAfterRenderAsync(bool firstRender)
{
    var currentId = Panel.Id.Value;
    if (!firstRender && string.Equals(_lastRegisteredPanelId, currentId, StringComparison.Ordinal))
        return;
    // Unregister old + Register new
    _lastRegisteredPanelId = currentId;
}
```

See `references/mouseenter-mouseleave-fix.md` for the complete pattern.

### When NOT to use this guard: parent components managing child refs

For a **parent** component (like ToolBar) that manages `ElementReference[]` arrays
populated by children's `OnAfterRender`, the guard is BACKWARDS:

```csharp
// WRONG for parents managing child refs:
var hash = PanelIdHash(Panels);
if (!firstRender && _lastHash == hash) return;  // ← GUARD
```

`StateHasChanged()` triggers re-render. Children populate `_entryRefs[i]` with NEW
ElementReferences. Parent checks hash → matches → returns. The NEW ElementReferences
never get drag handlers attached.

**Fix**: Remove the hash guard. Always detach old + re-attach:

```csharp
var hash = PanelIdHash(Panels);
if (firstRender || _lastHash != hash)
    _lastHash = hash;

await DetachAll();
// Always re-attach — _entryRefs may have new ElementReferences
for (var i = 0; i < _entryRefs.Count; i++) { ... }
```

**Rule of thumb**:
- **Leaf component** → use string/hash guard to skip redundant re-registration
- **Parent managing child refs** → NO guard; always detach + re-attach

## Parent-First Lifecycle Order (OnAfterRender vs OnAfterRenderAsync)

**Pitfall**: Merging `OnAfterRender(bool)` (synchronous) into `OnAfterRenderAsync(bool)` (async)
breaks parent-to-child communication when the parent depends on child `@ref` values being
populated before its own `OnAfterRenderAsync` runs.

### Blazor lifecycle order

```
1. OnAfterRender(bool)      — sync, parent → children depth-first
2. OnAfterRenderAsync(bool) — async, parent → children depth-first
```

### DO NOT merge

```csharp
// WRONG — parent reads _entryRefs before child has populated them
protected override async Task OnAfterRenderAsync(bool firstRender)
{
    RegisterElementRef?.Invoke(_elRef);   // runs AFTER parent's OnAfterRenderAsync
}
```

### Keep separate

```csharp
// RIGHT — sync registration in OnAfterRender, async hover in OnAfterRenderAsync
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
