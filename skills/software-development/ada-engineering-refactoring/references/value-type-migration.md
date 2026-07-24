# Value-Type Migration (string→StrongId, double→Ratio)

When migrating a codebase from primitive types (string for IDs, double for constrained values) to strongly-typed value types, the migration follows a predictable cascade. This reference covers the full pattern: cascade rules, spread order, Razor pitfalls, arithmetic gaps, clamp-vs-throw decisions, test adjustments, struct implementation, JSON serialization, and bulk strategy.

## The Cascade Pattern

| Original | New | Conversion Rule |
|----------|-----|-----------------|
| `FindDockPanel(stringId)` | `FindDockPanel(new PanelId(stringId))` | Constructor wrap at every call site |
| `panel.Id` → `string` param/member | `panel.Id.Value` | `.Value` property (PanelId → string) |
| `double` → `Ratio` property setter | `(Ratio)doubleValue` or `new Ratio(v)` | Explicit cast/constructor (implicit only Ratio→double) |
| `Assert.Equal(expected, panel.SizeRatio)` | Works as-is | Ratio→double implicit, so Assert.Equal(double, Ratio) compiles |
| `prop = 1.0` | `prop = (Ratio)1.0` | Literal doubles need explicit cast |

## Cascade Spread Order

Fix propagates through these layers:

1. **Service layer** — `FindDockPanel(string)` → `FindDockPanel(new PanelId(string))`, property assignments
2. **Command classes** — same FindDockPanel fix, plus `.Id` → `.Id.Value` when PanelId flows to string members or event payloads (`NotifyLayoutChanged(type, panel.Id.Value)`)
3. **DTO serialization** — `FromModel`: `.Id = model.Id` → `.Id = model.Id.Value`; `SetSizeConstraints`/build: double literal → `(Ratio)` cast
4. **Drag service** — one `FindDockPanel` call per handler
5. **Razor components** — event handlers, inline ternaries, `_entryPanelIds[index]` storage
6. **Test files** — all the same patterns as source, plus `panel.Id` in assertions → `.Value`
7. **Demo files** — any standalone panels or services

## Razor-Specific Pitfalls

