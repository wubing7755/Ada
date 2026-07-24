---
name: ada-srs-documentation
description: Author and review Software Requirements Specification (SRS) documents — structure patterns, quality rules, common pitfalls, and VS Code-style design referencing.
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [srs, documentation, requirements, quality, structure]
    related_skills: [ada-srs-writing, ada-srs-revision, ada-srs-lifecycle]
---

# SRS Documentation

Author, review, and refine Software Requirements Specification documents with a focus on structure, clarity, and separation of concerns.

## When to Use

- Writing a new SRS from scratch
- Reviewing an existing SRS for quality and completeness
- Restructuring an SRS to improve readability and traceability
- Separating concepts that have been conflated (e.g., different types of UI containers)
- Adding navigation aids (indexes, quick-finders, role-based summaries)

## Document Structure

A well-structured SRS should include these sections:

1. **Introduction** (§1)
   - Purpose: what the system is, who it's for, what problem it solves
   - Scope: what's in AND out of scope, design references
   - System architecture: high-level diagram + constraint table (keep it conceptual — detailed layouts go in §3)
   - Data model: ER diagram showing entity relationships
   - Terminology: all key terms defined in one table
   - Document conventions: numbering rules, priority definitions, requirement format
   - Spatial concepts: if the system has different types of containers (tabs, panels, entries), define them upfront

2. **Overall Description** (§2)
   - Product perspective, product functions (summary list)
   - **Quick-finder**: a navigation table or decision tree to help readers locate requirements by role/task
   - User characteristics, constraints, assumptions

3. **Functional Requirements** (§3)
   - Each section should have a **section index** ("本节需求索引") listing all requirements in that section with a "你想... | 看这条" table
   - Requirements grouped by concern, not by a flat list
   - Requirement format: `REQ-F-XXX` + priority emoji + `[Actor: Role]` header, then Title/Description/Acceptance Criteria with Given/When/Then

4. **Non-Functional Requirements** (§4)
   - Performance, compatibility, security, accessibility, memory
   - Each as testable, measurable criteria where possible

5. **Statistics** (§5)
   - By section/priority
   - By role

6. **Appendices**
   - Lifecycle state diagrams
   - Deferred/planned requirements
   - Traceability matrix
   - Change log

## Requirement Format

Each requirement uses:

```
REQ-F-XXX 🔴 [Actor: Role]

Title
<one-line title>

Description
<what the system should do>

Acceptance Criteria

AC1：<scenario name>

Given <precondition>
When <action>
Then <expected result>
And <additional result>
```

## Priority Usage

Priority emojis MUST be used in requirement headers, not just defined in a table:

| Symbol | Priority | Meaning |
|:------:|:--------:|---------|
| 🔴 | P0 | Must have — system unusable without it |
| 🟡 | P1 | Should have — significantly degrades usability if absent |
| 🟢 | P2 | Could have — enhancement |

## Quality Rules

### What Belongs in SRS (Behavior, Not Implementation)

- ✅ User-visible behavior: "面板折叠至折叠尺寸" (panel collapses to a small fixed size)
- ❌ Implementation details: "默认值为 36px" — pixel values, colors, exact timings belong in design docs
- ✅ Behavioral parameters: 4px drag threshold, 300ms debounce — these define user-perceptible interaction timing
- ✅ Performance targets: "≤200ms initialization" — measurable and verifiable

### Concept Separation

When a system has multiple types of "containers" or "content units", clearly separate them:

- **Define each concept upfront** (in §1.x "空间概念") with a comparison table showing: where it appears, how it's switched, lifecycle, applicable requirements
- **Don't mix requirements** for different concepts in the same section (e.g., Editor Tab requirements and Dock Panel requirements should be in separate chapters)
- **Name consistency**: Once a concept is named, use that name consistently across all requirements

Example from VS Code-style dock layout:
- Editor Tab: file tabs in the Editor Area (open/close/activate/overflow/pin/split)
- Dock Panel: tool windows in Dock regions (move/stack, switched via ToolBar)
- ToolBar Entry: navigation icons in LT/RT (one per panel, migrates with panel)

### Scope Boundaries

- §1.2 should explicitly list what's **out of scope** (touch support, specific framework bindings, server-side state, content component implementation)
- §1.2 should cite the **design reference** (e.g., "参照 VS Code Workbench 设计")

### Requirement Completeness

- When a behavior is a natural consequence of an existing constraint, add an **AC** rather than a new requirement
- Cross-reference related requirements explicitly: `（参见 REQ-F-xxx）`
- Mark merged/deleted requirements inline: `> **已合并**: REQ-F-xxx → REQ-F-yyy`

## Common Pitfalls

### Dead Requirements
Requirements describing scenarios that cannot occur at runtime. Example: "运行时检测到多个面板声明相同区域名称" — if no runtime operation can create duplicate region names, this AC is dead code.

### Swap vs Stack Confusion
Many SRS authors default to a "swap" model for panel movement. VS Code uses a "stack" model — dragging a panel to an occupied region adds it to the stack rather than swapping positions. This changes the semantics of region names (regions can host multiple panels) and eliminates the need for swap-specific requirements.

### Hierarchical Over-Nesting
Avoid intermediate containers that add no functional value. VS Code's Workbench is flat: all dock areas are direct children of the Work Area. Eliminate middle layers like "Content Area" and "Main Area" unless they carry real constraints.

### Tab/Panel Concept Mixing
The most common SRS error: using "tab" to mean both Editor file tabs AND Dock panel content units. If the system has two distinct switching mechanisms (Tab Bar for Editor, ToolBar for panels), the requirements must be separated.

## Bilingual Approach

When writing for Chinese-speaking teams:
- Body text in Chinese (简体中文)
- Technical terms include English equivalents: `Dock 面板（Dock Panel）`
- English-only for maintainer/architecture docs
- Terminology table: Chinese | English | Definition (three columns)

## Overview

`ada-srs-documentation` defines the canonical structure, format, and quality rules for Software Requirements Specification documents. It serves as the reference standard for what a well-formed SRS looks like: chapter organization (§1 Introduction through §5 Statistics plus Appendices), requirement formatting conventions (REQ-F-XXX with priority emoji, actor notation, Given/When/Then acceptance criteria), priority usage rules (🔴 P0 / 🟡 P1 / 🟢 P2), quality rules for separating behavior from implementation, concept separation patterns for systems with multiple container types, scope boundary documentation, and bilingual conventions for Chinese-English mixed teams. Use this as the structural template when creating a new SRS or when an existing SRS needs to be evaluated against quality expectations.

## Verification Checklist

- [ ] All required sections present: §1 Introduction (purpose, scope, architecture, data model, terminology, conventions, spatial concepts), §2 Overall Description (quick-finder, user characteristics, constraints), §3 Functional Requirements (grouped by concern, per-section indexes), §4 Non-Functional Requirements (testable criteria), §5 Statistics (by section/priority/role), Appendices (lifecycle diagrams, deferred reqs, traceability matrix, change log)
- [ ] Each requirement uses the canonical format: `### REQ-F-XXX` + priority emoji (🔴🟡🟢) + `[Actor: Role]`, followed by Title / Description / Acceptance Criteria with Given/When/Then in separate paragraphs
- [ ] Priority emojis appear in every requirement header — not just defined in §1 conventions and then forgotten
- [ ] Spatial concepts (if the system has multiple container types) are defined upfront in §1 with a comparison table showing where each appears, how it's switched, its lifecycle, and applicable requirements
- [ ] No implementation details leaked: pixel values, API field names, framework/pattern names, data structure type annotations removed or justified as behavioral parameters
