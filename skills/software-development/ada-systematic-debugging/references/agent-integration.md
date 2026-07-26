# Agent Integration

Use this reference when systematic debugging spans multiple components, needs sub-agent investigation, or needs to coordinate with test-driven development.

## Investigation Tools

Use these Hermes tools during Phase 1:

- `search_files`: find error strings, trace function calls, locate patterns.
- `read_file`: read source code with line numbers for precise analysis.
- `terminal`: run tests, check git history, reproduce bugs.
- `web_search` / `web_extract`: research current error messages, library docs, and official references when local evidence is insufficient.

## Delegated Investigation

For complex multi-component debugging, dispatch investigation subagents. The subagent investigates only; it does not fix.

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging:
    1. Read the error message carefully.
    2. Reproduce the issue.
    3. Trace the data flow to find root cause.
    4. Report findings with file evidence.
    5. Do not fix.

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=["terminal", "file"],
)
```

Main-agent responsibilities after delegation:

1. Verify subagent evidence directly.
2. Re-run any command the subagent claims passed if it affects the final answer.
3. Choose one root-cause hypothesis to test next.
4. Do not merge speculative fixes from multiple subagents.

## With Test-Driven Development

When fixing bugs:

1. Write a test that reproduces the bug (RED).
2. Debug systematically to find root cause.
3. Fix the root cause (GREEN).
4. The test proves the fix and prevents regression.

Use `ada-test-driven-development` when the user asks for TDD, regression coverage, or test-first work.
