---
name: ada-code-quality-report-verification
description: "Independently verify claims in a code quality report by reading source code, running reproducibility tools, and classifying each issue as confirmed/partially correct/false positive. For single-agent or sub-agent deployment."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-quality, verification, audit, report-validation]
    related_skills: [ada-code-quality-analysis, ada-code-efficiency-review, requesting-code-review, ada-code-quality-pipeline]
---

# Code Quality Report Verification

Independently verify claims in a pre-existing code quality report by
spot-checking issues or performing a full statistical self-consistency
audit against actual source code. Also covers independent fail-closed
reviews of an implementation phase against its SRS/design acceptance
criteria. Ensures the report or phase-completion claim doesn't contain
fabricated findings, arithmetic errors, stale statistics, unverified
semantics, or unsupported pass/fail verdicts before the user acts on its
recommendations.

**Core principle:** Never trust the report's text — trust the source code.
Every claim must survive a read of the actual file:line it references.
When a tool result is cited (e.g. `dotnet format` output), re-run the tool
to confirm. When the report claims N files and M lines, count them yourself.

## Overview

This skill independently validates claims made in a pre-existing code quality report
by reading actual source code, re-running reproducibility tools, and classifying each
issue as confirmed (✅), partially correct (⚠️), or false positive (❌). It supports
three verification modes: Mode A (issue sampling — quick sanity check on 5 issues),
Mode B (full statistical self-consistency audit — exhaustive 7-point verification),
and Mode C (implementation phase pass/fail review — fail-closed verification against
SRS/design acceptance criteria). The skill accumulates known verification heuristics
from real-world sessions, covering common failure modes like coverage miscounts,
instance count inaccuracies, duplicate code understatements, and header-vs-appendix
contradictions.

## When to Use

- User provides a quality report and asks you to verify it ("独立复核", "抽样验证")
- User asks "are these issues real" about findings in an existing report
- Before acting on a report's priority list (P0/P1 items) — validate they exist first
- During code review when the reviewer suspects a report may have inaccuracies
- User asks for an independent pass/fail review of a completed implementation phase
  ("Phase C passed?", "fail-closed review", "can this phase be considered passed")
  against SRS/design acceptance criteria and verification output
- **Statistical self-consistency audit**: user asks to verify "all 统计数字是否自洽"
  (all statistics are self-consistent) — full 7-point verification, not sampling

**Do NOT use for:** Generating a new quality report (use `code-quality-analysis`),
reviewing a single PR diff (use `requesting-code-review`), or efficiency-only audits
(use `code-efficiency-review`).

## Core Principles for Statistical Audits

These are the non-negotiable rules that prevent blind spots in verification:

1. **Count files before counting lines.** Always do `find | wc -l` first, then
   `find -exec cat {} + | wc -l`. A file count mismatch (e.g. report says 47, actual 50)
   traces the line count error to missing files.
2. **Exclude obj/ in all find commands.** Reports count source files; build artifacts
   under `obj/` inflate counts. Always add `-not -path "*/obj/*"`.
3. **Verify the report against itself first.** Add up every subdirectory line count
   from the report's own table. If the sum doesn't equal the report's claimed total,
   that's an internal inconsistency before you even touch the source.
4. **Trust your counts, not the report's categories.** The report may put `_Imports.razor`
   in one directory while physically it's in another. Your `find` output is the ground
   truth — reconcile categories afterwards.
5. **Cross-reference test coverage by grepping, not by reading the report's table.**
   A report may list DockPanelModel as "uncovered" while `DomainModelTests.cs` has
   a `DockPanelModelTests` class with 6 [Fact] tests. Aggregated test files are the
   most common cause of coverage miscounts.

## Three Verification Modes

### Mode A: Issue Sampling (fast check)
Randomly pick **5 issues** from the report's P0/P1/P2 lists, ensure at least 2 are
Critical/🔴 severity, probe uniformly across report sections. Use when the user
generally trusts the report and just wants a sanity check.

### Mode B: Full Statistical Self-Consistency Audit (exhaustive)
Use when the user explicitly asks for "独立复核" or "统计自洽性验证". Verify
every quantitative claim in the report. The standard protocol covers these 7 items:

| # | Check | How |
|---|-------|-----|
| 1 | Source file count & total lines | `find src -type f \( -name "*.cs" -o -name "*.razor" ... \) -not -path "*/obj/*"` |
| 2 | Test file count & total lines | Same for tests/, excluding obj/ |
| 3 | Coverage percentage & class list | Count source classes, verify each "uncovered" class has no tests, check aggregated test files |
| 4 | Subdirectory breakdown sums | Verify each subdir's file+line counts, then verify they sum to report's total |
| 5 | Test method counts | Count [Fact] + [Theory] attributes; verify against report's total test count |
| 6 | Random spot-check of individual files | Pick 3 files across different directories, `wc -l` each |
| 7 | Cross-report consistency | If report cites a prior report's line count, verify prior report's own numbers |

