# Lib Dedup Audit — Real-World Example

Context: Lib is a Blazor WASM docking layout component library (~42 .cs files).
Audit target: uncommitted changes adding auto-hide flyout support to ToolBar and DockPanel.

## Finding 1: Delay/Debounce Pattern Duplication

**File:** `src/Lib/Components/ToolBar.razor:145–163` — `StartFlyoutHideDelay()`
**Existing:** `src/Lib/Services/PersistenceService.cs:110–136` — `DebouncedSave()`

Identical CancellationTokenSource + Task.Delay + try/catch OperationCanceledException pattern.
Only differences: delay duration (300ms vs 500ms) and the action taken after the delay.

```csharp
// Both follow this exact template:
_cts?.Cancel();
_cts = new CancellationTokenSource();
var token = _cts.Token;
try {
    await Task.Delay(N, token);
    if (!token.IsCancellationRequested) { /* action */ }
}
catch (OperationCanceledException) { }
```

**Suggestion:** Extract `AsyncDebounce` helper. Both locations benefit.

---

## Finding 2: Debug Logging Duplication (3rd copy)

**File:** `src/Lib/Services/LayoutContext.cs:580–583` — `TraceMoveFailure()`
**Existing:**
- `DragService.cs:214` — `NotifyDragFailed` → `Debug.WriteLine($"[Lib] Drag failed: {reason}")`
- `PersistenceService.cs:125, 134` — manual `Debug.WriteLine($"[Lib] Auto-save ...")`

All four locations hardcode `System.Diagnostics.Debug.WriteLine` with `[Lib]` prefix.
The new `TraceMoveFailure` generalises the format but is the third parallel implementation.

**Suggestion:** Create `internal static class Diagnostics { static void TraceFailure(string context, string reason); }`.

---

## Finding 3: ~~DockPanel.OnAutoHideClick Bypasses LayoutContext~~ ✅ RESOLVED

**File:** `src/Lib/Components/DockPanel.razor:109–121`
**Status:** Fixed in 2026-07-20 diff. `OnAutoHideClick` now calls `Context.ExpandPanel(panelId)` / `Context.EnableAutoHide(panelId)` instead of model methods directly. Lock + event dispatch now fires correctly.

---

## Finding 4: Component LINQ vs State.FindDockPanel

**File:** `ToolBar.razor:117`, `DockPanel.razor:112`
**Existing:** `LayoutState.FindDockPanel(string panelId)` → `LayoutQuery.FindDockPanel()`

Both use `Panels.FirstOrDefault(p => p.Id == panelId)` when `Context?.State.FindDockPanel(panelId)` exists.

---

## Finding 5: CollapsePanel AutoHidden Guard Duplicates Model Constraint

**File:** `LayoutContext.cs:410–413`
**Model constraint:** `DockPanelModel.Collapse()` throws `InvalidOperationException` on AutoHidden

`CollapsePanel` guards against this at the service layer, making the model's exception unreachable.
Defensive but noted as dual responsibility.

---

## Finding 7: Auto-Hide Button Markup Duplication

**File:** `ToolBar.razor:57–62` (flyout header pin button)
**Existing:** `DockPanel.razor:45–52` (panel header auto-hide button)

Both render identical HTML: same CSS classes (`xd-dock-panel-autohide-btn`, `xd-autohide-active`),
same aria-labels ("Exit auto-hide"), same unicode emoji (📌). Only the `@onclick` target differs.

**Suggestion:** Extract a tiny `AutoHidePinButton.razor` sub-component accepting `OnClick` callback + `IsActive` bool.

---

## Finding 8: "Preset name is required." String 3× in Same File

**File:** `PersistenceService.cs:160, 168, 176` — `SavePresetAsync`, `LoadPresetAsync`, `DeletePresetAsync`

Same `string.IsNullOrWhiteSpace(presetName)` guard → same `DockErrorCode.InvalidLayoutData` → same message.

**Suggestion:** `private const string PresetNameRequiredMessage = "Preset name is required.";`

---

## Finding 9: Debug.WriteLine Format Inconsistency

**File:** `PersistenceService.cs:134, 143`
**Existing:** `LayoutContext.cs:564`, `DragService.cs:214`

PersistenceService uses inconsistent prefixes (`"Auto-save failed"` / `"Auto-save error"`)
while the rest of the codebase follows `"{Operation} failed: {reason}"`. All use `[Lib]` prefix.

**Suggestion:** Standardize on one format. `TraceMoveFailure` in LayoutContext already provides the template.

---

## Finding 10: FakeJsRuntime Test Double Lives Inline

**File:** `tests/Lib.Tests/Services/PersistenceServiceTests.cs:292–329`
**Existing:** `tests/Lib.Tests/TestFixture.cs` — shared test helpers, but no JS mock

`FakeJsRuntime` + `FakeJsVoidResult` + `FakeJsResult<T>` are only used in one test file today.
If future tests need JS mocking (drag interop, layout persistence), this should be promoted to test infrastructure.
