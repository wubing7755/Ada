# Agent-Assisted Development: Detailed Workflows

> Extracted from ada-agent-assisted-development SKILL.md for progressive disclosure.

## §5 — Architecture Upgrade Workflow

**Triggers:** User says: "refactor to engineering standards", "upgrade architecture", "apply X pattern project-wide", "migrate to value types"

### 4-Phase progressive refactoring:

**Phase 1: Audit.** Read codebase → identify patterns → produce audit report with specific violations and fix counts.
- Ask user: "Do you want example fixes first, or audit the whole project directly?"

**Phase 2: Fix Foundation (in the reference implementation).** Apply first wave on representative code.
- Use delegate_task batch to fix multiple violation categories simultaneously
- Each subagent fixes one category (e.g., mutable structs, null handling)
- Build + test after each batch

**Phase 3: Pattern Extraction.** Extract Phase 2 fixes into reusable patterns/scripts.
- Create reference files with before/after snippets
- Document common pitfalls and edge cases
- If Pattern 1 used manual fixes, write a migration script for Pattern 2

**Phase 4: Full Rollout.** Apply extracted patterns to remaining codebase.
- Use delegate_task for parallel category-fix agents
- String-replacement for bulk renames (replace_all=True), not manual line-by-line
- Build + test after each category
- Produce final report: before/after violation counts, remaining issues

**Evolution cycle:** If Phase 4 uncovers new patterns, loop back to Phase 3.

## §6 — SRS Coverage Analysis

**Triggers:** User says: "audit SRS coverage", "which requirements are implemented?", "traceability gap", "check REQ-F coverage"

**Capabilities:**
1. Parse SRS to extract all REQ-F/NF IDs with their Acceptance Criteria
2. Audit codebase (via subagents) to find which REQs are implemented
3. Cross-reference against existing traceability matrix
4. Produce gap report: implemented vs claimed vs missing

**Efficiency pattern:** Parallel subagent reading — each subagent reads one source file, extracts REQ references, reports back.

**Output format:**
| REQ ID | Title | Priority | SRS Status | Code Evidence | Verdict |
|---|---|---|---|---|---|
| REQ-F-001 | Layout | P0 | ✅ | LayoutManager.cs:45 | IMPLEMENTED |
| REQ-F-099 | Export | P1 | ✅ | — | NOT FOUND |

**Subagent per sub-region:** Split the codebase using the SRS's own section structure — e.g., REQ-F-001~050 to Agent A, REQ-F-051~100 to Agent B.

## §7 — Code Quality Report

**Triggers:** User says: "run quality analysis", "code audit", "produce quality report"

### Step 1: Statistical Baseline
Run per-language analysis scripts (e.g., `csharp-analysis-script.py` for .NET). Count: total files, LOC, method counts, cyclomatic complexity.

### Step 2: Pattern Audit (parallel subagents)
Subagent 1 → Complexity hotspots (methods > 50 LOC)
Subagent 2 → Duplication audit (copy-paste across files)
Subagent 3 → Null-safety audit (missing null checks)

### Step 3: Report Assembly
Merge subagent findings into structured report:
- Executive summary with PASS/FAIL counts
- Per-category breakdown with file:line references
- Severity classification: Critical / Major / Minor / Info

### Step 4: Verification
Run `ada-code-quality-report-verification` to independently confirm each claim before delivery.

### Key efficiency rules
- **Parallel subagents for independent audits** — complexity, duplication, null-safety run simultaneously
- **Use delegate_task, not serial terminal calls** — 3 subagents = 3x speed
- **Provide each subagent the exact analysis script path** — don't make them search for tools
- **Set a 5-minute timeout per subagent** — if stuck, return partial results
