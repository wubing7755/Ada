# Doc Cleanup Pattern — Concrete Decision Examples

From the 2026-07-24 Lib cleanup pass. Use these as a calibration reference.

## Deleted (3 files)

| File | Why deleted |
|------|------------|
| `docs/guides/ai-agent.md` | Single-line redirect to `AGENTS.md`. Empty shell, zero content. |
| `docs/reports/code-quality-2026-07-20.md` | Intermediate draft. `code-quality-2026-07-22-full.md` is the final version with all findings. |
| `docs/reports/code-quality-2026-07-22.md` | Intermediate draft. The `-full` variant contains the same audit plus full detail. |

## Archived to `docs/archive/` (4 files)

| File | Archive path | Why archived |
|------|-------------|-------------|
| `docs/deviation-analysis/architecture-debt-analysis-2026-07-23.md` | `archive/deviation-analysis/` | "Before" baseline: the 9 deviations that drove Phase 15-20 refactoring. All deviations now resolved. |
| `docs/deviation-analysis/srs-coverage-matrix.md` | `archive/deviation-analysis/` | Historical coverage snapshot (2026-07-20). Replaced by formal `requirements-traceability.md`. |
| `docs/refactoring/phase7-9-plan.md` | `archive/refactoring/` | 40KB completed plan. Documents engineering standards and type system design decisions. |
| `docs/reports/code-quality-optimization-plan-2026-07-21.md` | `archive/reports/` | Action plan with P0/P1 tracking. Useful for tracing which issues were addressed. |

## Kept Active (7 files)

| File | Why kept |
|------|---------|
| `docs/README.md` | Documentation entry point |
| `docs/SRS.md` | Software Requirements Specification (152 requirements) |
| `docs/requirements-traceability.md` | Active traceability matrix |
| `docs/adr/0001-*.md` | Architecture Decision Record |
| `docs/refactoring/architecture-refactoring-design-2026-07-23.md` | Current active refactoring design |
| `docs/refactoring/bottom-dock-auto-collapse-design-2026-07-23.md` | Active design (independent review pending) |
| `docs/reports/code-quality-2026-07-22-full.md` | Most recent final quality report |

## README Update Pattern

After cleanup, update `docs/README.md` to:

1. Remove entries for deleted files
2. Add an "Archive" section with one-line descriptions:

```markdown
## Archive

Historical snapshots preserved for decision traceability — no longer active:

| Document | Description |
|---|---|
| [archive/deviation-analysis/architecture-debt-analysis-*.md](...) | SRS deviation baseline (pre-refactoring) |
| [archive/refactoring/phase7-9-plan.md](...) | Phase 7–9 refactoring plan (completed) |
```

3. Keep archived entries to one line — the description answers "why would I ever look at this?"
