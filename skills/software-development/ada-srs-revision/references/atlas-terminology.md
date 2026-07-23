# Atlas (xDocker) Terminology Decisions

Session: 2026-07-16 — SRS terminology refactoring
Reference implementations: VS Code User Interface docs, JetBrains Rider

## Core Renames

| # | Old | New | Rationale |
|---|-----|-----|-----------|
| 1 | Dock 区域 | 停靠区 | "Dock" prefix overloaded; VS Code uses "View Container", "Side Bar", "Panel" |
| 2 | Dock 面板 / DockPanel | 面板 / Panel | Rider calls them "Tool Window"; "面板" is sufficient |
| 3 | Dock 层级布局 | Dock 布局 | Drop "层级"; "Dock" stays as top-level system name |
| 4 | Left Dock Upper | 左侧上部停靠区 | — |
| 5 | Left Dock Lower | 左侧下部停靠区 | — |
| 6 | Right Dock Upper | 右侧上部停靠区 | — |
| 7 | Right Dock Lower | 右侧下部停靠区 | — |
| 8 | Bottom Left Dock | 底部左侧停靠区 | — |
| 9 | Bottom Right Dock | 底部右侧停靠区 | — |

## Unchanged (保留)

| Term | Reason |
|------|--------|
| Dock 布局 | Top-level system name, single "Dock" is acceptable |
| Left Dock / Right Dock / Bottom Dock | Parent containers (grouping two 停靠区), not individual slots |
| 区域 / Region | Internal concept, spatial slot |
| 编辑区 / Editor Area | VS Code: Editor; Rider: Editor |
| 工具条 / ToolBar (LT/RT) | VS Code: Activity Bar; Rider: Tool Window Bar |
| 分割条 / Splitter | Standard term |

## Panel Stacking → Tab Group Model

Replaced "面板堆叠" (one panel expanded, others collapsed to ToolBar entries)
with Rider's Tab Group model:
- Multiple panels in same 停靠区 form a Tab Group
- Each panel has a 面板标签页 (Panel Tab) in a 面板标签栏 (Panel Tab Bar)
- LT/RT entries are persistent switches, not collapsed-panel proxies
- Clicking an LT/RT entry for an already-open panel activates its tab (doesn't close it)

## Tab Concept Generalization

Tab is now a general concept with two sub-types:
- 编辑器标签页 (Editor Tab) — in Editor View tab bars
- 面板标签页 (Panel Tab) — in 停靠区 Tab Group tab bars

## VS Code Reference Terminology

| VS Code Term | XDocker Equivalent |
|---|---|
| Workbench | Dock 布局 |
| Activity Bar | ToolBar (LT/RT) |
| Primary/Secondary Side Bar | Left Dock / Right Dock |
| Panel | Bottom Dock |
| View | 面板 / Panel |
| View Container | 停靠区 |
| Editor Group | Editor View |
| Status Bar | Status Bar |

## Rider Reference Terminology

| Rider Term | XDocker Equivalent |
|---|---|
| Tool Window | 面板 / Panel |
| Tool Window Bar / Stripe | ToolBar (LT/RT) |
| Editor | Editor Area |
| Status Bar | Status Bar |
