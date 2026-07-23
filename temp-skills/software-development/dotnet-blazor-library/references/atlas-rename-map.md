# Atlas Project: Public API Type Rename Map

Concrete before/after mapping from the XDocker → Atlas rename, plus the
Model-suffix disambiguation pass. Reference when doing similar namespace-level
renames in Blazor libraries.

## First Pass: XDocker → Atlas (all types)

### Domain Models

| Before | After |
|--------|-------|
| `LayoutState` | `AtlasLayoutState` |
| `DockPanelModel` | `AtlasDockPanel` |
| `EditorViewModel` | `AtlasEditorView` |
| `TabModel` | `AtlasTab` |
| `RegionModel` | `AtlasRegion` |
| `RegionNames` | `AtlasRegionNames` |

### Enums

| Before | After |
|--------|-------|
| `RegionKind` | `AtlasRegionKind` |
| `RegionSide` | `AtlasRegionSide` |
| `DockPanelType` | `AtlasDockPanelType` |
| `EditorViewType` | `AtlasEditorViewType` |
| `TabOverflowMode` | `AtlasTabOverflowMode` |
| `DedupMode` | `AtlasDedupMode` |
| `DragType` | `AtlasDragType` |

### EventArgs

| Before | After |
|--------|-------|
| `LayoutChangedEventArgs` | `AtlasLayoutChangedEventArgs` |
| `TabActivatedEventArgs` | `AtlasTabActivatedEventArgs` |
| `TabClosedEventArgs` | `AtlasTabClosedEventArgs` |

### Results

| Before | After |
|--------|-------|
| `DockResult` / `DockResult<T>` | `AtlasResult` / `AtlasResult<T>` |
| `DockErrorCode` | `AtlasErrorCode` |

### Requests / Strategies / Other

| Before | After |
|--------|-------|
| `OpenTabRequest` | `AtlasOpenTabRequest` |
| `OpenTabResult` | `AtlasOpenTabResult` |
| `IActivationStrategy` | `IAtlasActivationStrategy` |
| `DefaultActivationStrategy` | `AtlasDefaultActivationStrategy` |
| `RecentActivationStrategy` | `AtlasRecentActivationStrategy` |
| `ImportResult` | `AtlasImportResult` |
| `LayoutChangeType` | `AtlasLayoutChangeType` |

## Second Pass: Model-suffix disambiguation

After first pass, domain models clashed with Razor component names:

| After 1st pass | After 2nd pass | Reason |
|---------------|----------------|--------|
| `AtlasDockPanel` | `AtlasDockPanelModel` | Clashed with `<AtlasDockPanel>` component |
| `AtlasEditorView` | `AtlasEditorViewModel` | Clashed with `<AtlasEditorView>` component |
| `AtlasTab` | `AtlasTabModel` | Clashed with `<AtlasTabBar>`, `<AtlasTabContent>` |
| `AtlasRegion` | `AtlasRegionModel` | Clashed with `<AtlasRegion>` component |

## File Renames (domain files only)

| Before | After |
|--------|-------|
| `Domain/DockPanelModel.cs` | `Domain/AtlasDockPanelModel.cs` |
| `Domain/EditorViewModel.cs` | `Domain/AtlasEditorViewModel.cs` |
| `Domain/TabModel.cs` | `Domain/AtlasTabModel.cs` |
| `Domain/RegionModel.cs` | `Domain/AtlasRegionModel.cs` |
| `Results/DockResult.cs` | `Results/AtlasResult.cs` |
| `Results/DockErrorCode.cs` | `Results/AtlasErrorCode.cs` |

## Component Tag Fix Regex

After the Model-suffix pass, component tags in `.razor` files like
`<AtlasDockPanelModel ...>` needed reverting to `<AtlasDockPanel ...>` WITHOUT
touching generic type parameters like `List<AtlasDockPanelModel>`.

```python
import re

tag_fixes = {
    "AtlasDockPanelModel": "AtlasDockPanel",
    "AtlasEditorViewModel": "AtlasEditorView",
    "AtlasRegionModel": "AtlasRegion",
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
# No residual XDocker
grep -r "XDocker\|xdocker" src tests docs Atlas.slnx .gitignore --exclude-dir=bin --exclude-dir=obj
# Should return nothing

# Build
dotnet build Atlas.slnx
# Should produce Atlas.dll, Atlas.Demo.dll, Atlas.Tests.dll

# Test
dotnet test Atlas.slnx
# All 80 tests pass
```
