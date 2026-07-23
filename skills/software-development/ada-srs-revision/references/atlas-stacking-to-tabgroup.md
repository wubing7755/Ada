# Atlas/xdocker SRS: Stacking → Tab Group Revision

Worked example of a systematic semantic-concept revision across a 4700-line
SRS document. This is the session that produced the `srs-revision` skill.

## Context

The SRS (`docs/SRS.md`) originally modeled panel coexistence within a Dock
region as "stacking" — only one panel expanded, the rest collapsed into
ToolBar entries. After comparing VS Code (Activity Bar switching) and Rider
(Tab groups), the user chose Rider's model: multiple panels in the same Dock
region form a **Tab Group**, each panel gets a visible Tab, and clicking the
tab switches the active panel.

## Changes Applied

### §1.2 Scope Table

| Before | After |
|--------|-------|
| `Dock 面板移动` — 面板移动与堆叠 | `Dock 面板移动与 Tab 组` — 面板跨区域移动与 Tab 组管理 |

### §1.3 Architecture Constraints

```
- Old: "六个 Dock 区域支持面板堆叠。拖拽面板至已有面板的区域时，面板堆叠（Stack）而非互换位置"
+ New: "六个 Dock 区域支持 Tab 组。拖拽面板至已有面板的区域时，面板以 Tab 标签页形式加入该区域的 Tab 组"
```

```
- Old: "LT/RT 是面板导航入口"
+ New: "LT/RT 是面板的持久开关——条目不随面板展开/收起而创建或销毁..."
```

### §1.5 Terminology

Added: `| Tab 组 | Tab Group | 同一 Dock 区域内多个面板的组织形式。Tab 组内的每个面板对应一个 Tab 标签页，以 Tab 栏形式显示...`

Updated: `面板移动与堆叠` → `面板移动与 Tab 组`, `ToolBar 条目` definition.

### §1.7.2 DockPanel Property Table

All 6 property rows rewritten. Key change:

```
- Old: "堆叠 | 同一区域可容纳多个面板；仅活跃面板展开，其余折叠为 ToolBar 条目"
+ New: "堆叠 | 不适用——Dock 面板不使用 Editor Tab 栏；同一区域内的多个面板通过 Tab 组内的 Tab 栏切换"
```

### §3.5 REQ-F-069 (Panel Move)

AC2 completely rewritten:

```
- Old: AC2：面板移动至已有面板的区域（堆叠）
- Old: Panel B 应收起为 ToolBar 条目
+ New: AC2：面板移动至已有面板的区域（Tab 组）
+ New: Panel A 应以 Tab 标签页形式加入该区域的 Tab 组
+ New: Panel B 保留在 Tab 组中，其 Tab 切换为非活跃状态
```

Also fixed a bug in original AC3/AC4 where ToolBar entries were incorrectly
migrated across sides (Left Dock→Bottom Left should stay in LT, not migrate
to RT).

### REQ-F-022 (ToolBar Toggle Behavior)

Behavior change:

```
- Old: 点击当前可见且处于激活状态面板的条目应收起该面板
+ New: 点击当前已打开面板的条目应激活该面板的 Tab（获得焦点），不关闭面板
```

### New Requirements (§3.5.1)

Added 4 new Tab Group requirements:

| ID | Priority | Title |
|----|:--------:|-------|
| REQ-F-069-TG1 | 🔴 | Tab 组的 Tab 栏显示 |
| REQ-F-069-TG2 | 🔴 | Tab 组内 Tab 点击切换 |
| REQ-F-069-TG3 | 🟡 | Tab 组内 Tab 拖拽排序 |
| REQ-F-069-TG4 | 🟡 | Tab 组内关闭 Tab |

### Statistics Updated

```
- Old: 147 条需求（76 P0, 65 P1, 6 P2）
+ New: 151 条需求（78 P0, 67 P1, 6 P2）
```

## Pitfall: `replace_all` destroyed mermaid diagram

When fixing a `||` (double-pipe) formatting error introduced by earlier patches,
using `patch(replace_all=true, old="||", new="|")` also matched `||--o{` in the
mermaid ER diagram, corrupting all relationship lines. The fix: immediately
reverse-patch the mermaid block with the original text.

**Lesson:** Never use `replace_all` on punctuation sequences. Always use
targeted single-match patches with context.

## Verification

Final grep confirmation:

```
grep -n '堆叠' SRS.md
  52: Dock 层级布局由三个垂直堆叠的区域构成  ← correct (layout stacking, not panel behavior)
 252: 堆叠 | 不适用——...                        ← correct (explicitly says "not applicable")
 283: 堆叠 | 多 Tab 在 Tab 栏横向排列            ← correct (Editor Tab stacking)
 566: 可堆叠 | 否——LT/RT 是导航条而非面板容器     ← correct (LT/RT property table)

grep -c 'Tab 组' SRS.md  →  56
```
