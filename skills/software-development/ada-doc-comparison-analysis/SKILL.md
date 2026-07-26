---
name: ada-doc-comparison-analysis
description: "Use when comparing two technical documents (SRS, design docs, API specs) — synthesize an optimized version by extracting complementary strengths from each while respecting phase boundaries and avoiding regressions."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [documentation, comparison, srs, synthesis]
    related_skills: [ada-srs-writing, ada-docs-revision]
---

# Document Comparison & Optimization

Structured methodology for comparing two technical documents, extracting
strengths from each, and synthesizing an improved version. Primary use case
is SRS (Software Requirements Specification) documents, but the pattern
applies to design docs, API specs, and other technical references.

## Triggers

- User asks to compare two technical documents and identify what each does well
- User has an SRS and wants to improve it against a reference/example SRS
- "阅读 A 和 B，分析各自优点，然后优化 B"

## Workflow

### 1. Read Both Documents Completely

Read every section of both documents. Note structural choices (where are
diagrams placed? how are sections organized?) in addition to content.

### 2. Extract Strengths — One Table Per Document

For each document, produce a numbered strengths table:

| # | 优点 | 说明 |
|---|------|------|

Evaluate across these dimensions:
- **Structural**: Architecture diagrams, data models, lifecycle diagrams — where?
- **Navigational**: Quick-finder, per-section index, decision tree for readers?
- **Format**: How are requirements formatted? AC labeling (AC1/AC2)? Priority notation?
- **Completeness**: Terminology, role definitions, traceability, deferred reqs?
- **Readability**: Tables vs prose, diagrams, design rationale callouts?
- **Maintainability**: Change logs, merge annotations, version tracking?

### 3. Build a Complementarity Map

Show what each document's strengths fill in the other's gaps:

```
Doc A 强项 → 可补充 Doc B 的短板：
  ├── 架构图前置  → Doc B 缺少直观的系统总览
  ├── 数据模型 ER 图 → Doc B 缺少实体关系定义
  └── ...

Doc B 强项 → 可补充 Doc A 的短板：
  ├── AC 显式编号 → Doc A 缺少可测试的验收标准
  └── ...
```

### 4. Propose Optimized Structure

**CRITICAL — respect the document's phase boundaries.** An SRS is a
Requirements Analysis artifact (Phase 1). Do NOT inject:
- Implementation details (API signatures, algorithms)
- Technology choices beyond constraints
- Class diagrams, sequence diagrams, schemas with types

**Phase-appropriate additions for an SRS:**

| Add | Why it belongs in requirements |
|-----|-------------------------------|
| Architecture diagram (Mermaid flowchart) | System boundary and component relationships |
| Data model / ER diagram | Domain entities and cardinalities |
| Lifecycle state diagrams | Behavior specification (states, not implementation) |
| Terminology table | Shared vocabulary |
| Role definitions (per-requirement Actor) | Stakeholder identification |
| Requirement Quick-Finder (decision tree) | Navigation aid — no new content |
| Per-section requirement index | Accessibility of existing requirements |
| Explicit AC numbering (AC1/AC2) | Testability |
| Cross-references between requirements | Dependency analysis |
| Design Rationale callouts | Captures "why" for non-obvious decisions |
| Error code summary table | Derived from error-handling requirements |
| Requirement summary by role (appendix) | Stakeholder-facing view |
| Planned/deferred requirements (appendix) | Scope management |
| Traceability matrix (appendix) | Links to downstream artifacts |
| Change log / merge annotations | Document evolution |

### 5. Deliver Analysis + Concrete Proposal

Output structure:
1. **Strengths tables** for each document
2. **Complementarity summary** (tree or table)
3. **Optimized ToC** with move/add annotations
4. **Key optimization points** — concrete before/after for biggest wins
5. **Before/after comparison** — what improved on each dimension

End by asking: produce the full optimized document, or refine the proposal?

## References

- `references/srs-patterns.md` — Concrete SRS optimization patterns from
  PromptEditor ↔ XDocker: what transferred, what was kept, phase-boundary
  checklist.

## Execution Patterns

After the user approves the proposal, implement changes in this order:

1. **Start from the top** — sections are numbered; inserting new sections
   shifts everything below. Work top-to-bottom: §1 first, then §2, then
   appendices last. Otherwise you'll renumber sections you already modified.

2. **One semantic chunk per `patch()`** — each call changes one logical thing:
   a section insertion, a header rename, a table rewrite. Avoid one giant
   patch that touches three sections. Makes rollback and review easier.

3. **Match strings exactly from the file** — the `patch()` tool needs an
   exact substring. If your match fails, re-read the relevant lines with
   `read_file(offset=N, limit=5)` to get the exact whitespace and line
   endings. MSYS2 `.md` files often use `\r\n` — this doesn't affect
   matching but can affect display in search results.

