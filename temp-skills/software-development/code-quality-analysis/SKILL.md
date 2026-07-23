---
name: code-quality-analysis
description: "Multi-dimension code quality audit producing a structured report (complexity, duplication, dead code, security, dependencies, test coverage, code standards). Language-agnostic methodology with per-language analysis scripts."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-quality, static-analysis, audit, metrics, report]
    related_skills: [code-efficiency-review, requesting-code-review, codebase-inspection, code-quality-pipeline]
---

# Code Quality Analysis

Comprehensive multi-dimension code quality audit of a source tree, producing a
structured markdown report with severity ratings and prioritized recommendations.

**Core principle:** Automate what's automatable (line counts, CC estimation, pattern
matching), then manually read the hot spots. Never fabricate findings — every issue
in the report must be traceable to a specific file:line.

## When to Use

- User asks for "code quality analysis", "quality audit", or "static analysis report"
- User wants a multi-dimension assessment: complexity, duplication, dead code,
  security, dependencies, test coverage, code standards
- User specifies output to a `docs/reports/code-quality-YYYY-MM-DD.md` style path
- Before a major refactor to establish baseline metrics

**Skip for:** single-file reviews, efficiency-only audits (use `code-efficiency-review`),
pre-commit verification (use `requesting-code-review`), LOC-only queries (use `codebase-inspection`).

## Step 1 — Scope and file discovery

Determine the target directory. List all source files excluding generated code:

```bash
find <src_dir> -name '*.cs' -o -name '*.ts' -o -name '*.py' | grep -v '/obj/' | grep -v '/bin/'
```

Count lines per file to identify the largest files that warrant deep reading:
```bash
find <src_dir> -name '*.cs' -exec wc -l {} + | sort -rn
```

Also discover test files, config files, and non-code assets that affect the report.

## Step 2 — Automated static analysis (execute_code Python)

Run a Python script via `execute_code` that performs:

### 2.1 Complexity
- Estimate cyclomatic complexity: count `if`, `else if`, `case`, `for`, `foreach`,
  `while`, `catch`, `&&`, `||`, `? :` in each method body
- Extract method boundaries with brace-counting
- Flag methods with CC > 10, lines > 50
- Flag classes with total lines > 300
- Measure nesting depth per file

### 2.2 Duplication
- Sliding window (5-line blocks) across all source files
- Skip whitespace/brace-only blocks and comments
- Count identical block occurrences — report blocks appearing 3+ times

### 2.3 Dead code
- Private methods not called within their file (heuristic)
- Unused event handlers (defined in callback class but never subscribed)
- Legacy fallback paths marked "fall back to legacy"

### 2.4 Security
- Regex scan for hardcoded secrets: `password|secret|apikey|token|connectionString`
- Unsafe HTML rendering: `MarkupString|InnerHtml|Html.Raw`
- Insecure deserialization: `BinaryFormatter|SoapFormatter|NetDataContractSerializer`
- Empty catch blocks and generic `catch (Exception)`

### 2.5 Dependencies
- Extract class definitions and cross-reference usage across files
- Detect file-level circular dependencies (A depends on B and B depends on A)
- Check project manifest for dependency count and version status

### 2.6 Test coverage
- Count `[Fact]`/`[Theory]` attributes (or equivalent per language)
- Map test class names to source class names via substring matching
- List source files with no matching test file

### 2.7 Code standards
- Naming convention checks (private fields without `_` prefix, public fields)
- Error handling patterns (try-finally without catch, swallowed exceptions)
- XML doc comment coverage on public members

See `references/csharp-analysis-script.py` for the reference implementation.

## Step 3 — Deep reading of hot spots

After automated analysis identifies high-risk areas, manually `read_file` the
following:

1. **All methods with CC > 15**: understand why they're complex
2. **All classes > 300 lines**: assess if they need splitting
3. **All files with depth > 4**: verify the nesting is justified
4. **Security findings**: confirm false positives vs real issues
5. **Untested critical files**: verify they actually lack coverage

This step is essential — static analysis gives metrics but not context.

## Step 4 — Generate the report

Write to the user-specified path (typically `docs/reports/code-quality-YYYY-MM-DD.md`).

### Report structure

