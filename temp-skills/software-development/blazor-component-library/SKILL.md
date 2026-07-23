---
name: blazor-component-library
description: Patterns for building Blazor component libraries — state-driven architecture, namespace collision fixes, TS interop with IJSObjectReference, xUnit integration, convention-based commits, post-phase code review, and Razor Class Library extraction path.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    trigger_keywords: [Blazor, Razor, XDocker, dock layout, component library, .razor, DynamicComponent, WASM]
    usage_prompt: "Use when building or refactoring a Blazor component library — especially dock-panel / IDE-layout components, or any library with JS interop, xUnit tests, and eventual NuGet packaging."
---

# Blazor Component Library

Patterns for building maintainable Blazor (.NET 6+) component libraries with JS interop, tests, and a path to NuGet packaging.

## Core Principles

1. **State-driven, not MVVM**: Use a pure domain model + per-instance state container + command/reducer-style operations. Components only render and forward events. ViewModels are thin adapters for render projection, not business logic owners.
2. **Future RCL extraction**: Organize code so `src/XDocker/` (models, services, domain) is separate from `src/Components/XDocker/` (Razor components). Pages are demo consumers only.
3. **.NET 6 compatibility**: Keep target framework at `net6.0` for legacy customers unless explicitly upgraded by the user. Avoid `net7.0+` APIs.
4. **Result types over exceptions**: Return `DockResult` / `DockResult<T>` from all public APIs. Never throw for expected business failures (tab-not-found, duplicate-key, etc.).

## Architecture: State-driven Component Architecture

```text
Razor Components         → forward events, no domain logic
  ↓
XDockerLayoutContext     → per-instance state container + API surface
  ↓
Command/Reducer layer    → pure state transitions, testable
  ↓
Domain Model             → LayoutState, DockPanelModel, TabModel, etc.
```

Key rule: domain models must NOT depend on Razor, DOM, JSRuntime, or CSS.

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

In this project we used option (2): moved namespace to `XDocker.Components.Docking` via `_Imports.razor` with `@namespace XDocker.Components.Docking`, then removed redundant per-file `@using` directives.

## TypeScript Build Pipeline

### Convention

- **Source**: `ClientScripts/xdocker/index.ts` (TypeScript only)
- **Output**: `wwwroot/xdocker/xdocker.js` (generated, never committed)
- **Build tool**: `esbuild` via `npx` or `npm run build:js`

### package.json

```json
{
  "private": true,
  "scripts": {
    "build:js": "npx --yes esbuild@0.24.2 ClientScripts/xdocker/index.ts --bundle --format=esm --target=es2020 --outfile=wwwroot/xdocker/xdocker.js"
  },
  "devDependencies": {
    "esbuild": "0.24.2",
    "typescript": "^5.0.0"
  }
}
```

### MSBuild Integration

Add to `.csproj`:

```xml
<Target Name="BuildXDockerTypeScript" BeforeTargets="BeforeBuild">
  <Message Importance="high" Text="Building XDocker TypeScript interop..." />
  <Exec Command="npm run build:js" WorkingDirectory="$(MSBuildProjectDirectory)" />
</Target>
```

### .gitignore

```gitignore
node_modules/
src/wwwroot/xdocker/*.js
src/wwwroot/xdocker/*.js.map
```

## xUnit Test Integration

### Project structure

```text
tests/XDocker.Tests/XDocker.Tests.csproj   → net6.0, references src/XDocker.csproj
```

### Required packages

```xml
<PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.11.1" />
<PackageReference Include="xunit" Version="2.9.2" />
<PackageReference Include="xunit.runner.visualstudio" Version="2.8.2" />
<PackageReference Include="coverlet.collector" Version="6.0.2" />
```

### Test naming

Match source folder structure: `tests/XDocker.Tests/Services/XDockerLayoutValidatorTests.cs` tests `src/XDocker/Services/XDockerLayoutValidator.cs`.

