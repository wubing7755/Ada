---
name: ada-engineering-refactoring
description: Architectural-level code refactoring that meets Microsoft/NET library engineering standards — value-type-first, interface-based protocols, orchestration/implementation separation, and whole-project consistency. Use when the user rejects mechanical dedup and asks for engineering-level quality.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [refactoring, architecture, engineering-quality, dotnet, blazor]
    related_skills: [hermes-operations, deviation-analysis-refactoring, blazor-razor-authoring, ada-refactoring-lifecycle]
---

# Engineering-Grade Refactoring

Architectural-level code refactoring for entire projects. Not mechanical dedup — this is the skill for when the user says "Microsoft engineering level" or "this doesn't meet my standard."

## When to Use

- User explicitly rejects mechanical refactoring (extract-method, extract-helper) as insufficient
- User says "I want Microsoft-level code quality" or "engineering-grade"
- User asks for "whole-project consistency" — not one-file-at-a-time fixes
- User describes the goal as "a project a human can pick up and extend naturally"
- After a code quality report identified 5+ items, and the first mechanical fix was rejected

**Skip for**: single-file cleanup, pre-commit verification, bug fixes, small scoped changes.

## Signal: When Mechanical Dedup is Not Enough

The user will say things like:

- "这还没有达到我预期的想法"
- "我认为比较好的，应该类似于微软那种工程级的代码写法"
- "最后整套流程下来，你留给我的是一个工程化的项目，后续人类可以继续在该项目上扩展与编写"

When you hear this, **stop what you're doing** (the current file changes are likely rejected), revert or stash, and switch to this skill's workflow.

## Six Quality Gates for Engineering-Level Code

These gates define the gap between mechanical dedup and engineering-grade code. Check all six before claiming work is done:

### Gate 1 — Type System Carries Constraints, Not Runtime Validation
```csharp
// ✗ Mechanical: setter + static helper
private static void ValidateRange(double v, string n) { if (v < 0 || v > 1) throw ...; }
public double MinSizeRatio { set { ValidateRange(value); ... } }

// ✓ Engineering: value type with built-in constraint
public readonly record struct Ratio(double Value)
{
    public Ratio(double value) : this(
        value is >= 0.0 and <= 1.0 ? value
        : throw new ArgumentOutOfRangeException(...)) { }
}
public Ratio MinSizeRatio { get; set; }
```

### Gate 2 — API Names Reveal Intent, Not Implementation
```csharp
// ✗ Mechanical: exposes impl detail
private void ExecutePanelAction(string id, Action<DockPanelModel> a) { ... }

// ✓ Engineering: named for what it does, not how it works
// (The panel lookup + notification + locking are all impl details)
// Better: just keep the original method names and inline the action
```

### Gate 3 — Dependencies on Interfaces, Not Concrete Classes
```csharp
// ✗ Mechanical: still new-ing up concrete classes
private readonly UndoStack _undoStack = new();

// ✓ Engineering: depends on contract
private readonly IOperationCoordinator _coordinator;
```

### Gate 4 — Orchestration Separated from Implementation
A class >300 lines likely mixes two things:
- **Orchestration**: find entity → validate → invoke command → notify (what)
- **Implementation**: manage locks, lifecycle, internal state (how)

Extract implementation into helper classes. Orchestration layer should have zero implementation detail.

### Gate 5 — Whole-Project Consistency, Not File-at-a-Time
If you introduce a `Ratio` type for `DockPanelModel.MinSizeRatio`, every other property/param with the same range must use it too. If you rename `ExecuteLocked` to `Execute` in UndoStack, every call site must update. Partial application creates inconsistency — the exact state the user escapes.

### Gate 6 — Razor Files are Not Second-Class Citizens
Template duplication (>2 identical blocks) → extract child component. Inline C# `@{}` declarations → computed properties in `@code`. `OnInitialized` doing 3+ things → named helper methods.

## Workflow

### Phase 0 — Discovery and Plan

