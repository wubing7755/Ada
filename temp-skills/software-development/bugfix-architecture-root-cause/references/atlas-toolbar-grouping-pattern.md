# Atlas ToolBar — Region Grouping and Drag Handler Registration

## SRS Requirements

**REQ-F-021 AC5**: ToolBar Entry 按所属 Dock Region 分组排列，组间以视觉分隔符分隔，分组顺序为 Upper Dock → Lower Dock → Bottom Dock，组内条目按添加顺序排列。

## Region-to-Side Mapping

LayoutState initializes regions with Side:

| Region | RegionSide | ToolBar |
|--------|-----------|---------|
| LeftDockUpper | Left | LT |
| LeftDockLower | Left | LT |
| BottomLeftDock | Left | LT |
| RightDockUpper | Right | RT |
| RightDockLower | Right | RT |
| BottomRightDock | Right | RT |

AtlasLayout filters: `panels.Where(p => state.FindRegion(p.RegionName)?.Side == RegionSide.Left)` for LT, same for Right/RT.

## Correct Grouping Implementation

```razor
@{
    var groups = Panels
        .GroupBy(p => p.RegionName)
        .OrderBy(g => RegionGroupOrder(g.Key))
        .ToList();
}
@for (var i = 0; i < groups.Count; i++)
{
    if (i > 0) { <hr class="xd-toolbar-divider" aria-hidden="true" /> }
    @foreach (var panel in groups[i]) // NO OrderBy — preserves add order
    {
        <button data-xd-panel-entry="@panel.Id" ...>
            @if (panel.Icon is not null) { <span class="...">@panel.Icon</span> }
            else { <span>@GetInitial(panel.Title)</span> }
        </button>
    }
}

@code {
    private static int RegionGroupOrder(string regionName) => regionName switch
    {
        var n when n.Contains("Upper", ...) => 0,
        var n when n.Contains("Lower", ...) => 1,
        var n when n.Contains("Bottom", ...) => 2,
        _ => 3
    };
}
```

**Key: NO `.OrderBy(p => p.Title)`** — SRS requires add order, not alphabetical.

## Drag Handler Registration on ToolBar Entries

The same `firstRender` + boolean flag problem affects ToolBar drag source registration. Fix:

1. Use `ElementReference[]` array to capture each entry button
2. Use Panel ID hash to detect changes
3. Re-register on hash mismatch regardless of `firstRender`

```razor
@code {
    private static readonly int MaxEntries = 32;
    private readonly ElementReference[] _entryRefs = new ElementReference[MaxEntries];
    private readonly string?[] _entryPanelIds = new string?[MaxEntries];
    private int _renderIndex;
    private string? _lastPanelIdHash;

    private static string PanelIdHash(IReadOnlyList<DockPanelModel> panels) =>
        string.Join(",", panels.Select(p => p.Id));

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        if (Context is null || Panels.Count == 0) return;

        var currentHash = PanelIdHash(Panels);
        if (!firstRender && string.Equals(_lastPanelIdHash, currentHash, StringComparison.Ordinal))
            return;

        _lastPanelIdHash = currentHash;

        for (var i = 0; i < Panels.Count && i < MaxEntries; i++)
        {
            var panelId = _entryPanelIds[i];
            if (panelId is null) continue;
            var elRef = _entryRefs[i];
            if (!elRef.Equals(default(ElementReference)))
            {
                await DragInterop.AttachDragHandlers(JS, elRef, DragType.Panel, panelId, dotNetRef);
            }
        }
    }
}
```

## Icon Display Behavior

Each ToolBar entry shows the panel's Icon (or first-letter initial if no icon). Entries are rendered inside group sections delimited by `<hr>` dividers, so the visual result is:

```
[🔍 Search]         ← LeftDockUpper group (top)
─────────────       ← divider
[💻 Terminal]       ← LeftDockLower group (middle)
[🐛 Problems]
─────────────       ← divider
[📁 Explorer]       ← BottomLeftDock group (bottom)
```

This matches the spatial Top→Middle→Bottom layout of the actual Dock Regions.

## CSS Pitfall: Invisible Divider

**Problem**: `<hr>` elements have no visible default in most browsers without explicit styling. The `xd-toolbar-divider` CSS class was defined in `ToolBar.razor` markup (`<hr class="xd-toolbar-divider">`) but had zero CSS rules in `atlas.css`. Result: no visible separator between region groups.

**Fix**: Add these CSS rules:
```css
.xd-toolbar-divider {
    width: 22px;
    height: 1px;
    margin: 4px 0;
    border: none;
    background: var(--xd-border);
    flex-shrink: 0;
}
```
- `border: none` is critical — browsers apply default `border-top` to `<hr>` even when styled with `background`. Without `border: none`, the divider shows a gray border-top but zero background height, making it look like a fuzzy line or nothing.
- `flex-shrink: 0` prevents flexbox from collapsing the divider when the ToolBar is full.
- This is a **CSS-only bug** that HTML code review cannot catch — always verify `hr` styles in CSS when using them as visual separators.
