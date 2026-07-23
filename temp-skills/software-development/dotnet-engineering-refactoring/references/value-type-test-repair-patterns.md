# Value-Type Test Repair Patterns

When domain primitives (`TabId`, `EditorViewId`, `PanelId`) replace `string` IDs
in model and service signatures, every test that passes a bare string literal
breaks. This document catalogs the regex patterns and manual fixes needed.

## Regex Replacements (apply in this order)

All patterns below assume `python re.sub`. Run them as a script over `tests/`,
skipping `obj/` directories.

### 1. Constructor calls

| Before | After |
|--------|-------|
| `new EditorViewModel("id")` | `new EditorViewModel(new EditorViewId("id"))` |
| `new EditorViewModel("id", type)` | `new EditorViewModel(new EditorViewId("id"), type)` |
| `new TabModel("tid", "vid", ...)` | `new TabModel(new TabId("tid"), new EditorViewId("vid"), ...)` |
| `new OpenTabRequest("vid", ...)` | `new OpenTabRequest(new EditorViewId("vid"), ...)` |

```python
# EditorViewModel — two variants
(r'\bnew EditorViewModel\("([^"]*)"\)', r'new EditorViewModel(new EditorViewId("\1"))'),
(r'\bnew EditorViewModel\("([^"]*)", (EditorViewType\.\w+)\)', r'new EditorViewModel(new EditorViewId("\1"), \2)'),

# TabModel — both string and view.Id (already EditorViewId) variants
(r'\bnew TabModel\("([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)"\)', r'new TabModel(new TabId("\1"), new EditorViewId("\2"), "\3", "\4")'),
(r'\bnew TabModel\("([^"]*)", (view\.Id),\s*"([^"]*)", "([^"]*)"\)', r'new TabModel(new TabId("\1"), \2, "\3", "\4")'),

# OpenTabRequest
(r'\bnew OpenTabRequest\("([^"]*)", "([^"]*)", "([^"]*)"\)', r'new OpenTabRequest(new EditorViewId("\1"), "\2", "\3")'),
```

### 2. Method calls taking value types

| Before | After |
|--------|-------|
| `context.GetTab("id")` | `context.GetTab(new TabId("id"))` |
| `context.CloseTab("id")` | `context.CloseTab(new TabId("id"))` |
| `context.ActivateTab("id")` | `context.ActivateTab(new TabId("id"))` |
| `context.TogglePanel("id")` | `context.TogglePanel(new PanelId("id"))` |
| `context.ExpandPanel("id")` | `context.ExpandPanel(new PanelId("id"))` |
| `context.CollapsePanel("id")` | `context.CollapsePanel(new PanelId("id"))` |
| `context.MovePanel("id", region)` | `context.MovePanel(new PanelId("id"), region)` |
| `state.FindEditorView("id")` | `state.FindEditorView(new EditorViewId("id"))` |
| `state.FindTab("id")` | `state.FindTab(new TabId("id"))` |

```python
# LayoutContext methods
(r'\b(context)\.TogglePanel\("([^"]*)"\)', r'\1.TogglePanel(new PanelId("\2"))'),
(r'\b(context)\.ExpandPanel\("([^"]*)"\)', r'\1.ExpandPanel(new PanelId("\2"))'),
(r'\b(context)\.CollapsePanel\("([^"]*)"\)', r'\1.CollapsePanel(new PanelId("\2"))'),
(r'\b(context)\.MovePanel\("([^"]*)",\s*', r'\1.MovePanel(new PanelId("\2"), '),
(r'\b(context)\.GetTab\("([^"]*)"\)', r'\1.GetTab(new TabId("\2"))'),
(r'\b(context)\.CloseTab\("([^"]*)"\)', r'\1.CloseTab(new TabId("\2"))'),
(r'\b(context)\.ActivateTab\("([^"]*)"\)', r'\1.ActivateTab(new TabId("\2"))'),

# LayoutState queries (handle both 'state' and 'fresh' variable names)
(r'\b(state)\.FindEditorView\("([^"]*)"\)', r'\1.FindEditorView(new EditorViewId("\2"))'),
(r'\b(state)\.FindTab\("([^"]*)"\)', r'\1.FindTab(new TabId("\2"))'),
(r'\b(fresh)\.FindTab\("([^"]*)"\)', r'\1.FindTab(new TabId("\2"))'),
```

### 3. Property assignments

| Before | After |
|--------|-------|
| `TabId = "id"` | `TabId = new TabId("id")` |

```python
(r'\bTabId = "([^"]*)"', r'TabId = new TabId("\1")'),
```

### 4. Test fixture helpers

| Before | After |
|--------|-------|
| `TestFixture.CreateStateWithView("id")` | `TestFixture.CreateStateWithView(new EditorViewId("id"))` |

```python
(r'\bTestFixture\.CreateStateWithView\("([^"]*)"\)', r'TestFixture.CreateStateWithView(new EditorViewId("\2"))'),
```

### 5. Lambda / predicate comparisons

| Before | After |
|--------|-------|
| `t => t.Id == "id"` | `t => t.Id == new TabId("id")` |
| `t => t.ViewId == "id"` | `t => t.ViewId == new EditorViewId("id")` |

```python
(r'\.Id == "([^"]*)"', r'.Id == new TabId("\1")'),
(r'\.Id != "([^"]*)"', r'.Id != new TabId("\1")'),
(r'\.ViewId == "([^"]*)"', r'.ViewId == new EditorViewId("\1")'),
```

## Manual Fixes (regex cannot catch these)

After running the regex script, always `dotnet build` and grep for remaining
`error CS` entries. The remaining errors fall into these categories:

### 1. Assert.Equal with value typed comparisons

`Assert.Equal("string", view.ActiveTabId)` — xUnit's overload resolution fails
because `TabId?` doesn't match `string`. Fix:

```csharp
// Before (broken)
Assert.Equal("tab-c", view.ActiveTabId);

// After (fixed)
Assert.Equal(new TabId("tab-c"), view.ActiveTabId);
```

Same pattern for `EditorViewId`:
```csharp
Assert.Equal(new EditorViewId("target"), state.EditorViews[0].Id);
```

### 2. Variable type changes

When an event args type changed from `string` to value type, local variables
capturing those values need their types updated:

```csharp
// Before (broken — args.TabId is now TabId, not string)
string? closedId = null;
events.TabClosed += (_, args) => closedId = args.TabId;
Assert.Equal("tab-a", closedId);

// After (fixed)
TabId? closedId = null;
events.TabClosed += (_, args) => closedId = args.TabId;
Assert.Equal(new TabId("tab-a"), closedId);
```

### 3. DragService JS interop callbacks (do NOT change)

`drag.Callback.OnDragCommitted("tab-1", "target", "editor-view", "center")` —
these are correct as-is. The DragService receives strings from JavaScript interop
and internally converts to value types. The test invokes the callback directly,
so string arguments are appropriate.

## Verification Workflow

1. Run regex script over test files
2. `dotnet build tests/` → grep `error CS` for count and locations
3. Fix remaining errors with targeted `patch` calls
4. Rebuild → verify zero errors
5. `dotnet test` → verify all pass

Typical session: 173 initial errors → regex fixes ~150 → 20 remaining → manual
patches → 0 errors → 130/130 tests pass.
