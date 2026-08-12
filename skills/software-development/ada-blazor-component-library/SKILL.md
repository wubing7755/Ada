---
name: ada-blazor-component-library
description: "Use when building or maintaining Blazor component libraries — state-driven architecture patterns, namespace collision fixes, TypeScript interop with IJSObjectReference, xUnit integration testing, convention-based commits, and Razor Class Library extraction."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, component-library, razor, dotnet, nuget]
    related_skills: [ada-dotnet-blazor-library]
    trigger_keywords: [Blazor, Razor, Lib, dock layout, component library, .razor, DynamicComponent, WASM]
    usage_prompt: "Use when building or refactoring a Blazor component library — especially dock-panel / IDE-layout components, or any library with JS interop, xUnit tests, and eventual NuGet packaging."
---

# Blazor Component Library

Patterns for building maintainable Blazor (.NET 6+) component libraries with JS interop, tests, and a path to NuGet packaging.

## Overview

This skill captures battle-tested patterns from building a production Blazor dock-panel component library: state-driven architecture (domain model → context → commands → thin ViewModels), JS interop with `IJSObjectReference`, enum-to-interface migrations, collection encapsulation, and post-phase structured review. It documents deep pitfalls unique to Blazor's rendering model — `@ref` inside `RenderFragment` silently breaking `ElementReference`, `firstRender` boolean flags preventing JS re-registration, and drag-type inference fragility.

The skill emphasizes .NET 6 compatibility throughout (no `record struct`, no `@ref` lambdas) and provides patterns for enums-to-interfaces (Open/Closed Principle), `List<T>` to `IReadOnlyList<T>` encapsulation, and batch refactoring via `execute_code`.

## When to Use

Use when:
- Building or refactoring a Blazor component library with dock-panel, IDE-layout, or similar complex UI components
- Setting up JS interop with `IJSObjectReference` for a Blazor library
- Resolving namespace collision errors (`CS0234`) when Razor component folders match the root namespace
- Migrating from enum-based dispatch to interface strategy patterns
- Encapsulating mutable collections behind `IReadOnlyList<T>` / `IReadOnlyDictionary<K,V>` with named mutation methods
- Applying batch refactoring across 10+ files for an API migration
- Running a structured post-phase review before continuing to the next implementation phase

Do **not** use for: simple single-component development, server-side Blazor configuration, or non-Blazor .NET library design.

## Core Principles

1. **State-driven, not MVVM**: Use a pure domain model + per-instance state container + command/reducer-style operations. Components only render and forward events. ViewModels are thin adapters for render projection, not business logic owners.
2. **Future RCL extraction**: Organize code so `src/Lib/` (models, services, domain) is separate from `src/Components/Lib/` (Razor components). Pages are demo consumers only.
3. **.NET 6 compatibility**: Keep target framework at `net6.0` for legacy customers unless explicitly upgraded. Avoid `net7.0+` APIs.
4. **Result types over exceptions**: Return `DockResult` / `DockResult<T>` from all public APIs. Never throw for expected business failures.

## Architecture: State-driven Component Architecture

```text
Razor Components         → forward events, no domain logic
  ↓
LibLayoutContext     → per-instance state container + API surface
  ↓
Command/Reducer layer    → pure state transitions, testable
  ↓
Domain Model             → LayoutState, DockPanelModel, TabModel, etc.
```

Key rule: domain models must NOT depend on Razor, DOM, JSRuntime, or CSS.

## JS Interop: `IJSObjectReference` Pattern

### Avoid `eval` + `import()`

Using `js.InvokeVoidAsync("eval", $"...import('...').then(...)")` for ES module loading is brittle and hard to debug. Use the `IJSObjectReference` pattern instead.

### Initialize once at startup

```csharp
private static IJSObjectReference? _module;
public static async ValueTask InitializeAsync(IJSRuntime js)
{
    _module = await js.InvokeAsync<IJSObjectReference>("import", "./lib/lib.js");
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

Use `DotNetObjectReference<T>` with `[JSInvokable]` methods. Pass to JS via `DotNetObjectReference.Create(callback)` — the runtime handles reference counting automatically.

### Drag type: pass explicitly from JS to C#

**Wrong** — infer drag type on the C# side:
```csharp
_dragType = _context.State.FindTab(dragData) is not null ? DragType.Tab : DragType.Panel;
```

**Right** — include it as a parameter in the JS → C# callback:
```typescript
dotNet.invokeMethodAsync('OnDragStarted', dragData, dragType, clientX, clientY);
```

This eliminates brittle inference and makes data flow explicit.

## Magic Strings → LayoutChangeType Constants

All `NotifyLayoutChanged(string, string?)` calls should use a constants class, not raw strings:

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

Extract constants proactively — don't wait for event-mismatch bugs.

## Enum → Interface Strategy Pattern

When a domain concept (activation strategy, dedup mode, overflow mode) starts as an enum, it becomes an extension bottleneck: adding new behavior requires modifying every switch/if branch.

### Migration pattern

1. **Define the interface** in `Domain/` (stays dependency-free):
   ```csharp
   public interface IActivationStrategy
   {
       TabModel PickNext(EditorViewModel view, int closedIndex, IReadOnlyList<string> recentIds);
   }
   ```

2. **Implement concrete strategies** in `Domain/`:
   ```csharp
   public sealed class DefaultActivationStrategy : IActivationStrategy { ... }
   public sealed class RecentActivationStrategy : IActivationStrategy { ... }
   ```

3. **Replace the enum property** with the interface:
   ```csharp
   public IActivationStrategy ActivationStrategy { get; set; } = new DefaultActivationStrategy();
   ```

4. **Update tests** to use `new DefaultActivationStrategy()` instead of enum values.

5. **Delete the old enum** from `LayoutEnums.cs`.

This follows the Open/Closed Principle: new strategies can be added without modifying existing code.

## Collection Encapsulation: List → IReadOnlyList Pattern

When domain models expose mutable collections publicly, external code can bypass invariants.

### Migration pattern

1. **Add a private backing field** and expose read-only:
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

3. **For predicate-based removal**, add `RemoveXxxWhere(Predicate<T>)` passthrough.

4. **Batch-update all callers** — this is the bulk of the work. Use `execute_code` with regex rules for 10+ files (see `references/batch-refactoring.md`).

### Pitfall: `new Dictionary<K,V>(IReadOnlyDictionary)` does not compile

`IReadOnlyDictionary<K,V>` does NOT implement `IDictionary<K,V>`. Use `ToDictionary()`:
```csharp
// WRONG
new Dictionary<string, object?>(model.Parameters)
// RIGHT
model.Parameters.ToDictionary(kv => kv.Key, kv => kv.Value)
```

### Pitfall: object initializer order with cross-validated setters

When setters validate against each other (e.g. `MinSizeRatio <= MaxSizeRatio`), object-initializer assignment order is undefined. Provide an atomic setter:

```csharp
public void SetSizeConstraints(double min, double max)
{
    if (min > max) throw ...;
    _minSizeRatio = min;
    _maxSizeRatio = max;
}
```

### Query centralization

When the same query pattern appears in 3+ files, extract it to a single method on the model:
```csharp
public IReadOnlyList<DockPanelModel> FindDockPanelsInRegion(string regionName)
    => DockPanels.Where(p => string.Equals(p.RegionName, regionName, StringComparison.OrdinalIgnoreCase)).ToList();