```
# Project Name Code Quality Report

生成日期 / analysis date, scope, line count, methodology

## 整体评分 / Overall Score
Table: dimension | grade | one-line summary

## 1–7: Per-dimension sections
Each dimension:
  - Score badge (A-F)
  - Top N issues table: # | location | detail | severity emoji
  - Key recommendation

## 改进优先级 / Improvement Priorities
Four-tier priority table:
  🔴 P0 — immediate fix (crashes, data loss, security)
  🟠 P1 — this iteration (major complexity, missing test coverage)
  🟡 P2 — next iteration (refactoring, error handling)
  🟢 P3 — continuous improvement (naming, minor duplication)

## 附录 / Appendices
  Appendix A — File statistics table (per-directory file + line counts, verified by os.walk)
  Appendix B — Terminology glossary (bilingual if applicable)
  Appendix C — 复核记录 (verification record — see Step 5)
```

### Severity color key
- 🔴 严重 (Critical): correctness bugs, security vulnerabilities, data loss
- 🟠 高 (High): major complexity, missing coverage on critical paths, Dispose issues
- 🟡 中 (Medium): code duplication, deep nesting, generic exception catches
- 🟢 低 (Low): minor duplication, untested simple data classes, naming nits

### Grading scale
| Grade | Criteria |
|-------|----------|
| A | No critical/high issues, minor duplication only, good coverage |
| B | 1-3 high issues, manageable tech debt |
| C | 4+ high issues or 1 critical, significant gaps |
| D | Multiple critical issues, major coverage gaps |
| F | Security vulnerabilities, build failures, systemic issues |

## Step 5 — Independent verification (复核)

After generating the report, dispatch **3 parallel sub-agents** via `delegate_task`
to independently verify the report. This catches fabrication, missed findings, and
statistical errors before the user sees them.

### The three verification agents

| Agent | Task | Checks |
|-------|------|--------|
| **Agent 1 — Truth** | Randomly sample 5 Critical/High issues | Read actual source, confirm each issue is real (not fabricated). Mark each: ✅ 确认 / ⚠️ 部分正确 / ❌ 误报 |
| **Agent 2 — Completeness** | Global security scan across ALL source files (.cs, .ts, .razor, .json, .csproj) | Search for: `eval()`, hardcoded secrets, weak crypto (MD5/SHA1/DES/RC4), XSS patterns (`MarkupString`, `Html.Raw`, `document.write`), path traversal, insecure deserialization. Report any missed findings. |
| **Agent 3 — Consistency** | Verify all statistics are self-consistent | File counts, total line counts, test count breakdowns. Random spot-check 3+ file line counts. Cross-check Appendix A per-directory breakdown against `os.walk` traversal. |

### Verification workflow

1. Dispatch all 3 agents in a single `delegate_task` call (they run in parallel)
2. When results return:
   - Fix any discrepant findings directly in the report
   - Add **Appendix C: 复核记录** summarizing all 3 verification results
   - If Agent 2 failed (auth, timeout), re-run the security scan locally via `execute_code`
3. Follow the "复核最多两轮" rule from `hermes-operations`:
   - Errors < 5% → fix directly, no second round needed
   - Errors 5–15% → fix affected sections only, verify those sections in second round
   - Errors > 15% → don't patch the report; re-scan from Step 2

### Appendix C format

```markdown
## 附录 C: 复核记录

**复核日期**: YYYY-MM-DD
**复核方式**: 3 个独立子 agent 并行复核 + 主 agent 补充扫描

### C.1 问题真实性验证（Agent 1 — 抽样 N 项）
Table: # | 问题 | 结论 | 证据

### C.2 安全漏洞遗漏扫描（Agent 2）
Table: 检查项 | 扫描范围 | 结果

### C.3 统计自洽性验证（Agent 3）
Table: 验证项 | 结论 | 详情

### C.4 复核总结
Table: 维度 | 结果
```

## Step 6 — Implementation plan (optional follow-up)

If the user wants to act on the Top 5 P0/P1 items, produce a separate plan document
at `docs/reports/code-quality-plan-YYYY-MM-DD.md`:

### Plan structure

```
Phase A: <P0 issue> — scope, approach, before/after code, estimated time
Phase B: <P1 #1> — ...
...
Phase E: <P1 #5> — ...

Implementation order: ASCII dependency graph
Acceptance criteria: per-phase build + test pass conditions
Risk & rollback: what could break, how to revert (each phase independently committable)
```

