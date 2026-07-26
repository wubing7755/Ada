---
name: ada-research-planning
description: "Use when stress-testing a plan, building a domain model, decomposing large work into specs and tickets, analyzing books or articles strategically, or evolving Hermes skills through systematic audits. Covers grilling, wayfinder planning, and self-evolution workflows."
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, planning, grilling, domain-modeling, specs, tickets, self-evolution]
    related_skills: [ada-project-audit, ada-pre-implementation-audit]
---

# 研究、规划与自进化

从模糊想法到可执行计划的前半段工作流——压力测试、领域建模、任务分解、战略阅读、技能自优化。

## Grilling（审视）：压力测试方案

Grilling 是聚焦式访谈，用来给方案加压。直接问：
- 目标、约束、利益相关者
- 失败模式、权衡、不可逆决策
- 继续直到方案的弱点暴露

Grill-with-docs 同时产出文档：术语表、ADR、假设、开放问题、决策记录。

## 领域建模

1. 建立通用语言（ubiquitous language）
2. 识别实体、值对象、工作流、不变量、边界
3. 当术语或所有权变更时记录架构决策

关键原则：模型必须在团队中能被无歧义地使用。模糊的术语比没有术语更危险。

## Wayfinder：大任务分解

适用于超出一个 agent 会话的工作量。

1. 生成决策地图——列出所有需要做的决定和它们的依赖关系
2. 逐个 ticket 解决
3. 每个 ticket 应声明：阻塞边、范围、验收检查、预期文件

## To-Spec → To-Tickets

**To-Spec**：将当前对话综合为规范，保留决策、约束、开放问题和验收标准。

**To-Tickets**：将规范或计划分解为 tracer-bullet tickets。

每个 ticket 包含：
- 阻塞前置条件
- 范围边界
- 验收标准
- 预期产出文件

## 战略阅读

带着一个明确的战略问题阅读：
- 输出：Do / Avoid / Watch-for
- 短期 / 中期 / 长期建议
- 避免泛泛的摘要

## 书镜（Book Mirror）

逐章分析，双列对比：
- 左列：保留源思想
- 右列：映射到读者生活/语境
- 长书可用并行章节分析

## 技能自进化

Agent 使用的工作流往往也是该工作流最好的审查者——因为 agent 必须执行这些指令。

进化循环：
1. 完整阅读进化范围内的每个文件
2. 六个维度审计：
   - 流程设计：步骤顺序是否合理？是否有冗余步骤？
   - 逻辑完整性：首次使用者会在哪里卡住？
   - 示例质量：命令、名称、示例是否最新且可运行？
   - 边界与陷阱：失败模式和审批是否已说明？
   - 跨文件一致性：术语、计数、锚点、映射是否一致？
   - 技能效率：推荐的技能/工具链是否真的有用？
3. 记录发现再编辑
4. 修补最高价值变更
5. 级联修复：目录、锚点、计数、相关文档
6. 重读变更文件确认编辑真实有效
7. 当一轮无实质性改进时停止

**新场景门槛**：仅当需求真实且重复出现、不能作为现有场景的小变体处理、且不是自指性噪音时，才添加新场景。

## Common Pitfalls

- **Grilling 不够深入就出方案**：未暴露的假设是最大的风险。至少找出 3 个失败模式再停止。
- **Wayfinder 过于细节**：决策地图不是实现方案。保持 ticket 级别的粒度。
- **To-Spec 丢失开放问题**：规范中的"待定"比错误答案更好——至少诚实。
- **技能自进化变成重构成瘾**：两轮无实质性改进→停止。文档不是代码，不需要持续重构。
- **书镜变成摘要**：双列对比的核心是"映射"，不是"复述"。左列是原料，右列是烹饪。

## Verification Checklist

- [ ] Grilling 至少暴露 3 个失败模式或未陈述的假设
- [ ] 领域模型的关键术语在团队中可无歧义使用
- [ ] Wayfinder 决策地图的每个节点有明确的阻塞关系和验收标准
- [ ] To-Tickets 每个 ticket 声明了范围、依赖、验收检查和预期文件
- [ ] 战略阅读输出包含 Do / Avoid / Watch-for 三个维度
- [ ] 技能自进化在无实质性改进时收敛停止
