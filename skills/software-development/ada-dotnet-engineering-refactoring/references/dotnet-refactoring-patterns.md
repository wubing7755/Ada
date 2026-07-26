# .NET Engineering-Grade Refactoring — Core Patterns

Full code examples for each pattern described in the parent SKILL.md. Each pattern
includes key decisions documenting trade-offs: clamp vs. throw for constrained types,
manual `IEquatable<T>` for .NET 6 compatibility, implicit/explicit conversion operators,
JSON serialization via custom `JsonConverter<T>`, and `InternalsVisibleTo` for test access.

## 1. Domain Primitive Value Types

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

## 2. Orchestrator → Helper Decomposition

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

## 3. Command Base Class

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

## 4. API Naming: Hide Implementation Details

Remove implementation words from public API names:
- `ExecuteLocked` → `Execute` (the lock is an implementation detail)
- `_undoStack.ExecuteLocked(_undoStack.Undo)` → `_undoStack.Execute(_undoStack.Undo)`

## 5. Merge Overloads into a Shared Core

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

## 6. Blazor Component Extraction

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

## 7. Razor Named Handler Methods (Eliminate Inline Lambdas)

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

## 8. Blazor Layout Visibility: Collapse Empty Side Dock Columns

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
