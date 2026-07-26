---
name: ada-srs-writing
description: "Use when authoring or refining a Software Requirements Specification (SRS) — structural patterns, quality rules, VS Code-style design referencing, spatial diagram templates, requirement renumbering, and iterative refinement workflow."
version: 1.1.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [srs, writing, requirements, documentation, chinese]
    related_skills: [ada-srs-revision, ada-srs-lifecycle, ada-srs-review]
---

# SRS 文档编写与优化

编写和迭代优化软件需求规范文档的结构化方法论。涵盖文档结构模板、核心编写原则、四阶段优化工作流和实战陷阱。

## 文档结构与格式规范

### SRS 标准章节结构

| § | 章节 | 内容 |
|---|------|------|
| §1 | Introduction | Purpose, scope, system architecture diagram + constraint table, data model, terminology table, document conventions, spatial concepts |
| §2 | Overall Description | Product perspective, quick-finder navigation table, user characteristics, constraints, assumptions |
| §3 | Functional Requirements | Grouped by concern, per-section requirement index, REQ-F-XXX format |
| §4 | Non-Functional Requirements | Performance, compatibility, security, accessibility — testable criteria |
| §5 | Statistics | By section/priority, by role |
| Appendices | Lifecycle diagrams, deferred requirements, traceability matrix, change log |

### 需求格式规范

```
### REQ-F-XXX 🔴 [Actor: Role]
> **来源**: TP §x.x

**Title**: <one-line title>

**Description**: <what the system should do>

**AC**:
AC1：<scenario name>：
Given <precondition>
When  <action>
Then  <expected result>
```

### 优先级符号

| 符号 | 级别 | 含义 |
|:----:|:----:|------|
| 🔴 | P0 | Must have — 系统不可用 |
| 🟡 | P1 | Should have — 显著影响可用性 |
| 🟢 | P2 | Could have — 增强 |

必须在每个需求头中使用，不能仅在 §1 定义后就不再出现。

### 双语约定

- 术语表：`English（中文）` 格式（English 在前）
- 需求正文：每个分段首次出现术语时使用 `English（中文）`，后续可简化
- Region 名称（如 `Left Dock Upper`）保持纯英文以与代码映射一致
- 术语审计详细操作参见系统性 SRS 审查流程 (Pass C)

---

## 核心原则

### 1. 文档纯粹性

SRS 应自包含，不引用任何具体编辑器的实现：

- ❌ "参照 VS Code Workbench 设计"、"类似 IDE 的"、"类似 VS Code Activity Bar"
- ✅ "采用扁平层级模型"、"LT/RT 作为面板导航入口"、"Dock 负责容纳，ToolBar 负责导航"

同样，SRS 中不应保留"已合并: REQ-F-xxx"、"已删除: REQ-F-xxx"、"来源: REQ-F-xxx"等历史编辑注解——这些是草稿阶段的标注，最终文档的编号体系本身就是唯一的权威来源。

### 2. 需求≠实现细节

SRS 定义**行为**，不是**数值常量**。以下属于实现细节，不应出现：

| 反例 | 正例 |
|------|------|
| "默认值为 36px" | "折叠至最小显示尺寸（如仅保留标题栏高度），具体数值由详细设计确定" |
| "颜色为 #333333" | "以可辨识的视觉反馈表明交互状态" |
| 硬编码的超时值 | 定义行为后加"(具体数值由详细设计确定)" |

**例外**：行为参数（如拖拽触发阈值 4px、防抖延迟 500ms）和非功能性能指标（初始化 ≤200ms）可以在 SRS 中保留——它们是可测量的行为约束，不是实现决策。

### 3. 概念先行 — 三种容器必须区分

在 §1 中定义三种空间概念，全文必须严格遵循其适用范围：

| 概念 | 出现位置 | 切换方式 | 关键属性 |
|------|---------|---------|---------|
| **Editor Tab** (标签页) | 仅在 Editor Area | 点击 Tab / Ctrl+Tab | 横向排列、溢出、去重、固定、分屏 |
| **Dock Panel** (面板) | Dock 区域 | LT/RT 条目点击 | 堆叠（仅活跃面板展开）、跨区域移动 |
| **ToolBar Entry** (条目) | LT / RT | 条目点击 | 1:1 对应面板，移动时迁移 |

在 Editor 上下文中，拆分出的编辑器子区域称为**视图**，不能称为"面板"——避免与 Dock Panel 混淆。

### 4. 堆叠语义

同一 Dock 区域可有多个面板，但**仅活跃面板展开**，其余折叠为 ToolBar 条目。重要推论：
- 堆叠 ≠ 两个面板同时可见纵向排列（那是旧 SWAP 模型的遗留）
- 面板移动至已有面板的区域 → 新面板展开，旧面板收起到 ToolBar
- Bottom Dock 本身不参与五区域方向停靠——它只作为"下方停靠"的方向触发器

### 5. AC 扩展优先于新需求

当新行为是对已有约束的自然延伸时，扩展已有需求的 AC，而不是创建新的独立需求：
- 好处：上下文集中，评审时不需要对照多处
- 判断标准：新行为是否直接推导自已有约束？是 → 补 AC；否 → 新需求

