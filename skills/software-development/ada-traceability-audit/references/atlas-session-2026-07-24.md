# Atlas Audit Session — 2026-07-24

## Discovered Discrepancies

### Missing REQ in traceability
- **REQ-F-149** (ToolBar 空间分区布局) existed in SRS at line 1295 but was absent from traceability
- Root cause: requirement added to SRS after traceability was last regenerated
- Fix: added row to §3.5, recalculated stats (152 total)

### Wrong status labels
- **REQ-F-149**: traceability said "Not Implemented" → actually fully implemented in `ToolBar.razor:11-100`
- **REQ-F-023**: traceability said "Not Implemented" → actually tested (flyout + AutoHidden toggle in `PanelOperations` + `ToolBar.razor`)
- Root cause: Phase completed but traceability never updated

### Stale appendixes
- **Appendix A**: listed 10 test files / 93 methods → actual: 23+ files / 199 tests
- **Appendix B**: missing 18 implementation files (`DockVisibilityPlan.cs`, `LayoutVisibility.cs`, `ContentHost.razor`, `DockDropScaffold.razor`, `DockRegionHost.razor`, `AsyncDebouncer.cs`, `CommandHistory.cs`, etc.)
- **Line counts**: 4 component files had "—" instead of actual line numbers
- **Total lines**: claimed 3,120+ → actual 5,100+

### Cross-document count mismatch
- `docs/README.md` said 151 requirements → actual: 152 (after adding F-149)

### Design doc status lag
- `docs/refactoring/phase7-9-plan.md:3` said "待确认" → actual: completed (Phase 7-14 merged)

## Root Cause Analysis

The pattern across all discrepancies: traceability was generated from a historical
snapshot (`srs-coverage-matrix.md`, 2026-07-20) and never regenerated after Phase
15-20 + bottom-dock work was completed. The appendices were copied verbatim from
the snapshot without updating for new files created during those phases.

## Verification Method

Used three parallel subagents to read all source files, then cross-referenced
findings against traceability claims. The subagents read 50+ source files and
20+ test files, while the parent compared docs-to-code at the REQ level.
