# Invisible Drop Targets: JS Dynamic Creation (v3 Final)

Pattern for providing drag-and-drop targets for hidden regions in Blazor
without affecting CSS Grid / Flex layout. Used in Atlas for REQ-F-150 AC4
("隐藏的 Dock Region 不因悬浮层而展开") and REQ-F-069 AC6.

**Evolution:**
- **v1** (FAILED): C#-rendered invisible divs inside `@if` blocks — no DOM elements when container hidden
- **v2** (PARTIAL): JS dynamic creation with hardcoded 65%/35% vertical split — wrong positions when actual layout differs
- **v3** (FINAL): JS dynamic creation with three-tier rect resolution — always correctly positioned

## Problem

During drag operations, hidden layout regions need DOM elements to serve as
JS drop targets (`getBoundingClientRect` hit-testing). Rendering these in
Razor markup is fragile — Blazor conditional rendering (`@if`) removes the
entire DOM subtree, and hardcoded layout ratios produce incorrect positions.

## Solution: v3 — Three-Tier Rect Resolution

Create all 6 drop-target divs **from JavaScript** when drag starts, with
`position: fixed` and `document.createElement`. Resolve each region's
bounding rect using a three-tier fallback (best → worst):

| Tier | Source | When used |
|------|--------|-----------|
| 1 | `.xd-dock-panel-host[data-xd-region="..."]` | Region has expanded panels, visible in layout |
| 2 | `.xd-toolbar-group[data-xd-region="..."]` | Panels exist but region hidden (collapsed) |
| 3 | `.xd-toolbar-upper` / `.xd-toolbar-lower` split | No panels in region at all |

For Tiers 2-3, the X position uses ToolBar boundaries (always rendered)
and the Y position comes from the toolbar element's `getBoundingClientRect()`.
The drop zone is placed at the **dock region area** (between ToolBar and
Editor), not at the ToolBar itself.

```typescript
const _panelDropTargets: HTMLElement[] = [];

function createPanelDropTargets(): void {
  const body = document.querySelector('.xd-layout-body');
  const lt = document.querySelector('.xd-toolbar-left');
  const rt = document.querySelector('.xd-toolbar-right');
  if (!body || !lt || !rt) return;

  const ltRect = lt.getBoundingClientRect();
  const rtRect = rt.getBoundingClientRect();

  // Dock column boundaries
  const leftDockLeft = ltRect.right;
  const rightDockRight = rtRect.left;
  const defaultDockWidth = 240;
  const leftDockRight = Math.min(leftDockLeft + defaultDockWidth, rightDockRight * 0.4);
  const rightDockLeft = Math.max(rightDockRight - defaultDockWidth, rightDockRight * 0.6);

  const ltUpper = lt.querySelector('.xd-toolbar-upper');
  const ltLower = lt.querySelector('.xd-toolbar-lower');
  const rtUpper = rt.querySelector('.xd-toolbar-upper');
  const rtLower = rt.querySelector('.xd-toolbar-lower');

  const regionDefs = [
    { name:'LeftDockUpper',   side:'left',  isBottom:false, isUpper:true  },
    { name:'LeftDockLower',   side:'left',  isBottom:false, isUpper:false },
    { name:'RightDockUpper',  side:'right', isBottom:false, isUpper:true  },
    { name:'RightDockLower',  side:'right', isBottom:false, isUpper:false },
    { name:'BottomLeftDock',  side:'left',  isBottom:true,  isUpper:false },
    { name:'BottomRightDock', side:'right', isBottom:true,  isUpper:false },
  ];

  for (const def of regionDefs) {
    const dockLeft = def.side === 'left' ? leftDockLeft : rightDockLeft;
    const dockRight = def.side === 'left' ? leftDockRight : rightDockRight;
    const dockWidth = dockRight - dockLeft;

    // Tier 1: actual rendered dock region element
    const dockEl = document.querySelector(
      '.xd-dock-panel-host[data-xd-region="' + def.name + '"], ' +
      '.xd-dock-drop-scaffold[data-xd-region="' + def.name + '"]'
    ) as HTMLElement | null;

    let left: number, top: number, width: number, height: number;

    if (dockEl) {
      const r = dockEl.getBoundingClientRect();
      left = r.left; top = r.top; width = r.width; height = r.height;
    } else {
      // Tier 2: ToolBar group for this region
      const toolbar = def.side === 'left' ? lt : rt;
      const group = toolbar.querySelector(
        '.xd-toolbar-group[data-xd-region="' + def.name + '"], ' +
        '.xd-toolbar-group-bottom[data-xd-region="' + def.name + '"]'
      ) as HTMLElement | null;

      if (group) {
        const gr = group.getBoundingClientRect();
        top = gr.top; height = gr.height;
      } else {
        // Tier 3: proportional split from ToolBar section
        const section = def.isBottom
          ? (def.side === 'left' ? ltLower : rtLower)
          : (def.side === 'left' ? ltUpper : rtUpper);
        if (section) {
          const sr = section.getBoundingClientRect();
          const portionH = def.isBottom ? sr.height : sr.height / 2;
          const offsetY = def.isUpper ? 0 : (def.isBottom ? 0 : portionH);
          top = sr.top + offsetY;
          height = Math.max(portionH, 40);
        } else {
          continue;
        }
      }
      left = dockLeft;
      width = dockWidth;
    }

    const el = document.createElement('div');
    el.style.cssText =
      'position:fixed;left:' + left + 'px;top:' + top + 'px;' +
      'width:' + width + 'px;height:' + height + 'px;z-index:10000;';
    // CRITICAL: all three data attributes are required
    el.setAttribute('data-xd-dropzone', 'dock-region');
    el.setAttribute('data-xd-target-id', def.name);
    el.setAttribute('data-xd-region', def.name);  // ← ToolBar indicator side detection
    document.body.appendChild(el);
    dropTargets.set(el, { targetType: 'dock-region', targetData: def.name });
    _panelDropTargets.push(el);
  }
}
```

