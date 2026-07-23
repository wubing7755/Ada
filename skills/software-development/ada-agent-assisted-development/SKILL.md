---
name: ada-agent-assisted-development
description: "Structured workflows for software development with Hermes Agent — bug fixes, features, reviews, quality, architecture. Covers context management, sub-agent orchestration, and risk-tiered verification."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [workflow, development, context, subagent, review, quality, orchestration]
    related_skills: [requesting-code-review, systematic-debugging, ada-simplify-code, test-driven-development, plan]
---

# Agent-Assisted Development

Structured workflows for using Hermes Agent in software development — from bug
reports to architecture upgrades. Each workflow chains context management,
sub-agent reviews, and risk-tiered verification into an end-to-end process.

**Core principle:** Context is the scarcest resource. Never let the same
session do analysis → design → implementation → review. Fresh contexts (via
`/new` or `delegate_task`) find what stale contexts miss.

## Overview

This skill provides structured end-to-end development workflows for Hermes Agent
covering seven scenarios: bug fixes, feature implementation, code review, code quality
optimization, architecture upgrades, SRS coverage analysis, and quality reporting.
Every workflow follows a common meta-pattern — Understand → Plan → Execute → Review →
Report — with baked-in context management rules: fresh contexts between phases,
sub-agent isolation for reviews (reviewer never equals implementer), and hard limits
on auto-fix retries (max 2 cycles, then escalate). The skill also enforces context
hygiene rules (when to `/new`, `/compress`, or split sessions) and a "trust nothing"
verification discipline where every sub-agent output is a claim to be independently
confirmed by re-running commands.

## When to Use

- User asks to fix a bug, implement a feature, review code, optimize quality,
  or upgrade architecture
- User says "用子 agent 审查", "开独立 reviewer", "分阶段实施"
- User expresses frustration with agent degradation ("越改越乱", "效果越来越差")
- After a complex task completes — offer to generate a structured report

## The Meta-Pattern

All five workflows share this skeleton:

```
1. UNDERSTAND — clarify scope, read relevant docs, identify constraints
2. PLAN — output a plan for user approval (never jump to implementation)
3. EXECUTE — phased implementation, one change at a time, verify each step
4. REVIEW — delegate_task with independent sub-agent (fresh context)
5. REPORT — structured summary: what changed, review verdict, test results
```

Context management rules baked into every step:
- Between phases: use `/new` or `delegate_task` to reset context
- Review phase: ALWAYS use a sub-agent, never self-review
- Fix phase: use a separate sub-agent from the reviewer
- Long sessions: `/compress` proactively; split if >50 turns

## Workflow Selection

| User says | Workflow | Key skills loaded |
|-----------|----------|-------------------|
| "修复这个 bug" | Bug Fix (1) | systematic-debugging, test-driven-development, requesting-code-review |
| "实现 REQ-XXX" | Feature (2) | srs-driven-development, plan, srs-writing |
| "审查代码" | Code Review (3) | requesting-code-review, code-efficiency-review |
| "优化/简化代码" | Quality (4) | simplify-code, code-dedup-audit |
| "升级/重构架构" | Architecture (5) | systematic-refactoring, plan, spike, codeagent |
| "SRS 覆盖率" | SRS Coverage (6) | srs-review, srs-terminology-audit |
| "代码质量报告" | Quality Report (7) | codebase-inspection, code-efficiency-review |

## §1 — Bug Fix Workflow

```
Describe → Reproduce → Root Cause → Confirm → Fix → Sub-Agent Review → Verify → Report
```

### Step-by-step prompts (user → agent)

**1. Reproduce (before any fix):**
> "复现这个 bug，写一个最小测试用例确认失败。先别修。"
>
> Bug description: [症状 + 复现步骤 + 相关文件]

**2. Root cause:**
> "分析根因。用 systematic-debugging 追溯数据流，输出分析报告。别改代码。"

Agent must output: file:line, root cause, fix approach, risk assessment, impact scope.

**3. Fix (after user confirms):**
> "方案确认。只修复根因，不要动其他代码。改完跑测试验证。"