## Commit Convention

Use Conventional Commits with per-module scopes:

```text
<type>(<scope>): <summary>
```

Preferred scopes for this project:

```text
model, domain, layout, content, tabs, views, toolbar, panel, splitter,
drag, persist, interop, a11y, demo, docs, srs, build, test, ci
```

### Commit granularity

One commit = one complete, buildable, verifiable feature slice. Do NOT commit:

- Every tiny enum/class separately
- An entire milestone in one oversized commit
- Formatting-only changes mixed with behavior changes

### Example commit history

```text
build(test): add xUnit and TypeScript build scaffolding
feat(model): add result and layout enum primitives
feat(model): add core layout state models
feat(layout): validate core dock hierarchy rules
feat(content): add content registry
feat(layout): add per-instance layout context
feat(layout): render static dock hierarchy
style(layout): add neutral dock hierarchy styling
feat(content): render registered tab content
feat(demo): use formal XDocker components on dock page
docs(requirements): complete phase 1 traceability matrix
```

## Patch Tool Pitfall

When using `patch` with Razor files, a future `patch` call that removes a `@using` line may accidentally consume the next line of markup if the old_string is ambiguous. Always verify the file content after patching Razor files. If corrupted, prefer `write_file` to restore the complete file.

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

## Post-Phase Review

After completing each major implementation phase, run a structured review BEFORE starting the next phase:

1. **Build + test**: `dotnet build --no-restore` then `dotnet test --no-build`. Must pass before review begins.
2. **Re-read all changed files**: read every modified file in full. Look for consistency across callers.
3. **Analysis checklist**:
   - Any dead code, unused imports, or drift between similar call sites?
   - Did we introduce a behavior change beyond the scope? (e.g., RecordRecent dedup)
   - Any pre-existing issues exposed by the change? Flag them but don't fix (scope creep).
   - Are there better designs than what we implemented? (Specifically ask "would Plan B be better here?")
4. **Present summary**: table of changes per file, lines changed, verification status.
5. **User gates on "continue"**: do not proceed to next phase until user explicitly approves.

The user explicitly requires this step. Skipping review causes compound technical debt.

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

## JS Interop: `IJSObjectReference` Pattern

### Pitfall: `eval` + `import()` is fragile

Avoid using `js.InvokeVoidAsync("eval", $"...import('...').then(...)")` for ES module loading. It's brittle, async-module-resolution-dependent, and hard to debug.

### Fix: `IJSObjectReference` pattern

```csharp
// Initialize once at startup (Program.cs)
private static IJSObjectReference? _module;
public static async ValueTask InitializeAsync(IJSRuntime js)
{
    _module = await js.InvokeAsync<IJSObjectReference>("import", "./xdocker/xdocker.js");
}

// Then call module methods directly
await _module!.InvokeVoidAsync("attachDragHandlers", element, dragType, dragData, callback);
```

### TypeScript side

Export plain functions (no default export needed):

```typescript
export function attachDragHandlers(
  element: HTMLElement,
  dragType: string,
  dragData: string,
  dotNetHelper: DotNet.DotNetObject
): void { ... }
```

### C# → JS callback pattern

Use `DotNetObjectReference<T>` with `[JSInvokable]` methods:

```csharp
public sealed class XDockerDragCallback
{
    [JSInvokable] public void OnDragStarted(string data, string type, double x, double y) { ... }
}
```

Pass to JS: `DotNetObjectReference.Create(callback)` — the .NET runtime handles reference counting automatically.

### Drag type: pass explicitly from JS to C#

**Wrong**: infer drag type on the C# side by checking if the ID belongs to a tab:
```csharp
_dragType = _context.State.FindTab(dragData) is not null ? DragType.Tab : DragType.Panel;
```

**Right**: include it as a parameter in the JS → C# callback:
```typescript
dotNet.invokeMethodAsync('OnDragStarted', dragData, dragType, clientX, clientY);
```

