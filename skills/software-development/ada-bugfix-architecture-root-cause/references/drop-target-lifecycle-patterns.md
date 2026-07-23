# Drop Target Registration Lifecycle — Blazor Patterns

## The Problem

In Blazor drag-and-drop systems, drop targets are registered via JS interop in `OnAfterRenderAsync(firstRender: true)`. Two common pitfalls:

1. **Coupling registration to content existence** — registering a region's drop target only when `Panels.Count > 0`, making empty regions invisible to drag operations.
2. **One-shot `firstRender` registration** — after a Blazor re-render replaces DOM elements, the JS `Map<HTMLElement, ...>` holds stale references, and `firstRender` is already `false` so no re-registration occurs.

## Root Cause Architecture Pattern

Both pitfalls share a root cause: **infrastructure properties (region droppability) are coupled to content state (panel presence).**

## Corrected Pattern

### Principle: Infrastructure Registration is Independent of Content State

A drop zone that represents a region/slot should always be registered, regardless of whether that slot currently has content:

```razor
@code {
    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        // Always register: the region exists whether or not it has panels
        if (firstRender)
        {
            await RegisterDropTarget(JS, _hostRef, "dock-region", RegionName);
            _lastRegisteredRegionName = RegionName;
        }
    }
}
```

### Principle: Re-register When Identity Changes

Track the identifier used for registration and re-register when it changes (not just on firstRender):

```razor
@code {
    private string? _lastRegisteredRegionName;

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        var regionChanged = !string.Equals(
            _lastRegisteredRegionName, RegionName, StringComparison.OrdinalIgnoreCase);

        if (firstRender || regionChanged)
        {
            await RegisterDropTarget(JS, _hostRef, "dock-region", RegionName);
            _lastRegisteredRegionName = RegionName;
        }
    }
}
```

### Drag Source: Track by Active Panel ID (String Comparison), Not Boolean Flag

For drag sources (panel headers), the active panel may change after moves/collapses. Using a boolean `_headerRegistered` flag is fragile because Blazor can reuse component instances across renders, preserving the `true` state from a previous cycle even for a new DOM element.

**Correct approach: track by string identity of the active panel.** Register every render if the active panel ID changes:

```razor
@code {
    private string? _lastHeaderPanelId;

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        var hasActivePanel = Panels.Count > 0;
        var currentPanelId = hasActivePanel
            ? (Panels.FirstOrDefault(p => p.IsActive) ?? Panels[0]).Id
            : null;

        var headerChanged = !string.Equals(_lastHeaderPanelId, currentPanelId,
            StringComparison.Ordinal);

        if (currentPanelId is not null && headerChanged && DragService is not null)
        {
            if (!_headerRef.Equals(default(ElementReference)))
            {
                await AttachDragHandlers(JS, _headerRef, DragType.Panel,
                    currentPanelId, DragService.CallbackReference);
                _lastHeaderPanelId = currentPanelId;
            }
        }
        else if (currentPanelId is null)
        {
            _lastHeaderPanelId = null;
        }
    }
}
```

**Why string comparison is better than a boolean flag:**
- A boolean `_headerRegistered = true` can persist across Blazor component reuse even when the component parameter tree changes.
- String comparison detects identity changes naturally — when the active panel moves in/out, the string value changes → `headerChanged = true` → re-registration fires.
- No manual "reset to false" logic is needed when content disappears.
- No coupling to `firstRender` — works correctly on every render cycle.

### Critical: Add @key in the Parent Template

Even with correct per-render comparison logic, Blazor can reuse a component instance across parameter changes while preserving its instance fields (including `_lastHeaderPanelId`). **Always add `@key` to the component in the parent template** to ensure fresh instances when the logical identity changes:

```razor
@* Parent AtlasLayout.razor *@
<div class="xd-left-dock">
    <DockPanel @key="@RegionNames.LeftDockUpper"
               RegionName="@RegionNames.LeftDockUpper" ... />
    <DockPanel @key="@RegionNames.LeftDockLower"
               RegionName="@RegionNames.LeftDockLower" ... />
</div>
```

The `@key` value should be the stable logical identity (like `RegionName`), not a volatile value (like panel count). This ensures:
- Blazor creates a new component instance when the region's panel content changes
- Instance fields (`_lastHeaderPanelId`, `_lastRegisteredRegionName`) start fresh
- The JS interop registration runs correctly on the new DOM elements

## Related SRS Requirements

| SRS § | Requirement | Implication for Drop Target |
|-------|-------------|----------------------------|
| §3.5 (intro) | "Dock Panel 的拖拽停靠**不区分方向**" | Panel drags to dock-region should show full-region highlight, not directional zones |
| REQ-F-069 AC1 | Move panel to *empty* region | Empty regions MUST be valid drop targets |
| REQ-F-069 AC5 | "该 Dock Region 应以高亮样式显示" | Region-highlight, not split-zone highlight |
| REQ-F-070 AC1 | "Dock Panel 内容渲染不受影响" | After move, panel content must survive re-render (no forced rebuild) |

## Visual Feedback by Drag Type

| Drag Type | Target Type | Direction Algorithm | Visual Feedback |
|-----------|-------------|-------------------|-----------------|
| panel | dock-region | Always `'center'` | Full region border highlight |
| tab | editor-view | 5-zone (outer 25%, center 50%) | Directional zone overlay |
