# SRS Terminology Audit — Execution Methodology

How to systematically unify terminology across a large SRS document after
concept confusion has been detected (see `tab-panel-confusion.md` for detection).

## Workflow

### 1. Inventory phase — count all term variants

Use `grep -c` to count every term variant for the key concepts. Build a raw
inventory like:

```
停靠区: 119
Dock Region: 5
Dock 区域: 0
Bottom Region: 57
Bottom Dock: 12
Left Region: 26
Left Dock: 10
Tab 组: 62
面板标签页: 58
面板标签栏: 22
面板（裸）: 31
```

The numbers reveal the dominant (wrong) term and the replacement order.

### 2. Classification phase

Group findings by severity:

| Severity | Criteria | | Example |
|:--------:|----------|:--------:|---------|
| 🔴 | Two different names for the same concept | `Bottom Region` vs `Bottom Dock` |
| 🟡 | Chinese-only term without English equivalent | `停靠区` with no `Dock Region` |
| 🟢 | Minor inconsistency | `Dock层级布局` vs `Dock 层级布局` (missing space) |

### 3. Proposal phase — bilingual glossary FIRST

**Do NOT modify the document yet.** Produce a unified bilingual glossary in
`English（中文）` format. The user must approve before execution.

The glossary must list:
- Unified term
- All deprecated terms (with occurrence counts)
- Replacement rules

### 4. Replacement phase — most specific first

Order matters. Apply replacements in this sequence:

1. **Six Dock region names** (most specific): `左侧上部停靠区` → `Left Dock Upper`
2. **Container names**: `Left Region` → `Left Dock`, `Bottom Region` → `Bottom Dock`
3. **Generic term**: `停靠区` → `Dock Region` (only after specific names replaced)
4. **Legacy model cleanup**: `Tab 组` → (remove), `面板标签页` → (remove)
5. **Standardize**: `Dock 布局` → `Dock 层级布局`, `编辑器标签页` → `Editor Tab`
6. **Clean up double-replacements**: `Dock Region（Dock Region）` → `Dock Region`

When ≥10 term classes need replacement, use a Python script with a dict of
`{old: new}` pairs rather than manual patch calls. The script should count
occurrences for each replacement and report them.

### 5. Manual rewrite phase

Some sections cannot be fixed by simple replacement and need full rewrites:
- Glossary (§1.5.1) — full table rewrite
- Spatial concepts (§1.7) — concept count may change (e.g., 5 → 4)
- Architecture constraints (§1.3) — constraint descriptions change
- ER diagram / data model (§1.4) — fields added/removed
- Entire subsections — e.g., §3.5.1 "Tab 组行为" deleted entirely

### 6. SVG label fix

SVG `<text>` elements contain hardcoded Chinese labels that grep-based
replacements may miss. Check all SVGs manually for:
- Old region names in text labels
- "面板" → "Dock Panel" in callout text
- "堆叠" / "Tab 组" in annotation text
- Callout label wording that referenced the old model

### 6.5 Bilingual enforcement per requirement segment

After bulk terminology replacement, requirement entries still need
consistent `English（中文）` bilingual format on first use. Process
each requirement block independently:

**Rule**: Within each requirement's Title, Description, and each individual
AC, the **first occurrence** of a technical term uses `English（中文）`;
subsequent within-segment uses may stay in Chinese or English alone.

**Execution**: Split each requirement block by `Title\n`, `Description\n`,
and `Acceptance Criteria\n` markers, then further split ACs by `AC\d+`
markers. Apply bilingual replacement to each text segment independently
using a guard condition (don't add if the English form already appears).

Key patterns for replacement (longest/most-specific first to avoid substring
matches):

```python
rules = [
    (r'(?<![a-zA-Z])标签页(?![a-zA-Z])', 'Editor Tab（编辑器标签页）', 'Editor Tab'),
    (r'(?<![a-zA-Z])面板(?![a-zA-Z标签类型栏])', 'Dock Panel（Dock 面板）', 'Dock Panel'),
    (r'(?<!模板)(?<!动态)(?<![a-zA-Z])视图(?![a-zA-Z])', 'Editor View（编辑器视图）', 'Editor View'),
    (r'分割条', 'Splitter（分割条）', 'Splitter'),
    # ... etc for all glossary terms
]
```

The guard (third tuple element) prevents double-annotation: if `Editor Tab`
already appears, don't add the bilingual form again.

**Pitfalls**:
- Do NOT process the glossary (§1.5.1) or section headers — they already
  have bilingual format established.
- "视图" needs negative lookbehind for "模板" and "动态" to avoid mangling
  "Template View" and "Dynamic View".
- After adding bilingual, verify with `grep -c "English（中文）"` to confirm
  counts are reasonable (not 200+ for a single term).

### 7. Delegation for scattered fixes

When the bulk replacement script handles ~80% of changes, delegate the
remaining scattered fixes (SVG labels, appendix tables, leftover bare terms
in edge cases) to a background subagent. Provide the subagent with:
- Exact `grep -n` commands to locate issues
- Old→new replacement strings for each fix
- Clear boundaries (don't touch already-rewritten sections §1.3~§1.7)

This parallelizes the work and prevents context-bloat in the main session.

After removing sub-requirements (like REQ-F-069-TG1~TG4):
- Update §5 statistics table (count, P0/P1/P2 distribution)
- Update appendix index table (section headers, requirement titles)
- Update numbering note

### 8. Verification

Write a small Python script that reads the final document and asserts:
- Every forbidden term = 0 occurrences
- Requirement count matches expected total
- Build/lint passes if applicable

```python
forbidden = [
    "停靠区", "Tab 组", "Tab Group",
    "Bottom Region", "Left Region", "Right Region",
    "面板标签页", "面板标签栏", "Panel Tab",
    "面板移动与堆叠", "REQ-F-069-TG",
]
for term in forbidden:
    assert content.count(term) == 0, f"'{term}' still present"
```

## Pitfalls

- **Replacement order is critical**: If you replace `停靠区` → `Dock Region` BEFORE replacing `左侧上部停靠区` → `Left Dock Upper`, you'll get `左侧上部Dock Region` instead of `Left Dock Upper`.
- **sed on Windows**: `grep -c` may return 0 for Chinese terms due to encoding issues in MSYS2 bash. Use Python with explicit UTF-8 encoding instead.
- **Bilingual doubling**: Automatic replacement of `面板` → `Dock Panel` can create "Dock Dock Panel" when the original was "Dock 面板". Always check for double-replacement artifacts.
- **SVG inside blockquotes**: SVG lines in SRS docs often start with `> `. Replacement patterns must match text inside those prefixes. Use `replace` (exact string) not `sed` to avoid mangling SVG attributes.
- **Stale cross-references**: The data model table may reference the wrong REQ ID (e.g., REQ-F-105 for isolation when it should be REQ-F-109). Check cross-references after terminology changes.
- **Client-only verification**: The SRS is a Markdown document. `dotnet build` verifies the project builds but doesn't validate the SRS. Always run a dedicated terminology audit script as well.