**4. Sub-agent review:**
> "用子 agent 独立审查这次修复。加载 requesting-code-review，输出审查报告。"

**5. Report:**
> "汇总成修复报告: Bug 描述、根因分析、修复内容、审查结果、测试结果。"

### Pitfalls

- **Skipping reproduction.** "I know the fix" without a red test = gambling.
  Always create the tight feedback loop first (`systematic-debugging` Iron Law).
- **Self-review.** The implementer reviewing its own work misses what a
  fresh context catches. Always `delegate_task` for the review phase.
- **Bundled fixes.** "While I'm here" improvements during a bug fix introduce
  unrelated risk. One change, one verify.

---

## §2 — Feature Implementation Workflow

```
Describe → SRS Align → Plan → Confirm → Phased Implement → Sub-Agent Review → Traceability → Report
```

### Step-by-step prompts (user → agent)

**1. Align with requirements:**
> "对照 docs/SRS.md 的 REQ-F-XXX，确认需求理解，检查是否和其他 REQ 冲突。
> 输出实现方案（改动文件、新增类/方法、估计改动量、实施顺序）。"

**2. Phased implementation (after user approves plan):**
> "方案确认。按顺序逐步实施，每步跑 build + test 验证。
> 先从 [Domain 模型 / 服务层 / ...] 开始。"

After each phase: verify, then proceed to next.

**3. Sub-agent review:**
> "全部实施完毕。并行开 3 个子 agent 审查: 安全性、SRS 合规性、代码质量。
> 输出合并审查报告。"

**4. Traceability update:**
> "审查通过。更新 docs/requirements-traceability.md 的状态。"

### Pitfalls

- **Implementing without SRS alignment.** Feature work without checking the
  spec leads to rework. Always read SRS + traceability matrix first.
- **One-shot implementation.** Complex features implemented in one giant diff
  are unreviewable. Phase by module boundary.

---

## §3 — Code Review Workflow

```
Diff → Static Scan → Independent Reviewer (sub-agent) → Risk Tier → Report
```

### One-line trigger

> "审查我最近的改动，用 requesting-code-review 流程。"

Agent auto-executes the full pipeline: `git diff` → grep for secrets/injection →
`delegate_task` for independent review → risk-tier (SAFE/CAREFUL/RISKY) → report.

### Fine-grained control

> "审查最近的改动，但只审 src/Atlas/Services/，SAFE 自动修，CAREFUL 和 RISKY 只报告。"

---

## §4 — Code Quality Optimization

```
Diff → 3 Parallel Reviewers (reuse / quality / efficiency) → Aggregate → Risk-Tier → Apply → Report
```

### One-line trigger

> "用 simplify-code 分析最近的改动。"

Agent spawns 3 sub-agents in parallel via `delegate_task(tasks=[...])`:

| Reviewer | Focus |
|----------|-------|
| Code Reuse | Duplicated logic, existing utilities to use instead |
| Code Quality | Redundant state, parameter sprawl, copy-paste, type safety |
| Efficiency | Redundant computation, N+1 queries, memory leaks, silent failures |

Results are merged, deduped, and applied by risk tier:
- **SAFE** → auto-apply (unused imports, commented-out code)
- **CAREFUL** → apply one file at a time, run tests between each
- **RISKY** → flag for human review only

---

## §5 — Architecture Upgrade Workflow

```
Goal → Research → Plan → Confirm → Phased Implement → Per-Phase Review → Cross-Phase Review → Report
```

This workflow is unique: it includes **per-phase retrospectives** and a
**cross-phase review** — the user's preferred pattern for high-risk changes.

### Step-by-step prompts (user → agent)

**1. Research:**
> "分析当前架构 → 评估方案可行性 + 风险 → 调研报告 + 升级方案（含 Phase 拆分）。"

**2. Phased execution with retrospectives:**
> "方案确认。按 Phase 实施。每个 Phase 完成后:
> 1. 跑 build + test
> 2. 主动回顾本 Phase，分析有没有更好的写法
> 3. 有则二次优化，无则进入下一 Phase"

