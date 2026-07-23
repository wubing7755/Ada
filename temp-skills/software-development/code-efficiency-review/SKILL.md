---
name: code-efficiency-review
description: "Efficiency-focused code review: spot redundant work, N+1, missed concurrency, hot-path bloat, TOCTOU races, memory leaks, excessive reads, and silent failures. Language-agnostic checklist with actionable fix recommendations."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, efficiency, performance, audit, optimization]
    related_skills: [requesting-code-review, systematic-debugging, systematic-refactoring]
---

# Efficiency-Focused Code Review

Audit a diff or codebase for efficiency and resource-management issues: wasted
computation, unnecessary allocations, missed parallelism, hot-path bloat,
concurrency bugs, and memory leaks. Every finding includes a concrete fix
recommendation and is graded by confidence and risk.

**Core principle:** Don't guess. Read every changed file in full, trace cross-file
dependencies (interop layers, domain models, service registrations), and validate
against actual execution paths — not just surface-level diff reading.

## When to Use

- User asks to "review for efficiency", "audit performance", "check for waste"
- After a feature lands with 3+ changed files and the user wants a second pass
- Before merging a PR that touches hot-path code (startup, render loops, event handlers)
- User flags "N+1", "memory leak", "TOCTOU", or "silent failure" as explicit concerns

**Skip for:** style-only changes, documentation, config tweaks, or when user says
"just check for bugs, not efficiency."

**This skill vs `requesting-code-review`:** `requesting-code-review` checks
security, logic errors, and test regressions before commit. This skill targets
waste — things that work correctly but do too much work, allocate too often,
or leak over time.

## Step 1 — Get the full picture

Don't stop at the diff. Read the files the diff touches so you understand
surrounding context, call sites, and cross-file dependencies.

```bash
git diff HEAD --stat          # list changed files
git diff HEAD                  # full diff
```

For each changed source file (skip docs/tests on first pass), read it in full:

```
read_file(path=<file>)
```

Also read any files called by the changed code — interop wrappers, domain
models, service registrations. Missing a cross-file dependency is the most
common cause of false-negative findings (a leak hides in the JS interop layer,
a hot call chain is obscured by layering).

## Step 2 — Walk the 8-category checklist

For each changed file and each new/changed code block, check:

### 2.1 Unnecessary repeated computation / IO / API calls

- Same value computed multiple times in the same scope?
- JS interop calls (`InvokeVoidAsync`, `Import`) that could be batched or cached?
- `Task.Delay` + `CancellationTokenSource` allocations that fire on every event?
- `GroupBy().ToList()`, `Where().ToList()` on every render cycle?
- String interpolation in `Debug.WriteLine` (or equivalent) that's compiled
  into Release builds? (Check `[Conditional("DEBUG")]` — if present, safe.)

### 2.2 N+1 access patterns

- Loop body calls `FirstOrDefault()` / `Find()` on the same collection each
  iteration, or on a collection that's already being iterated in the template?
- Each mouse/hover event re-scans a linear collection?
- Inner query that could be satisfied by a pre-built lookup (dictionary)?

### 2.3 Missed concurrency (independent operations run serially)

- Multiple independent JS interop calls or I/O operations in `OnAfterRenderAsync`
  that could be `Task.WhenAll`?
- Independent `ElementReference` registrations done sequentially?

(Blazor WASM note: true parallelism is limited, but independent async operations
that don't depend on each other's results CAN be concurrent with `WhenAll`.)

### 2.4 Hot-path bloat (startup / render path heavy operations)

- `OnAfterRenderAsync(firstRender=true)` doing heavy work?
- Object allocations in render tree (`.ToList()`, `new List<>()`) that could be
  cached or computed once in `OnParametersSet`?
- DOM node count explosion from wrapper divs?

### 2.5 TOCTOU races

- Shared mutable field read, then used after `await` without re-checking?
- `CancellationTokenSource` field replaced between `.Cancel()` and `.Token` read?
- Blazor WASM is single-threaded (no true TOCTOU), but `await` re-enters the
  dispatcher — other events can fire in between. Verify CTS-based cancellation
  handles this correctly.

### 2.6 Memory issues (unbounded growth, missing cleanup, event handler leaks)

