# Lib Dock Panel Move — Architecture Root Cause Example

## Context

Project: Lib (Blazor WASM dock layout library, .NET 6)
Three user-reported symptoms:
1. Left/Right Bottom Dock can't receive panel drops
2. Dock Panel shows direction zones (left/right/up/down) on hover — should be full-region highlight
3. After a panel is dropped into a region, it can't be dragged out again

## Root Cause Cluster

All three symptoms traced to ONE design flaw: **Drop target registration lifecycle was coupled to panel content state.**

### Trace per symptom

| Symptom | Code path | Mechanism |
|---|---|---|
| Bottom Dock can't receive drops | `DockPanel.razor:134-147` → `registerDropTarget` | Guard `Panels.Count > 0` meant empty regions never registered |
| Wrong direction zones | `index.ts:219-240` → `computeDirection()` | JS computed five-zone (left/right/up/down/center) for ALL target types, not distinguishing `dock-region` from `editor-view` |
| Can't drag out after first drop | `DockPanel.razor:134-147` + `index.ts:48-55` | `firstRender` guard never re-fires; new DOM element after re-render has no registration |

### SRS evidence

- **SRS §3.5** explicitly says "Dock Panel 的拖拽停靠**不区分方向**"
- **REQ-F-069 AC1** requires moving panels into *empty* regions
- **REQ-F-069 AC5** requires high-light indication on hover — not directional zones

### Fix principle

Region droppability is a Region attribute, not a Panel attribute. Always register a Region as a valid drop target regardless of its panel content count.

### Fix files

| File | Change | Rationale |
|---|---|---|
| `DockPanel.razor` | Register drop target unconditionally (not gated on `Panels.Count > 0`); re-register when `RegionName` changes (not just `firstRender`) | Empty regions must be valid drop targets (SRS §3.5) |
| `DockPanel.razor` | Track drag source by string comparison (`_lastHeaderPanelId`) instead of boolean `_headerRegistered` flag | Bool flags persist across Blazor component reuse; string comparison detects identity changes naturally |
| `LibLayout.razor` | Add `@key="@RegionNames.xxx"` to every `DockPanel` in the template | Prevents Blazor from reusing component instances across render cycles with stale instance fields |
| `index.ts` | Pass `dragType` to `computeDirection` and `updateIndicator`; for panel drags return `'center'` always, show full-region highlight only | Panel drags need directionless feedback (SRS §3.5); tab drags need 5-zone feedback (SRS §3.4.1) |

### Deep root cause (reproduced in round 2)

After the first fix pass, a second round of testing revealed: after moving Panel A → Region1, then Panel A → Region2, dragging Panel A again failed. Root cause: Blazor reused the `DockPanel` component instance for Region2, preserving the `_headerRegistered = true` field from a previous render cycle. Since `_headerRegistered` was already `true`, `OnAfterRenderAsync` never re-registered drag handlers on the new DOM element.

**Fix:** Replace boolean flag (`_headerRegistered`) with string comparison (`_lastHeaderPanelId` vs current active panel ID), and add `@key="@RegionName"` in the parent template to force fresh component instances when region identity changes.
