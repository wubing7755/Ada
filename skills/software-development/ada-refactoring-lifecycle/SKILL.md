---
name: ada-refactoring-lifecycle
description: "Use when planning and executing engineering-grade refactoring — unified entry point for general architectural refactoring and .NET-specific refactoring. Covers the full lifecycle from proposal design through phased execution."
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [refactoring, architecture, engineering, dotnet, umbrella]
    related_skills: [ada-engineering-refactoring, ada-dotnet-engineering-refactoring]
    sub_skills: [engineering-refactoring, dotnet-engineering-refactoring]
---

# 工程级重构生命周期

从"能用"到"工程级可维护"的重构方法论。适用于用户说"工程级""达不到我的标准""架构升级"等场景。

## Overview

This skill serves as the unified entry point for engineering-grade refactoring across technology stacks. It routes .NET/C#/Blazor projects to .NET-specific refactoring patterns (domain primitives, orchestrator extraction) (which provides domain primitives, orchestrator patterns, and Blazor component patterns) and all other languages to language-agnostic architectural refactoring (language-agnostic architectural methodology). Both sub-skills share a common engineering philosophy: type systems carry constraints, interfaces carry protocols, orchestration is separated from implementation, and whole-project consistency is non-negotiable.

The lifecycle follows a strict sequence: produce a detailed plan document (`docs/refactoring/phase-N-M-plan.md`), get user approval, execute phase by phase, independently verify each phase (`dotnet build → dotnet test → dotnet format`), and commit each phase separately.

## When to Use

Use when:
- The user says "工程级" (engineering-grade), "架构升级" (architecture upgrade), or "达不到我的标准" (doesn't meet my standard)
- A project needs systematic multi-phase refactoring rather than one-off cleanup
- The technology stack is known and a specific sub-skill should be routed to
- Each refactoring phase needs independent verification and isolated commits

Do **not** use for: single-file fixes, pre-commit formatting, one-off code review findings, or bug fixes.

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

## Common Pitfalls

- **Jumping straight to implementation without a plan.** The user's rejection of mechanical changes means the approach must be rethought — not just the code. Always write the plan document first and get explicit approval.
- **Mixing changes across phases in a single commit.** Each phase must be independently verifiable and committed separately. Cross-phase mixing makes bisecting and reverting impossible.
- **Skipping the verification step between phases.** `dotnet build → dotnet test → dotnet format` is mandatory after every phase. A phase that "looks correct" but fails the gate compounds errors in subsequent phases.
- **Using the wrong sub-skill for the stack.** .NET/C#/Blazor projects need the domain-primitive and Blazor-component patterns in .NET-specific refactoring patterns (domain primitives, orchestrator extraction). Using the generic skill misses stack-specific optimizations.
- **Abandoning the plan mid-way without updating it.** If a phase reveals new information that changes later phases, update the plan document before continuing — don't just improvise.

## Verification Checklist

- [ ] Plan document exists in `docs/refactoring/` with all required sections (quality standards, phase goals, change lists, verification criteria, dependency diagram)
- [ ] User has explicitly approved the plan before any code changes begin
- [ ] Each phase passes `dotnet build`, `dotnet test`, and `dotnet format --verify-no-changes` independently
- [ ] Each phase is committed as a separate, isolated git commit
- [ ] The correct sub-skill was routed to based on technology stack (.NET → ada-dotnet-engineering-refactoring, other → ada-engineering-refactoring)