```

## Commit Convention

Use Conventional Commits with per-module scopes:

```text
<type>(<scope>): <summary>
```

Preferred scopes: `model, domain, layout, content, tabs, views, toolbar, panel, splitter, drag, persist, interop, a11y, demo, docs, srs, build, test, ci`

One commit = one complete, buildable, verifiable feature slice. Do NOT mix formatting-only changes with behavior changes, or commit every tiny enum separately.

## Post-Phase Review

After each major implementation phase, run a structured review BEFORE starting the next:

1. **Build + test**: `dotnet build --no-restore && dotnet test --no-build`. Must pass.
2. **Re-read all changed files**: read every modified file in full.
3. **Analysis checklist**: dead code, scope creep, pre-existing issues (flag but don't fix), better design alternatives ("would Plan B be better?").
4. **Present summary**: table of changes per file, lines changed, verification status.
5. **User gates on "continue"**: do not proceed until user explicitly approves.

Generate a **code quality report** (save to `docs/code-quality-report.md`) covering architecture, class SRP, extensibility risks, readability, and test coverage. Address 🔴 items immediately, 🟡 in follow-up, 🟢 when convenient.

## Common Pitfalls

- **`@ref` inside `RenderFragment` silently breaks**: `@ref` only works in `.razor` templates, not inside `__builder` lambdas. Keep `@ref` inline; only extract display-only content to helper methods.
- **`firstRender` boolean flags preventing JS re-registration**: Blazor reuses component instances. Use string-identity comparison (`_lastHeaderPanelId`) instead of boolean flags, or add `@key` in the parent template.
- **`@ref` in `foreach` loop only captures the last element**: Use a pre-allocated `ElementReference[]` array with an index counter, not a `Dictionary` (which Razor cannot bind to).
- **Dedup check ordering in `OpenTab`**: Dedup must run before duplicate-ID check. When `DedupMode = ActivateExisting`, tests for `DuplicateTabId` must set `DedupMode = AllowDuplicates`. See `references/component-patterns.md`.
- **Capture index before removing from list**: In `CloseTab`, capture `closedIndex` before `Remove`, or `IndexOf` returns -1. See `references/component-patterns.md`.
- **Drag type inference on C# side is brittle**: Pass drag type explicitly from TypeScript. See JS Interop section above.
- **Object initializer order with cross-validated setters**: Use atomic setter methods after construction. See Collection Encapsulation section above.

## Verification Checklist

- [ ] `dotnet build --no-restore && dotnet test --no-build` passes with zero failures
- [ ] All `@ref` assignments are inline in `.razor` templates — no `@ref` inside extracted `RenderFragment` helper methods
- [ ] Components that re-register JS handlers have either `@key` in the parent or string-identity tracking (no boolean `_registered` flags)
- [ ] All `NotifyLayoutChanged` calls use `LayoutChangeType` constants, not raw strings
- [ ] Post-phase structured review completed: all changed files re-read, analysis checklist passed, summary presented to user
- [ ] Enums that have become extension bottlenecks are migrated to interface strategy patterns
- [ ] Mutable collections exposed publicly are encapsulated behind `IReadOnlyList<T>` / `IReadOnlyDictionary<K,V>` with named mutation methods

## Reference Files

Detailed patterns and setup guides are in `references/`:

| Reference | Content |
|---|---|
| `references/component-patterns.md` | Namespace collision fixes, close-tab activation, dedup ordering, OpenTab callback transfer, test fixture extraction, patch tool pitfall |
| `references/typescript-build-pipeline.md` | esbuild setup, MSBuild integration, .gitignore |
| `references/xunit-integration.md` | Test project structure, NuGet packages, naming conventions |
| `references/batch-refactoring.md` | `execute_code` + regex for 10+ file API migrations |
| `references/typescript-guards.md` | Window resize and visibility change drag cancellation |
| `references/phase1-plan-template.md` | Phase 1 task sequence and design constraints reference |