- Dictionaries that only grow (`dict[key] = value` without corresponding remove)?
- `DotNetObjectReference` never `.Dispose()`d?
- JS event listeners registered via interop but never unregistered on dispose?
- `CancellationTokenSource` never disposed?
- Event handler subscriptions (`+=`) without matching `-=` in `Dispose()`?

### 2.7 Excessive reads

- Reading the same property / field / collection multiple times in a method when
  once would suffice?
- Finding the same object (`FirstOrDefault`, `Find`) when the caller already
  had a reference?

### 2.8 Silent failures (empty catch, swallowed errors)

- `catch { }` with no logging?
- `catch (OperationCanceledException) { }` without comment? (CTS cancellation
  IS a valid expected path — it just needs documentation.)
- Error paths that `return` without notifying callers or logging?
- Direct state mutation bypassing the service layer (no event, no undo, no lock)?

## Step 3 — Output format

One finding per section. Format:

```
### 🔴/🟡/🟢 N. Short title

**File**: `path/file.ext:line-range`
**Problem**: What's wrong — be specific about the waste/risk.
**Fix**: Concrete code or architectural change. Include before/after if helpful.
**Confidence**: HIGH | MEDIUM | LOW
**Risk**: HIGH | MEDIUM | LOW
```

Severity color key:
- 🔴 HIGH risk: state inconsistency, data loss, crashes, or correctness bugs
- 🟡 MEDIUM risk: allocations/churn on frequent paths, missing cleanup
- 🟢 LOW risk: minor waste, pre-existing issues, negligible allocations

## Step 4 — Summary table

End with a prioritized table:

| # | Severity | Problem | Fix |
|---|:---:|------|-----|
| 1 | 🔴 | Short summary | One-line fix description |

## Pitfalls

- **Reviewing only the diff, not the whole file.** A changed line might look
  fine in isolation but be called from a hot loop 50 lines above. Always read
  the full file.
- **Missing cross-file dependencies.** The interop layer, the domain model's
  query method, the service registration — efficiency issues often span files.
- **Flagging pre-existing issues as new.** Diff → blame: if the pattern existed
  before the change and the change doesn't make it worse, mark it "pre-existing,
  out of scope" rather than flagging it.
- **Over-flagging small-N linear scans.** `FirstOrDefault` on a collection of
  5 items is fine. Flag it only if N can grow large or the call is on a hot path.
- **Assuming Blazor WASM is multi-threaded.** No true TOCTOU between synchronous
  statements, but `await` yields to the dispatcher. Status checks after `await`
  must handle interleaved events.
- **Confusing `[Conditional("DEBUG")]` methods with runtime waste.** `Debug.WriteLine`
  is compiled OUT in Release builds — the call site disappears entirely.
- **CTS replace-without-dispose.** When debounce/delay patterns use a
  `CancellationTokenSource` field that gets reassigned (`_cts = new()`), the
  old CTS must be disposed first. Cancelling alone isn't enough — CTS
  implements `IDisposable` and holds timer resources. Grep for
  `= new CancellationTokenSource()` on fields — each reassignment without a
  prior `.Dispose()` is a leak.
- **Event handler leak via captured-this lambdas.** In Blazor components, event
  subscriptions (`+=`) with lambdas that capture `this` in `OnInitialized` must
  be unsubscribed (`-=`) in `Dispose`. When the event source is an
  externally-injected service/context, the component leaks even after disposal.
  *Always pair `+=` with `-=` in Blazor lifecycle; named methods make this auditable.*
- **`.ToList()` in Blazor computed properties.** Properties called from Razor
  markup run on every render cycle. If they allocate (`ToList`, `new List`,
  `Select`) and the markup calls them multiple times, the cost multiplies. Use
  `ToLookup`/`ToDictionary` for grouped access, cache in `OnParametersSet`.
- **Helper-collection staleness after reset.** When a `Reset()`/`Clear()` method
  zeroes out primary state, check whether secondary collections (recent-item
  lists, caches, MRU buffers) are also cleared — stale entries can cause
  incorrect behavior in downstream strategy methods.

## References

- `references/atlas-review-example.md` — Real output from a Blazor WASM review
  (2026-07-20). Concrete example of report structure, severity grading, and
  fix recommendations. Includes pitfalls specific to Blazor WASM `await`
  re-entrancy and JS interop listener lifecycle.
