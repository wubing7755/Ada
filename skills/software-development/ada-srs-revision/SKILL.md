---
name: ada-srs-revision
description: Systematically revise SRS and large technical requirements documents — semantic-concept replacement, mass terminology standardization, iterative review-then-execute workflow, and safe replace_all techniques. Use when the user asks to change core concepts, rename terms, or restructure sections across a large spec document.
version: 1.1.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [srs, requirements, documentation, revision, patch, markdown, refactoring, terminology]
    related_skills: [ada-hermes-agent-skill-authoring, ada-srs-lifecycle]
---

# SRS & Technical Requirements Document Revision

Revise large structured technical documents (SRS, design docs, standards). Developed on a 4700-line SRS document where "面板堆叠 (Panel Stacking)" was replaced with "Tab 组 (Tab Group)" across every section, table, diagram caption, term definition, and requirement.

## Triggers

- User asks to change a core concept in an SRS or technical spec
- User says "review the terminology" or "this term isn't right"
- User wants to align spec terminology with industry references (VS Code, Rider, etc.)
- User asks to add/remove/restructure sections in a numbered specification
- Any change exceeding ~5 individual edits in a large document

## Workflow (Mandatory: Review-Then-Execute)

> Never execute mass changes without explicit user approval. The cost of getting a term wrong across 100+ occurrences is much higher than the cost of one extra confirmation round-trip.

### 1. Understand the semantic change

Before touching the document, clarify exactly what changes:

- **What is the old concept?** Map every surface form it takes (noun, verb, adjective, table headers, diagram labels, requirement titles).
- **What is the new concept?** Define the replacement and whether it changes behavior (acceptance criteria) in addition to naming.
- **What are the behavioral implications?** If the concept changes behavior (e.g., "stacking collapses to toolbar entries" → "tab group shows a tab bar"), identify every requirement whose AC must be rewritten, not just search-replaced.

Example from the Atlas/xdocker revision:

| Old | New | Behavioral? |
|-----|-----|:-----------:|
| 堆叠 (Stack) | Tab 组 (Tab Group) | Yes |
| 面板移动与堆叠 | 面板移动与 Tab 组 | Rename |
| 可堆叠 (Stackable) | 支持 Tab 组 | Rename |
| ToolBar 条目 = 开关+收起代理 | ToolBar 条目 = 持久开关 | Yes |

### 2. Map the blast radius

```sh
grep -n '旧术语' docs/SRS.md
```

Map results to sections — some may be false positives that should be left untouched.

### 3. Propose options, get a decision

Present changes as a comparison table BEFORE executing:

| 当前 | 建议 | 参考 | 影响范围 |
|------|------|------|----------|

Wait for explicit approval ("可以"/"请修改") before touching any file.

### 4. Patch in dependency order

Start from the foundation and work outward. **Replace terms in order of specificity — longest/most specific first:**

```
1. Compound phrases first:   "Dock 层级布局" → "Dock 布局"
2. Two-word terms next:      "Dock 区域" → "停靠区"
3. Single-word terms last:   "Dock 面板" → "面板"
```

Section order:
1. **Terminology (§1.5)** — Add new term definition, update related terms
2. **Data model (§1.4)** — Update entity descriptions
3. **Concept overviews (§1.2, §1.3, §1.7)** — Tables, constraints, property sheets
4. **Functional requirements (§3)** — Descriptions and acceptance criteria
5. **Diagrams** — SVG text, mermaid flowcharts
6. **Statistics and indexes (§5, Appendix)** — Counts, tables, totals

Use `replace_all` for unambiguous global terms. Use targeted `patch` for context-sensitive replacements. Keep each patch focused on one logical unit.

### 5. Fix fallout: common breakage patterns

After replacements, check and fix:

**Double-pipe corruption in Markdown tables:** `replace_all` of `||` can accidentally match `||` at the start of table rows. Check: `grep -n '^||' spec.md`

**Mermaid diagram corruption:** Mermaid ER diagrams use `||--o{` syntax. A naive `replace_all` of `||` → `|` will destroy them. Always verify mermaid blocks after batch operations.

**Missing words after compound replacement:** Replacing "X Y" → "Z" inside "通过 X Y切换" leaves "通过 Z切换" — the connector word is lost. Check for orphan patterns.

**Area name slash patterns:** Terms like "Left Dock Upper/Lower" need sequential replacements — replace each variant individually, then clean up remaining remnants.

**Spacing artifacts:** "六个 Dock 区域" → "六个 停靠区" leaves a double space. Fix with targeted `replace_all` on the specific pattern.

**SVG text labels:** When patching SVG text, use the simplest unique substring without XML attributes — avoid escape hell with quotes:
```diff
- Good: patch("支持堆叠与跨区域移动", "支持 Tab 组与跨区域移动")
- Bad:  patch('<text x="130" ...>支持堆叠...</text>', ...)
```
For SVG changes in blockquote-wrapped markdown, `sed -i '<line>s/old/new/'` with exact line numbers is more reliable than the patch tool.

### 6. Validate: grep counts

After all changes, run zero-count checks on every old term:

```sh
for term in "Dock 区域" "Dock 面板" "Dock 层级布局"; do
  count=$(grep -c "$term" spec.md 2>/dev/null || echo 0)
  echo "$term: $count"
done
```

