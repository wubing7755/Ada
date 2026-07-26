# Atlas Value-Type Migration: Full Cascade Record (2026-07-22)

Session: refactor/base-class-optimization branch, Atlas Blazor Dock Layout project (net6.0).

## New Types Introduced

| Type | File | Constraint | JSON Converter |
|------|------|------------|---------------|
| `Ratio` | `Domain/Primitives/Ratio.cs` | [0, 1] — silently clamps | `RatioJsonConverter` (writes number) |
| `PanelId` | `Domain/Primitives/PanelId.cs` | Non-empty string | `PanelIdJsonConverter` (writes string) |
| `TabId` | `Domain/Primitives/TabId.cs` | Non-empty string | `TabIdJsonConverter` (writes string) |

All three are **structs with IEquatable<T>** (not `readonly record struct` — net6.0 compatibility requires manual `.Equals`/`.GetHashCode`/`operator ==`).

## Clamp vs Throw Decision

`Ratio` silently clamps instead of throwing on out-of-range input.
**Reason**: splitter arithmetic can produce intermediate values > 1.0 (e.g., `panelA.SizeRatio + panelB.SizeRatio - clamped` when both start at 1.0).
Tests also use `< (Ratio)3.0` as setup values. Silent clamping preserves the constraint
(`Ratio.Value` always in [0, 1]) without forcing callers to pre-validate every construction site.

If you need to validate at an API boundary, check `Ratio.Value` explicitly rather than relying on the constructor to throw.

## Cascade Order (Actual Execution)

### Phase 1a — Type Definitions
1. Create `Ratio.cs`, `PanelId.cs`, `TabId.cs` in `Domain/Primitives/`
2. **Pitfall**: initial `readonly record struct` approach caused CS0111 (duplicate ctor) on net6.0. Switched to plain `struct` with manual IEquatable.

### Phase 1b — Source Changes (in order)
1. `DockPanelModel.cs` — `string Id` → `PanelId`, `double` props → `Ratio`, remove range validation in setters
2. `LayoutQuery.cs` — `FindDockPanel(string)` → `FindDockPanel(PanelId)`
3. `LayoutState.cs` — delegate signature update
4. `SplitterService.cs` — `FindDockPanel(new PanelId(...))` + `(Ratio)` on all assignments
5. `LayoutDto.cs` — `model.Id.Value` for serialization, `new PanelId(...)` for deserialization, `(Ratio)` for all ratio assignments
6. `DragService.cs` — `FindDockPanel(new PanelId(...))`
7. `LayoutContext.cs` — all `FindDockPanel(new PanelId(panelId))` call sites
8. `MovePanelCommand.cs` — `FindDockPanel` + snapshot `Id` type change (delegated to subagent)

### Phase 1c — Razor Files
1. `ToolBar.razor` — `var panelId = panel.Id.Value` (3 locations via `replace_all`), `_entryPanelIds` assignment back to `panelId` (already string), `OnEntryMouseLeave` comparison `_hoveredPanel?.Id.Value != panelId`, `ExpandPanel(_hoveredPanel.Id.Value)`
2. `DockPanel.razor` — event handler params: `activePanel.Id.Value`
3. `AtlasLayout.razor` — `TogglePanel(panels[index].Id.Value)`

### Phase 1d — Demo & Tests
1. `src/Atlas.Demo/Pages/Dock.razor` — 4 `new DockPanelModel(new PanelId(...))` calls
2. **Bulk test fix** — Python script replaced all `DockPanelModel("id"` → `DockPanelModel(new PanelId("id"` and `SizeRatio = X.0` → `SizeRatio = (Ratio)X.0` across 7 test files
3. **Post-script cleanup** — `MovePanel` still accepts `string` (not `PanelId`), so `new PanelId(...)` incorrectly inserted by script was reverted manually
4. **Test assertions** — `Assert.Equal("p1", panel.Id)` → `Assert.Equal(new PanelId("p1"), panel.Id)` (overload resolution failed)
5. **Test value adjustment** — All `(Ratio)1.5`, `(Ratio)2.0`, `(Ratio)3.0` reduced to in-range values; assertion expectations updated accordingly