### 6. 文档内一致性

- §1.6.2 定义优先级符号（🔴🟡🟢），则所有需求头中必须使用这些符号
- 术语表定义过的概念，全文统一使用
- 层级树/架构图中的标注要与约束表一致
- **新增需求编号规则**：新增独立需求时，编号从现有最大编号后自动递增（如当前最大为 REQ-F-139，则新增为 REQ-F-140），不受所在章节号约束。编号不必按章节分组。
- **术语双语规则**：术语表采用 `English（中文）` 格式（English 在前，中文在括号中）。在需求条目内部（Title、Description、每个 AC 各自独立分段），**每个分段中首次出现的术语**使用 `English（中文）` 格式，同一分段内后续出现可简化为英文或中文。Region 名称（如 `Left Dock Upper`）保持纯英文以与代码映射一致，不在正文中添加中文括号。术语审计的详细操作参见系统性术语审计流程 (Pass C)。
- **系统性术语审查**：当文档出现大量术语混用时，运行系统性术语审计流程进行术语审计。核心流程：扫描→分类→术语表提案→批量替换→手动重写→双语注释→验证。

---

## 优化工作流

### Phase 1: 理解现状
- 阅读完整 SRS 文档
- 对照设计参照（VS Code）检查概念模型是否一致
- 识别：过时概念、死代码、概念混用、实现细节泄漏

### Phase 2: 提案
- **先讨论方案再动手**：列出要改什么、为什么改、影响范围
- 大改动（概念模型变更、大量需求重写）必须提案并获得确认
- 小改动（删一个 AC、修正措辞）可以直接执行

### Phase 3: 执行
- 从基础层改起：§1（架构/数据模型）→ §3 特征表 → 具体需求 → 交叉引用
- 每次改动后全局搜索残留引用（如旧术语、已删除的错误码）
- 使用 `replace_all=true` 处理批量替换（如 `Editor Container` → `Editor Area`）

### Phase 4: 收尾
- 更新附录变更记录
- 更新 §1.2 范围表（如果章节名称或内容变了）
- 更新各节的需求索引
- 更新 §5 需求统计

---

## 常见陷阱

- **AC 描述不可能发生的场景**：检查"运行时检测"类 AC 是否真的有触发路径
- **概念混用**：Editor Tab（标签栏操作）≠ Dock Panel（LT/RT 切换），不能把 Tab 特有的需求（溢出/去重/固定）套在 Dock 面板上。在 Editor 上下文中拆分出的编辑器子区域称为"视图"而非"面板"
- **中间容器层**：Content Area / Main Area 这类无功能语义的中间层应该移除，采用扁平 Workbench 模型
- **层级树重复**：§1.3 和 §3.1 不应各画一遍相同的层级树——树在 §1.3，视觉图在 §3.1，互相引用即可
- **Work Area 双重定义**：全局替换 "Main Area→Work Area" 可能导致术语表中出现两个矛盾的 Work Area 条目，必须检查并合并
- **互换 vs 堆叠**：堆叠模型中同一区域仅一个面板展开。旧 SWAP 模型的残留（如"面板互换后分割条方向适配"）应彻底删除
- **需求头格式**：`REQ-F-XXX` + 优先级符号 + `[Actor: 角色]`，不要混用 `[P0]` 文本格式
- **自动替换导致的术语碰撞**：执行全局 `停靠区`→`Dock 区域（Dock Region）` 替换后，可能误将 REQ-F-052 中的 "方向停靠区"（drop zone，视觉概念）改为 "方向Dock Region"（layout slot，空间概念）。这两个是不同的语义域——修复时改回 "方向停靠区" / "中心停靠区"
- **不实现堆叠时的清理**：如果项目明确不实现面板堆叠（Stack），移除所有 "堆叠"、"Tab 组"、"面板标签页/栏" 相关术语。§3.5.1 整节（REQ-F-069-TG1~TG4）应完全删除而非重写，附录索引表中对应行同步移除
- **Splitter 调整的是区域边界而非 Dock Panel**：§3.6 的需求常将分割条描述为"调整 Dock Panel 尺寸"，实际上它们调整的是相邻 **Region** 的边界（Left Dock ↔ Editor Area、Work Area ↔ Bottom Dock 等）。修正时在 §3.6 开头列出所有 6 条分割条位置，并将需求中的 `Dock Panel`/`面板` 统一改为 `区域`
- **分割条最小尺寸约束的回弹滞后**：拖拽分割条达到最小尺寸限制后，分割条停止移动。如果鼠标继续向前然后反向，分割条不应立即跟随鼠标回弹——应等鼠标越过分割条实际位置后才恢复联动。这是一种标准的拖拽 UX 行为（VSCode/Rider 均有）。Editor Tab 拖拽到 Editor View 上有 5 个方向区域（上/下/左/右/中心），Dock Panel 移动只有单一区域——拖至目标 Dock Region 任意位置释放即完成（类似 VSCode/Rider 的 Tool Window 拖拽）。§3.5 适用范围中必须明确写出此区别
- **`replace_all=True` 仅限单行短文本**：对多行、跨段落文本**永远不要**使用 `replace_all=True`——它会在文档中多处匹配，造成灾难性的大面积删除（覆盖标题、需求正文、SVG 代码等）。多行替换用 Python 脚本精确匹配+逐个替换。append 操作（如新增需求）用 `patch` + `replace` 插入精确位置
- **需求删除后清理代码围栏**：每个需求用 ``` 包裹。删除需求时必须同时删除其开始和结束的 ``` 标记。删除后运行脚本检查：总 ``` 数量必须是偶数，且不应出现连续两个 ``` 中间无内容。否则 Markdown 渲染错乱，后续 `grep -n REQ-F-XXX` 也会显示孤儿行
- **恢复备份后批量重放修改**：patch 破坏文件后，从最新备份恢复，然后写一个 Python 脚本一次性重放所有已批准的修改——不要逐个 patch，容易再次出错且难以追踪已应用了哪些变更。脚本中用 `str.replace()` 做精确字符串匹配（每项只替换一次），对真正复杂的替换用 `re.sub()` + `count=1`。最后用验证脚本确认关键检查点全部通过
- **冗余需求的识别与删除**：当已有需求明确定义了全集行为（如 `六个 Dock Region 任意两个之间均可跨区域拖拽`），后续专门针对某两个区域的需求即为冗余，应删除。同步更新章节索引、§5 统计、附录。对不合理的需求也要质疑并删除（如 REQ-F-130 "禁止全部折叠"——Rider 中所有面板均可折叠，LT/RT 条目始终可恢复）
- **删除需求后更新依赖 AC**：当删除某条需求时，搜索所有引用该编号的其他需求（如 REQ-F-XXX 被 REQ-F-YYY AC3 用 `（REQ-F-XXX）` 引用），更新引用文本并检查语义影响——被删除需求的约束可能使依赖需求的 AC 从"拒绝操作"变为"允许操作"
- **SVG 在 VS Code Markdown 中的渲染规则**：
  1. 每行必须有 `> ` 前缀（blockquote 内）
  2. `rx` 不是 CSS 属性，必须用内联属性 `<rect rx="2">`
  3. 避免特殊 Unicode（`✕` U+2715 会使 SVG 静默失败）
  4. `stroke-dasharray` 必须配 `stroke-width`
  5. `<style>` 块在 blockquote 内安全，非 blockquote 内不可靠
  6. 备用方案：ASCII 框图 / Mermaid flowchart / 需要颜色编码时才用 SVG

