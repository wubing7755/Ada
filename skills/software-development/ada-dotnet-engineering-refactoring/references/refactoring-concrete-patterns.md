# Concrete C# Patterns with Code (Lib Session 2026-07-22)

## Ratio — Domain primitive replacing double

```csharp
// src/Lib/Domain/Primitives/Ratio.cs
public readonly struct Ratio : IEquatable<Ratio>
{
    public double Value { get; }
    public static readonly Ratio Zero = new(0.0);
    public static readonly Ratio One = new(1.0);
    public static readonly Ratio DefaultMin = new(0.05);
    public static readonly Ratio DefaultMax = new(0.95);

    public Ratio(double value) { Value = value is < 0.0 ? 0.0 : value > 1.0 ? 1.0 : value; }
    public static implicit operator double(Ratio r) => r.Value;
    public static explicit operator Ratio(double v) => new(v);

    public bool Equals(Ratio other) => Value.Equals(other.Value);
    public override bool Equals(object? obj) => obj is Ratio other && Equals(other);
    public override int GetHashCode() => Value.GetHashCode();
    public static bool operator ==(Ratio l, Ratio r) => l.Equals(r);
    public static bool operator !=(Ratio l, Ratio r) => !l.Equals(r);
}

// JSON converter
internal sealed class RatioJsonConverter : JsonConverter<Ratio>
{
    public override Ratio Read(ref Utf8JsonReader reader, Type type, JsonSerializerOptions options)
        => new(reader.GetDouble());
    public override void Write(Utf8JsonWriter writer, Ratio value, JsonSerializerOptions options)
        => writer.WriteNumberValue(value.Value);
}
```

## PanelId — Domain primitive replacing string

```csharp
// src/Lib/Domain/Primitives/PanelId.cs
[JsonConverter(typeof(PanelIdJsonConverter))]
public readonly struct PanelId : IEquatable<PanelId>
{
    public string Value { get; }
    public PanelId(string value) {
        if (string.IsNullOrWhiteSpace(value))
            throw new ArgumentException("Panel id is required.", nameof(value));
        Value = value;
    }
    public override string ToString() => Value;
    public bool Equals(PanelId o) => StringComparer.Ordinal.Equals(Value, o.Value);
    // ... IEquatable boilerplate
}

internal sealed class PanelIdJsonConverter : JsonConverter<PanelId>
{
    public override PanelId Read(ref Utf8JsonReader reader, ...) {
        var str = reader.GetString();
        return string.IsNullOrWhiteSpace(str) ? default : new PanelId(str!);
    }
    public override void Write(Utf8JsonWriter writer, PanelId value, ...)
        => writer.WriteStringValue(value.Value);
}
```

## CommandBase — shared guard for 4 command classes

```csharp
internal abstract class CommandBase : ICommand
{
    private bool _executed;
    protected bool HasBeenExecuted => _executed;
    protected void GuardSingleExecution() { if (_executed) throw new InvalidOperationException("..."); _executed = true; }
    protected void ResetExecutionGuard() { _executed = false; }
    public abstract void Execute();
    public abstract void Undo();
}

// Usage: CloseTabCommand (supports redo)
public override void Execute() { GuardSingleExecution(); ... }
public override void Undo() { if (!HasBeenExecuted || ...) return; ResetExecutionGuard(); ... }

// Usage: MoveTabCommand (one-shot undo)
public override void Execute() { GuardSingleExecution(); ... }
public override void Undo() { if (!HasBeenExecuted) return; /* no reset */ ... }
```

## TabOperations — Orchestrator helper extraction

Before: LayoutContext 606 lines. After: LayoutContext 519 lines + TabOperations 200 lines.
Extracted methods: FindViewAndTab, RemoveTabInternal, ActivateTabInView,
PickNextTab, RecordRecent, GenerateTabId, ActivateTabRaw, CloseTabRaw.
Moved fields: _nextGeneratedTabId, _recentTabIds, MaxRecentCount.

## UndoStack API rename

```csharp
// Before
public void ExecuteLocked(Action action) { ... }
public T ExecuteLocked<T>(Func<T> func) { ... }

// After — shared core + renamed overloads
public void Execute(Action action) => ExecuteCore<int>(() => { action(); return 0; });
public T Execute<T>(Func<T> func) => ExecuteCore(func);
private T ExecuteCore<T>(Func<T> func) { Wait; try return func(); catch(OperationCanceledException) {throw;} finally Release; }
```

## Bulk test repair after value type migration

See `references/value-type-test-repair-patterns.md` for the complete regex catalog
and manual edge-case checklist. Covers TabId, EditorViewId, PanelId migrations.

## Known tool failures (MSYS2 on Windows)

- `search_files` fails on MSYS2 paths with "系统找不到指定的路径" — use `terminal` grep instead
- `execute_code` Python subprocess with shell=True + MSYS2 path can get encoding errors
- `dotnet build` takes 60-90 seconds on this machine — cache results, don't re-run unnecessarily