4. **Batch independent renames** — when you have 5+ sections to renumber
   (e.g. §2.3→§2.4, §2.4→§2.5, §2.5→§2.6), do each as a separate `patch()`
   call but fire them back-to-back. They don't depend on each other because
   each targets a unique string.

5. **Check your work incrementally** — after each major phase (intro done,
   navigation done, section indexes done, appendices done), run a
   `search_files` verification:
   ```sh
   # Confirm renumbering: are all expected headers present?
   search_files(pattern='^## 1\\.(3|4|5|6)|^## 2\\.(2|3|4|5|6)')
   # Confirm Design Rationale count
   search_files(pattern='💡 Design Rationale')
   # Confirm section index count
   search_files(pattern='本节需求索引')
   ```

6. **Append new content at EOF** — appendices and new sections at the end
   of the file are the safest change. Find the last non-empty line with
   `read_file(offset=total_lines-10)` and `patch()` after it.

7. **Use a TODO list** — for multi-phase edits (>10 tool calls), track
   progress with `todo()` to avoid losing your place across turns.

## Common Pitfalls

- **Don't propose changes the target already does well.** Acknowledge existing
  strengths (e.g. XDocker already had AC numbering and cross-references — keep
  those, don't list them as "to add").
- **Phase creep is real.** Architecture diagrams at requirements phase show
  *what exists and how it relates*; at design phase they show *how it
  communicates*. Stay on the requirements side.
- **Domain mismatch.** A CLI tool's SRS benefits from Command Quick-Finders
  and option tables. A UI component's SRS benefits from state diagrams and
  interaction flows. Don't blindly port patterns that don't fit.
- **Intermediate containers with no functional semantics.** When a hierarchy
  has nesting layers that carry zero behavioral constraints (e.g. Content Area,
  Main Area that are pure grouping), consider flattening by aligning with an
  established reference design (e.g. VS Code Workbench). See
  `references/srs-patterns.md` → Hierarchy Flattening for the full checklist.
- **Bilingual convention.** When the target doc uses Chinese with English
  terminology (common in Chinese engineering), preserve this strategy — don't
  force English-only or Chinese-only. Adopt structural patterns from the
  reference while keeping the target's language convention.
- **Don't skimp on reading.** Read 100% of both documents before proposing
  anything. Skimming leads to missing patterns buried in later sections (e.g.
  PromptEditor's strength is its appendices: requirement-summary-by-role,
  planned-requirements, traceability-matrix — all in the last 10%).
- **patch() unique-match failures on large files.** After many edits, the
  file content shifts and previously unique strings may no longer match.
  Always re-read the target area with `read_file(offset, limit)` to get
  the current exact text before patching. Never assume a string you read
  20 turns ago is still valid after 10 other patches above it.
- **Section insertion shifts all downstream line numbers.** When inserting
  content between existing sections, use the section header text as the
  match anchor — never rely on line numbers from old `read_file` output
  after the file has been modified above.

## Overview

`ada-doc-comparison-analysis` provides a structured methodology for comparing two technical documents (typically SRS documents, but applicable to design docs, API specs, and other structured references), extracting complementary strengths from each, and synthesizing an improved version that respects the target document's phase boundaries. The five-step workflow — read both documents completely, extract strengths into dimensioned tables, build a complementarity map, propose an optimized structure (with strict phase-boundary discipline: no implementation details in requirements-phase documents), and deliver a concrete proposal with before/after comparisons — ensures that improvements are evidence-based, not subjective. Developed on the PromptEditor vs XDocker SRS comparison, the skill's reference patterns catalog what transfers between documents and what stays behind.

## When to Use

Use when:
- User asks to compare two technical documents and identify what each does well
- User has an SRS and wants to improve it against a reference or example SRS
- User says "阅读 A 和 B，分析各自优点，然后优化 B" or similar comparison-then-optimize requests
- Merging the best structural patterns from two versions of the same specification
- Cross-pollinating navigation aids (quick-finders, section indexes, role-based summaries) from a well-structured document into a less-structured one

Don't use for:
- Comparing a document against a live product (not another document) — use `ada-srs-review` Pass G (framework coverage) or Pass K (SRS-to-code coverage)
- Simple diff/merge of two versions of the same document — use git diff/merge tooling
- Single-document review or quality audit — load `ada-srs-review`

## Verification Checklist

- [ ] Both documents read completely (100% coverage) before any analysis or proposals — no skimming
- [ ] Strengths tables produced for each document across all six dimensions: structural, navigational, format, completeness, readability, maintainability
- [ ] Complementarity map built: each document's strengths explicitly mapped to the other's gaps
- [ ] Optimized structure proposal respects the target document's phase boundaries: no implementation details (API signatures, algorithms, technology choices) injected into a requirements-phase SRS
- [ ] Proposal ends with a concrete before/after comparison and an explicit question: produce the full optimized document, or refine the proposal?
