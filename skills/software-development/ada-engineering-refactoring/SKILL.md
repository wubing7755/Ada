---
name: ada-engineering-refactoring
description: 'Use when an agent is doing architecture-level refactoring outside .NET-specific workflows: type-system constraints, interface protocols, orchestration/implementation separation, and whole-project consistency. For C#/.NET/Blazor refactors, route through ada-refactoring-lifecycle to ada-dotnet-engineering-refactoring.'
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [refactoring, architecture, engineering-quality, dotnet, blazor]
    related_skills: [ada-refactoring-lifecycle]
---

# Engineering-Grade Refactoring

Architectural-level code refactoring for entire projects. Not mechanical dedup — this is the skill for when the user says "Microsoft engineering level" or "this doesn't meet my standard."

## Overview

This skill defines a disciplined, architecture-first approach to whole-project refactoring. It replaces ad-hoc cleanup with six engineering quality gates: type-system constraints, intent-revealing API names, interface-based dependencies, orchestration/implementation separation, whole-project consistency, and Razor-first parity. The workflow emphasizes discovery, planning, user approval, phased execution, and a final consistency pass — ensuring the result is a maintainable codebase a new developer can pick up and extend naturally.

Unlike mechanical dedup (extract-method, extract-helper), this skill targets the structural choices that separate "it works" from "it is engineered." Detailed procedures for value-type migrations and Blazor component extraction are in the [references/](references/) directory.

## When to Use

- User explicitly rejects mechanical refactoring (extract-method, extract-helper) as insufficient
- User says "I want Microsoft-level code quality" or "engineering-grade"
- User asks for "whole-project consistency" — not one-file-at-a-time fixes
- User describes the goal as "a project a human can pick up and extend naturally"
- After a code quality report identified 5+ items, and the first mechanical fix was rejected

**Skip for**: single-file cleanup, pre-commit verification, bug fixes, small scoped changes.


Don't use for: .NET/C#/Blazor projects — use stack-specific refactoring patterns with domain primitives and orchestrator extraction. Single-file cleanup — use `patch` or parallel code cleanup workflows.

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
Template duplication (>2 identical blocks) → extract child component. Inline C# `@{}` declarations → computed properties in `@code`. `OnInitialized` doing 3+ things → named helper methods. See [references/blazor-patterns.md](references/blazor-patterns.md) for detailed patterns.

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

## Common Pitfalls

- **Applying changes file-by-file instead of whole-project.** Engineering-grade refactoring requires whole-project consistency (Gate 5). Introducing a `Ratio` type in one file but leaving bare `double` in others creates inconsistency worse than the original state.
- **Skipping the plan-and-approve step.** Jumping straight to implementation after the user rejects mechanical changes wastes effort. Always write the plan, present it, and get explicit approval before coding.
- **Forgetting test/demo projects.** Value-type migrations ripple beyond `src/` — test projects, demo apps, and Razor components all need the same fixes. Stop only when `dotnet build` passes across the entire solution. See [references/value-type-migration.md](references/value-type-migration.md) for the full cascade spread order.
- **Using `throw` instead of `clamp` for constrained value types.** Throwing on out-of-range construction breaks test setup and intermediate calculations. Default to silent clamping; reserve throws for API boundary inputs. See [references/value-type-migration.md#clamp-vs-throw-choosing-the-right-behavior](references/value-type-migration.md#clamp-vs-throw-choosing-the-right-behavior).
- **Computing arithmetic after mutating a source value.** When redistributing values (e.g., resize two panels), capture the original sum before mutating any variable. See [references/value-type-migration.md](references/value-type-migration.md) for the critical bug pattern.
- **Relying on `record struct` on .NET 6.** Use manual `readonly struct` with explicit `IEquatable<T>`, `Equals`, `GetHashCode`, and operator overloads. See [references/value-type-migration.md#value-type-implementation-struct-not-record-struct](references/value-type-migration.md#value-type-implementation-struct-not-record-struct).
- **Forgetting to add `@key` on Blazor components that re-register.** Without `@key`, Blazor reuses component instances across parameter changes, keeping stale `_registered` boolean flags that prevent re-registration.

## Verification Checklist

- [ ] All six quality gates pass on every modified file (re-read each file explicitly — do not assume)
- [ ] `dotnet build` succeeds across the entire solution (src + tests + demo)
- [ ] `dotnet test` passes with no regressions (compare test count before/after)
- [ ] `dotnet format --verify-no-changes` reports zero formatting violations
- [ ] Whole-project consistency confirmed: any new pattern (value type, naming convention, extracted helper) is applied uniformly — no partial migrations left behind
- [ ] `.razor` files match `.cs` quality standards (no inline `@{}` declarations, no repeated template blocks, no untestable lambdas)

## Reference Documents

Detailed procedures extracted from this skill for maintainability:

| Reference | Contents |
|-----------|----------|
| [references/value-type-migration.md](references/value-type-migration.md) | Full value-type migration cascade: pattern rules, spread order, Razor pitfalls, arithmetic gaps, clamp-vs-throw, error codes, test adjustments, struct implementation, JSON serialization, bulk strategy |
| [references/value-type-migration-atlas.md](references/value-type-migration-atlas.md) | Atlas project case study (2026-07-22): 108-error cascade record, actual execution order, file manifest, delegate_task lessons learned |
| [references/blazor-patterns.md](references/blazor-patterns.md) | Blazor-specific refactoring: template dedup → child components, inline declarations → computed properties, lifecycle methods → named methods, common pitfalls |
| [references/refactoring-plan-template.md](references/refactoring-plan-template.md) | Plan document template for Phase 0 (Chinese) |
| [references/quality-checklist.md](references/quality-checklist.md) | Per-phase quality verification checklist (Chinese) |

## Related Skills

- `hermes-operations` — Load for the overall quality-chain workflow (diagnose → plan → execute → review)
- `deviation-analysis-refactoring` — Use when starting from an existing analysis document
- `blazor-razor-authoring` — Razor component authoring patterns (RenderFragment, @ref, lifecycle)
