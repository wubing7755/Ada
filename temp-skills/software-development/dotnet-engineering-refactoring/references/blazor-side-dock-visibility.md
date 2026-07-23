# Blazor side-dock visibility and empty-column collapse

Use this reference when a Blazor dock/layout component shows empty Left/Right Dock chrome after every panel in the side's Upper/Lower dock regions has been collapsed, hidden, or auto-hidden.

## Durable lesson

Do not let layout tracks be driven only by declared panel collections. For work-area layout, distinguish:

- **Declared panels / toolbar entries** — persistent navigation affordances; collapsed and auto-hidden panels may still need ToolBar entries.
- **Visible dock content columns** — space-reserving regions in the central grid; these should exist only when the side's Upper/Lower dock regions contain at least one expanded panel.

A side can have ToolBar entries but no content-column track.

## Atlas implementation pattern

1. Add a domain-level visibility helper rather than scattering Razor conditions:

```csharp
internal static class LayoutVisibility
{
    public static bool SideDockHasExpandedPanels(LayoutState state, RegionSide side)
    {
        if (state is null) throw new ArgumentNullException(nameof(state));

        return state.DockPanels.Any(panel =>
            IsSideDockRegion(panel.RegionName, side) &&
            panel.DisplayState == PanelDisplayState.Expanded);
    }
}
```

Key rule: only Left/Right **Upper** and **Lower** regions participate. BottomLeft/BottomRight belong to Bottom Dock and must not keep the upper work-area side column alive.

2. Make the grid-template dynamic:

```csharp
public string GetUpperWorkAreaColumnsStyle(bool showLeftDock, bool showRightDock)
{
    var tracks = new List<string>();
    if (showLeftDock)
    {
        tracks.Add(FormatPercent(_state.Ratios.LeftDockRatio));
        tracks.Add("4px");
    }

    tracks.Add("minmax(200px,1fr)");

    if (showRightDock)
    {
        tracks.Add("4px");
        tracks.Add(FormatPercent(_state.Ratios.RightDockRatio));
    }

    return $"grid-template-columns:{string.Join(" ", tracks)};";
}
```

3. In the Razor layout, conditionally render both the content column and its adjacent splitter:

```razor
<section class="xd-upper-work-area" style="@_style.GetUpperWorkAreaColumnsStyle(ShowLeftDock, ShowRightDock)">
    @if (ShowLeftDock)
    {
        <div class="xd-left-dock">...</div>
        <Splitter ... />
    }

    <EditorArea ... />

    @if (ShowRightDock)
    {
        <Splitter ... />
        <div class="xd-right-dock">...</div>
    }
</section>
```

4. Keep ToolBar rendering based on declared side panels. Do not remove ToolBar entries simply because content columns collapse; ToolBar entries are how users reopen collapsed panels or interact with auto-hide panels.

## Test shape

Add focused tests for both style generation and the domain predicate:

- `UpperWorkAreaColumnsStyle_CollapsesHiddenSideDockTracks`
  - both sides visible => five tracks: left, splitter, editor, splitter, right
  - left hidden => editor + right tracks only
  - right hidden => left tracks + editor only
  - both hidden => editor-only track
- `SideDockHasExpandedPanels_OnlyCountsUpperAndLowerExpandedPanels`
  - no panels => false
  - collapsed/auto-hidden panels => false
  - BottomLeft/BottomRight expanded panels => false for upper work-area side column
  - Upper/Lower expanded panel => true

## Browser smoke

For a manual/browser smoke on a demo page:

1. Collapse the last expanded panel in the left Upper/Lower side.
2. Assert `.xd-left-dock` count is `0`.
3. Collapse the last expanded panel in the right Upper/Lower side.
4. Assert `.xd-right-dock` count is `0`.
5. Assert the upper work-area grid has only the editor track when both sides are hidden, e.g. `grid-template-columns:minmax(200px,1fr)`.
6. Assert no content-host errors, e.g. `.xd-content-error` count is `0`.

## Pitfalls

- Do not count raw panel presence. A collapsed or auto-hidden panel should not reserve side content-column space.
- Do not include BottomLeft/BottomRight in the upper work-area side-column predicate.
- Do not hide/remove ToolBar entries when content columns collapse; that breaks reopening and auto-hide navigation semantics.
- When documenting this behavior, trace it to both folding/space release requirements and toolbar persistence requirements.