1. **Listen to the rejection**. When the user says "not engineering level", they are telling you the standard. Press for specifics: "What specifically doesn't meet the standard? The naming? The scope? The approach?"

2. **Revert**. `git checkout -- <files>` the mechanical changes before writing the plan. A plan proposed while the rejected changes are still on disk wastes the user's attention.

3. **Map the full scope**. Read ALL affected files across the project, not just the ones in the current issue. List every file that would need to change for each phase.

4. **Write the plan**. Create a comprehensive markdown document in `docs/refactoring/` using the template in `references/refactoring-plan-template.md`. The plan must cover ALL phases (not just the first 3 — include subsequent phases as stubs even if details are TBD). Each phase must include:
   - Goal, current state analysis, design approach, file change list, verification criteria
   - Verification criteria split into "build/test" and "architecture/quality" layers
   - For quality checks, use the checklist in `references/quality-checklist.md`
   - Phase dependency chain diagram (ASCII art)
   - Totals table at the end
   - Quality standards defined upfront (sealed/internal/XML docs/is null/IEquatable/etc.) so all phases reference a single baseline

5. **Present to user. Do NOT start implementation until approved.**

### Phase N — Execute

1. Create a `todo` with each atomic change
2. Build after each item
3. Test after the phase completes
4. **Self-review**: re-read every modified file and check all 6 gates
5. If any gate is not met, fix before presenting to user

### Final Review — Whole-Project Consistency Pass

After all phases complete:

- Is the pattern applied uniformly across the codebase? (Gate 5)
- Do the `.razor` files match the same quality standard as `.cs`? (Gate 6)
- Is the coding style consistent — one project, one team feel?
- Run `dotnet build && dotnet test && dotnet format --verify-no-changes`
- Verify all quality checklist items from `references/quality-checklist.md`

## Value-Type Migration (string→StrongId, double→Ratio)

When migrating a codebase from primitive types (string for IDs, double for constrained values) to strongly-typed value types, the migration follows a predictable cascade. Add this section after Gate 1 when executing the actual migration work.

### The Cascade Pattern

| Original | New | Conversion Rule |
|----------|-----|-----------------|
| `FindDockPanel(stringId)` | `FindDockPanel(new PanelId(stringId))` | Constructor wrap at every call site |
| `panel.Id` → `string` param/member | `panel.Id.Value` | `.Value` property (PanelId → string) |
| `double` → `Ratio` property setter | `(Ratio)doubleValue` or `new Ratio(v)` | Explicit cast/constructor (implicit only Ratio→double) |
| `Assert.Equal(expected, panel.SizeRatio)` | Works as-is | Ratio→double implicit, so Assert.Equal(double, Ratio) compiles |
| `prop = 1.0` | `prop = (Ratio)1.0` | Literal doubles need explicit cast |

### Cascade Spread Order

Fix propagates through these layers:

1. **Service layer** — `FindDockPanel(string)` → `FindDockPanel(new PanelId(string))`, property assignments
2. **Command classes** — same FindDockPanel fix, plus `.Id` → `.Id.Value` when PanelId flows to string members or event payloads (`NotifyLayoutChanged(type, panel.Id.Value)`)
3. **DTO serialization** — `FromModel`: `.Id = model.Id` → `.Id = model.Id.Value`; `SetSizeConstraints`/build: double literal → `(Ratio)` cast
4. **Drag service** — one `FindDockPanel` call per handler
5. **Razor components** — event handlers, inline ternaries, `_entryPanelIds[index]` storage
6. **Test files** — all the same patterns as source, plus `panel.Id` in assertions → `.Value`
7. **Demo files** — any standalone panels or services

### Razor-Specific Pitfalls

