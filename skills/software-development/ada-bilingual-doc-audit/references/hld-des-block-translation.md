# HLD DES-Block Translation Recipe (ZH → EN)

Session-proven for HLD part files (this session: `docs/HLD.md` lines
950–1840 → `docs/en/HLD.part2.md`, 1010 lines out, all checks green).
SRS ranges use the REQ-* tuple scripts instead; this recipe is for the
HLD/SDD style where the document is a series of plain ``` fences, each
starting with a `DES-XXX-###` id line.

## HLD block anatomy

Each DES block is one plain ``` fence (no language tag):

    ```
    DES-INT-001
    <Chinese title line>
    <body: prose + code/struct/XML/HTML/ASCII samples>
    Source: NF-004, F-050~068, F-073~078   (来源： footer → "Source:")
    ```

Contract tuple per block: (DES id line, title line, 来源/Source footer,
fence pair). Section headings `## N 中文标题` translate to English with
github-slugger anchors (`## 5 交互架构` → `## 5 Interaction Architecture`).

## What stays byte-identical

- Code/struct definitions (`PanelDragSession`, `SplitterProjection`, ...),
  XML samples, Razor templates, `data-项目-*` HTML, state-machine arrow
  diagrams, shortcut tables — identifiers, indentation, alignment, arrows
  (`↓`, `→`, `↘`, `\→`) all verbatim.
- Inside structs, translate only `//` Chinese comments; inside ASCII
  diagrams, translate only human labels (node IDs kept).
- Cross-references (`DES-INT-006`, `F-xxx`, `NF-xxx`, `OI-xxx`,
  `ADR-xxxx`) and inline enum values — never translated.
- `流程：Parse DTO → Check Version → ...` — keep the English pipeline step
  names, translate only the lead-in word (`Flow:`).

## Verification battery (session-proven, run from repo root)

1. **Token multiset diff — the strongest single check.** Extract every
   (DES|F|NF|OI|ADR) token from the SOURCE RANGE and from the OUTPUT, sort,
   diff:

       sed -n '950,1840p' docs/HLD.md | grep -oP '(DES-[A-Z]+-[0-9]+|F-[0-9]+(~[0-9]+)?|NF-[0-9]+(~[0-9]+)?|OI-[0-9]+|ADR-[0-9]+)' | sort > /tmp/src_tokens.txt
       grep -oP '(DES-[A-Z]+-[0-9]+|F-[0-9]+(~[0-9]+)?|NF-[0-9]+(~[0-9]+)?|OI-[0-9]+|ADR-[0-9]+)' docs/en/HLD.part2.md | sort > /tmp/out_tokens.txt
       diff /tmp/src_tokens.txt /tmp/out_tokens.txt && echo TOKENS-IDENTICAL

   (This session: 157/157 tokens identical, 29 distinct DES IDs.)
   Note: source-range tokens must come from `sed -n` of the SOURCE, never
   from memory — same rule as the REQ-F-135 vs F-135 pitfall.
2. **Fence balance:** `grep -c '^```$' out` must be EVEN (2 × N blocks;
   50 for 25 blocks). Odd count = unterminated fence.
3. **Residual CJK:** `grep -cP '[\x{4e00}-\x{9fff}]' out` must be 0 — HLD
   translations are FULL-English; the SRS bilingual-annotation allowlist
   convention (`--cjk-allow`) does NOT apply here. Caveat: git-bash
   multibyte grep can silently return 0; if paranoid, cross-check with
   python `re.findall(r'[\u4e00-\u9fff]', text)`.
4. **Headings:** `grep -n '^## ' out` — every section heading present, in
   order, English slug-able. Verify the range's first line against source
   headings before extracting (`grep -n '^## ' docs/HLD.md`).
5. **Block count:** `grep -oP 'DES-[A-Z]+-[0-9]+' out | sort -u` — all
   expected blocks present (INT/RND/PER/... groups).

## Part-seam coordination (parallel multi-part translations)

Before writing: `ls docs/en/` + `git status --short docs/en/` to see which
sibling parts already exist (part1/part3/SRS/traceability). Afterwards
cross-check seams:

    tail -3 docs/en/HLD.part1.md && head -3 docs/en/HLD.part3.md

- The parent's literal line range may include the NEXT section's heading
  (e.g. range "950–1842" where 1842 = `## 8 错误处理与质量属性`). If the
  sibling part file already starts with that heading, EXCLUDE it from your
  part and state the exclusion in the summary — do not duplicate.
- Adjacent parts CAN legitimately overlap by exactly one line (a section
  heading: part1 ends `## 5 Interaction Architecture` AND part2 starts with
  it). Keep the heading your range explicitly assigns; flag the 1-line
  duplicate for merge-time dedupe instead of silently dropping it.
- Part2-style ends are often the `---` separator after the last DES block —
  end there; the blank line + next heading belong to the next part.

## Delivery summary

Report: output line count (`wc -l`), verification results (token-diff
count, CJK residual, fence count, DES block count), boundary decisions
with file:line evidence, and any preserved source inconsistencies.
