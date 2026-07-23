# Concrete Techniques from xdocker SRS Revision

## SVG Text Editing with sed

When the patch tool fails on SVG elements (escaped quotes in blockquote
context), use `sed` with exact line numbers:

```sh
# Targeted line replacements
sed -i '511s/>Upper</>左侧上部停靠区</' SRS.md
sed -i '512s/>Lower</>左侧下部停靠区</' SRS.md

# Verify
sed -n '511p;512p' SRS.md
```

## Multi-pattern sed for Prose

Use semicolons to chain multiple replacements:

```sh
sed -i '
s/包含 LT、Left Dock、Editor Area、Right Dock/包含 LT、Left Region、Editor Area、Right Region/g
s/LT 服务于 Left Dock（/LT 服务于 Left Region（/g
s/Left Dock 包含/Left Region 包含/g
' SRS.md
```

## Block-level sed with Address Ranges

Use address ranges to scope replacements:

```sh
# Only replace within the Right Region section
sed -i '
/Right Region.*可停靠面板区域/,/Bottom Region/{
    s/左侧上部停靠区/右侧上部停靠区/
    s/左侧下部停靠区/右侧下部停靠区/
}
' SRS.md
```

## Mermaid ER Diagram Restoration

After a `replace_all` of `||` → `|` corrupted the mermaid ER diagram,
restore with a patch that includes the surrounding context:

```sh
# Check if corrupted
grep -n '|--o{\||--||' doc.md

# Restore: patch with erDiagram + entity lines as context
```

Key mermaid ER symbols: `||--o{` (one-to-many), `||--||` (one-to-one),
`}o--||` (many-to-one).

## Batch Terminology Replacement Order

When renaming multiple related terms in a large document, follow this order:

1. **Longest/specific phrases first** — "Dock 层级布局" before "Dock 区域"
2. **Standalone terms with replace_all** — "Dock 区域" → "停靠区"
3. **Compound terms second** — "Dock 面板" → "面板"
4. **Entity/area names** — "Left Dock Upper" → "左侧上部停靠区"
5. **Clean up abbreviations** — "左侧上部停靠区/Lower" → "左侧上部停靠区 / 左侧下部停靠区"
6. **Fix spacing** — "六个 停靠区" → "六个停靠区"

After each step, verify no corruption before proceeding.
