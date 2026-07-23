---
name: ada-requirements-authoring
description: Write and review software requirements specifications (SRS). Use when authoring, reviewing, or supplementing requirements documents — especially for keeping SRS at the right abstraction level and avoiding design-level details.
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [srs, requirements, authoring, quality, specification]
    related_skills: [ada-srs-writing, ada-srs-documentation]
---

# Requirements Authoring: SRS vs Design Boundary

## When to Load

- User asks you to review an SRS for completeness or quality
- User asks you to write or supplement a requirements document
- You're writing requirements and need to stay at the right abstraction level
- User corrects you for writing design-level details in a requirements context

## Core Principle

> **SRS = 合同（交付什么、什么标准验收）。Design = 施工图（用什么工具怎么盖）。**

SRS describes **WHAT** — externally observable behavior and information. Design describes **HOW** — internal mechanisms, data structures, framework conventions.

## Self-Check: Three Questions

After writing each requirement, ask:

| # | Question | If YES, it crossed into design |
|---|----------|-------------------------------|
| 1 | 去掉框架/语言名词后，这句话意思还完整吗？ | "通过 React useEffect 返回清理函数" → 去掉 "React useEffect" 后意思变了 → 越界 |
| 2 | 换一个框架（React→Vue→Web Components），这句话还成立吗？ | "通过名为 `tabId` 的 prop 传入" → Vue 用 `:tab-id`，Web Components 用 attribute → 不通用 → 越界 |
| 3 | 这句话描述的是**外部可观察到的行为**，还是**内部如何做到的**？ | "系统使用 Map 存储页签映射" → 内部实现 → 越界 |

## Dangerous Vocabulary — Red Flags

These words signal you've likely entered design territory. Replace them:

| Category | Dangerous (Design) | Safe (SRS) |
|----------|-------------------|------------|
| Framework/API | `useEffect`, `useState`, `computed`, `watch`, `v-if` | Remove entirely; describe behavior |
| Data structures | `Map<K,V>`, `Set`, `Array<T>`, `Record<string, T>` | "集合""列表"等自然语言 |
| Design patterns | `Observer`, `Singleton`, `Factory`, `EventEmitter` | "通知""创建"等动词 |
| Rendering | `Virtual DOM`, `re-render`, `diff`, `commit` | "更新显示""刷新界面" |
| CSS mechanism | `CSS Variables`, `CSS-in-JS`, `styled-components`, `Tailwind` | "外观""视觉样式" |
| Browser APIs | `localStorage.setItem(...)`, `IndexedDB`, `fetch(...)` | "持久化存储""网络请求" |
| DOM | `DOM 节点`, `从文档中移除`, `事件监听器`, `渲染至 DOM` | "界面元素""从界面中移除""交互响应""显示在界面上" |
| Data format | `JSON` (when describing internal processing), specific file formats | "可序列化数据" (for external interfaces, JSON is acceptable as an interface contract) |

## Safe Sentence Patterns

### Describing WHAT information is provided
```
❌ 系统应向内容组件传递 { tabId: string, isActive: boolean } props 对象
✅ 内容组件应能够获取其所属页签的标识和激活状态
```

### Describing WHEN the system does something
```
❌ 系统应调用组件的 useEffect cleanup 函数释放资源
✅ 系统应在移除内容组件之前提供资源释放时机
```

### Describing conditions and outcomes
```
❌ 当 reducer 收到 CLOSE_TAB action 时更新 state
✅ 当页签被关闭时，系统应将该页签从所属面板中移除
```

### Describing observable quality
```
❌ 拖拽时系统使用 requestAnimationFrame 更新分割条位置
✅ 拖拽分割条时，面板尺寸的视觉更新应流畅无抖动
```

## The "Up-One-Level" Technique

Write the requirement, then deliberately rewrite it one notch more abstract. Ask: do the extra details in the original version affect acceptance?

```
【初稿】系统应通过 CSS 变量 --xdock-accent-color 暴露强调色
   ↓ 升一级
【二稿】系统应允许开发者自定义布局的强调色
   ↓ 检查：二稿足够验收吗？是否丢了关键约束？
【终稿】系统应允许开发者自定义布局的强调色  ← 刚好
```

The CSS variable mechanism belongs in the design document's "主题方案" section, not in SRS.

## What IS Legitimate SRS Content

These are often mistaken for design but are actually behavioral specifications:

- **Quantitative thresholds**: "折叠尺寸 36px", "拖拽阈值 4px", "延迟 300ms" — these define user-observable behavior
- **Algorithm as behavior rule**: "将面板划分为五个区域，外缘 25% 为方向停靠" — this defines HOW the user's drop position maps to docking direction (user-observable)
- **External interface contracts**: ARIA roles/attributes, JSON export format — these are external API specifications, analogous to REST endpoint definitions
- **International standards**: BCP 47 language tags (`zh-CN`, `en-US`) — referencing existing standards is fine
- **Quantitative quality metrics**: "帧率 ≥60fps", "初始化 ≤200ms", "偏移 ≤2px" — measurable acceptance criteria

## Common Pitfalls

1. **"I'm just being specific"** — Specificity about WHAT is good. Specificity about HOW is design. "The tab identifier must be available to the content component" is specific about WHAT. "Passed via a prop named `tabId` of type `string`" is specific about HOW.

2. **"The framework is already chosen"** — Even if the team has decided on React, the SRS should remain framework-agnostic. The architecture document captures the React-specific decisions. This keeps the SRS valid if the framework changes.

3. **"ARIA is design"** — No. ARIA is an external interface specification between the component and assistive technology. It's a contract, not an implementation choice. Similar to defining REST API response fields in an SRS.

4. **"Timing values are design"** — No. "300ms delay before auto-hide" defines user-perceivable behavior. The user experiences the delay. It's a behavioral specification.

## Review Checklist

When reviewing an SRS for design-level leakage, scan for:

- [ ] Any framework or library names
- [ ] CSS mechanism references (variables, modules, Tailwind class names)
- [ ] Browser API names (`localStorage`, `IndexedDB`, `fetch`)
- [ ] DOM terminology (`节点`, `事件监听器`, `文档`)
- [ ] Data structure type annotations (`Map<...>`, `Record<...>`)
- [ ] Design pattern names
- [ ] File format specifics (when describing internal processing, not external interfaces)
