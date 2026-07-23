# Tab vs Panel Concept Confusion — Detection Pattern

A common SRS defect: using the same term for different UI abstractions,
or different terms for the same abstraction. This reference documents the
pattern discovered while reviewing the Atlas (XDocker) SRS.

## The Five-Entity Model

Define FIVE distinct spatial and functional concepts upfront before auditing:

| Entity | Location | Switching | Multi | Drag | Overflow | Dedup | Pin |
|--------|----------|-----------|:-----:|------|:--------:|:-----:|:---:|
| **Region** | Layout tree | N/A | N/A | N/A | N/A | N/A | N/A |
| **Editor Tab** | Editor View | Click tab / Ctrl+Tab | Yes (tab bar) | Tab-level | Yes (scroll/menu/wrap) | Yes | Yes |
| **Dock Panel** | Dock regions | LT/RT entry click | Yes (stacked, one active) | Panel header | No (LT/RT switches) | No | No |
| **Editor View** | Editor Area only | Activate internal Tab | Yes (split) | N/A | N/A | N/A | N/A |
| **ToolBar Entry** | LT / RT | Click | 1:1 with Dock Panel | N/A | N/A | N/A | N/A |

Key rules:
- Region is a spatial slot only — no content lifecycle, no open/close/activate
- Dock Panel is a tool-window container, NOT an Editor container
- Editor View is an Editor Area subcontainer, NOT a Dock Panel
- Editor Tab belongs ONLY to Editor View; Dock Panel uses ToolBar Entry for switching
- ToolBar Entry is 1:1 with Dock Panel and migrates when panel moves between sides

## Audit checklist

When reviewing an SRS, for each requirement about "tabs" or "panels", ask:

1. **Does this behavior apply to Editor Tabs, Dock Panels, or both?**
   - "Fixed/pinned tabs" → Editor Tab only
   - "Overflow mode for tabs" → Editor Tab only
   - "Dedup when opening" → Editor Tab only
   - "Drag header to move to another region" → Dock Panel only
   - "Fold/auto-hide" → Dock Panel only
   - "Split view" → Editor Area only
   - "Close last one → container removed/retained" → Dynamic/Template types:
     - Editor View dynamic → remove view (REQ-F-031)
     - Editor View template → retain empty view (REQ-F-032)
     - Dock Panel dynamic → remove panel (REQ-F-019)
     - Dock Panel template → retain empty panel (REQ-F-019)

2. **Is this requirement in the right section?**
   - Editor Tab APIs (open/close/activate by tab ID) → §3.4 (Editor section)
   - Dock Panel move APIs → §3.5 (Panel move section)
   - Tab drag-and-drop (directional/center docking) → §3.4.1 (Editor subsection)

3. **Are the cross-references self-consistent?**
   - A "close tab" API should not reference "dynamic panel removal"
   - An "activate tab" API should not reference "auto-hide panel expansion"

4. **Are region names consistent across all sections?**
   - The document may use three name families: `停靠区`, `Dock 区域`, `Dock Region` — pick ONE
   - `Bottom Region` vs `Bottom Dock`, `Left Region` vs `Left Dock` — same entity, different names
   - See `terminology-audit-execution.md` for the full replacement methodology and pitfall checklist

5. **Is the Tab Group legacy model fully purged?**
   - `Tab 组` (Tab Group), `面板标签页` (Panel Tab), `面板标签栏` all describe the OLD model
   - The NEW model uses ToolBar entries for switching; these old terms are dead

## Red flags

- "在指定面板中打开新页签" — opening a tab in an arbitrary "panel"
- "若目标面板处于折叠或自动隐藏状态" — fold/auto-hide in a tab API
- "关闭后按面板类型规则处理" — panel type lifecycle in a tab close API
- "在当前面板的页签间切换" — tab switching in an arbitrary "panel"
- "可互换" used to describe panel interactions — should be "可移动" or "可堆叠"
- `停靠区` or `Bottom Region` in sections that should use `Dock 区域` or `Bottom Dock`
- `Tab 组` or `面板标签页` anywhere — these are the old model leaking through
- Bare `面板` where `Dock 面板` is meant (especially outside §3.4 sections)

## Fix strategy

1. Define the five entities in a dedicated section (e.g., §1.7)
2. Rename all occurrences of the ambiguous term to the specific entity name
3. Move requirements to their correct section
4. Add scope notes at the top of each section
5. Remove cross-references that span entity boundaries incorrectly
6. Replace all region names with unified terms (use replace_all for mechanical substitutions)
7. Purge all Tab Group legacy terms — they have no equivalent in the stack model

