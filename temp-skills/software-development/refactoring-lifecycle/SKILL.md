---
name: refactoring-lifecycle
description: 工程级重构全流程 — 通用架构重构与 .NET 专项重构的统一入口。从方案设计到分阶段执行的完整方法论。
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
metadata:
  hermes:
    tags: [refactoring, architecture, engineering, dotnet, umbrella]
    sub_skills: [engineering-refactoring, dotnet-engineering-refactoring]
---

# 工程级重构生命周期

从"能用"到"工程级可维护"的重构方法论。适用于用户说"工程级""达不到我的标准""架构升级"等场景。

## 技术栈路由

| 项目类型 | 入口技能 | 说明 |
|---------|---------|------|
| **.NET / C# / Blazor** | `dotnet-engineering-refactoring` | 包含领域原语、Orchestrator 模式、Blazor 组件模式等 .NET 专项 |
| **通用 / 其他语言** | `engineering-refactoring` | 语言无关的架构级重构方法论 |

## 共享工程哲学

两个子技能共享以下原则：

### 核心标准

- **类型系统承载约束**，不靠注释和约定
- **接口承载协议**，不靠文档描述契约
- **编排与实现分离**，Orchestrator 不干 Executor 的活
- **全项目一致性**，同一概念同一模式，不允许特例

### 执行模式

```
方案文档 → 逐 Phase 执行 → 独立验证 → 提交
  │            │              │           │
  docs/      实现改动     dotnet build   git commit
  refactoring/           dotnet test    (每 Phase)
                         dotnet format
```

1. 先出详细方案文档（`docs/refactoring/phase-N-M-plan.md`）
2. 方案确认后逐 Phase 执行
3. 每 Phase 独立验证：`dotnet build` → `dotnet test` → `dotnet format`
4. 每 Phase 独立 `git commit`，Phase 间不混合改动

### 方案文档必备

- 工程质量标准
- 每 Phase 目标 / 设计 / 变更清单 / 分级验证
- 依赖图
- 后续规划

## 使用方式

根据项目技术栈选择入口技能，执行前先出方案文档，确认后逐 Phase 推进。