---

## 变更记录格式

每次修改后追加到附录变更记录：

```markdown
| 日期 | 变更 | 作者 |
|------|------|:----:|
| YYYY-MM-DD | **简短标题**: 具体变更描述 | — |
```

---

## Overview

`ada-srs-writing` provides a structured, four-phase methodology for writing and iteratively refining Software Requirements Specification documents. Grounded in real-world SRS authoring experience (notably the Atlas/xDocker dock-layout system), it covers document structure templates (§1-§6 canonical layout, requirement format, priority conventions, bilingual rules), core principles (document purity, requirements-vs-implementation boundary, concept separation, stacking semantics), the optimization workflow (Understand → Propose → Execute → Wrap-up), and an extensive pitfall catalog capturing hard-won lessons from multi-thousand-line document revisions. This is the primary writing skill in the SRS lifecycle.

## When to Use

Use when:
- Writing a new SRS section or requirement from scratch
- Refining or "optimizing" an existing SRS — restructuring, improving clarity, fixing concept confusion
- User asks to "优化 SRS", "修改需求文档", or "讨论这条需求是否合理"
- Aligning SRS terminology and concepts with a reference design (e.g., VS Code Workbench)
- Adding, removing, or restructuring functional requirements and their acceptance criteria
- Incorporating review findings into the document into the document

Don't use for:
- One-off typo fixes — use a simple `patch` call instead
- Full-document audit — use systematic 12-pass SRS review methodology
- Large-scale terminology revision across hundreds of occurrences — use large-scale revision with blast-radius analysis for global terminology changes

## Verification Checklist

- [ ] Document purity: no references to specific editor implementations (VS Code, Rider) or historical edit annotations ("已合并: REQ-F-xxx", "已删除: REQ-F-xxx")
- [ ] Requirements describe WHAT, not HOW: pixel values, colors, and exact timings are in design docs (behavioral parameters like 4px drag threshold and 200ms performance targets are acceptable)
- [ ] Concept separation enforced: Editor Tab (标签页), Dock Panel (面板), and ToolBar Entry (条目) are defined in §1 and used consistently — no Tab-requirements on Dock Panels or vice versa
- [ ] Terminology consistency: same concept uses same term everywhere; §2 glossary is the single source of truth; bilingual annotations follow `English（中文）` format on first use per segment
- [ ] After any structural change: §5 statistics recalculated, section indexes updated, appendix change log appended, and cross-references verified with `search_files`

## 参考文件

- `references/srs-renumbering.md` — 需求重编号的可靠程序（避免 ID 重复/跳号）
- `references/spatial-diagram-templates.md` — 空间概念图的 ASCII/SVG/Mermaid 模板及 VS Code 渲染规则
