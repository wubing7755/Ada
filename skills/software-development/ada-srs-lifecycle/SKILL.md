---
name: ada-srs-lifecycle
description: "Use when managing the full SRS lifecycle — unified entry point routing from technical protocol derivation through authoring, reviewing, and large-scale revision. Dispatches to the appropriate sub-skill for each phase."
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [srs, lifecycle, requirements, umbrella]
    related_skills: [ada-srs-writing, ada-srs-review, ada-srs-revision, ada-tp-to-srs-derivation, ada-requirements-authoring]
    sub_skills: [tp-to-srs-derivation, srs-writing, srs-review, srs-revision]
---

# SRS 生命周期

SRS 文档从无到有、从初稿到终稿的完整流程。根据当前所处阶段加载对应子技能。

## 生命周期四阶段

```
TP 文档 ──→ [Phase 1: Derive] ──→ [Phase 2: Write] ──→ [Phase 3: Review] ──→ [Phase 4: Revise]
              tp-to-srs-            srs-writing          srs-review            srs-revision
              derivation
```

| 阶段 | 技能 | 输入 | 输出 | 触发词 |
|------|------|------|------|--------|
| **Derive** | `tp-to-srs-derivation` | 技术协议 (TP .md/.docx) | SRS 初稿 | "基于这份协议写 SRS" |
| **Write** | `srs-writing` | 需求描述/初稿 | 结构化 SRS | "编写 SRS""优化 SRS" |
| **Review** | `srs-review` | 已有 SRS 文档 | 审查报告 | "审查 SRS""检查需求" |
| **Revise** | `srs-revision` | SRS + 变更指令 | 修订后 SRS | "改这个概念""术语统一" |

## 共享约定

### REQ-F 格式

```
### REQ-F-XXX 🔴 [Actor] 标题
> **来源**: TP §x.x

**Description**: ...

**AC**:
AC1：场景名：
Given ...
When  ...
Then  ...
```

### 文档结构

1. Introduction (§1)
2. 术语定义 (§2)
3. 功能需求 (§3, REQ-F-XXX)
4. 非功能需求 (§4, NFR-XXX)
5. 附录

### 核心原则（贯穿全部阶段）

- **文档纯粹性**: 不引用具体编辑器实现，不保留历史编辑注解
- **需求≠实现**: 描述 What，不描述 How
- **术语一致性**: 同一概念全文统一，入口在 §2 术语定义
- **可追溯性**: 每条需求标注 TP 来源

## 使用方式

加载本 skill 后，根据用户意图选择对应阶段，再加载对应子技能获取详细工作流。

## Overview

`ada-srs-lifecycle` is the umbrella entry point for the complete SRS document lifecycle — from deriving requirements from a Technical Protocol (TP), through structured writing, systematic review, to large-scale revision. Rather than re-implementing any single phase, it routes to the appropriate sub-skill based on where you are in the process, enforces shared conventions (REQ-F format, document structure, core principles), and ensures consistency across all four phases. Load this skill first whenever starting SRS work to get oriented, then follow its routing to the phase-specific sub-skill.

## When to Use

Use when:
- Starting SRS work and unsure which phase to begin with — this skill diagnoses the current state and routes accordingly
- You have a TP document and need to produce an SRS from it (routes to the derivation phase)
- You need to write or refine an SRS from scratch (routes to the authoring phase)
- You need to audit an existing SRS for quality issues (routes to the review phase)
- You need to perform large-scale terminology or concept changes (routes to the revision phase)

Don't use for:
- Single, isolated edits that don't span multiple phases — load the specific sub-skill directly
- Design documents, API specs, or test plans — this lifecycle is SRS-specific
- One-off typo fixes or formatting corrections — use a simple `patch` call

## Common Pitfalls

1. **Skipping phase ordering.** The lifecycle is sequential for a reason: derivation produces raw material for writing, review findings feed revision, and revision output may need re-review. Jumping directly to revision without reviewing first misses issues that review would catch.
2. **Loading this skill and stopping.** This skill is a router — after it identifies the correct phase, you must load the corresponding sub-skill to get detailed workflows, checklists, and pitfalls specific to that phase.
3. **Mixing conventions across phases.** The shared conventions (REQ-F format, document structure, core principles) apply uniformly. Deviating in one phase (e.g., using a different requirement format during writing) creates inconsistency that downstream phases must clean up.
4. **Not updating traceability during revision.** When revising, cross-references, statistics tables, and appendix entries silently rot. Always run the post-edit consistency sync from post-edit consistency sync after any revision.

## Verification Checklist

- [ ] Correct sub-skill loaded for the current phase (check: does the sub-skill's triggers match the user's stated intent?)
- [ ] Shared conventions reviewed: REQ-F format uses `###` heading + emoji priority (🔴🟡🟢) + `[Actor: Role]`
- [ ] Document structure follows: §1 Introduction → §2 Terminology → §3 Functional Requirements → §4 Non-Functional Requirements → §5 Appendices
- [ ] Core principles upheld: no implementation details in requirements, no editor-specific references, terminology consistency via §2 glossary, TP traceability on every requirement
- [ ] Cross-phase data flows correctly: derivation output feeds writing input; review findings feed revision scope