These only surface in `.razor` files (Blazor compiler, not C# compiler):

- **Delegate calls** — `@onclick="@(() => OnHeaderClick(activePanel.Id))"` fails CS1503 because C# delegate creation requires explicit type. Fix: `activePanel.Id.Value`.
- **HTML rendering** — `data-xd-panel="@activePanel.Id"` works fine without `.Value` because Blazor's `@` expression calls `.ToString()` which returns `Value`.
- **Ternary type inference** — `var current = hasPanels ? somePanel.Id : null;` fails CS0173 (can't infer type between PanelId and null). Fix: `.Value` on the PanelId side gives `string?`, or cast `(PanelId?)null`.
- **`?.` null-conditional** — `_hoveredPanel?.Id != stringVar` fails (PanelId? vs string). Fix: `_hoveredPanel?.Id.Value != stringVar`.

### Ratio Arithmetic Gap

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

### Clamp vs Throw: Choosing the Right Behavior

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
// ✓ Engineering: clamp, don't throw
public Ratio(double value)
{
    Value = value is < 0.0 ? 0.0 : value > 1.0 ? 1.0 : value;
}
```

### Test Value Adjustment Pattern

After introducing a constrained value type, tests that used values outside the new range will fail. **Don't remove or weaken the tests — adjust the values within the new range.** The test semantics stay the same:

| Original | After Migration | Rationale |
|----------|----------------|-----------|
| `SizeRatio = 3.0; Equalize(); Assert.Equal(2.0, ...)` | `SizeRatio = 0.7; Equalize(); Assert.Equal(0.5, ...)` | Equalize still splits the pair evenly |
| `SizeRatio = 2.0; Export(); Assert.Equal(2.0, ...)` | `SizeRatio = 0.8; Export(); Assert.Equal(0.8, ...)` | Round-trip test still validates serialization |
| `SizeRatio = 1.5; Resize("a","b",0.5); Assert.Equal(1.5, ...)` | Pairs must sum to ~1.0: `SizeRatio = 0.6; SizeRatio2 = 0.4; Resize("a","b",0.3); Assert.Equal(0.7, ...)` | Resize redistributes within the pair |

### One-Shot Bulk Migration Strategy

For large migrations with 50+ errors across many files:

1. **Read ALL error messages first** — `dotnet build 2>&1 | grep "error CS"` — to understand every affected file and pattern
2. **Group by file** — files with all `FindDockPanel` errors are fastest (one pattern per call site), files with mixed `FindDockPanel` + `Ratio` need more attention
3. **Fix .cs source files first** — C# compiler catches these clearly
4. **Then .razor files** — Blazor-compiled files have different line numbering; re-read to match source line numbers. Use `replace_all=true` for identical patterns across 3+ blocks in the same file (e.g. ToolBar.razor 3 identical `_entryPanelIds[...] = panelId`)
5. **Then test files** — same patterns but more files. `Assert.Equal(expected, panel.SizeRatio)` compiles fine (implicit Ratio→double). Only `.Id` in assertions needs `.Value`.
6. **Rebuild after every file** — stop cascade early: if main .csproj is clean but tests still fail, you know you're in test-only territory
7. **Don't stop at the main `.csproj`** — test projects and demo projects also need fixing

## Blazor-Specific Patterns

### Template Duplication → Child Component

When a `.razor` template repeats a markup block ≥2× with different data:

```razor
@* Extract: ToolBarEntry.razor *@
<div class="xd-toolbar-entry-wrapper @(IsAutoHidden ? "xd-autohidden" : null)"
     @onmouseenter="() => OnMouseEnter.InvokeAsync(Panel.Id)">
    <button class="xd-toolbar-entry @ActiveClass" @ref="_elRef"
            @onclick="() => OnClick.InvokeAsync(Panel.Id)">
        @if (Panel.Icon is not null) { <span>@Panel.Icon</span> }
        else { <span>@GetInitial(Panel.Title)</span> }
    </button>
</div>
@code {
    [Parameter, EditorRequired] public DockPanelModel Panel { get; set; } = null!;
    [Parameter] public EventCallback<string> OnClick { get; set; }
    private ElementReference _elRef;
    public ElementReference ElementRef => _elRef;
}
```

**Known Blazor constraint**: `@ref` on RenderFragment cannot capture ElementReference from parent. Expose via a public property on child.

### Inline Declarations → Computed Properties

```razor
@* ✗ Inline *@
@{ var upperGroups = UpperSectionPanels.GroupBy(...).ToList(); }

@* ✓ Property *@
@code { private IReadOnlyList<...> UpperGroups => UpperSectionPanels.GroupBy(...).ToList(); }
```

### Lifecycle Sequence → Named Methods

```csharp
protected override void OnInitialized()
{
    _context = Context ?? new LayoutContext(State);
    _style = new LayoutStyleAdapter(State);
    SubscribeToEvents();
}
private void SubscribeToEvents() { ... }
```

## Value-Type Migration (string→StrongId, double→Ratio)

When migrating a codebase from primitive types (string for IDs, double for constrained values) to strongly-typed value types, the migration follows a predictable cascade.

### The Cascade Pattern

| Original | New | Conversion Rule |
|----------|-----|-----------------|
| `FindDockPanel(stringId)` | `FindDockPanel(new PanelId(stringId))` | Constructor wrap at every call site |
| `panel.Id` → `string` param/member | `panel.Id.Value` | `.Value` property (PanelId → string) |
| `double` → `Ratio` property setter | `(Ratio)doubleValue` or `new Ratio(v)` | Explicit cast/constructor (implicit only Ratio→double) |
| `Assert.Equal(expected, panel.SizeRatio)` | Works as-is | Ratio→double implicit, so Assert.Equal(double, Ratio) compiles |
| `prop = 1.0` | `prop = (Ratio)1.0` | Literal doubles need explicit cast |

### Cascade Spread Order

Fix propagates through these layers:

1. **Service layer** — `FindDockPanel(string)` → `FindDockPanel(new PanelId(string))`, property assignments
2. **Command classes** — same FindDockPanel fix, plus `.Id` → `.Id.Value` when PanelId flows to string members or event payloads (`NotifyLayoutChanged(type, panel.Id.Value)`)
3. **DTO serialization** — `FromModel`: `.Id = model.Id` → `.Id = model.Id.Value`; `SetSizeConstraints`/build: double literal → `(Ratio)` cast
4. **Drag service** — one `FindDockPanel` call per handler
5. **Razor components** — event handlers, inline ternaries, `_entryPanelIds[index]` storage
6. **Test files** — all the same patterns as source, plus `panel.Id` in assertions → `.Value`
7. **Demo files** — any standalone panels or services

### Razor-Specific Pitfalls

These only surface in `.razor` files (Blazor compiler, not C# compiler):

- **Delegate calls** — `@onclick="@(() => OnHeaderClick(activePanel.Id))"` fails CS1503 because C# delegate creation requires explicit type. Fix: `activePanel.Id.Value`.
- **HTML rendering** — `data-xd-panel="@activePanel.Id"` works fine without `.Value` because Blazor's `@` expression calls `.ToString()` which returns `Value`.
- **Ternary type inference** — `var current = hasPanels ? somePanel.Id : null;` fails CS0173 (can't infer type between PanelId and null). Fix: `.Value` on the PanelId side gives `string?`, or cast `(PanelId?)null`.
- **`?.` null-conditional** — `_hoveredPanel?.Id != stringVar` fails (PanelId? vs string). Fix: `_hoveredPanel?.Id.Value != stringVar`.
- **Ref is a keyword** — `@ref="ref => list[index] = ref"` fails CS1041. Use a different parameter name: `@ref="elRef => list[index] = elRef"`.

### Ratio Arithmetic Gap

`Ratio` has `implicit operator double` but NO arithmetic operators (+, -, *, /):

```csharp
// ✓ Compiles: both Ratios auto-convert to double
var sum = panelA.SizeRatio + panelB.SizeRatio;  // double result

// ✗ Fails: double can't implicitly convert back to Ratio
panelA.SizeRatio = sum;  // CS0266

// ✓ Fix: explicit cast
panelA.SizeRatio = (Ratio)sum;
```

**Critical bug to avoid**: Compute the sum BEFORE mutating any panel, then assign to both:
```csharp
// ✗ Wrong: panelA already mutated when panelB is computed
panelA.SizeRatio = (Ratio)newRatio;
panelB.SizeRatio = (Ratio)(panelA.SizeRatio + panelB.SizeRatio - newRatio); // uses MUTATED panelA!

// ✓ Right: capture sum first
var sum = panelA.SizeRatio + panelB.SizeRatio;
panelA.SizeRatio = (Ratio)clamped;
panelB.SizeRatio = (Ratio)(sum - clamped);
```

### Clamp vs Throw: Choosing the Right Behavior

When introducing a constrained value type (`Ratio`) to replace bare `double`, the initial instinct is to **throw** on out-of-range input. However, tests and intermediate calculations often use values outside [0, 1]:

**Decision rule**: Clamp silently when:
- The type will be used as a struct-initialized property (`SizeRatio = (Ratio)1.5` in test setup)
- Arithmetic operations can produce intermediate results outside range
- Users of the type are unlikely to pre-validate every construction site

Throw when:
- The type is an API boundary input (user-facing method parameter)
- Out-of-range indicates a genuine bug, not a rounding artifact

**Default for `Ratio`**: silently clamp.
```csharp
public Ratio(double value)
{
    Value = value is < 0.0 ? 0.0 : value > 1.0 ? 1.0 : value;
}
```

### Test Value Adjustment After Migration

After introducing a constrained value type, tests that used values outside the new range will fail. **Don't remove or weaken the tests — adjust the values within the new range.** The test semantics stay the same:

| Original | After Migration | Rationale |
|----------|----------------|-----------|
| `SizeRatio = 3.0; Equalize(); Assert.Equal(2.0, ...)` | `SizeRatio = 0.7; Equalize(); Assert.Equal(0.5, ...)` | Equalize still splits the pair evenly |
| `SizeRatio = 2.0; Export(); Assert.Equal(2.0, ...)` | `SizeRatio = 0.8; Export(); Assert.Equal(0.8, ...)` | Round-trip test still validates serialization |
| `SizeRatio = 1.5; Resize("a","b",0.5); Assert.Equal(1.5, ...)` | Pairs must sum to ~1.0: `SizeRatio = 0.6; SizeRatio2 = 0.4; Resize("a","b",0.3); Assert.Equal(0.7, ...)` | Resize redistributes within the pair |

### Value-Type Implementation (struct not record struct)

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

### JSON Serialization Pattern

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

### One-Shot Bulk Migration Strategy

For migrations with 50+ errors across many files, **don't use delegate_task** — the subagent's slow `dotnet build` pipeline (90s per build on Windows/MSYS2) makes it impractical. Instead:

1. **Read ALL error messages first** — `dotnet build 2>&1 | grep "error CS"` — group by file and error pattern
2. **Fix .cs source files first** — use `patch` with `replace_all=true` for identical patterns across a file, Python scripts for cross-file patterns
3. **Then .razor files** — Blazor-compiled files need different line-number matching. Use `replace_all=true` for identical patterns in 3+ template blocks
4. **Then test files** — larger volume but same patterns. A Python script with regex replace (`re.sub`) handles batch fixes efficiently. **Warning**: Python `Path.write_text()` may introduce `\r\n` line endings; run `dotnet format --fix-whitespace` after.
5. **Rebuild after each category** — stop cascade early
6. **Don't stop at the main `.csproj`** — test projects and demo projects also need fixing

## Related Skills

- `hermes-operations` — Load for the overall quality-chain workflow (diagnose → plan → execute → review)
- `deviation-analysis-refactoring` — Use when starting from an existing analysis document
- `blazor-razor-authoring` — Razor component authoring patterns (RenderFragment, @ref, lifecycle)
