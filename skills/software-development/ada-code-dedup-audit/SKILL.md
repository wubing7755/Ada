---
name: ada-code-dedup-audit
description: "Audit uncommitted/new code against the existing codebase for duplicated patterns, reinvention, and missed reuse opportunities."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, deduplication, DRY, reuse, audit, code-quality]
    related_skills: [requesting-code-review, github-code-review, ada-simplify-code]
---

# Code Deduplication / Reuse Audit

Audit uncommitted changes against the whole codebase to find where new code
reimplements existing utilities, helpers, constants, or behavioural patterns
instead of calling them. Answers the question "am I reinventing the wheel?"

## When to Use

- User says "审查本次改动中是否存在重复造轮子" or "检查是否可以复用已有代码"
- User asks "is any of this already implemented elsewhere?"
- Before merging a feature branch: catch DRY violations early
- When a new developer contributes to a mature codebase
- During refactoring preparation — identify what's already shared before extracting

**Skip for:** greenfield projects with no existing code, pure configuration changes.

## Methodology

### Phase 1 — Scope the change

```bash
git diff HEAD --stat        # what files changed
git diff HEAD -- <paths>    # the actual diff content
```

Identify every **new pattern** introduced:
- New method signatures (methods, lambdas, event handlers)
- New type usage (CancellationTokenSource, SemaphoreSlim, etc.)
- New framework calls (Task.Delay, Debug.WriteLine, Console.Write)
- New CSS class names, keyframes, magic numbers
- New control flow patterns (try/catch for specific exception types)
- New field/property initializations with non-trivial types

### Phase 2 — Pattern extraction

For each new pattern found, extract a **searchable signature**. Examples:

| New code | Search pattern |
|----------|---------------|
| `new CancellationTokenSource()` | `CancellationTokenSource` in codebase |
| `Task.Delay(300, token)` | `Task\.Delay` in codebase |
| `System.Diagnostics.Debug.WriteLine(...)` | `Debug\.Write` in codebase |
| `Panels.FirstOrDefault(p => p.Id == panelId)` | `FirstOrDefault` + the entity type |
| `.xd-toolbar-flyout` CSS class | the class name in existing CSS |
| `panel.Expand()` called from component | `\.Expand\(\)` across components |

### Phase 3 — Codebase search

Run **all searches in parallel** (they're independent):

```bash
search_files(pattern="CancellationTokenSource", target="content", path=<src>)
search_files(pattern="Task\.Delay", target="content", path=<src>)
search_files(pattern="Debug\.Write", target="content", path=<src>)
search_files(pattern="<specific-method-name>", target="content", path=<src>)
```

Also search for **shared infrastructure** that should exist but doesn't:
```bash
search_files(pattern="*Util*", target="files", path=<src>)
search_files(pattern="*Helper*", target="files", path=<src>)
search_files(pattern="*Common*", target="files", path=<src>)
search_files(pattern="*Diagnostics*", target="files", path=<src>)
```

### Phase 4 — Read and compare

For every match found in Phase 3, read the **full existing implementation**
and compare with the new code. Ask:

1. **Same signature?** — Could new code literally call the existing code?
2. **Same pattern?** — Same sequence of calls (e.g. CTS cancel → create → delay → check)?
3. **Same purpose?** — Different signature but same intent (e.g. two Debug.WriteLine methods that both log `[Atlas]` prefix)?
4. **Bypass risk?** — Does new code skip a layer that existing code goes through (lock, event dispatch, validation)?

### Phase 5 — Report

For each finding, output:

```
### Finding N: <title>
**File:** `path:line` — new code location
**Existing:** `path:line` — existing implementation that could be reused
**Issue:** <what's duplicated and why it matters>
**Suggestion:** <concrete fix — what to change, what to extract, where to put it>
**Confidence:** High | Medium | Low
**Risk:** High | Medium | Low
```

Provide a summary table at the end.

## Priority Tiers

When multiple findings exist, prioritise by:

1. **Event/lock bypassing** (HIGH risk) — new code mutates state without going through the service layer that owns locking and event notification. This causes silent data loss (e.g. auto-save won't fire).

2. **Identical pattern, different context** (MEDIUM risk) — same CancellationTokenSource + Task.Delay + try/catch pattern repeated verbatim. Extract a shared utility.

3. **Identical call, different wrapper** (LOW risk) — two methods that both end up calling `Debug.WriteLine("[Atlas] ...")`. Extract a shared helper.

4. **Component-level LINQ vs existing State queries** (VERY LOW risk) — `Panels.FirstOrDefault(p => p.Id == x)` when `State.FindDockPanel(x)` exists. Same result, minor inconsistency.

## Common Duplication Patterns to Watch For

### Debounce / delay pattern
```csharp
// If you see this pattern more than once, extract it:
_cts?.Cancel();
_cts = new CancellationTokenSource();
var token = _cts.Token;
try { await Task.Delay(N, token); if (!token.IsCancellationRequested) { /* action */ } }
catch (OperationCanceledException) { }
```

### Logging / tracing
```csharp
// If you see Debug.WriteLine with a consistent prefix format more than once:
System.Diagnostics.Debug.WriteLine($"[ProjectName] {context} failed: {reason}");
```

### Component-to-service bypass
```csharp
// Watch for components directly calling model methods when a service method exists:
panel.Expand();          // component calls model directly
// vs
Context.ExpandPanel(id); // component calls through service (lock + event)
```

### CSS magic numbers
```css
/* If new CSS uses pixel values that match existing component dimensions,
   they should use the same CSS custom properties or shared class */
.xd-new-thing { width: 240px; max-height: 400px; }
```

### Repeated string literals
```csharp
// If the same error/validation message appears ≥3 times in one file:
return DockResult.Failure(DockErrorCode.InvalidLayoutData, "Preset name is required.");
// → extract to private const string
```

### Blazor/Razor markup duplication
```html
<!-- If two components render identical button/header markup with same CSS
     classes, aria-labels, and click handlers, extract a shared sub-component -->
<button class="xd-dock-panel-autohide-btn xd-autohide-active"
        aria-label="Exit auto-hide" ...>📌</button>
<!-- Appears in both DockPanel.razor and ToolBar.razor → AutoHidePinButton.razor -->
```

## Pitfalls

- **Don't flag legitimate specialisation.** Two methods that look similar but serve different domains (e.g. debouncing UI vs debouncing persistence) may legitimately stay separate if they have different lifecycle requirements.
- **Component-local LINQ is often OK.** Blazor components receive a filtered `IReadOnlyList` and searching it with `FirstOrDefault` is cheap. Only flag when there's a semantic benefit to using the state query (consistency, future-proofing against filter changes).
- **Model-level guard + service-level guard is defensive, not duplication.** If `Collapse()` throws on AutoHidden and `CollapsePanel()` guards before calling it, both serve different consumers. Note it but don't demand a fix.

## Reference

See `references/atlas-dedup-example.md` for a real-world example from the Atlas Blazor docking library audit.
