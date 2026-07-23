# XDocker SRS Optimization — Session Learnings

This reference captures the specific patterns and decisions from the XDocker SRS optimization session (2026-07-15).

## Applied Patterns

### Upfront Architecture
- Moved from inline ASCII tree (§3.1) to a dedicated §1.3 "系统架构" with both visual layout and hierarchy tree
- §1.4 "数据模型" with ER diagram showing Layout→Panel→Tab→ContentIdentifier relationships
- §1.7 "空间概念" defining three distinct containers: Editor Tab, Dock Panel, ToolBar Entry

### Hierarchy Flattening
- Eliminated "Content Area" and "Main Area" intermediate layers
- All Dock regions became direct children of Work Area
- Referenced VS Code Workbench model as authority

### Stack Model (vs Swap)
- Changed from "面板互换" to "面板移动+堆叠"
- Key insight: VS Code doesn't swap panels — it stacks them in regions
- This eliminated REQ-F-063 (swap splitter adaptation) entirely
- Removed DUPLICATE_REGION_NAME error code (stacking makes duplicate region names expected behavior)

### Tab/Panel Separation
- Renamed §3.4 from "内容渲染与页签管理" to "Editor 标签页管理"
- Added §3.4.1 "Editor Tab 拖拽停靠" — all tab-level drag operations
- Split old §3.5 into:
  - §3.4.1: Editor Tab drag (REQ-F-052~057, 065~078)
  - §3.5: Dock Panel move (REQ-F-061, 062, 064, 079)
- Fixed REQ-F-066: "目标面板的激活页签" → "目标视图中的激活标签页"

### Requirement Fixes
- Removed AC3 from REQ-F-004 (runtime duplicate region name — dead code)
- Removed "36px" from REQ-F-012 (implementation detail in SRS)
- Added REQ-F-026 AC3 (Bottom Dock region visibility behavior)
- Used emoji priority symbols consistently (🔴🟡🟢) in all requirement headers

### Navigation Aids
- §2.2 "功能导航" — role-based quick-finder table
- Section indexes with "你想...→看这条" tables for each §3 subsection
- §5.1 Role-based requirement summary
- Appendix B: Deferred requirements
- Appendix C: Traceability matrix
- Appendix D: Change log

## Key Design Decisions

1. **VS Code as authority**: All architectural decisions referenced VS Code Workbench as the canonical design
2. **AC vs new requirement**: When a behavior is a natural consequence of an existing constraint, extend the existing requirement with a new AC rather than creating a standalone requirement
3. **Region name semantics**: In a stacking model, region names are location identifiers, not 1:1 bindings — multiple panels can share the same region name
4. **LT/RT entries represent panels, not regions**: One ToolBar entry per Dock Panel, not per region