### Phase template

Each phase should include:
- **文件**: exact file path(s)
- **问题**: 1-line description
- **方案**: concrete code change (before/after)
- **影响范围**: what else is touched
- **验证**: build + specific test commands
- **预估耗时**: realistic estimate in minutes/hours

## Step 7 — Post-fix execution and report update (when fixes are applied)

If the user acts on the implementation plan (Step 6), after completing the fixes:

### 7.1 Verify all changes
- Run `dotnet build` (or equivalent) — must be 0 errors
- Run the full test suite — must be 0 failures, no regression
- If applicable, check specific invariants (e.g., `_operationLock.Wait` count dropped from 14→2)

### 7.2 Dispatch post-fix review agent
Dispatch a **single sub-agent** via `delegate_task` to verify the fix status of every
issue in the original report against the current source code:

```
Goal: 复核所有报告中问题的修复状态。逐一读源码验证。
Context: 原始报告路径、已知修复了哪些项 (Phase A-E)、需检查所有15个问题。
```

Output: table with #, risk level, current status (✅/⏳/⬜), evidence (file:line).

### 7.3 Update the original report
Patch the original quality report (NOT a new file) to reflect post-fix reality:
- **整体评分**: Add a "修复后" column showing per-dimension improvement
- **Section 6 (测试覆盖)**: Update test counts, mark newly-covered files
- **Section 9 (改进优先级)**: Add "状态" column (✅/⬜/⏳) to every issue row
- **新附录**: Add Appendix D with change manifest, build/test results, key metric deltas
- **Section 6.2**: Cross out files that are now tested (~~strikethrough~~ → ✅)

### 7.4 Produce standalone review document (optional)
If the review agent produces detailed findings, write them to
`docs/reports/code-quality-fix-review-YYYY-MM-DD.md` for traceability.

## Pitfalls

- **Fabricating findings**: Never list an issue you didn't actually find in the code.
  If a scan comes up empty for a dimension, say so rather than inventing plausible issues.
- **False positives in method extraction**: Regex-based method detection is heuristic.
  Always verify high-CC findings by reading the actual code.
- **Dependency cycle false positives**: File-level dependency detection catches
  legitimate patterns (e.g., factory pattern). Mark expected cycles as "by design".
- **Test coverage mapping**: Test class name matching (FooTests → Foo) is a heuristic.
  Some files are tested indirectly through integration tests.
- **Language-specific regex**: The analysis scripts need per-language patterns.
  See `references/csharp-analysis-script.py` for C#; adapt for Python, TypeScript, etc.
- **Generated code exclusion**: Always exclude `obj/`, `bin/`, `node_modules/`,
  `AssemblyInfo.cs`, and `GlobalUsings.g.cs` from analysis.
- **Appendix A per-directory accuracy**: Compute per-directory file/line counts with
  actual `os.walk` traversal, not manual estimation. A report where per-directory
  subtotals don't add up to the verified total undermines trust. Never type directory
  stats from memory — always run the counting script and paste the output.
- **Security scan completeness**: Always run a second-pass security scan across ALL
  source file types (.cs, .ts, .razor, .json, .csproj, .css, .html) after the
  automated analysis. The initial analysis scripts typically only scan .cs files
  and may miss patterns in non-C# source types.
- **Automated script-based code transformation risks**: When applying refactorings
  (especially lock-pattern deduplication or method extraction), prefer manual
  `patch` calls over `execute_code` Python scripts that rewrite files. Automated
  rewrites can produce silently broken code (e.g., recursive helper methods that
  call themselves instead of the lock, partial transformations missing
  value-returning methods). Always `read_file` the result and verify with
  `dotnet build` immediately. If a script-produced file has bugs, revert via
  git and redo with manual patches.
- **Catch-clause ordering**: `TaskCanceledException` inherits from
  `OperationCanceledException`. When replacing generic `catch (Exception)` with
  specific types, order `catch (TaskCanceledException)` BEFORE
  `catch (OperationCanceledException)`, or omit the subclass entirely since the
  base class already catches it. The C# compiler enforces this (CS0160).