Any non-zero count needs investigation.

### 7. Update collateral

After terminology changes, update:
- Requirement index tables (§5 appendix)
- Statistics summary (total counts, priority breakdowns)
- Cross-references in other sections that use the old terms
- `docs/requirements-traceability.md` if implementations reference old terms

## Common Pitfalls

### `replace_all` on short terms is dangerous

`replace_all` of "Tab" → "面板标签页" will also hit "Tab 组" → "面板标签页 组". Always test the scope by grep-checking what patterns the term appears in before doing a global replace.

### `replace_all` on punctuation sequences

**NEVER** use `patch(replace_all=true)` on short punctuation-only strings like `||` → `|`. This will corrupt mermaid ER diagrams, markdown pipe tables, and any other syntax that uses repeated punctuation. Always use targeted single-match patches with enough surrounding context.

### Single-word replacements create context problems

"面板" alone is too generic — it appears in "模板面板", "动态面板", "折叠面板", and standalone. A replace_all of "Dock 面板" → "面板" is safe, but "面板" → something else would NOT be safe.

### Table header rename chain

When renaming a table header, check whether the same pattern appears in other tables (there may be 3-4 copies of the same column in different sections). Patch them all.

### Requirement renumbering

Avoid renumbering existing requirements when adding new ones. Use suffix notation instead (`REQ-F-069-TG1`) so that existing cross-references and traceability matrices don't break. Update the stats section to reflect the new total.

### Acceptance criteria rewriting

When a concept change affects behavior, don't just search-replace the description — rewrite the Given/When/Then acceptance criteria to match the new model. This is the most error-prone step.

### Chinese+English mixed terms

When a term exists in both Chinese and English (e.g., "Dock Panel 面板"), present them as clean pairs: `面板（Panel）` for introduction, `面板` for prose. Never mix `Dock Panel 面板` — pick one language.

## Terminology Design Principles

When aligning terminology with real-world products:

1. **Check two references** — VS Code and Rider cover different philosophies
2. **Avoid the same word at multiple levels** — e.g., don't use "Dock" for both the layout system, the spatial container, AND the tool window
3. **English column stays clean** — in term definition tables, the English equivalent should be the canonical class/concept name
4. **Container ≠ slot** — parent grouping containers (Left Region) and individual dockable slots are different concepts

## Verification Checklist

After all patches are applied:

```sh
# 1. Remaining old-term references (should be 0 or only intentional ones)
grep -n '旧术语' docs/SRS.md

# 2. No double-pipe table corruption
grep -n '^||' docs/SRS.md

# 3. Mermaid diagram integrity (||--o{ patterns intact)
grep -c '||--o{' docs/SRS.md

# 4. New term appears in all expected sections
grep -c '新术语' docs/SRS.md

# 5. Requirement count matches stats table
# (manually verify: count of REQ-F-xxx lines vs §5 total)

# 6. Line count sanity check
wc -l docs/SRS.md
```

## Overview

`ada-srs-revision` is the disciplined methodology for executing large-scale revisions on structured technical documents — primarily SRS documents but applicable to design docs and standards. Developed on a 4700-line SRS where a core concept ("面板堆叠 / Panel Stacking") was replaced with "Tab 组 / Tab Group" across every section, table, diagram caption, term definition, and requirement, it enforces a review-then-execute workflow: understand the semantic change (old surface forms + behavioral implications), map the blast radius with `grep`, propose options with comparison tables for user approval, patch in dependency order (terminology → data model → concepts → requirements → diagrams → statistics), fix common breakage patterns (double-pipe corruption, mermaid damage, spacing artifacts, SVG text), and validate with grep-based zero-count checks. The cost of getting a term wrong across 100+ occurrences is far higher than the cost of an extra confirmation round-trip — this skill bakes that discipline into every step.

## When to Use

Use when:
- Changing a core concept or term across an entire SRS or technical specification
- User says "review the terminology" or "this term isn't right" for a term that appears dozens of times
- Aligning specification terminology with industry references (VS Code, Rider, IntelliJ)
- Adding, removing, or restructuring numbered sections in a large specification
- Any change exceeding ~5 individual edits in a large document — the workflow overhead pays for itself at scale
- Mass terminology standardization (e.g., "Dock 区域" → "停靠区", "堆叠" → "Tab 组") across all sections, tables, diagrams, and code blocks

Don't use for:
- Single-line typo fixes — use a simple `patch` call
- Writing new content from scratch — load `ada-srs-writing`
- Auditing or reviewing a document — load `ada-srs-review` first to identify what needs changing, then use this skill to execute the changes
- Changes that don't affect terminology or structure (e.g., adding a single new requirement) — load `ada-srs-writing`

## References

- `references/atlas-stacking-to-tabgroup.md` — Full before/after diff of the xdocker SRS stacking→Tab Group revision
- `references/atlas-terminology.md` — Atlas (xDocker) project terminology decisions: old→new term mapping, VS Code/Rider reference terminology, Tab group model decisions
- `references/survey-commands.md` — Pre-edit survey commands (grep patterns for terminology audit)
- `scripts/verify-terminology.py` — Script to validate term counts after refactoring
