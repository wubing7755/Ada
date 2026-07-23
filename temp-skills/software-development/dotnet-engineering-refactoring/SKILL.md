---
name: dotnet-engineering-refactoring
description: Engineering-grade .NET refactoring — domain primitives, orchestrator extraction, command base classes, API naming, Blazor component patterns. Use when upgrading codebase quality beyond superficial cleanup.
version: 1.2.0
author: Hermes Agent
metadata:
  hermes:
    tags: [dotnet, refactoring, engineering, csharp, blazor, patterns]
    related_skills: [code-quality-analysis, systematic-refactoring, requesting-code-review, refactoring-lifecycle]
---

# .NET Engineering-Grade Refactoring

Guide for elevating a .NET codebase from "works" to "human-maintainable engineering
quality" — the level where a new developer can read, extend, and trust the code.

## Trigger

- User asks for "工程级" (engineering-grade) refactoring
- User rejects superficial changes (e.g. just extracting a validation helper)
- User says "不要嫌麻烦，要改就重构地改" (don't avoid work, refactor deeply)
- User wants the project ready for human successors to extend

**Not for:** simple bug fixes, single-file cleanup, pre-commit formatting.

## Guiding Principle

**Refactor to the type system, not to helper methods.** When the user demands
"微软那种工程级的代码写法", they mean:

- Constraints live in types, not in setter validation blocks
- Orchestrator classes delegate implementation to focused helpers
- API names reveal intent, not implementation details
- Every pattern is consistent across the project

## Core Patterns

### 1. Domain Primitive Value Types

Replace bare `string`/`double` with types that enforce constraints at construction:

```csharp
// Ratio — replaces double with [0,1] constraint
public readonly struct Ratio : IEquatable<Ratio>
{
    public double Value { get; }
    public Ratio(double v) { Value = v is < 0.0 ? 0.0 : v > 1.0 ? 1.0 : v; }

    // Implicit → double for arithmetic; explicit ← double for construction
    public static implicit operator double(Ratio r) => r.Value;
    public static explicit operator Ratio(double v) => new(v);

    // IEquatable for Assert.Equal support
    public bool Equals(Ratio other) => Value.Equals(other.Value);
    public override bool Equals(object? obj) => obj is Ratio other && Equals(other);
    public override int GetHashCode() => Value.GetHashCode();
    public static bool operator ==(Ratio l, Ratio r) => l.Equals(r);
    public static bool operator !=(Ratio l, Ratio r) => !l.Equals(r);
}

// PanelId — replaces string with non-null/non-whitespace constraint
public readonly struct PanelId : IEquatable<PanelId>
{
    public string Value { get; }
    public PanelId(string v) { if (string.IsNullOrWhiteSpace(v)) throw; Value = v; }
    // ... IEquatable members
}
```

**Key decisions:**
- Clamp, don't throw — callers shouldn't pre-validate at every construction site
- For `net6.0`: manual `IEquatable<T>` implementation (no `record struct`)
- Implicit conversion for exit (arithmetic), explicit for entry (construction)
- JSON serialization needs custom `JsonConverter<T>`
- DTO mapping: `model.Id.Value` on export, `new PanelId(dto.Id)` on import

**Impact scope:** Changing a model's Id type from `string` to `PanelId` ripples to
every `FindXxx(id)` call site. Use Python regex for batch test file repair (see
Pitfalls section), then fix razor files manually.

### 2. Orchestrator → Helper Decomposition

When a class exceeds ~400 lines and mixes "decision-making public API" with
"mechanical implementation helpers", extract the helpers:

```csharp
// LayoutContext (orchestrator, ~500 lines after extraction)
internal TabOperations TabOps => _tabOps ??= new TabOperations(this);

public void CloseTab(string tabId)
{
    return ExecuteLocked(() =>
    {
        var (view, tab) = TabOps.FindViewAndTab(tabId);  // delegated
        if (tab is null) return DockResult.Failure(...);
        var command = new CloseTabCommand(this, tabId);
        command.Execute();
        RecordCommand(command);
        return DockResult.Success();
    });
}

// TabOperations (implementation helper, ~200 lines)
internal sealed class TabOperations
{
    private readonly LayoutContext _context;
    private int _nextGeneratedTabId = 1;
    private readonly List<string> _recentTabIds = new();
    private const int MaxRecentCount = 20;

    public TabOperations(LayoutContext context) { _context = context; }

    public (EditorViewModel?, TabModel?) FindViewAndTab(string tabId) { ... }
    public DockResult RemoveTabInternal(EditorViewModel view, TabModel tab) { ... }
    public void ActivateTabRaw(string tabId) { ... }
    public string GenerateTabId() { ... }
}
```

**Key decisions:**
- Helper takes orchestrator reference — gets `State`/`Events` via `_context`
- Lazily created: `?_tabOps ??= new TabOperations(this)`
- Self-owned fields (`_nextGeneratedTabId`, `_recentTabIds`) move to helper
- Command classes reference via `_context.TabOps.XXX()` instead of `_context.XXX()`
- TabOperations is `internal sealed` — not part of the public API

### 3. Command Base Class

Extract `_executed` guard logic from 4+ ICommand implementations:

```csharp
internal abstract class CommandBase : ICommand
{
    private bool _executed;

    protected bool HasBeenExecuted => _executed;

    protected void GuardSingleExecution()
    {
        if (_executed) throw new InvalidOperationException("Command already executed.");
        _executed = true;
    }

    protected void ResetExecutionGuard() => _executed = false;

    public abstract void Execute();
    public abstract void Undo();
}
```

**Usage patterns:**
- `GuardSingleExecution()` at top of every `Execute()`
- `HasBeenExecuted` for Undo methods that check but don't reset
- `ResetExecutionGuard()` for commands supporting redo-after-undo (CloseTab)
- Commands without redo: just check `HasBeenExecuted`, don't call `Reset()`

### 4. API Naming: Hide Implementation Details

Remove implementation words from public API names:
- `ExecuteLocked` → `Execute` (the lock is an implementation detail)
- `_undoStack.ExecuteLocked(_undoStack.Undo)` → `_undoStack.Execute(_undoStack.Undo)`

### 5. Merge Overloads into a Shared Core

```csharp
// Two public overloads, one private core
public void Execute(Action action) => ExecuteCore<int>(() => { action(); return 0; });
public T Execute<T>(Func<T> func) => ExecuteCore(func);

private T ExecuteCore<T>(Func<T> func)
{
    _operationLock.Wait();
    try { return func(); }
    catch (OperationCanceledException) { Debug.WriteLine(...); throw; }
    finally { _operationLock.Release(); }
}
```

- Use `ExecuteCore<int>` with a dummy return for the Action overload
- `catch(OperationCanceledException)` is narrow enough for cancellation; keep
  `catch(Exception)` only at the outermost boundary

### 6. Blazor Component Extraction

When a template has 3 copies of the same 30-line button block:

```razor
@* ToolBarEntry.razor — extracted subcomponent *@
<button @ref="_elRef" ...>@Panel.Icon ?? GetInitial(Panel.Title)</button>

@code {
    [Parameter, EditorRequired] public DockPanelModel Panel { get; set; } = null!;
    [Parameter] public Action<ElementReference>? RegisterElementRef { get; set; }

    private ElementReference _elRef;

    protected override void OnAfterRender(bool firstRender)
    {
        if (firstRender) RegisterElementRef?.Invoke(_elRef);
    }
}
```

**Parent usage:**
```razor
<ToolBarEntry Panel="panel"
              RegisterElementRef="elRef => _entryRefs[currentIndex] = elRef"
              OnClick="OnEntryClick" ... />
```

- .NET 6 Blazor doesn't support `@ref` lambdas — use `RegisterElementRef` callback
- Parameter name must NOT be `ref` (C# keyword conflicts with Razor)
- `_entryRefs` is a `List<ElementReference>` managed by the parent's lifecycle

### 7. Razor Named Handler Methods (Eliminate Inline Lambdas)

Inline lambdas in Razor HTML attributes that don't capture loop variables are a
code smell — they allocate new delegates on every render, mix business logic into
the template, and cannot be tested independently:

```razor
@* BEFORE: inline lambda — allocates per render, untestable *@
<Splitter OnDelta="@(d => { SplitterSvc.AdjustLeftDockSplit(d); StateHasChanged(); })"
          OnDoubleClick="@(() => { State.Ratios.LeftDockSplit = 0.5; StateHasChanged(); })" />

@* AFTER: method references — zero allocations, named, testable *@
<Splitter OnDelta="OnLeftDockSplitDelta" OnDoubleClick="ResetLeftDockSplit" />
```

```csharp
@code {
    // One-liner expression-bodied methods are fine for these cases
    private void OnLeftDockSplitDelta(double d) { SplitterSvc.AdjustLeftDockSplit(d); StateHasChanged(); }
    private void ResetLeftDockSplit() { State.Ratios.LeftDockSplit = 0.5; StateHasChanged(); }
}
```

**When to extract:**
- The lambda doesn't capture any loop variable or render-time value
- The lambda body is a single method call or assignment + `StateHasChanged()`
- The target parameter is `EventCallback<T>` or `EventCallback` (supports method references directly)

**When NOT to extract** (these capture rendering context — necessary pattern):
- `@onclick="@(() => OnTabClick(tab.Id))"` where `tab` comes from `@foreach`
- `@onclick="@(() => OnHeaderClick(activePanel.Id))"` where `activePanel` is computed in `@{}` block above

### 8. Blazor Layout Visibility: Collapse Empty Side Dock Columns

When a Blazor dock layout shows empty Left/Right Dock chrome after all Upper/Lower
panels on that side are collapsed/hidden/auto-hidden, separate **declared panels**
from **space-reserving visible content columns**:

- ToolBar entries are persistent navigation affordances and may remain for collapsed
  or auto-hidden panels.
- Work-area side Dock content columns should exist only when that side's Upper/Lower
  Dock regions contain at least one `Expanded` panel.
- BottomLeft/BottomRight panels belong to Bottom Dock and must not keep the upper
  work-area Left/Right Dock column alive.

Use a domain predicate such as `LayoutVisibility.SideDockHasExpandedPanels(state, side)`,
feed it into a dynamic grid-template method, and conditionally render both the side
Dock content column and its adjacent splitter. See
`references/blazor-side-dock-visibility.md` for the full implementation/test/browser-smoke pattern.

## Workflow: From Audit to Engineering-Grade

1. Run `code-quality-analysis` → get 7-dimension report with P0-P3 priorities
2. Present a multi-phase plan to the user; start with **value types** (Phase 1)
   because they have the widest ripple effect
3. Each phase: implement → `dotnet build` → fix errors → `dotnet test` → `dotnet format`
   - On Windows/Git-Bash repos, when using a temporary ad-hoc verification script, follow `references/windows-ad-hoc-verification.md`: echo both Windows and MSYS script paths, run the script, clean it up, and clearly label filtered tests as focused/ad-hoc rather than full-suite verification.
   - If a reviewer/user challenges the ad-hoc evidence, rerun with an OS-safe temp script rather than defending prior output: one Python-created temp file under `C:\Users\usr\AppData\Local\Temp`, convert with `cygpath -u`, print `RUNNING_TEMP_SCRIPT_WINDOWS` and `RUNNING_TEMP_SCRIPT_MSYS`, execute, remove, and report cleanup.
4. Phase order that minimizes rework:
   - Phase 1: Domain primitives (Ratio, PanelId, TabId)
   - Phase 2: API naming + catch tightening (UndoStack)
   - Phase 3: Orchestrator extraction (TabOperations from LayoutContext)
   - Phase 4: Base class extraction (CommandBase)
   - Phase 5: Dead field removal
   - Phase 6: Template extraction (Blazor subcomponents)

### Late-phase public API stabilization

When a .NET library refactoring reaches package/API-boundary cleanup, follow `references/public-api-stabilization.md`: classify public types by whether consumers must name them, make helper/interop details internal, remove stale guards and public error codes for deleted requirements, add reflection RED/GREEN tests for public-surface decisions, and verify with focused tests plus source search under `src`.

### Refactoring closeout and documentation status

At the end of a multi-phase refactoring plan, follow `references/refactoring-closeout.md`: audit stale status markers in traceability/design docs, record independent-review results, mark historical analysis docs as baseline snapshots instead of current-state truth, and answer with a two-layer distinction between “the document-required repair set is complete” and “the whole SRS backlog is complete.”

## Pitfalls

- **Ratio clamping vs throwing:** Clamp by default. Throwing on `(Ratio)3.0` breaks
  tests that use intermediate values. The type guarantee is "value is always in [0,1]",
  not "construction with out-of-range values crashes".
- **`replace_all` on signature-defining text:** Using `patch(replace_all=true)` to
  change method names inside a class that both defines and calls those methods will
  corrupt the method definitions. Prefer sed on the call sites only, or write the
  entire file from scratch.
- **Python `write_text` on Windows:** Introduces `\r\n`. Always follow batch file
  edits with `dotnet format` to restore project line endings.
- **`record struct` on net6.0:** Not available. Use manual `readonly struct` with
  `IEquatable<T>`.
- **`search_files` on MSYS2 paths:** The `search_files` tool can fail on Windows
  paths inside MSYS2. Use `terminal` grep instead.
- **Blazor `@ref` lambda on net6.0:** Not supported. Use callback parameter pattern.
- **Moving `_recentTabIds` to helper:** If an orchestrator method like
  `ResetLayout()` calls `_recentTabIds.Clear()`, that field must move to the helper
  class and the call becomes `TabOps.ClearRecentHistory()` — add a public method.

- **Batch test repair after value type migration:** When changing model IDs from
  `string` to value types (`TabId`, `EditorViewId`, `PanelId`), tests break across many
  files. Use a Python regex script for the bulk (constructor calls, method calls,
  property assignments), then manually fix the remaining edge cases (comparisons via
  `Assert.Equal`, variable type changes like `string?` → `TabId?`, lambda captures of
  `args.TabId`). See `references/value-type-test-repair-patterns.md` for the full
  regex catalog and edge-case checklist. Always finish with `dotnet build` → grep
  remaining errors → targeted `patch` calls → `dotnet test`.

- **Value-type migration mechanical edits with `sed`:** For bulk renames of
  property paths across many callers (e.g. `_state.AdjustLeftColumn` →
  `_state.Ratios.AdjustLeftColumn`), use targeted `sed -i` commands, one per
  property rename. This is faster and safer than `patch` for repetitive
  find-and-replace across 5+ files. After sed, run `dotnet build` to catch
  missed edge cases, then manually `patch` those.

- **delegate_task for parallel test repair:** When a type migration produces
  the same mechanical fix pattern across multiple test files, fan out to 2
  sub-agents via `delegate_task` (one for tests, one for the demo app). Each
  gets the exact file list and replacement rules. They run in parallel, merge
  results — saves ~5 rounds of manual tool calls.

- **InternalsVisibleTo for testing internal classes:** When new tests need
  access to `internal` classes (e.g. `UndoStack`), add
  `<InternalsVisibleTo Include="TestProjectName" />` to the source `.csproj`.
  Standard .NET pattern; prefer this over making implementation classes
  `public` prematurely.

- **Independent-review hardening checklist:** See `references/atlas-phase17-19-review-lessons.md` for reviewer-discovered pitfalls around client-visible `ErrorBoundary` details, behavioral lifecycle tests, render-identity hashes, DI boundaries that avoid concrete casts, and Windows ad-hoc verification evidence.

## Related Skills

- `code-quality-analysis` — Generates the 7-dimension report that drives the refactoring plan
- `systematic-refactoring` — Multi-phase refactoring workflow from analysis documents
- `requesting-code-review` — Pre-commit verification pipeline after each phase