These only surface in `.razor` files (Blazor compiler, not C# compiler):

- **Delegate calls** — `@onclick="@(() => OnHeaderClick(activePanel.Id))"` fails CS1503 because C# delegate creation requires explicit type. Fix: `activePanel.Id.Value`.
- **HTML rendering** — `data-xd-panel="@activePanel.Id"` works fine without `.Value` because Blazor's `@` expression calls `.ToString()` which returns `Value`.
- **Ternary type inference** — `var current = hasPanels ? somePanel.Id : null;` fails CS0173 (can't infer type between PanelId and null). Fix: `.Value` on the PanelId side gives `string?`, or cast `(PanelId?)null`.
- **`?.` null-conditional** — `_hoveredPanel?.Id != stringVar` fails (PanelId? vs string). Fix: `_hoveredPanel?.Id.Value != stringVar`.
- **`@ref` parameter naming** — `@ref="ref => list[index] = ref"` fails CS1041 because `ref` is a keyword. Use a different parameter name: `@ref="elRef => list[index] = elRef"`.

## Ratio Arithmetic Gap

`Ratio` has `implicit operator double` but NO arithmetic operators (+, -, *, /):

```csharp
// ✓ Compiles: both Ratios auto-convert to double
var sum = panelA.SizeRatio + panelB.SizeRatio;  // double result

// ✗ Fails: double can't implicitly convert back to Ratio
panelA.SizeRatio = sum;  // CS0266

// ✓ Fix
panelA.SizeRatio = (Ratio)sum;
```

All arithmetic expressions that produce a `double` result and assign to a `Ratio` property need explicit `(Ratio)` cast. Common sites: `Clamp()` return values, `(sum / 2.0)` results, `sum - clamped` subtractions.

### Critical Bug: Compute Sum Before Mutating

When redistributing values across two panels, capture the original sum before mutating any variable. Otherwise the second computation uses the already-changed first value:

```csharp
// ✗ Wrong: panelA already mutated when panelB is computed
panelA.SizeRatio = (Ratio)newRatio;
panelB.SizeRatio = (Ratio)(panelA.SizeRatio + panelB.SizeRatio - newRatio); // uses MUTATED panelA!

// ✓ Right: capture sum first
var sum = panelA.SizeRatio + panelB.SizeRatio;
panelA.SizeRatio = (Ratio)clamped;
panelB.SizeRatio = (Ratio)(sum - clamped);
```

## Clamp vs Throw: Choosing the Right Behavior

When introducing a constrained value type (`Ratio`) to replace bare `double`, the initial instinct is to **throw** on out-of-range input. This preserves the "compile-time enforcement" contract. However, tests and intermediate calculations often use values outside [0, 1] — e.g. `Resize("a", "b", 0.5)` where panel B ends up with `sum - 0.5 = 1.5`, or tests that construct `SizeRatio = 3.0` as a setup value.

**Decision rule**: Clamp silently when:
- The type will be used as a struct-initialized property (`SizeRatio = (Ratio)1.5` in test setup)
- Arithmetic operations can produce intermediate results outside range
- Users of the type are unlikely to pre-validate every construction site

Throw when:
- The type is an API boundary input (user-facing method parameter)
- Out-of-range indicates a genuine bug, not a rounding artifact

**Default for `Ratio`**: silently clamp. The constraint still holds (`Ratio.Value` is always in [0, 1]) but callers aren't forced to pre-validate.

```csharp
public Ratio(double value)
{
    Value = value is < 0.0 ? 0.0 : value > 1.0 ? 1.0 : value;
}
```

## Test Value Adjustment After Migration

After introducing a constrained value type, tests that used values outside the new range will fail. **Don't remove or weaken the tests — adjust the values within the new range.** The test semantics stay the same:

| Original | After Migration | Rationale |
|----------|----------------|-----------|
| `SizeRatio = 3.0; Equalize(); Assert.Equal(2.0, ...)` | `SizeRatio = 0.7; Equalize(); Assert.Equal(0.5, ...)` | Equalize still splits the pair evenly |
| `SizeRatio = 2.0; Export(); Assert.Equal(2.0, ...)` | `SizeRatio = 0.8; Export(); Assert.Equal(0.8, ...)` | Round-trip test still validates serialization |
| `SizeRatio = 1.5; Resize("a","b",0.5); Assert.Equal(1.5, ...)` | Pairs must sum to ~1.0: `SizeRatio = 0.6; SizeRatio2 = 0.4; Resize("a","b",0.3); Assert.Equal(0.7, ...)` | Resize redistributes within the pair |

## Value-Type Implementation (struct not record struct)

.NET 6 does not support `partial void OnValueChanged()` on `readonly record struct`. Use a plain `readonly struct` with explicit `IEquatable<T>`:

```csharp
public readonly struct Ratio : IEquatable<Ratio>
{
    public double Value { get; }
    public Ratio(double value) { Value = Clamp(value); }
    public bool Equals(Ratio other) => Value.Equals(other.Value);
    public override bool Equals(object? obj) => obj is Ratio other && Equals(other);
    public override int GetHashCode() => Value.GetHashCode();
    public static bool operator ==(Ratio left, Ratio right) => left.Equals(right);
    public static bool operator !=(Ratio left, Ratio right) => !left.Equals(right);
}
```

## JSON Serialization Pattern

Include a `JsonConverter` inside the same file for value types that need to serialize cleanly:

```csharp
[JsonConverter(typeof(PanelIdJsonConverter))]
public readonly struct PanelId : IEquatable<PanelId> { ... }

internal sealed class PanelIdJsonConverter : JsonConverter<PanelId>
{
    public override PanelId Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var str = reader.GetString();
        return string.IsNullOrWhiteSpace(str) ? default : new PanelId(str!);
    }
    public override void Write(Utf8JsonWriter writer, PanelId value, JsonSerializerOptions options)
        => writer.WriteStringValue(value.Value);
}
```

## Key Error Codes and Fix Patterns

These CS error codes appear predictably during value-type migrations. Use them to quickly diagnose build output:

| Error | Pattern | Fix |
|-------|---------|-----|
| CS1503 | `string` → `PanelId` | `FindDockPanel(new PanelId(panelId))` |
| CS0266 | `double` → `Ratio` (implicit) | `panel.SizeRatio = (Ratio)doubleVal` |
| CS0029 | `PanelId` → `string` (implicit) | `panel.Id.Value` |
| CS0173 | Ternary with `PanelId` and `null` | `cond ? panel.Id.Value : null` |
| CS1503 | `PanelId` → `string` in Razor lambdas | `OnHeaderClick(panel.Id.Value)` |
| CS0019 | `PanelId?` compared to `string` | `hovered?.Id.Value != panelId` |

## One-Shot Bulk Migration Strategy

For large migrations with 50+ errors across many files, **don't use delegate_task** — the subagent's slow `dotnet build` pipeline (90s per build on Windows/MSYS2) makes it impractical. Instead:

1. **Read ALL error messages first** — `dotnet build 2>&1 | grep "error CS"` — to understand every affected file and pattern
2. **Group by file** — files with all `FindDockPanel` errors are fastest (one pattern per call site), files with mixed `FindDockPanel` + `Ratio` need more attention
3. **Fix .cs source files first** — C# compiler catches these clearly. Use `patch` with `replace_all=true` for identical patterns across a file, Python scripts for cross-file patterns.
4. **Then .razor files** — Blazor-compiled files have different line numbering; re-read to match source line numbers. Use `replace_all=true` for identical patterns across 3+ blocks in the same file (e.g. ToolBar.razor 3 identical `_entryPanelIds[...] = panelId`).
5. **Then test files** — larger volume but same patterns. A Python script with regex replace (`re.sub`) handles batch fixes efficiently. **Warning**: Python `Path.write_text()` may introduce `\r\n` line endings; run `dotnet format --fix-whitespace` after.
6. **Rebuild after every file** — stop cascade early: if main .csproj is clean but tests still fail, you know you're in test-only territory
7. **Don't stop at the main `.csproj`** — test projects and demo projects also need fixing
