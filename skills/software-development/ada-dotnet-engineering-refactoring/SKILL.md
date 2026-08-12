---
name: ada-dotnet-engineering-refactoring
description: "Use when refactoring C#/.NET/Blazor code beyond superficial cleanup: domain primitives, value-type migrations, orchestrator extraction, command base classes, public API stabilization, or Razor component architecture. For non-.NET projects, use ada-engineering-refactoring."
version: 1.3.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [dotnet, refactoring, engineering, csharp, blazor, patterns]
    related_skills: [ada-code-quality-analysis, ada-requesting-code-review, ada-refactoring-lifecycle]
---

# .NET Engineering-Grade Refactoring

Guide for elevating a .NET codebase from "works" to "human-maintainable engineering
quality" — the level where a new developer can read, extend, and trust the code.

## Overview

This skill provides the concrete .NET/C#/Blazor patterns that implement the engineering-grade refactoring philosophy. Every pattern includes documented trade-offs: clamp vs. throw for constrained types, manual `IEquatable<T>` for .NET 6 compatibility, implicit/explicit conversion operators, JSON serialization via custom `JsonConverter<T>`, and `InternalsVisibleTo` for test access. The workflow section specifies the build-verify-format loop per phase and cross-platform CI considerations.

Full code examples for all patterns live in [references/dotnet-refactoring-patterns.md](references/dotnet-refactoring-patterns.md); detailed workflow steps in [references/dotnet-refactoring-workflow.md](references/dotnet-refactoring-workflow.md).

## When to Use

Use when:
- The user asks for "工程级" (engineering-grade) refactoring of a .NET/C#/Blazor project
- The user rejects superficial changes and demands architectural depth («不要嫌麻烦，要改就重构地改»)
- The project needs to be handed off to human successors for long-term maintenance
- A code quality audit has identified systemic issues across type safety, naming, and structure
- Multi-phase refactoring needs a proven phase-ordering strategy to minimize rework

Do **not** use for: simple bug fixes, single-file cleanup, pre-commit formatting, or one-off mechanical dedup.

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

See **[references/dotnet-refactoring-patterns.md](references/dotnet-refactoring-patterns.md)** for full code examples and key decisions for each pattern.

