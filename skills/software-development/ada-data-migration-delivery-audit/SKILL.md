---
name: ada-data-migration-delivery-audit
description: 'Verify data migration refactor delivery (DB forensics).'
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [audit, data-migration, verification, database, refactor-review]
    related_skills: [ada-project-audit, ada-code-quality-analysis, ada-dotnet-verification]
---

# Data Migration Delivery Audit

Verify — with direct evidence, never from commit messages, tool docstrings, or
plan checkboxes — that a refactor whose core promise is "data moved from
source A (XML/files/legacy store) to source B (DB)" actually delivered.
Typical triggers: "DB 唯一数据源", "one-time migration tool", "delete old
files after migration", post-refactor delivery review before merge.

**Discipline:** read-only. Inspect the real DB, real files, real git history.
Every finding must carry file:line (or DB table/row) evidence. Do not run
full test suites that a parallel process may be executing; targeted read-only
queries and small directed checks are fine.

## When to Use

- Reviewing a multi-phase refactor that ends with "delete the old data source"
- Verifying a ContentImporter / migration tool actually populated the target DB
- Checking that fallback/degradation semantics survive the migration
- Confirming recovery paths still exist after deletion commits

## The Evidence Checklist

1. **Inspect the real DB read-only.**
   `sqlite3.connect('file:<db>?mode=ro', uri=True)` — list tables, row counts
   per migrated table, and `__EFMigrationsHistory`. Migration applied ≠ data
   migrated: full schema + 0 rows = "migration ran, import never completed".

2. **Timestamp forensics.** Import tools usually stamp `CreatedAt = now`;
   preserved-data imports keep original dates. Rows with original dates mean a
   different (earlier) tool wrote them — the new importer never completed on
   this DB. This overturns "the importer imported the posts" assumptions.

3. **CWD-relative connection-string trap.** `Data Source=portfolio.db`
   (relative) silently creates a fresh empty DB wherever the tool is invoked.
   `search_files(target='files')` for stray DB files at repo root / tool
   directories. Flag tools that
   don't print the absolute DB path and lack per-table progress logging.

4. **Idempotency claims vs implementation.** An "idempotent" importer that
   unconditionally `Add()`s (no upsert key) duplicates on re-run — verify each
   table's upsert path. Check ordering columns: all-0 `SortOrder` means display
   order silently relies on rowid/insertion order.

5. **Deleted-source recovery check.** `git show <del-commit>^:<path>` on
   deleted files: what did the old source contain, and what recovery path
   remains (e.g. XML deleted → only the JSON snapshot survives)?

6. **Empty-table behavior of consumers.** What do API/frontend do when
   migrated tables are EMPTY?
   - `200 + empty DTO` is treated as SUCCESS by fallback chains → static
     fallback never triggers → pages render blank despite good snapshots.
   - Snapshot exporters that export empty tables OVERWRITE good static
     fallback data on the next sync (empty profile/projects into the repo).
   Both silently destroy content visibility. Recommend empty-table guards
   (refuse export / warn) and treat "API healthy but empty" as a distinct
   state from "API down".

7. **Derived-field re-render data loss.** Migration writes
   `BodyHtml=HTML, BodyMarkdown=""`, but the admin save endpoint re-renders
   `BodyHtml = Render(BodyMarkdown ?? "")` unconditionally → ANY admin edit
   wipes the body permanently. Trace the save path's handling of empty source
   fields before signing off.

8. **Process gates & phase mapping.** Per-phase-commit workflows: `git status`
   dirty files are a gate violation worth reporting. Map commits to plan
   phases via `git log --stat`; check deletion and doc-cleanup phases
   explicitly — stale docs still describing the retired format are the classic
   last-phase miss.

## Output Format

Structured review (Chinese or user's language):
- `verdict` (可行 / 需修改 / 不可行)
- `verified_points` — evidence list with file:line / DB facts
- `issues` — severity (高/中/低) + basis
- `risks` — recovery, deployment, CI-gate risks
- `recommendations` — file-level fixes

Verdict = 需修改 when: the migration end state is unverified/unmet, or a
data-loss path exists (even latent, e.g. only triggered for importer-imported
rows), or process gates were violated before merge.

## Pitfalls

- Believing the importer ran because the target tables have a schema (the
  migration did run — the import didn't).
- Treating "posts present" as "migration complete" — check ALL migrated
  tables, not the one with data.
- Missing the latent data-loss bug because current rows happen to carry the
  safe values (markdown present today; importer-imported rows won't be).
- Reporting "importer swallowed exceptions" without reading the code — the
  more common failure is "importer never ran here / ran against the wrong
  CWD-relative DB", which leaves the same empty-table signature.

## Reference

本技能无独立 references：DB 取证式交付审计协议（只读纪律、直查取证、门禁重跑、回归语义）均在正文。
