# .NET Engineering-Grade Refactoring — Workflow

Full workflow detail moved from the parent SKILL.md.

## From Audit to Engineering-Grade

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

At the end of a multi-phase refactoring plan, follow `references/refactoring-closeout.md`: audit stale status markers in traceability/design docs, record independent-review results, mark historical analysis docs as baseline snapshots instead of current-state truth, and answer with a two-layer distinction between "the document-required repair set is complete" and "the whole SRS backlog is complete."