This eliminates the brittle inference and makes the data flow explicit.

Maintain a `docs/requirements-traceability.md` with columns:

```markdown
| Requirement | Priority | Title | Phase | Status | Implementation | Tests |
```

Status values: `Planned`, `In Progress`, `Implemented`, `Tested`, `Deferred`.

Update it in the same commit that changes implementation status — never batch traceability updates separately from the code change.

## Magic Strings → LayoutChangeType Constants

All `NotifyLayoutChanged(string, string?)` calls should use a constants class, not raw strings. Raw strings can't be checked by the compiler and cause silent event-mismatch bugs.

```csharp
public static class LayoutChangeType
{
    public const string TabOpened = "tab-opened";
    public const string TabMoved = "tab-moved";
    public const string ViewSplit = "view-split";
    public const string ViewRemoved = "view-removed";
    public const string ViewEmptied = "view-emptied";
    public const string PanelMoved = "panel-moved";
    public const string LayoutReset = "layout-reset";
}
```

Usage: `Events.NotifyLayoutChanged(LayoutChangeType.TabOpened, tab.Id);`

This pattern applies to any event system using string-based discrimination. Extract constants proactively — don't wait for a bug.

## Enum → Interface Strategy Pattern

When a domain concept (activation strategy, dedup mode, overflow mode) starts as an enum, it becomes an extension bottleneck: adding new behavior requires modifying the enum + every switch/if branch.

### Migration pattern

1. Define the interface in `Domain/` (so it stays dependency-free):
   ```csharp
   public interface IActivationStrategy
   {
       TabModel PickNext(EditorViewModel view, int closedIndex, IReadOnlyList<string> recentIds);
   }
   ```

2. Implement concrete strategies in `Domain/`:
   ```csharp
   public sealed class DefaultActivationStrategy : IActivationStrategy { ... }
   public sealed class RecentActivationStrategy : IActivationStrategy { ... }
   ```

3. Replace `LayoutState`'s enum property with the interface:
   ```csharp
   public IActivationStrategy ActivationStrategy { get; set; } = new DefaultActivationStrategy();
   ```

4. Update tests to use `new DefaultActivationStrategy()` / `new RecentActivationStrategy()` instead of enum values.

5. Delete the old enum from `LayoutEnums.cs`.

This follows the Open/Closed Principle: new strategies can be added without modifying existing code.

## Collection Encapsulation: List→IReadOnlyList Pattern

When domain models expose mutable collections publicly (`List<T>`, `Dictionary<K,V>`), external code can bypass the owning class's invariants.

### Migration pattern

1. **Add a private backing field** and expose `IReadOnlyList<T>` / `IReadOnlyDictionary<K,V>`:
   ```csharp
   private readonly List<TabModel> _tabs = new();
   public IReadOnlyList<TabModel> Tabs => _tabs;
   ```

2. **Add named mutation methods** on the owning class:
   ```csharp
   public void AddTab(TabModel tab) { _tabs.Add(tab); }
   public bool RemoveTab(TabModel tab) => _tabs.Remove(tab);
   public void ClearTabs() => _tabs.Clear();
   public int IndexOfTab(TabModel tab) => _tabs.IndexOf(tab);
   ```

3. **For predicate-based removal**, add `RemoveXxxWhere(Predicate<T>)` passthrough:
   ```csharp
   public int RemoveDockPanelsWhere(Predicate<DockPanelModel> match) => _dockPanels.RemoveAll(match);
   ```

4. **Batch-update all callers** — this is the bulk of the work. Use `execute_code` with regex rules (see Batch Refactoring pattern below).

### Pitfall: `new Dictionary<K,V>(IReadOnlyDictionary)` does not compile

`IReadOnlyDictionary<K,V>` does NOT implement `IDictionary<K,V>`, so the copy constructor fails. Use `ToDictionary()` instead:
```csharp
// WRONG
new Dictionary<string, object?>(model.Parameters)
// RIGHT
model.Parameters.ToDictionary(kv => kv.Key, kv => kv.Value)
```