**Output format**: For each of the 7 items, output **✅ 一致** or **❌ 不一致**
with actual value vs reported value. End with a summary table.

### Mode C: Implementation Phase Pass/Fail Review (fail-closed)
Use when the user asks whether a named implementation phase can be considered
passed, especially when they provide or imply an SRS/design acceptance contract.
The goal is not to write a broad code-quality report; it is to decide whether the
phase's stated semantics and verification criteria are actually satisfied.

Required checks:

1. **Read acceptance criteria first**: inspect SRS, design/refactoring plan,
   traceability matrix, and any phase checklist before judging source code.
2. **Inspect the changed source and adjacent call paths**: verify state transitions,
   events, undo/redo semantics, and edge-case handling against the acceptance criteria.
3. **Inspect focused tests**: tests must assert the required semantics directly,
   not just exercise the path. For stateful commands, look for source state,
   target state, event behavior, and undo/redo restoration.
4. **Run a focused test slice** for the reviewed behavior, then run the appropriate
   broader gate (`dotnet build`, full tests, `dotnet format`, `git diff --check`, etc.).
5. **Fail closed**: return `passed:false` if a required semantic branch is untested,
   a verification command fails, or implementation behavior is ambiguous enough that
   a user would be unsafe to treat the phase as complete.

Recommended compact output when requested:

```js
{
  passed: true | false,
  security_concerns: [],
  logic_errors: [],
  test_gaps: [],
  evidence: [],
  recommended_fixes: []
}
```

See `references/phase-pass-fail-review-example.md` for a concise Atlas MovePanel
review pattern and command set.

## Verification Methodology

### For each sampled issue or statistic, do:

1. **Navigate to the exact file:line** the report claims
   - If the report says `LayoutContext.cs:275-407`, read those lines
   - If the report says a range like `UndoStack.cs:19-42`, read the entire file for context
   - On Windows, when `search_files` fails, fall back to `find` + `grep` via terminal

2. **Read the actual source code** — do not rely on memory or the report's description

3. **Run reproducibility tools** for tool-based claims:
   - Formatting claims: `dotnet format --verify-no-changes` (capture exit code + output)
   - Pattern counts: `grep -c` or `rg -c` to independently count occurrences
   - Test coverage: `grep -rl "ClassName" tests/` to find test files referencing the class
   - Report's claim vs tool output: if they differ, the report may be stale or wrong
   - File counts: `find <dir> -type f -name "*.cs" -not -path "*/obj/*" | wc -l`
   - Line counts: `find <dir> -type f -name "*.cs" -not -path "*/obj/*" -exec cat {} + | wc -l`
   - Subdirectory line totals: run per-directory, then add them up manually to verify internal consistency

4. **Cross-reference test coverage manually**:
   - List all test `.cs` files (excluding obj/)
   - For each "uncovered" source class, grep all test files for class references
   - Watch out for **aggregated test files** (e.g. `DomainModelTests.cs` that contains
     multiple test classes like `DockPanelModelTests`, `TabModelTests`) — these are
     easily missed by automated coverage mappers
   - Also check **result test files**: `DockResultTests.cs` may test `DockResult` which
     the report may not even list as a source class

5. **For each issue or statistic, assign one of three outcomes**:

### Outcome Classification

| Outcome | Meaning | When to use |
|---------|---------|-------------|
| ✅ 确认存在 | The report was accurate | Description matches source, counts are correct, severity is appropriate |
| ⚠️ 部分正确 | The core issue exists but details are wrong | Wrong count (22→20), missing instances (5→7), wrong line range, misstated pattern description, wrong severity grade |
| ❌ 误报 | The issue does not exist in the source | Claimed method doesn't exist, tool output not reproducible, or class is actually tested when report says it isn't |

