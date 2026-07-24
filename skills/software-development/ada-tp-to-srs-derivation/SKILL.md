---
name: ada-tp-to-srs-derivation
description: Derive a Software Requirements Specification (SRS) from a Technical Protocol (TP) document — four derivation paths, multi-system SRS structure, REQ-F format with Chinese-English bilingual conventions, traceability matrix maintenance, and strict fidelity to source.
version: 1.5.0
platforms: [windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [srs, tp, requirements, derivation, chinese, avionics]
    related_skills: [ada-srs-writing, ada-srs-documentation, ada-requirements-authoring, ada-srs-lifecycle]
---

# TP-to-SRS Derivation（从技术协议派生 SRS）

当用户提供一份技术协议（TP / Technical Protocol）并要求编写 SRS 时使用本技能。特别适用于航空电子、嵌入式显示等领域的技术合同需求分析。

## When to Use

- 用户提供一份技术协议（.md/.docx）并要求编写 SRS
- 用户说「基于这份协议写一份SRS」
- 从合同/协议条款中系统化派生出软件需求

## TP-to-SRS 工作流

### Phase 1: 阅读与理解

1. 完整阅读 TP 文档，建立产品全景
2. 明确：有多少个系统/子工具、它们之间的上下游关系
3. 识别 TP 中所有的「要素」：界面、功能、文件格式、交互流程

### Phase 2: 向用户确认架构决策

在开始编写 SRS 之前，必须向用户确认以下决策（TP 通常不会涉及）：

| 问题 | 说明 |
|:----:|------|
| 部署方式 | 单机 / 网络 / B/S 架构 |
| 前端框架 | 如 Blazor WASM、Vue、React |
| 后端框架 | 如 ASP.NET Core、Node.js |
| 多个系统的关系 | 独立应用 / 同一平台的不同模块 |
| 系统间交互方式 | 文件传递（本地保存后导入）/ API 调用 / 共享后端存储 |
| 各系统是否共享后端 | **必须明确询问**：独立完整 B/S 系统（各有独立前后端）还是共享同一后端的不同前端。默认假设为独立系统 |
| 用户认证 | 需要登录吗？权限管理？是实际鉴权还是仅作为启动入口？ |

先输出规划方案，待用户确认后再正式撰写。

### Phase 2.5: 起草工作流

架构决策确认后，按以下顺序起草 SRS：

1. **§§1-2**（引言+总体描述）：术语表、架构图、功能概览、约束假设
2. **§3** 公共需求：登录入口等跨系统公共需求
3. **§4** 系统 A 功能需求：按子工具分组，提取公共模式
4. **§5** 系统 B 功能需求：界面布局、主要功能、文件交互
5. **§6** 系统间交互：文件传递、前后端通信
6. **§7** 非功能需求：性能、兼容性、可靠性、可维护性、安全
7. **附录**：变更记录、需求统计表、追迹矩阵
8. **格式校验**：检查编号连续性、围栏配对、优先级一致性
9. **统计校验**：确认附录统计与头部一致，用 Python 脚本逐行提取需求头部

**需求编号方案**：默认使用全局连续编号 `REQ-F-XXX`。对于 100+ 条需求的大规模 SRS，可选百位区间编号（REQ-F-0100~0199 对应 TP §1.x，REQ-F-0200~0299 对应 TP §1.3 等），区间内可灵活增补。一次选定后避免大规模重编号。

### Phase 3: 六条派生路径

| 路径 | 说明 | 应用场景 |
|:----:|:-----|:---------|
| **直接映射** | TP 条款直接对应一条需求 | TP「提供图形人机交互界面」→界面布局需求 |
| **拆分细化** | TP 一个条款拆为多条需求 | TP「生成 .c/.h」→参数配置 + 文件生成 + 编译兼容 |
| **跨子工具提取公共** | 多个子工具共享特性的公共需求 | 多个子工具都生成 .c/.h → 公共文件生成规范 |
| **架构衍生** | 从已确认的架构方案派生 | B/S → 登录入口、前后端通信、文件上传 |
| **精度修正** | 逐句回归 TP，修正表述精度 | TP「过程中同步」→修正 AC 时序；TP「线型」→补充线型类型选择 AC |
| **AC 原子化拆分** | 将粗粒度需求中独立的 AC 条件提升为独立需求 | 一条「线型.c/.h 文件生成」→拆为 .c 生成 / .h 生成 / A661 格式 / 编译兼容 / 索引获取 / 空配置校验 |

**约束**：前四类在首次编写阶段使用；精度修正（第五类）在用户要求进一步检查时使用，不新增 REQ-F 条目；AC 原子化拆分（第六类）在用户明确要求细化粒度时使用，**不主动做**——默认保持适中粒度。

### Phase 4: 需求条目编写

#### 4.0 子工具需求的三层组织结构

对每个子工具，按三层组织需求：

| 层级 | 包含内容 | 典型 Actor | 示例 |
|:----:|:---------|:----------:|------|
| **配置层** | 用户输入/导入/配置参数的功能 | Application Developer | 线型条目添加、占空比配置、颜色选择 |
| **生成层** | 系统处理、生成文件、校验的功能 | Application Developer | .c 文件生成、.h 文件生成、A661 格式、空校验 |
| **验证层** | 生成结果的外部验证 | Verification Engineer | 编译兼容性、按索引获取正确性 |

分层原则：配置层 = 用户做什么（每条配置独立为需求）；生成层 = 系统做什么（生成/输出/校验各一条）；验证层 = 外部验证（每条验证场景独立为需求）。

#### 4.1 需求条目格式

每条需求使用结构化格式（详见 `references/requirement-format-example.md`）：

```markdown
### REQ-F-XXX 🔴 [Actor: Application Developer]

**Title**
<中文标题>

**Description**
<中文功能描述>

**Acceptance Criteria**

AC1：<中文场景名称>

Given <英文前置条件>
When <英文触发操作>
Then <英文预期结果>
```

格式要点：
- 需求编号用 `###` 标题级；优先级符号放在编号后（🔴 P0 / 🟡 P1 / 🟢 P2）
- Actor 用方括号 `[Actor: RoleName]`；多角色用逗号分隔
- Title/Description/Acceptance Criteria 各为独立段落，用 `**粗体**` 作为段落标题
- 每个 AC 必须有场景名称（`AC1：显示登录界面`），不可只写 `AC1：`
- Given/When/Then 使用英文，各自独立一行
- 整个需求条目用代码围栏（`` ``` ``）包裹，围栏内包含从 `###` 标题行到最后一个 AC 的全部内容
- 每个需求条目末尾添加来源标注：`> **来源**: TP §x.x`

#### 4.2 优先级定义

| 符号 | 优先级 | 含义 |
|:----:|:------:|------|
| 🔴 | P0 — Mandatory | 必须有 — 系统不可用或无法交付 |
| 🟡 | P1 — Desirable | 建议有 — 缺失会显著降低可用性 |
| 🟢 | P2 — Optional | 可以有 — 增强功能 |

#### 4.3 常用 Actor

| Actor 名 | 对应角色 | 常见需求范围 |
|:--------:|:--------:|-------------|
| `Application Developer` | 应用开发工程师 | 使用资源工具，操作各子工具，生成文件 |
| `Verification Engineer` | 测试/验证工程师 | 验证生成文件格式正确性，预览效果 |
| `System Integrator` | 系统集成工程师 | 工程文件管理，DF 导入导出，工具间交互 |

#### 4.4 需求格式参考

参考 `references/requirement-format-example.md` 获取完整格式示例。更详细的格式规则（围栏配对、AC 编号、语言约定等）另见 `srs-requirement-format` 技能。双语约定详见 `references/bilingual-conventions.md`。

### Phase 5: 多系统 SRS 章节结构

| 章节 | 内容 |
|:----:|------|
| §1 | 引言（目的、范围、术语表、文档约定、系统架构） |
| §2 | 总体描述（产品全景、功能概览、用户特性、约束、假设） |
| §3 | 公共需求（登录入口等两个系统共享的需求） |
| §4 | 系统 A 功能需求 |
| §5 | 系统 B 功能需求 |
| §6 | 系统间交互需求 |
| §7 | 非功能需求 |
| 附录 | 变更记录、需求统计表、追迹矩阵 |

### Phase 6: 追迹矩阵维护

附录 C 必须包含 TP 条款 → SRS 需求的映射表。每条 TP 条款都被覆盖以证明无遗漏；架构衍生项标注「衍生：xxx」与协议派生项区分。

### Phase 7: 统计校验

编写完成后，通过 Python 脚本或 grep 从需求头部提取编号、优先级、角色，与附录 B 统计表逐项比对，确保 🔴🟡🟢 计数与表一致，总需求数 = 各章节之和。

### Phase 7.5: 来源标注

每个需求条目末尾（关闭 ``` 围栏之前）添加来源标注：`> **来源**: TP §x.x`。直接映射/拆分派生标注 TP 条款；架构衍生标注 `无（衍生：xxx）`；从 AC 独立出的子需求标注 `TP §x.x（自 REQ-F-XXX 派生）`。来源标注与附录 C 追迹矩阵应保持一致。

### Phase 8–10: 自进化迭代

自进化检查聚焦三个维度：术语一致性、AC 可测试性、边界案例遗漏。多轮迭代按轮次切换审视维度（第 1 轮：边界案例+AC 可测试性；第 2 轮：交叉引用+单 AC 需求扩充；第 3 轮：TP 原文逐句回归+架构一致性）。收敛标准：连续两轮改动量 < 5% 且 TP 逐句回归无遗漏。

第 3 轮（TP 逐句回归）实质上构成**第五类派生路径**——精度修正：重新审视已覆盖的 TP 条款，发现首次编写时的表述精度不足，通过修改 AC 内容来提升文档忠实度，不增加新 REQ-F 条目。

详细的自进化方法论和常见遗漏派生点模式清单见 `references/srs-self-evolution.md`。

## Common Pitfalls / 常见陷阱

### 1. 过度偏离 TP
引入了协议中未约定的功能。**对策**：所有需求应能从 TP 中找到直接或间接依据；架构衍生需求必须经用户确认。

### 2. 遗漏跨子工具公共需求
每个子工具重复定义相同的生成规范。**对策**：书写前先横向扫描各子工具，提取共同的交互/输出模式。

### 3. 统计表与需求头不一致
附录统计写 P0=27，实际头部只有 26 个 🔴。**对策**：用 Python 脚本从需求头部正则提取，自动生成计数。

### 4. Given/When/Then 语言混用
同一文档中有的 AC 用英文、有的用中文。**对策**：在 §1 文档约定中明确约定，全文统一。详见 `references/bilingual-conventions.md`。

### 5. 假设多个系统共享后端
TP 描述了多个独立工具，SRS 错误假设它们共享同一个后端。**对策**：Phase 2 中必须明确询问多系统的部署关系；除非用户明确说「共享」，否则默认视为独立系统；工具间文件交换通常通过本地文件系统完成；架构图应描绘每个系统的独立边界。

### 6. 需求编号格式不匹配用户预期
用户要求 `REQ-F-XXX` 而非 `REQ-{类别}-{序号}`。**对策**：TP 派生场景下默认使用全局连续编号 `REQ-F-XXX`。

### 7. 登录入口需求优先级模糊
登录界面是启动入口但没有实际鉴权。**对策**：登录入口需求（非实际鉴权）应标为 🟡 P1，只有 TP 明确要求强制身份验证时才标 🔴 P0。

### 8. 架构图未能体现系统独立边界
多系统场景中画成了共享同一个后端的结构。**对策**：每个系统画独立的竖列（前、后端的独立边界）；独立系统间文件交换用横向箭头标注「保存到本地 → 导入」；每个后端标注其专有职责。

### 9. 忽略需求编号与 TP 条款的映射标注
遗漏将 REQ-F 映射回 TP 条款的来源标注。**对策**：在每个需求末尾添加 `> **来源**: TP §x.x`，与附录 C 保持一致。

### 10. AC 中使用模糊用语
使用「正常」「相关」「主流」「合理」等不可测量的词。**对策**：替换为具体描述（如「正常执行，无异常报错」「Google Chrome 和 Microsoft Edge 的最新版本」）；编写完后扫描全文检查模糊词残留。

### 11. 遗漏异常/边界场景
AC 只描述 Happy Path。**对策**：每条需求至少检查 1 个异常场景；多输入需求检查空值、越界、格式错误；多文件操作检查同名处理策略；外部依赖检查组件不可用时的行为。

### 12. 需求条目包裹围栏后格式错乱
批量加 ``` 围栏后出现空围栏或与 `---` 分隔线冲突。**对策**：编写时同步加围栏，不要事后批量添加；完成后用 `scripts/verify-srs-fences.py` 验证围栏数 = 需求数 × 2。

### 13. 架构描述需要联动调整
用户纠正一个架构点后，§1.5 架构图、§1.6 系统关系、§6 交互需求、追迹矩阵都需要联动更新。**对策**：全文搜索所有相关描述（「共享」「同一后端」「上传至后端」等关键词），确保没有残留。

### 14. AC 独立为子需求时引用替换不完整
提取 AC 后仅删除原 AC 但忘记在 Description 中补充引用。**对策**：原 AC 位置替换为 `参见 REQ-F-XXX`；Description 末尾补充说明；追迹矩阵追加新行；统计表同步更新。详见 `references/ac-as-sub-requirements.md`。

### 15. 多个系统交互方式描述不清
TP 描述了工具间文件传递，但 SRS 未明确交互协议。**对策**：§6 系统间交互需求必须明确文件格式、传递方向、触发条件和异常处理。

### 16. TP §2 插件工具需求的细化深度不足
直接将 TP §2 的每节映射为一条简单需求，遗漏了可进一步派生的行为约束。**对策**：§2 的每个条款应根据「开发」「管理」「编辑」等动词进一步拆分；界面布局条款定义每个功能区的基本交互行为；对每个功能区检查是否有「操作 → 预览 → 修改」循环覆盖。

### 17. 需求粒度过粗，AC 承载了多条独立功能点
一条需求的多个 AC 描述了互不依赖的不同功能。**粒度判断标准**：如果 AC 的 Given/When/Then 与其他 AC 完全不共享相同的前置条件和触发操作，且有独立的可判定结果，则应为独立需求。详见 `references/ac-as-sub-requirements.md`。

## Overview

`ada-tp-to-srs-derivation` is the complete methodology for deriving a Software Requirements Specification from a Technical Protocol (TP) document — the contractual or technical agreement that defines what a system must do. Originally developed for avionics/embedded display systems, the skill covers every stage: reading and understanding the TP, confirming architecture decisions with the user (deployment, framework, multi-system relationships), six derivation paths (direct mapping, decomposition, cross-tool extraction, architecture-derived, precision correction, AC atomization), structured requirement authoring with REQ-F format and Chinese-English bilingual conventions, multi-system SRS chapter structures, traceability matrix maintenance, statistical verification, self-evolution iterations, and TP sentence-by-sentence regression. All requirements must be traceable to a TP clause — this skill enforces that fidelity.

## Verification Checklist

- [ ] All TP clauses covered: every paragraph in the TP document has at least one corresponding REQ-F requirement or a documented reason for exclusion
- [ ] Architecture decisions confirmed with user before drafting: deployment type, framework choices, multi-system relationships, shared vs independent backends, authentication requirements
- [ ] Requirement format validated: `### REQ-F-XXX` heading + priority emoji (🔴🟡🟢) + `[Actor: Role]`, Title/Description/Acceptance Criteria with Given/When/Then, source annotation (`> **来源**: TP §x.x`)
- [ ] Traceability matrix (Appendix C) complete: every TP clause mapped to REQ-F IDs; architecture-derived items marked "衍生：xxx"; no orphan REQ-F entries without a TP source
- [ ] Statistical verification passed: REQ-F count from headers matches Appendix B totals; priority distribution (🔴🟡🟢) matches; no ID gaps or duplicates; fence count = REQ-F count × 2

## 参考文件

- `references/requirement-format-example.md` — 完整的 SRS 需求条目格式示例（包含 REQ-F 编号、Actor 格式、AC 场景命名、Given/When/Then 规范）
- `references/srs-self-evolution.md` — SRS 文档自进化检查清单（术语一致性、AC 可测试性、边界案例遗漏三个维度 + 多轮迭代工作流 + 常见遗漏派生点模式清单）
- `references/bilingual-conventions.md` — 中文环境的双语约定（各文档元素语言分配表、约定的由来、常见格式问题及对策）
- `references/ac-as-sub-requirements.md` — AC 独立为子需求的完整工作流（适用条件、提取步骤、引用替换完整性、粒度判断标准与正反示例）
- `scripts/verify-srs-fences.py` — 围栏配对与格式验证脚本。使用 `python scripts/verify-srs-fences.py <SRS.md>` 运行。检查围栏数 = 需求数 × 2、连续围栏、围栏前分割线、ID 连续性、优先级分布、模糊词残留。
