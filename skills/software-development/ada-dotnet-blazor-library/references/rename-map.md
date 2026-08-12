# Lib Project: Public API Type Rename Map

Concrete before/after mapping from a real project-name → Lib rename, plus the
Model-suffix disambiguation pass. Reference when doing similar namespace-level
renames in Blazor libraries.

## First Pass: 旧项目名 → Lib (all types)

### Domain Models

| Before | After |
|--------|-------|
| `LayoutState` | `LibLayoutState` |
| `DockPanelModel` | `LibDockPanel` |
| `EditorViewModel` | `LibEditorView` |
| `TabModel` | `LibTab` |
| `RegionModel` | `LibRegion` |
| `RegionNames` | `LibRegionNames` |

### Enums

| Before | After |
|--------|-------|
| `RegionKind` | `LibRegionKind` |
| `RegionSide` | `LibRegionSide` |
| `DockPanelType` | `LibDockPanelType` |
| `EditorViewType` | `LibEditorViewType` |
| `TabOverflowMode` | `LibTabOverflowMode` |
| `DedupMode` | `LibDedupMode` |
| `DragType` | `LibDragType` |

### EventArgs

| Before | After |
|--------|-------|
| `LayoutChangedEventArgs` | `LibLayoutChangedEventArgs` |
| `TabActivatedEventArgs` | `LibTabActivatedEventArgs` |
| `TabClosedEventArgs` | `LibTabClosedEventArgs` |

### Results

| Before | After |
|--------|-------|
| `DockResult` / `DockResult<T>` | `LibResult` / `LibResult<T>` |
| `DockErrorCode` | `LibErrorCode` |

### Requests / Strategies / Other

| Before | After |
|--------|-------|
| `OpenTabRequest` | `LibOpenTabRequest` |
| `OpenTabResult` | `LibOpenTabResult` |
| `IActivationStrategy` | `ILibActivationStrategy` |
| `DefaultActivationStrategy` | `LibDefaultActivationStrategy` |
| `RecentActivationStrategy` | `LibRecentActivationStrategy` |
| `ImportResult` | `LibImportResult` |
| `LayoutChangeType` | `LibLayoutChangeType` |

## Second Pass: Model-suffix disambiguation

After first pass, domain models clashed with Razor component names:

| After 1st pass | After 2nd pass | Reason |
|---------------|----------------|--------|
| `LibDockPanel` | `LibDockPanelModel` | Clashed with `<LibDockPanel>` component |
| `LibEditorView` | `LibEditorViewModel` | Clashed with `<LibEditorView>` component |
| `LibTab` | `LibTabModel` | Clashed with `<LibTabBar>`, `<LibTabContent>` |
| `LibRegion` | `LibRegionModel` | Clashed with `<LibRegion>` component |

## File Renames (domain files only)

| Before | After |
|--------|-------|
| `Domain/DockPanelModel.cs` | `Domain/LibDockPanelModel.cs` |
| `Domain/EditorViewModel.cs` | `Domain/LibEditorViewModel.cs` |
| `Domain/TabModel.cs` | `Domain/LibTabModel.cs` |
| `Domain/RegionModel.cs` | `Domain/LibRegionModel.cs` |
| `Results/DockResult.cs` | `Results/LibResult.cs` |
| `Results/DockErrorCode.cs` | `Results/LibErrorCode.cs` |

## Component Tag Fix Regex

After the Model-suffix pass, component tags in `.razor` files like
`<LibDockPanelModel ...>` needed reverting to `<LibDockPanel ...>` WITHOUT
touching generic type parameters like `List<LibDockPanelModel>`.

```python
import re

tag_fixes = {
    "LibDockPanelModel": "LibDockPanel",
    "LibEditorViewModel": "LibEditorView",
    "LibRegionModel": "LibRegion",
}

for old, new in tag_fixes.items():
    content = re.sub(
        r'(^|\s|=|\")<' + re.escape(old) + r'(\s|>|/)',
        r'\1<' + new + r'\2',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r'</' + re.escape(old) + r'>',
        r'</' + new + r'>',
        content
    )
```

## Final Verification

```bash
# No residual Lib
grep -r "Lib\|lib" src tests docs Lib.slnx .gitignore --exclude-dir=bin --exclude-dir=obj
# Should return nothing

# Build
dotnet build Lib.slnx
# Should produce Lib.dll, Lib.Demo.dll, Lib.Tests.dll

# Test
dotnet test Lib.slnx
# All 80 tests pass
```
