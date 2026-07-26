---
name: ada-dotnet-engineering-refactoring
description: "Use when performing engineering-grade .NET refactoring — domain primitives, orchestrator extraction, command base classes, public API stabilization, and Blazor component patterns. Upgrades codebase quality beyond superficial cleanup."
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