A "部分正确" verdict must state both:
- What the report **got right** (the underlying problem is real)
- What the report **got wrong** (the specific detail that's inaccurate)

## Known Verification Heuristics

Accumulated from real-world verification sessions:

### Coverage miscounts
- Reports may miss aggregated test files (`DomainModelTests.cs`) that cover multiple
  classes. Always grep test files explicitly rather than trusting the report's table.
- A report claiming "22/30 zero coverage" may actually be 20/30 — 2 classes in the
  list may have tests they didn't detect.

### Instance count inaccuracies
- Reports may claim N instances when the actual code has N+M. Always count with grep.
- Reports may include lines in a range that don't match the described pattern
  (e.g. a method called `ExecuteLocked` that does NOT contain `NotifyLayoutChanged`
  in a list of methods said to use "ExecuteLocked + Notify" pattern).

### Duplicate code extent understatements
- Reports may say "X lines duplicate" based on a quick glance, but the actual overlap
  may be larger (entire try/catch/finally blocks, not just 4 lines).
- Always read both methods end-to-end; count repeated lines yourself.

### Non-reproducible formatting errors
- `dotnet format --verify-no-changes` results may differ between report generation
  and verification time. If formatting errors don't reproduce, note this as
  "may have been fixed" rather than calling it a false positive.
- Run the exact command from the report context (full project, not single file).

## Report Format

For each of the 5 sampled issues, output:

```
### N️⃣ <Issue Title>

**<Outcome badge>**

- **证据**: file:line, relevant code snippet, tool output
- **偏差** (if ⚠️): what the report got wrong and why
- **结论**: one-line verdict
```

End with a summary table:

```
### Summary

| # | Issue | Severity | Outcome | Core Deviation |
|---|-------|----------|---------|----------------|
| 1 | P0-1: ... | 🔴 | ⚠️ | Report claimed 22 zero-coverage; actual 20 |
```

## Common Pitfalls

- **Don't trust the report's table without reading source**: The report may list
  "8/30 covered" when the actual count is 10/30 because it missed aggregated tests.
  Or it may claim 30 source classes when the codebase has 45 — silently omitting
  interfaces, enums, internal DTOs, and nested event arg classes.
- **Don't just verify existence — verify accuracy**: An issue can exist but the
  report can be wrong about its details. That's ⚠️, not ✅.
- **Don't call it a false positive when it's just stale**: If `dotnet format` no
  longer shows the error, the issue was probably fixed between report and verification.
  Note it as "cannot reproduce, likely fixed" — that's ⚠️, not ❌.
- **Don't invent new issues**: Your job is to verify what the report says, not to
  find additional problems. If you discover new issues, note them briefly but don't
  add them to the verdict — that's scope creep.
- **Don't skip validation because the report "feels right"**: Always read the code.
  Even a 95% accurate report has subtle inaccuracies that matter for priority decisions.
- **Watch the header claim vs the detail table**: A report may say "48 个源文件"
  in the header but list 47 in the appendix table. The header and body can contradict.
  Always use the most detailed breakdown as your starting point and flag the header
  as a separate potential inconsistency.
- **Don't assume subdirectory line numbers in the report add up**: A report claiming
  5,510 total lines may have subdirectory breakdowns summing to 5,566. Always add up
  the report's own sub-totals first before comparing to source.
- **Beware of the "class counting methodology" gap**: A report counts 30 "源类" while
  your grep finds 45+ public/internal classes. The report may be excluding enums,
  interfaces, nested DTOs, event args, and generic type specializations. Understand
  the report's inclusion criteria — if it's not documented, flag the methodology gap
  in your verdict rather than calling the count flat wrong.
- **When spot-checking individual files, prefer files the report gives exact line
  numbers for** (e.g. Appendix A per-file listings). If the report only provides
  subdirectory totals, note that spot-checking can only validate at the subdirectory
  level, not per-file.
- **Verify the previous report's own numbers** when the current report cites it.
  Don't trust the current report's characterization of the previous report's line
  count — read the previous report's appendix yourself.
- **For phase pass/fail reviews, don't stop at green tests**: green tests are only
  evidence after you have read the SRS/design acceptance criteria and confirmed the
  tests assert the required semantics. A phase with passing tests but missing direct
  assertions for a required branch should be reported as a test gap or `passed:false`
  depending on severity.
- **Keep requested JSON-like verdicts compact**: when the user asks for fields such
  as `passed`, `security_concerns`, `logic_errors`, `test_gaps`, `evidence`, and
  `recommended_fixes`, return that shape directly with evidence-dense bullets rather
  than a long narrative.

## Verification Checklist

- [ ] Every sampled issue was verified against actual source code at the claimed file:line (never from memory or the report's description alone)
- [ ] All quantitative claims (file count, line count, test count, coverage percentage) were independently counted with `find`/`wc -l`/`grep` (not taken from the report)
- [ ] Each sampled issue was assigned one of three outcomes (✅ confirmed / ⚠️ partially correct / ❌ false positive) with concrete evidence
- [ ] The report's own sub-totals were summed and checked for internal consistency before comparing to independently collected source data
- [ ] For Mode C (pass/fail) reviews: SRS/design acceptance criteria were read first, and tests were verified to assert required semantics (not just exercise the path)

## Reference Files

- `references/session-verification-example.md` — Full worked example from an actual
  verification session (Atlas code quality report). Contains 5 verified issues with
  real file:line evidence, tool output, and deviation classification. Use this as
  a template for the expected level of detail when sampling issues (Mode A).
- `references/full-statistical-audit-example.md` — Complete 7-point statistical
  self-consistency audit of the same report, tracing every quantitative claim
  to ground truth. Use this as a template when doing full statistical verification
  (Mode B). Includes per-item ✅/❌/⚠️ verdicts with actual-vs-reported values.
- `references/phase-pass-fail-review-example.md` — Compact pattern for independent
  fail-closed implementation phase reviews (Mode C), including SRS/design anchors,
  focused/full verification commands, and the JSON-like verdict shape.
