# Component Patterns

Detailed patterns for common Blazor component library challenges: namespace collisions, tab lifecycle, and test fixture extraction.

## Namespace Collision: Razor Components in Root-Namespace Projects

### Pitfall

When component files live under `Components/XDocker/` and the project root namespace is `XDocker`, Razor's code generation resolves `@using XDocker.Domain` to the **current nested namespace** (`XDocker.Components.XDocker.Domain`) instead of the global one.

This produces cascading `CS0234: 命名空间 'XDocker.Components.XDocker' 中不存在类型或命名空间名 'Domain'` errors.

### Fix

Three options, in order of preference:

1. **Use `global::` prefix** (best for existing projects):
   ```razor
   @using global::XDocker.Domain
   @using global::XDocker.Services
   ```

2. **Rename the component folder** to avoid the collision:
   ```text
   Components/Docking/  → namespace XDocker.Components.Docking
   ```

3. **Move domain code to a separate project** (best for NuGet packaging).

In the XDocker project we used option (2): moved namespace to `XDocker.Components.Docking` via `_Imports.razor` with `@namespace XDocker.Components.Docking`, then removed redundant per-file `@using` directives.

## Close-Tab Activation: Capture Index Before Removal

### Pitfall

When implementing `CloseTab` with a "right-first, then left" activation strategy, you must capture the closed tab's index **before** removing it from the list:

```csharp
// WRONG — IndexOf returns -1 after removal
view.Tabs.Remove(tab);
var idx = view.Tabs.IndexOf(tab); // -1!
```

```csharp
// RIGHT — capture index first
var closedIndex = view.Tabs.IndexOf(tab);
view.Tabs.Remove(tab);
// Now use closedIndex to pick the next tab
if (closedIndex < view.Tabs.Count) return view.Tabs[closedIndex];   // right neighbor
if (closedIndex > 0) return view.Tabs[closedIndex - 1];              // left neighbor
```

This caused 7 test failures before the fix was identified.

## Dedup vs Duplicate-ID Ordering in OpenTab

In `OpenTab`, the dedup check MUST run before the duplicate tab ID check, per SRS REQ-F-046. When `DedupMode = ActivateExisting` and a matching dedup key exists, return the existing tab's activation result WITHOUT checking for duplicate TabId.

This means tests for `DuplicateTabId` rejection must either:
- Set `DedupMode = AllowDuplicates`, or
- Use different content keys between the two tabs

Otherwise the dedup check silently activates the existing tab and the test's `Assert.False()` fails.

## OpenTab: Transfer Request Callbacks to Model

### Pitfall

When `OpenTabRequest` carries an optional callback (e.g. `BeforeCloseCallback`), it must be explicitly assigned to the `TabModel` during construction. Adding a field to the request without wiring it in `OpenTab` silently drops the configuration:

```csharp
// WRONG — callback is silently lost
var tab = new TabModel(tabId, view.Id, request.ContentKey, request.Title)
{
    IsClosable = request.IsClosable,
    IsPinned = request.IsPinned
};

// RIGHT — every request field propagated
var tab = new TabModel(tabId, view.Id, request.ContentKey, request.Title)
{
    IsClosable = request.IsClosable,
    IsPinned = request.IsPinned,
    BeforeCloseCallback = request.BeforeCloseCallback
};
```

Found during Phase 1+2 review pass. Tests passed but REQ-F-041 was silently broken.
Tip: grep for `request\.` in `OpenTab` and ensure every non-null field is assigned.

## Test Fixture Extraction

When `CreateStateWithView` (or similar setup) appears in 3+ test files, extract to a shared helper:

```csharp
namespace XDocker.Tests;
internal static class TestFixture
{
    public static LayoutState CreateStateWithView(string viewId) { ... }
    public static LayoutState CreateStateWithViews(params string[] viewIds) { ... }
}
```

Then replace all private copies with `TestFixture.CreateStateWithView(...)`. This prevents test-setup drift where different test files initialize models with slightly different defaults.

## Patch Tool Pitfall

When using `patch` with Razor files, a future `patch` call that removes a `@using` line may accidentally consume the next line of markup if the old_string is ambiguous. Always verify the file content after patching Razor files. If corrupted, prefer `write_file` to restore the complete file.