**3. Cross-phase review:**
> "全部 Phase 完成。跨阶段审视: 对比升级前后、分析整体层面更好的设计、
> 检查旧代码路径是否全部迁移。输出最终架构升级报告。"

### Pitfalls

- **Mixing feature work with architectural change.** Architecture upgrades
  should be pure refactors — behaviour must stay identical. If new features
  are needed, do them in a separate workflow.
- **Skipping per-phase retrospectives.** The user's pattern is "implement
  → review → optimize → next phase", not "implement all → review once".
  Per-phase optimization catches design issues early.
- **No cross-phase review.** Even if each phase passed, the combined result
  might have integration issues or a simpler overall design. Always do the
  final cross-phase pass.

---

## 6 — SRS Coverage Analysis

```
SRS + Codebase -> Extract Requirements -> Scan Code -> Cross-Reference -> Gap Analysis -> Sub-Agent Review -> Report
```

**When:** User has an SRS document and wants to know which requirements are
implemented. Triggers: "SRS 覆盖率", "需求覆盖率分析", "生成覆盖率报告".

### Step-by-step prompts (user -> agent)

**1. Full scan (recommended for first run):**
> "分析 docs/requirements.md 中的全部需求，对照代码库重新扫描验证。
> 不要依赖旧的 traceability-matrix.md。输出覆盖率报告。"

**2. Incremental update (faster, for small changes):**
> "以 docs/traceability-matrix.md 为基础，只重新验证 Planned/Deferred 条目。"

**3. Sub-agent review:**
> "复核覆盖率报告: 抽样验证 10 条 Tested 条目、检查遗漏、验证统计数字。"

**4. Re-review decision tree (same as all workflows):**
> Errors <5% mechanical -> fix directly. 5-15% substantive -> fix + light re-review of corrected items only. >15% -> re-scan from scratch. Hard cap: 2 rounds.

### Pitfalls

- **Trusting old matrix.** Always do a fresh scan on first run. The old
  traceability matrix may be stale.
- **Partial status misjudgment.** Agent may mark a requirement as "Implemented"
  just because it found a function signature, without verifying all ACs.
  Sub-agent review MUST spot-check Partial entries.
- **Infinite re-review loops.** Max 2 rounds. Two independent reviews finding
  significant problems = methodology issue, not a report issue.

---

## 7 — Code Quality Report

```
Scope -> Static Analysis Tools -> Categorize + Risk-Tier -> Report -> Sub-Agent Review -> Deliver
```

**When:** User wants a project-wide health check. Triggers: "代码质量报告",
"项目健康度", "技术债务盘点", "质量巡检". This workflow is **report-only** —
it does not modify code. After the report, route findings to Bug Fix (1) for
Critical issues or Quality (4) for optimization.

### Step-by-step prompts (user -> agent)

**1. Full analysis:**
> "对 src/ 做全量质量分析。维度: 复杂度、重复、死代码、安全、依赖、测试覆盖、代码规范。
> 按严重/高/中/低分级，输出到 docs/reports/code-quality-YYYY-MM-DD.md。"

**2. Scoped analysis (large projects):**
> "对 src/services/ 做质量分析，重点关注安全漏洞和复杂度。"

**3. Trend comparison:**
> "做质量分析，与上月报告对比，标注趋势变化。"

**4. Sub-agent review (3-agent parallel):**
> "复核报告: 用 3 个子 agent 独立复核 —
> ① 抽查 5 个严重/高风险问题验证真伪;
> ② 全局搜索遗漏的安全问题 (eval/硬编码密钥/XSS/路径遍历);
> ③ 验证统计数字自洽 (文件数/行数/测试数)。
> 合并输出复核报告，标注不一致项。"

This 3-agent pattern — issue verification, security sweep, stats audit — catches
the three most common report-quality failure modes: false positives, missed
vulnerabilities, and numerical errors.

### Output format

Report must include: overall scorecard (A-F per dimension), Critical issues
table, High priority table, per-module breakdown, Top 5 improvement
recommendations ranked by ROI.

### Pitfalls

- **Mixing report with fixes.** This workflow is analysis-only. Fixing belongs
  in other workflows. "边诊断边手术" produces chaos.
