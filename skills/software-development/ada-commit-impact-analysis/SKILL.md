---
name: ada-commit-impact-analysis
description: "Use when analyzing a commit/branch's changes and impact."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [code-review, git, impact-analysis, commit, branch, pr]
    related_skills: [ada-dotnet-blazor-library, ada-ui-interaction-protocol-contracts, ada-requesting-code-review]
---

# Commit / Branch Impact Analysis

Analyze what a commit, branch, or PR actually changed and what the consequences
are — for the user's "读提交/分支，分析改了什么、有什么影响" request pattern.
Do NOT trust commit messages as the whole story; trace the change to its real
integration points and verify with executable evidence.

## When to Use

- User asks to review a branch/PR's commits: what changed, what's the impact
- User asks a follow-up about a changed behavior: "折叠后的 X 还存在吗？",
  "为什么不直接用 Y？"
- Pre-merge sanity review before the user's linear-history rebase/merge workflow
- Estimating blast radius of a change before adopting it

Do **not** use for: preparing your own code for review (ada-requesting-code-review),
full code-quality audits (ada-code-quality-analysis), or docs-vs-source drift audits
(ada-doc-implementation-audit).

## Workflow

### 1. Enumerate the commits against the real baseline

```sh
git branch --show-current
git log --oneline origin/main..HEAD            # commits unique to this branch
git log origin/main..HEAD --stat               # file-level scope per commit
```

Check `git status` first — the branch may be behind/ahead or already merged.

### 2. Read full diffs per commit (`git show <sha>`)

Read the actual diff, not just the message. For each hunk ask: what invariant
changed, what callers are affected, what behavior is now reachable/unreachable.

### 3. Trace cross-cutting integration points

A change that looks local often ripples through layers. For each touched concept,
grep for every consumer. Concrete checklist for a NEW protocol/target kind
(drag/drop, DOM metadata, message types):

1. Shared type union / schema (e.g. protocol.ts `DropTargetKind`)
2. Producer/resolver — emitted under the right source-kind × geometry gating
3. Consumer host — whitelist/mapping to the domain operation
4. Presentation — highlight/preview CSS for the new kind (generic attribute rule may cover it)
5. Tests — producer, consumer mapping, domain operation semantics
6. Contract docs — SRS ACs, ADR enabled set, traceability, remediation references

A missing slice means the feature is half-dead (emitted but unmapped, mapped but
unhighlighted, etc.).

### 4. Verify with real test runs

Run the actual gates before claiming impact:
- Node/TS: `npm run typecheck && npm run test:js`
- .NET: `dotnet build && dotnet test` (per AGENTS.md conventions)
- Report real counts (e.g. "Node 42, Core 267, Blazor 114 passed")

### 5. Answer "does X still exist?" by tracing the FULL stack

Don't answer from the diff alone. Follow the state from model → component render
→ CSS → layout math. Example chain for collapsed groups:
Core node survives (Visibility=Collapsed) → `GroupView` still renders the
`<section>` (empty-state branch) → CSS `.group-collapsed { visibility:
hidden }` (NOT display:none — grid placement preserved) → split track set to `0px`
via `IsSubtreeEffectivelyHidden`/`CollapseAdjustedStyle`.
Answer = "exists but invisible + 0px", with each hop evidenced by file:line.

### 6. Answer "why not just use X?" by comparing code consequences

When the user proposes an alternative ("为什么不直接声明为 Dynamic?"), compare
what each option ACTUALLY does in code, not abstract semantics:
- Dynamic removal = structural: deletes node + parent split, promotes sibling
  (position memory lost, drop-back needs rebuild)
- Persistent collapse = state change: node/topology/ToolBar slot survive, track 0px
Present a comparison table, name the deciding factor (position retention /
identity), then acknowledge the reasonable kernel of the user's objection and
state the case where their alternative IS the right choice.

## Pitfalls

- **Commit message claims ≠ code fact.** Verify re-expand/fallback claims exist in
  the planner/operation code before repeating them (e.g. "re-expands via
  SelectItemPlanner" — check SelectItemPlanner actually forces Expanded).
- **Collapse ≠ delete.** Check whether the node, split topology, ToolBar slot, and
  drop target survive. Collapsed-but-present is a common hidden state.
- **Null/absent index semantics.** A nullable index often means append
  (`TargetIndex ?? ItemIds.Count`); state that explicitly instead of saying
  "no index".
- **Defensive gaps in the host whitelist.** Controller may gate a kind that the
  host accepts without re-checking (e.g. own-group region-center). Note it as a
  low-risk protocol-level gap.
- **Don't conclude from diff alone.** Run the tests; report real pass counts.

## Verification

- [ ] Read full diff of every commit, not just messages
- [ ] Grepped every consumer of changed types/kinds/CSS hooks
- [ ] Ran the project's real gates (typecheck, JS tests, dotnet build/test)
- [ ] Answers cite file:line evidence
- [ ] Design-question answers compare code consequences, not abstractions

## Reference

本技能无独立 references：提交影响分析的追踪协议与架构判断要点均在正文。

## Follow-up: architecture judgment after impact analysis

When the user moves from "what changed / what's the impact" to "is this change
APPROPRIATE long-term" (合适吗 / 更好的方案), the analysis shifts from impact
to architecture. Key moves that worked:

1. Audit sibling mutation paths for the SAME state rule. A rule fixed in one
   path but missing in a sibling is a real inconsistency — grep for the
   transition's outcome across move/close/open/select/restore/reconcile/
   deserialize. Real example: one planner collapses an emptied Persistent
   group, but a sibling operation keeps original Visibility → close leaves a
   blank expanded panel.
2. Recommend promoting the rule to a MODEL-LEVEL invariant (construction-time
   normalize) instead of per-planner edits or commit-point-only fixes — the
   latter leaves materialization/deserialization holes.
3. Present the design as explicit decision points (reject vs auto-correct vs
   allow) aligned with the model's existing validation style, then a phased
   plan (invariant core → conflicting-operation decision → test matrix → docs)
   with a precise file-change list and impact assessment.
4. Long-term architecture plans belong in `.hermes/plans/` via the `plan`
   skill; do not start editing code during the decision phase.
