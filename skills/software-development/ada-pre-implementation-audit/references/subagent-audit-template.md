# Subagent Audit Dispatch Template

Use this template with `delegate_task` batch mode for pre-implementation codebase audits.
The 3-agent fan-out covers Domain/Results/Interop, Services/Commands/Dto, and Components/CSS in parallel.

## Template

```python
delegate_task(tasks=[
    {
        "goal": "Audit Domain, Results, and Interop source files. Read every file, summarize what each implements, note any SRS requirement references, TODOs, or incomplete markers. Also read the matching test files and report test coverage per class.",
        "context": """Repo root: {REPO_ROOT}

Files to read (Domain):
{list domain/*.cs files with absolute paths}

Files to read (Results):
{list Results/*.cs}

Files to read (Interop):
{list Interop/*.cs + ClientScripts/*.ts}

Test files:
{list matching test files}

For each file, report:
1. Key types/classes and their purpose
2. SRS requirements referenced (REQ-F-XXX comments)
3. Any TODO, FIXME, or incomplete markers
4. Test coverage: which test files cover this code
"""
    },
    {
        "goal": "Audit Services, Commands, and Dto source files. Read every file, summarize what each implements, note any SRS requirement references, TODOs, or incomplete markers. Also read the matching test files and report test coverage per class.",
        "context": """Repo root: {REPO_ROOT}

Files to read (Services):
{list Services/*.cs}

Files to read (Commands):
{list Services/Commands/*.cs}

Files to read (Dto):
{list Services/Dto/*.cs}

Test files:
{list matching test files}

For each file, report:
1. Key types/interfaces and their purpose
2. SRS requirements referenced
3. Any TODO/FIXME markers
4. Test coverage
"""
    },
    {
        "goal": "Audit all Razor components, CSS, and csproj files. Read every file, summarize what each component implements, note SRS requirement references, JS interop calls, TODOs, or incomplete markers. Report test coverage per component.",
        "context": """Repo root: {REPO_ROOT}

Files to read (Components):
{list Components/*.razor}

Files to read (static assets):
{list CSS, csproj}

Test files:
{list component test files}

For each file, report:
1. Key components and their purpose
2. SRS features implemented (REQ-F-XXX references)
3. JS interop calls, event handlers, lifecycle methods
4. Any TODO/FIXME markers
5. Test coverage
"""
    }
])
```

## Concrete example: Lib audit (2026-07-24)

Used 30 files per agent. Aggregate findings in ~3 minutes. Key discoveries:
- `REQ-F-149` (ToolBar spatial sections): **Already implemented** in `ToolBar.razor:11-100`, traceability wrong
- `REQ-F-023` (Auto-hide unification): **Already implemented**, tests coverage exists
- `REQ-F-140` (ToolBar Entry drag): Cross-region drag **already works** via existing infrastructure
- Traceability appendices: 50% of test files missing, line counts stale by 60%

Original plan had 4 phases → revised to 1 docs fix + 2 code additions.

## Post-audit cross-check

After subagents return, build a discrepancy table:

```markdown
| REQ | Traceability says | Code actually | Delta |
|-----|------------------|---------------|:---:|
| F-149 | Not Implemented | ToolBar.razor:11-100 AC1-AC5 | Remove from plan |
| F-023 | Not Implemented | PanelOps + ToolBar flyout complete | Remove from plan |
```

Present this to the user before writing the revised plan.
