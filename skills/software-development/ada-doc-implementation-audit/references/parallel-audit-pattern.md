# Parallel 3-Subagent Audit Pattern

Common dispatch pattern for source-code audits that split the codebase into three module clusters and deploy parallel subagents. Used by `ada-doc-implementation-audit` and `ada-pre-implementation-audit`.

## Module Split

| Agent | Module | Typical Files |
|-------|--------|---------------|
| **Agent 1** | Domain + Results + Interop | All `.cs` in Domain/, Results/, Interop/ + `ClientScripts/index.ts` + matching test files |
| **Agent 2** | Services + Commands + Dto | All `.cs` in Services/ (including Abstractions/, Commands/, Dto/) + matching test files |
| **Agent 3** | Components + Demo | All `.razor` in Components/ + `.css` + `.csproj` + matching test files |

## Dispatch Template

```python
delegate_task(tasks=[
    {
        "goal": "Audit Domain/Results/Interop files — read every .cs and .ts file",
        "context": "Repo root: <ABSOLUTE_PATH>. Files: [list exact paths]. For each, report: key types, REQ references, TODOs, test coverage."
    },
    {
        "goal": "Audit Services/Commands/Dto files — read every .cs file",
        "context": "Repo root: <ABSOLUTE_PATH>. Files: [list exact paths]. For each, report: key types, REQ references, TODOs, test coverage."
    },
    {
        "goal": "Audit Components/Razor files — read every .razor/.css file",
        "context": "Repo root: <ABSOLUTE_PATH>. Files: [list exact paths]. For each, report: key types, REQ references, TODOs, JS interop, test coverage."
    }
])
```

## Subagent Prompt Template

```
Repo root: C:\Users\usr\source\repos\<Project>

Your job: Read every source file in these directories and produce a structured
implementation report for each.

Files to read: [list exact paths]

Test files to read: [list exact paths]

For each file, report:
1. File path and line count
2. Key types/classes defined
3. SRS requirements referenced (look for comments mentioning REQ-F-XXX)
4. Any TODO, FIXME, or incomplete markers
5. Test coverage: which test files and methods cover this code

Output format: structured markdown sections per file.
Do NOT modify any files.
```

## Prerequisites

- Run `find` to get the complete file list BEFORE dispatching subagents
- Provide the **absolute repo path** — subagents have no context about project structure
- Every subagent gets the exact file list — never rely on subagent discovery

## Pitfalls

- **Partial audits**: This pattern ONLY works when ALL source and test files are read. If a subagent times out, re-dispatch with a smaller file set.
- **Subagent output truncation**: Large summaries may be truncated. Always use the full output file path from the subagent result for detailed review.
- **Stale file lists**: File counts may differ between the `find` discovery phase and subagent execution. Re-run `find` if the gap exceeds a few minutes.