1. **Domain Primitive Value Types** — Replace bare `string`/`double` with types that enforce constraints at construction (Ratio, PanelId, TabId). Clamp, don't throw. Manual `IEquatable<T>` for net6.0. DTO mapping: `model.Id.Value` on export, `new PanelId(dto.Id)` on import.
2. **Orchestrator → Helper Decomposition** — When a class exceeds ~400 lines, extract mechanical helpers. Helpers take orchestrator reference (`_context`); lazily created. Self-owned fields move to helper class.
3. **Command Base Class** — Extract `_executed` guard logic from 4+ ICommand implementations. `GuardSingleExecution()`, `HasBeenExecuted`, `ResetExecutionGuard()`.
4. **API Naming: Hide Implementation Details** — Remove implementation words from public API names (e.g. `ExecuteLocked` → `Execute`).
5. **Merge Overloads into a Shared Core** — Two public overloads, one private core. Use `ExecuteCore<int>` with dummy return for Action overload. Narrow catch: `OperationCanceledException` only.
6. **Blazor Component Extraction** — Extract repeated template blocks. Use `RegisterElementRef` callback for ElementReference passthrough (net6.0 doesn't support `@ref` lambdas). Always add `@key` in parent templates.
7. **Razor Named Handler Methods** — Replace inline lambdas with method references for zero allocations and testability. Keep lambdas only when capturing loop variables or render-time values.
8. **Blazor Layout Visibility** — Collapse empty side dock columns using a domain predicate. See [references/blazor-side-dock-visibility.md](references/blazor-side-dock-visibility.md) for full implementation.

## Workflow

See **[references/dotnet-refactoring-workflow.md](references/dotnet-refactoring-workflow.md)** for full detail including ad-hoc verification scripts and closeout procedures.

1. Run `code-quality-analysis` → 7-dimension report with P0-P3 priorities
2. Present multi-phase plan; start with **value types** (widest ripple effect)
3. Each phase: `dotnet build` → fix errors → `dotnet test` → `dotnet format`
4. Phase order:
   - Phase 1: Domain primitives (Ratio, PanelId, TabId)
   - Phase 2: API naming + catch tightening (UndoStack)
   - Phase 3: Orchestrator extraction (TabOperations from LayoutContext)
   - Phase 4: Base class extraction (CommandBase)
   - Phase 5: Dead field removal
   - Phase 6: Template extraction (Blazor subcomponents)

**Late-phase:** For public API stabilization, see [references/public-api-stabilization.md](references/public-api-stabilization.md). For closeout/documentation status, see [references/refactoring-closeout.md](references/refactoring-closeout.md).

## Common Pitfalls

- **Starting with the wrong phase.** Phase order matters — value types have the widest ripple effect and must come first. Starting with API naming or template extraction forces rework when value types change signatures.
- **Using `patch(replace_all=true)` on method definitions.** When a file both defines and calls a method, `replace_all` corrupts the definitions. Use sed on call sites only, or rewrite the entire file.
- **Python `write_text` on Windows:** Introduces `\r\n`. Always follow batch file edits with `dotnet format` to restore project line endings.
- **`record struct` on net6.0:** Not available. Use manual `readonly struct` with `IEquatable<T>`.
- **`search_files` on MSYS2 paths:** The `search_files` tool can fail on Windows paths inside MSYS2. Use `terminal` grep instead.
- **Blazor `@ref` lambda on net6.0:** Not supported. Use callback parameter pattern.
- **Forgetting `@key` on extracted Blazor subcomponents.** Without `@key`, Blazor reuses component instances and stale `_registered` flags prevent JS interop re-registration. Use string-identity tracking instead of boolean flags.
- **Moving `_recentTabIds` to helper:** If orchestrator methods call field methods directly, add a public method on the helper (e.g. `TabOps.ClearRecentHistory()`).
- **Fixing only the main `.csproj`.** Value-type migrations cascade through test projects, demo apps, and Razor files. Run `dotnet build` on the entire solution and grep remaining errors before declaring done.
- **Skipping `dotnet format` after batch edits.** Always follow batch file edits with `dotnet format` to restore project line endings.
- **Losing callback fields during model construction.** When `OpenTabRequest` carries optional callbacks, every non-null field must be explicitly assigned to the `TabModel` during construction. Grep for `request\.` in the construction method to verify completeness.

- **Batch test repair after value type migration:** See [references/value-type-test-repair-patterns.md](references/value-type-test-repair-patterns.md) for full regex catalog and edge-case checklist. Use Python regex for bulk fixes (constructor calls, method calls, property assignments), then manual fixes for edge cases (`Assert.Equal`, variable type changes, lambda captures). Always finish with `dotnet build` → grep remaining errors → targeted `patch` calls → `dotnet test`.
- **Value-type migration mechanical edits with `sed`:** For bulk renames across 5+ files, use targeted `sed -i` per property rename — faster and safer than `patch`. After sed, `dotnet build` to catch missed edges.
- **delegate_task for parallel test repair:** Fan out to 2 sub-agents (tests + demo app) for the same mechanical fix pattern across multiple files. Saves ~5 rounds of manual tool calls.
- **InternalsVisibleTo for testing internal classes:** Add `<InternalsVisibleTo Include="TestProjectName" />` to the source `.csproj`. Prefer this over making implementation classes `public` prematurely.
- **Independent-review hardening checklist:** See [references/atlas-phase17-19-review-lessons.md](references/atlas-phase17-19-review-lessons.md) for reviewer-discovered pitfalls around client-visible `ErrorBoundary` details, behavioral lifecycle tests, render-identity hashes, DI boundaries, and Windows ad-hoc verification evidence.

## God-Class Partial File Splitting

When a single class exceeds ~1000 lines and has several independent change
reasons, split it into a thin shell plus `ClassName.{Domain}.cs` **partial
files by responsibility**. Pure file organization — members moved verbatim,
**zero behavior or public API change**, tests stay green, risk ≈ 0. Phase 2
(extracting real collaborator classes) is a separate, optional, riskier step;
do not bundle them.

**When to use**: class >1000 lines with multiple change domains; reviewers
call it a "god class" but the public API is frozen; immediate readability
without touching behavior; strong test coverage exists to prove the move was
lossless. **Not for**: large single-responsibility classes (splitting just
thins lines, not coupling).

**File layout**: main file keeps base class + interfaces
(`public sealed partial class BigClass : ComponentBase, IAsyncDisposable`);
partial files declare `public sealed partial class BigClass` (no base, no
interfaces) — `sealed` must match everywhere. Each partial file carries its
own `using` block (copy the main file's full block; unused usings harmless).
Nested private classes move with the member that precedes them.

**Script-based splitting** (manual cut/paste of 50+ methods invites errors;
keep the script in the repo so the split is reproducible). Member-name regex
pitfalls that broke naive parsers:
1. **Exclude initializers from method detection.** `Guid.NewGuid()` and
   `= new()` must NOT count as method declarations:
   `(?<![.=\w{])(?!new\b)([A-Za-z_]\w*)\s*(?:<[^()]*>)?\s*\(`.
2. **Attribute-only lines (`[Inject]`) belong to the NEXT member.** Buffer
   them and prepend to the following member.
3. **Comment-only lines (`/// <inheritdoc />`) belong to the NEXT member.**
   Otherwise CS1591 (missing XML doc) fires on public members.
4. **Multi-line field declarations** must stay together; keep member-name
   parsing single-line.
5. **LF normalization on Windows.** Python's `write_text` silently converts
   `\n` back to `\r\n` — use `open(path, "w", encoding="utf-8", newline="\n")`
   and normalize input with `.replace("\r\n", "\n")` first.
6. **Member order:** emit partial members in source order, never sorted.

**Verification**: every moved method's definition line appears exactly once
across shell + partials (POSIX `grep -E` does NOT support `(?:...)` — use a
capturing group `(<[^()]*>)?`); `dotnet build` / `dotnet test` unchanged /
`dotnet format --verify-no-changes`; render-sequence check if the class
contains render methods; browser smoke for Blazor components. Merge-conflict
note: two PRs adding the same tool script report an **add/add conflict** —
resolve by taking the newer, more general version (`git checkout --theirs`).

## Model Invariant Enforcement (.NET stateful models)

When the same state rule is enforced on SOME mutation paths but diverges on a
sibling path (e.g. one operation collapses an empty group but a sibling does
not), promote the rule to a model invariant enforced at ONE construction
boundary — do not patch the sibling path.

**Core principle**: **Only auto-correct conditions that are ALWAYS true. Never
normalize away a state that is a legal user action.** The classic failure:
adding a defensive second rule to a normalizer ("non-empty → expanded") breaks
a real feature — collapsing a NON-EMPTY group is a legal user action. The
invariant must enforce ONLY the always-true direction; re-expansion on content
entry stays a planner concern.

**Design checklist**:
1. Audit every mutation path that produces or consumes the state; present the
   divergence table to the user — the divergent sibling path justifies the
   invariant.
2. Confirm decision points with the user before coding: should the operation
   that *sets* the now-illegal state fail fast (typed error) or be silently
   normalized? Does loading/materializing from a definition get normalized too?
3. Put auto-correction at ONE construction boundary (the immutable
   snapshot/model constructor), not in each planner. Make it idempotent:
   return the original instance when nothing changed, so compliant commits pay
   zero allocation.
4. Pair normalization with fail-fast rejection where the state is
   user-settable — otherwise the operation silently commits a state the
   invariant immediately rewrites.
5. Write a per-path test matrix that would have failed BEFORE the invariant
   and passes after: every operation path, materialization, and persistence
   round-trip.

**Verification**: new invariant tests + existing suites green; existing tests
that asserted PRE-invariant behavior may need fixture changes (make the
fixture non-illegal and comment why); `dotnet format --verify-no-changes` and
`git diff --check` clean.

## Verification Checklist

- [ ] `dotnet build` succeeds across the entire solution (all `.csproj` files — src, tests, demo)
- [ ] `dotnet test` passes with no regressions — compare pass/fail counts before and after
- [ ] `dotnet format --verify-no-changes` reports zero formatting changes
- [ ] All domain primitives are applied uniformly: no bare `string` IDs or bare `double` values remain where strong types were introduced
- [ ] Extracted subcomponents have `@key` in parent templates and use callback patterns (not `@ref` lambdas) for ElementReference passthrough
- [ ] `git diff --check` shows no whitespace violations

## Related Skills

- `code-quality-analysis` — Generates the 7-dimension report that drives the refactoring plan
- `systematic-refactoring` — Multi-phase refactoring workflow from analysis documents
- `requesting-code-review` — Pre-commit verification pipeline after each phase