### Pitfall: object initializer order with cross-validated setters

When setters validate against each other (e.g. `MinSizeRatio <= MaxSizeRatio`), object-initializer assignment order is undefined. If `Min=0.8` is set before `Max=0.95` (default), the intermediate `0.8 > 0.95` fails.

**Fix**: provide an atomic setter and call it after construction:
```csharp
public void SetSizeConstraints(double min, double max)
{
    if (min > max) throw ...;
    _minSizeRatio = min;
    _maxSizeRatio = max;
}
// Usage after object initializer:
var panel = new DockPanelModel(...) { Title = "X" };
panel.SetSizeConstraints(0.8, 0.9);
```

When the same `string.Equals` pattern appears in 3+ files:

```csharp
State.DockPanels.Where(p => string.Equals(p.RegionName, name, StringComparison.OrdinalIgnoreCase))
```

Extract it to a single helper on `LayoutState`:

```csharp
public IReadOnlyList<DockPanelModel> FindDockPanelsInRegion(string regionName)
{
    return DockPanels
        .Where(p => string.Equals(p.RegionName, regionName, StringComparison.OrdinalIgnoreCase))
        .ToList();
}
```

This pattern applies to any repeated query across services, validators, and components. Centralize queries on the model, not in callers.

## Batch Refactoring with execute_code

When an API migration requires updating the same pattern across 10+ files, `patch(mode='replace')` with `replace_all` does not work on directory targets (it needs a file path). Use `execute_code` with hermes_tools and regex:

```python
from hermes_tools import read_file, write_file
import re

files = ["file1.cs", "file2.cs", ...]
rules = [
    (r"(\w+)\.DockPanels\.Add\(",      r"\1.AddDockPanel("),
    (r"(\w+)\.EditorViews\.RemoveAll\(", r"\1.RemoveEditorViewsWhere("),
    # Order matters: longer/more-specific patterns first
]

for f in files:
    r = read_file(f, limit=2000)
    # Strip line numbers from read_file output format
    lines = [l.split("|", 1)[1] if "|" in l else l for l in r["content"].split("\n")]
    text = "\n".join(lines)
    for pat, rep in rules:
        text = re.sub(pat, rep, text)
    write_file(f, text)
```

**Caveat**: `read_file` returns line-numbered output (`N|content`). Strip the prefix before regex, or include `\d+\|` in patterns. The script above strips them.

**Verification**: After batch refactoring, always `dotnet build` to catch any missed call sites before running tests.

## TypeScript: Window Resize + Visibility Change Guards

Per SRS REQ-F-129 and REQ-F-137, drag operations must cancel when:
- The browser window is resized mid-drag
- The page becomes hidden (tab switch)

Add to `startDrag()`:
```typescript
window.addEventListener('resize', onWindowResize);
document.addEventListener('visibilitychange', onVisibilityChange);
```

Both handlers call `cleanupDrag()` + remove all listeners (pointer, key, resize, visibility). The same cleanup must be added to `onDragEnd()` and `onKeyDown()` (Escape).

Pitfall: forgetting to remove these listeners in normal drag-end paths causes stale handlers that fire on the next session.

## Post-Phase Code Quality Report

After each major phase, generate a structured review report before proceeding. The report should cover:

| Section | Content |
|---|---|
| Architecture | Layer diagram, dependency direction check |
| Class SRP | Table of every class: lines, responsibilities, SRP rating |
| Extensibility | Enums that should become interfaces, hardcoded strings |
| Readability | Naming conventions, XML doc coverage, method lengths |
| Test coverage | Counts by module, missing scenarios with SRS references |
| Overall score | Per-dimension rating with action items |

Save to `docs/code-quality-report.md`. Address 🔴 items immediately, 🟡 items in a follow-up commit, 🟢 items when convenient.
