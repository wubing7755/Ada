---
name: ada-docs-revision
description: 'Use when revising general technical documents at scale: terminology replacement, mass rename, section restructuring, README/design-doc cleanup, or blast-radius analysis. For SRS-specific requirement terminology, numbering, or traceability changes, use ada-srs-revision.'
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [documentation, revision, terminology, srs, markdown]
    related_skills: [ada-srs-revision, ada-srs-writing]
---

# Documentation Revision

Use when the user asks to revise, review, or restructure a technical document
(SRS, design doc, API spec), especially involving terminology alignment,
concept disambiguation, or large-scale renaming.

## Workflow

### Phase 1: Audit

Before changing anything, read the full document and identify ALL occurrences
of the problematic term or concept. Use `grep -n` with multiple patterns:

```sh
grep -n 'TermA\|TermB\|TermC' doc.md
```

### Phase 2: Reference

Ground the analysis in real-world products. For UI component terminology,
reference VS Code and JetBrains Rider/IntelliJ as canonical sources. For
API docs, reference established frameworks. Present evidence, not opinion.

### Phase 3: Propose

Present a BEFORE/AFTER mapping table. DO NOT jump straight to edits —
the user must approve the direction first. The table should include:

| 当前 | 建议 | 参考 | 说明 |
|------|------|------|------|

Include a count of affected occurrences and a list of sections impacted.
Wait for explicit approval before touching any file.

### Phase 4: Execute

Do replacements in dependency order:
1. Specific compound phrases first (e.g., "Dock 层级布局" before "Dock 区域")
2. Then standalone terms with `replace_all`
3. Then area/entity names
4. Then clean up compound abbreviations (e.g., "Left Dock Upper/Lower")
5. Finally fix spacing issues and run final grep verification

### Phase 5: Verify

```sh
# Confirm old terms are gone
grep -c 'OldTerm' doc.md  # should be 0

# Confirm new terms are present
grep -c 'NewTerm' doc.md

# Check for formatting corruption
grep -n '^\|\|' doc.md  # double-pipe in markdown tables
```

## Common Pitfalls

### replace_all corrupts mermaid ER diagrams

`||--o{` in mermaid ER diagrams WILL be corrupted by a `replace_all`
of `||` → `|`. After any `replace_all`, immediately check mermaid blocks:

```sh
grep -n '|--o{\||--||' doc.md
```

If corrupted, restore with a targeted patch using the surrounding mermaid
context (e.g., the `erDiagram` line and the entity definitions).

### patch tool fails on SVG text

SVG elements with escaped quotes (`\"`) in blockquote-prefixed lines
(`>   <text x=\"...`) often fail with the patch tool due to matching
ambiguity. Fall back to `sed -i '<line>s/old/new/'` with exact line numbers.

### Chinese+English mixed terms

When a term exists in both Chinese and English (e.g., "Dock Panel 面板"),
present them as clean pairs: `面板（Panel）` for introduction, `面板` for prose.
Never mix `Dock Panel 面板` — pick one language.

### Space cleanup after replacement

`replace_all` of "Dock 区域" → "停靠区" will leave double spaces in phrases
like "六个 停靠区" (was "六个 Dock 区域"). Run a final pass to collapse them:

```sh
# Only if the space is truly unwanted (Chinese number+classifier+noun)
sed -i 's/六个 停靠区/六个停靠区/g' doc.md
```

## Terminology Design Principles

When the user asks to align terminology with real-world products:

1. **Check two references** — VS Code and Rider cover different philosophies
2. **Avoid the same word at multiple levels** — e.g., don't use "Dock" for both
   the layout system, the spatial container, AND the tool window
3. **English column stays clean** — in term definition tables, the English
   equivalent should be the canonical class/concept name, not a compound
   of the Chinese prefix
4. **Container ≠ slot** — parent grouping containers (Left Region) and
   individual dockable slots (左侧上部停靠区) are different concepts

## Overview

`ada-docs-revision` is the general-purpose structured revision methodology for technical documentation — SRS documents, design docs, API specs, and standards. It provides a five-phase workflow (Audit → Reference → Propose → Execute → Verify) that grounds every change in real-world product references (VS Code, JetBrains Rider), requires explicit user approval before any file is touched, executes replacements in dependency order (specific compound phrases → standalone terms → area/entity names → cleanup), and validates with grep-based zero-count checks. The skill also captures the most common breakage patterns from large-scale document revisions: `replace_all` corrupting mermaid ER diagrams, patch tool failures on SVG text with escaped quotes, Chinese-English mixed-term normalization, and double-space artifacts after replacement.

## When to Use

Use when:
- User asks to revise, review, or restructure a technical document (SRS, design doc, API spec)
- Aligning terminology across a document, especially when real-world product references are available
- Disambiguating overloaded concepts (e.g., a word used for three different things in the same document)
- Performing large-scale renaming with `replace_all` — this skill's pitfalls section warns about the specific breakage patterns
- User wants changes proposed and approved before execution (the mandatory review-then-execute gate)

Don't use for:
- SRS-specific revision with the full lifecycle context — use SRS-specific revision which extends this skill with SRS-specific patterns (terminology → data model → concepts → requirements → diagrams → statistics dependency order)
- Document comparison and synthesis — use document comparison and synthesis
- Writing new documentation from scratch — use full SRS authoring or lightweight requirement writing

## Verification Checklist

- [ ] Audit complete: all occurrences of the problematic term mapped with `grep -n` across the entire document before any changes
- [ ] Reference grounded: proposed terminology checked against at least one real-world product (VS Code, Rider, or applicable domain reference)
- [ ] Proposal approved: explicit user confirmation obtained before any file modification
- [ ] Replacements executed in dependency order: specific compound phrases first, standalone terms next, area/entity names after, cleanup last
- [ ] Post-revision validation: old terms at zero count (`grep -c 'OldTerm'` returns 0), new terms present, no double-pipe table corruption, mermaid ER diagrams intact

## Related Skills

- `hermes-agent-skill-authoring` — for creating and validating SKILL.md files
- `plan` — for creating structured plans before large document refactors