## Indicator Sizing: Full Rect, Not Fixed

The `updateIndicator` function for panel drags must use the **target's full
bounding rect**, not hardcoded 180×120 constants. Since the drop target is
already positioned to match the dock region's expected bounds, mirroring
its rect ensures the indicator covers the correct area:

```typescript
// v3 (correct): full rect mirroring
if (dragType === 'panel' && dropzone === 'dock-region') {
  indicator.style.left   = rect.left + 'px';
  indicator.style.top    = rect.top + 'px';
  indicator.style.width  = rect.width + 'px';
  indicator.style.height = rect.height + 'px';
}

// v1-2 (removed): fixed 180×120 centered — wrong size, wrong position
// const cx = rect.left + rect.width / 2;
// indicator.style.left = (cx - 180/2) + 'px';
```

## Why v2's Hardcoded Ratios (65%/35%) Failed

```typescript
// v2: hardcoded split — wrong when actual layout differs
const upperH = bodyRect.height * 0.65;  // ← assumption
const bottomH = bodyRect.height * 0.35;
```

On real machines: the Bottom Dock ratio may differ from defaults;
upper/lower splits depend on configurable ratios; with no bottom panels,
the bottom row has zero height. Hardcoding any ratio will be wrong.

The v3 approach avoids all ratio assumptions by anchoring to actual DOM
elements (ToolBar groups and sections) that faithfully reflect the layout.

## Why `data-xd-region` is Required

The toolbar indicator (`updateToolbarIndicator`) uses `getRegionSideFromElement()`:

```typescript
function getRegionSideFromElement(target: HTMLElement): 'left' | 'right' {
  const region = target.getAttribute('data-xd-region') ?? '';
  if (region.includes('left') || region.includes('Left')) return 'left';
  return 'right';  // ← default: ALL invisible divs → right side
}
```

Without `data-xd-region`, the default `'right'` fallback means all drop
targets are treated as right-side regions. The ToolBar indicator always
appears on the RT. All three attributes are required:

| Attribute | Purpose | Missing → symptom |
|-----------|---------|-------------------|
| `data-xd-dropzone` | `computeDropDirection` type check | Direction returned as `'none'`, drop rejected |
| `data-xd-target-id` | `OnDragCommitted` payload | C# receives empty target, drop rejected |
| `data-xd-region` | `getRegionSideFromElement` side detection | Defaults to `'right'`, ToolBar indicator wrong |

## Design Principle

When a DOM element must exist for JS interop **regardless of Blazor component visibility**:

1. ❌ Do NOT render it in Razor markup (Blazor `@if` will kill it)
2. ✅ Do create it from JS with `document.createElement`
3. ✅ Do anchor it to always-visible DOM elements for positioning
4. ✅ Do use `position: fixed` so it doesn't depend on parent container sizing
5. ✅ Do include all required `data-xd-*` attributes
6. ✅ Do use multi-tier rect resolution — don't hardcode layout ratios