## Complete File Manifest

```
src/Atlas/Domain/Primitives/Ratio.cs              (new)
src/Atlas/Domain/Primitives/PanelId.cs             (new)
src/Atlas/Domain/Primitives/TabId.cs               (new)
src/Atlas/Domain/DockPanelModel.cs                 (modified)
src/Atlas/Domain/LayoutQuery.cs                    (modified)
src/Atlas/Domain/LayoutState.cs                    (modified)
src/Atlas/Services/UndoStack.cs                    (modified — Phase 2)
src/Atlas/Services/SplitterService.cs              (modified)
src/Atlas/Services/LayoutDto.cs                    (modified)
src/Atlas/Services/DragService.cs                  (modified)
src/Atlas/Services/LayoutContext.cs                (modified — Phase 1 + 2)
src/Atlas/Services/Commands/CommandBase.cs         (new — Phase 4)
src/Atlas/Services/Commands/CloseTabCommand.cs     (modified — Phase 4)
src/Atlas/Services/Commands/MoveTabCommand.cs      (modified — Phase 4)
src/Atlas/Services/Commands/OpenTabCommand.cs      (modified — Phase 4)
src/Atlas/Components/ToolBar.razor                 (modified)
src/Atlas/Components/DockPanel.razor               (modified)
src/Atlas/Components/AtlasLayout.razor             (modified)
src/Atlas.Demo/Pages/Dock.razor                    (modified)
tests/.../Domain/DomainModelTests.cs               (modified)
tests/.../Domain/LayoutStateTests.cs               (modified)
tests/.../Services/DragServiceTests.cs             (modified)
tests/.../Services/LayoutContextTests.cs           (modified)
tests/.../Services/LayoutSerializerTests.cs        (modified)
tests/.../Services/LayoutValidatorTests.cs         (modified)
tests/.../Services/SplitterServiceTests.cs         (modified)
```

## Error Counts
- Initial: 108 errors
- After source fix: 0 errors in `Atlas.csproj`
- After all fixes: 0 errors across all projects

## Key Error Patterns

```
error CS1503: string → PanelId
  → FindDockPanel(panelId) → FindDockPanel(new PanelId(panelId))

error CS0266: double → Ratio (implicit)
  → panel.SizeRatio = doubleVal → panel.SizeRatio = (Ratio)doubleVal

error CS0029: PanelId → string (implicit)
  → _entryPanelIds[i] = panel.Id → _entryPanelIds[i] = panel.Id.Value

error CS0173: ternary type inference with PanelId and null
  → var x = cond ? panel.Id : null → var x = cond ? panel.Id.Value : null

error CS1503: PanelId → string in razor lambdas
  → OnHeaderClick(panel.Id) → OnHeaderClick(panel.Id.Value)

error CS0019: PanelId? compared to string
  → hovered?.Id != panelId → hovered?.Id.Value != panelId
```

## delegate_task for Mechanical Fixes — CAUTION

Dispatched a subagent to fix 108 compile errors from the type migration. Result: after 10 minutes,
the subagent had fixed only ~20% of errors and was spending 90s per `dotnet build` cycle.
**Ineffective for high-volume mechanical fixes.** Bottleneck: each `dotnet build` takes ~90s
(Blazor WASM + Node.js build), and the subagent can only fix 1-2 files per build cycle.

✅ **Better approach**: Python script for bulk pattern replacement across all affected files
(executed in <1s), then manual fix-up for the remaining 5-10 edge cases.

delegate_task is best for **reasoning** tasks (code review, architecture analysis, research),
not for **mechanical** tasks (type conversion, find-replace, compile-error cleanup).