- **Drowning in Low-tier findings.** Prioritize: Critical first, then High.
  Don't let 100 Medium/Low items distract from 3 Critical ones.
- **Single-point analysis.** One report is a snapshot. Trends over 3+ months
  tell the real story. Use Hermes cronjob for monthly auto-analysis.

---

## Context Management: The Foundation

These rules apply across ALL workflows:

### When to reset context

| Signal | Action |
|--------|--------|
| Moving from analysis to implementation | `/new` |
| Starting a review (ANY review) | `delegate_task` (fresh sub-agent) |
| Agent seems "dumber" than usual | `/compress` or `/new` |
| Session exceeds ~50 turns | Consider splitting |
| After a failed approach | `/new` — don't let failed reasoning pollute the retry |

### Sub-agent isolation rules

1. **Reviewer never = implementer.** Fresh context finds what the implementer missed.
2. **Fixer never = reviewer.** The fixer only gets the issue list, not the review reasoning.
3. **Max 2 auto-fix cycles.** If 2 rounds of auto-fix don't resolve all issues, escalate to user.

### The Rule of Three

If 3 consecutive fix attempts fail for the same bug → STOP. Question the
architecture, not the fix. This is the escape hatch from the "fix → break →
fix → break" spiral.

---

## Common Pitfalls

- **Self-review blindness**: The implementer reviewing its own work misses what a fresh context catches. Always `delegate_task` for the review phase — reviewer never equals implementer.
- **Skipping reproduction in bug fixes**: Jumping to a fix without first reproducing the bug with a failing test is gambling. The `systematic-debugging` Iron Law: create the tight feedback loop before touching code.
- **Bundled fixes**: "While I'm here" improvements during a bug fix or feature implementation introduce unrelated risk. One change, one verify.
- **Implementing without SRS alignment**: Feature work without checking the spec leads to rework. Always read SRS + traceability matrix first.
- **Mixing feature work with architecture upgrades**: Architecture upgrades should be pure refactors — behavior must stay identical. If new features are needed, do them in a separate workflow.
- **Ignoring the Rule of Three**: If 3 consecutive fix attempts fail for the same bug, stop and question the architecture, not the fix. This is the escape hatch from the fix→break→fix→break spiral.
- **Single-point quality reports**: One report is a snapshot. Trends over 3+ months tell the real story. Use Hermes cronjob for monthly auto-analysis.
- **Partial status misjudgment in SRS coverage**: Marking a requirement as "Implemented" because a function signature exists, without verifying all acceptance criteria, produces misleading coverage reports. Sub-agent review must spot-check Partial entries.

## Verification: Trust Nothing

Every sub-agent output is a **claim**, not a **fact**. Always verify:

| Claim | Verification |
|-------|-------------|
| "Tests pass" | Run `dotnet test` (or equivalent) yourself |
| "File written" | `read_file` to confirm content |
| "Review passed" | Check report has concrete file:line references |
| "Uploaded successfully" | Fetch the URL to confirm |

If a sub-agent report lacks file:line evidence, treat it as INCOMPLETE —
ask for specifics or re-run with a stricter prompt.

---

## Report Templates

Every workflow ends with a structured report. Minimum sections:

```
[N] 修复/实现/审查/优化/升级 报告
═══════════════════════════════════

目标: [一句话]
变更范围: [文件列表 + 行数]
实施过程: [Phase 总结]
审查结果: [子 Agent 结论 + 风险分级]
测试结果: [通过/失败 + 覆盖范围]
遗留问题: [如有]
```

Full scenario guides with detailed prompts and expected outputs are in
`references/scenario-guides.md`.

## Verification Checklist

- [ ] Workflow phases executed in order: Understand → Plan → Execute → Review → Report (no phase skipped)
- [ ] Review phase used a fresh sub-agent via `delegate_task` — not self-review by the implementing session
- [ ] Fix phase used a separate sub-agent from the reviewer (reviewer ≠ fixer)
- [ ] All sub-agent claims (tests pass, file written, review passed) were independently verified by re-running commands
- [ ] Context was reset between analysis → implementation and before any review phase
