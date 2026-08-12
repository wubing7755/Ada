# Lib Dock visibility + drop-scaffold pattern

Use this when a Dock layout bug involves empty/hidden Dock regions, Bottom Dock collapse, or dragging a panel back into a region that is normally hidden.

## Problem class

Symptoms usually appear together:

- Left/Right Dock columns collapse when their Upper/Lower regions are empty, but Bottom Dock still reserves an empty row.
- A side Dock column remains visible because one child region has panels while the other child region is empty, producing an empty `DockPanel` chrome.
- After hiding an empty child region, users can no longer drag a panel back into it because no DOM drop target exists.
- A user expects a hidden lower/upper/bottom child region to temporarily reappear as a drop target during a panel drag.

## Core design rule

Separate these two concerns:

1. **Normal space occupancy** — whether a Dock Region reserves layout space.
2. **Droppability** — whether a logical Dock Region can receive a dragged Dock Panel.

A logical Dock Region still exists even when it occupies no normal layout space.

## Normal-mode visibility

In normal render mode, a Dock Region should occupy content-area space only when it contains at least one `PanelDisplayState.Expanded` panel.

Collapsed and AutoHidden panels stay reachable through ToolBar entries, but do not reserve content-area space.

Suggested predicates:

```csharp
HasExpandedPanels(regionName)
SideDockHasExpandedPanels(side)
BottomDockHasExpandedPanels()
```

Then derive structural visibility:

```text
ShowLeftUpper = HasExpandedPanels(LeftDockUpper)
ShowLeftLower = HasExpandedPanels(LeftDockLower)
ShowLeftColumn = ShowLeftUpper || ShowLeftLower
ShowLeftInnerSplitter = ShowLeftUpper && ShowLeftLower

ShowBottomLeft = HasExpandedPanels(BottomLeftDock)
ShowBottomRight = HasExpandedPanels(BottomRightDock)
ShowBottomRow = ShowBottomLeft || ShowBottomRight
ShowBottomInnerSplitter = ShowBottomLeft && ShowBottomRight
```

Apply the same pattern to Right Dock.

## Panel-drag mode

During a Dock Panel drag, hidden logical Dock Regions must be exposed as **drop scaffolds** so the user can drag back into them.

Do not render them as normal empty panels. Render a lightweight placeholder/highlight target such as:

```text
Drop to Left Lower
Drop to Bottom Left
```

The scaffold should register as a `dock-region` drop target and carry the real `RegionName`.

## Architecture implication

Do not let `DockPanel.razor` own both content rendering and region droppability. That couples visibility to drop-target availability.

Prefer a deeper module such as:

```text
DockVisibilityPlan.Compute(LayoutState state, DockRenderMode mode)
DockRenderMode.Normal
DockRenderMode.PanelDrag
```

and/or a host component such as:

```razor
<DockRegionHost RegionName="..."
                Visible="..."
                Scaffold="..."
                Panels="..." />
```

The host decides whether to render a normal `DockPanel`, a drop scaffold, or nothing.

## Drag-state requirement

For scaffold mode, the layout must know when a panel drag starts/ends. The drag service should expose enough state or events for render planning, for example:

```csharp
bool IsPanelDragging { get; }
LayoutChangeType.DragStarted
LayoutChangeType.DragEnded
```

Notify the layout on drag start, commit, and cancel so hidden drop scaffolds appear/disappear predictably.

## SRS coverage checklist

When changing this area, map and verify at least:

| Requirement | Why it matters |
|---|---|
| REQ-F-014 | Collapsed/hidden Dock space is released to adjacent visible regions / Editor Area. |
| REQ-F-017 | AutoHidden panels do not reserve content-area space, but ToolBar entries remain. |
| REQ-F-018 | Cancel Auto-hide / expand returns the panel to normal layout occupancy. |
| REQ-F-022 | ToolBar toggles reopen and activate panels without losing entries. |
| REQ-F-069 | Panels can move into all six Dock Regions, including empty/hidden ones. |
| REQ-F-070 | Panel content/state survives moves. |
| REQ-F-071 | Fixed regions remain invalid panel drop targets. |
| REQ-F-149 | ToolBar upper/lower/bottom grouping remains synchronized. |

## Test checklist

- Normal mode hides empty child regions and their internal splitters.
- Normal mode hides Bottom Dock row when BottomLeft and BottomRight have no expanded panels.
- Normal mode shows a single child region full-size when its sibling is hidden.
- Panel drag mode exposes hidden child regions as drop scaffolds, not empty panels.
- Dropping onto a hidden scaffold moves the panel to that region and expands it.
- Moving a panel out of a region hides that region if no expanded panels remain.
- Moving into a region with an active panel expands the moved panel and collapses/deactivates the previous active panel per SRS.
