---
name: ada-refactoring-lifecycle
description: "Use when an agent is planning or executing engineering-grade refactoring, especially multi-phase architecture work, .NET/C#/Blazor refactors, domain primitives, orchestration extraction, or user requests like 工程级, 架构升级, 达不到标准. Load this router before choosing the stack-specific refactoring skill."
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [refactoring, architecture, engineering, dotnet, umbrella]
    related_skills: [ada-engineering-refactoring, ada-dotnet-engineering-refactoring]
    sub_skills: [ada-engineering-refactoring, ada-dotnet-engineering-refactoring]
---

# 工程级重构生命周期

从"能用"到"工程级可维护"的重构方法论。适用于用户说"工程级""达不到我的标准""架构升级"等场景。

## Overview

This skill serves as the unified entry point for engineering-grade refactoring across technology stacks. It routes by project type: .NET/C#/Blazor projects use stack-specific patterns (domain primitives, orchestrator extraction, Blazor component patterns), while all other languages use language-agnostic architectural methodology. Both share a common engineering philosophy: type systems carry constraints, interfaces carry protocols, orchestration is separated from implementation, and whole-project consistency is non-negotiable.

The lifecycle follows a strict sequence: produce a detailed plan document (`docs/refactoring/phase-N-M-plan.md`), get user approval, execute phase by phase, independently verify each phase (`dotnet build → dotnet test → dotnet format`), and commit each phase separately.

## When to Use

Use when:
- The user says "工程级" (engineering-grade), "架构升级" (architecture upgrade), or "达不到我的标准" (doesn't meet my standard)
- A project needs systematic multi-phase refactoring rather than one-off cleanup
- The technology stack is known and a specific sub-skill should be routed to
- Each refactoring phase needs independent verification and isolated commits

Do **not** use for: single-file fixes, pre-commit formatting, one-off code review findings, or bug fixes.

## 技术栈路由

| 项目类型 | 适用模式 | 说明 |
|---------|---------|------|
| **.NET / C# / Blazor** | .NET 专项重构 | 领域原语、Orchestrator 模式、Blazor 组件模式 |
| **通用 / 其他语言** | 语言无关架构重构 | 类型系统约束、接口协议、编排分离 |

## 共享工程哲学

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

## Agent Activation

Use this as a router when refactoring scope spans multiple files, phases, or architectural boundaries. Once the stack is known, read the routed sub-skill before proposing edits.

| Project/task signal | Route to |
|---------------------|----------|
| `.sln`, `.csproj`, `.cs`, `.razor`, Blazor, C#, public API stabilization | `ada-dotnet-engineering-refactoring` |
| Other stacks, general architecture refactor, interface/protocol/orchestration redesign | `ada-engineering-refactoring` |

Do not use for one-line bug fixes, simple formatting, or isolated code review comments.

## Common Pitfalls

- **Jumping straight to implementation without a plan.** The user's rejection of mechanical changes means the approach must be rethought — not just the code. Always write the plan document first and get explicit approval.
- **Mixing changes across phases in a single commit.** Each phase must be independently verifiable and committed separately. Cross-phase mixing makes bisecting and reverting impossible.
- **Skipping the verification step between phases.** `dotnet build → dotnet test → dotnet format` is mandatory after every phase. A phase that "looks correct" but fails the gate compounds errors in subsequent phases.
- **Using the wrong approach for the stack.** .NET/C#/Blazor projects need domain-primitive and Blazor-component patterns specific to that stack. Using the generic language-agnostic approach misses stack-specific optimizations.
- **Abandoning the plan mid-way without updating it.** If a phase reveals new information that changes later phases, update the plan document before continuing — don't just improvise.

## Test Migration across a Removed API

Migrate tests when a library's public API is removed or replaced (e.g. a
legacy template API → DI/Route/Map). The failure mode this prevents: removing
the API first, then discovering every test and the NuGet consumer sample
break, then scrambling to migrate under a broken build.

**Migrate-then-remove ordering (safe sequence)**:
1. **Migrate consumers while the old API still exists.** Rewrite tests and the
   NuGet consumer sample to the new mechanism; run the focused suite until
   green. This separates migration errors from removal errors.
2. **Add replacement coverage in a NEW test file** for behavior the old API
   used to prove (lifecycle remount, single-update, dispose/no-stale callback,
   error code + no exception details). Do not weaken existing tests to assert
   less.
3. **Remove the API and every consuming branch** — component parameters,
   render-tree pass-through attributes (renumber the `sequence` values),
   recovery-key tuple members, legacy branches with `TODO(phase-N)` markers.
4. **Delete the `PublicAPI.Unshipped.txt` entries** for the removed members.
5. **Verify the NuGet consumer**: pack new packages, delete only the
   consumer's local package cache dirs, `dotnet restore <consumer>.sln
   --configfile NuGet.Config`, then build/test/format the consumer against the
   packed artifacts.
6. **Full gate + stale-reference scan**: solution build/test, `dotnet format
   --verify-no-changes`, `git diff --check`, and grep src+tests for the removed
   identifier (zero matches).

**bUnit TestContext pitfalls**:
- **Service freeze after first render.** bUnit's `TestServiceProvider` throws
  once any component rendered. Register ALL content kinds and services before
  the first `RenderComponent` — including kinds used by a second host later in
  the same test.
- **Nullable `[Inject]` still requires registration.** `[Inject] private Foo?
  Probe` throws `Cannot provide a value for property 'Probe'` when `Foo` is
  not registered; nullability does not make injection optional. Register the
  probe/tracker singleton in the test class constructor and resolve it via
  `Services.GetRequiredService<T>()`.
- **Per-test service instances.** Each xUnit test gets a fresh TestContext, so
  constructor registrations are safe; register a state holder in the test body
  when a test needs its own instance with a custom initial value.
- When migrating a template wrapper to DI: if the wrapped component already
  derives from a content component/`ComponentBase` with a `Content` parameter,
  the DI path auto-injects `Content` — the wrapper is redundant and can be
  deleted outright.

**Scripted mechanical edits: the correct rule**. Deleting identical
`.Add(component => component.X, Value));` lines across a file is the classic
trap. The deleted line carries the chain's statement terminator.
- **Correct rule**: when deleting the LAST `.Add(...));` line of a fluent
  chain, append the statement terminator to the PREVIOUS line. A self-balanced
  single-line `.Add(...)` always needs exactly `);` appended.
- Do NOT append `));` blindly: count open parens (`.Add(component =>
  component.ChildContent, Declaration("Before"))` is already self-balanced and
  needs only `);`).
- **Compile after EVERY script step.** A second "fix" script that recomputes
  parens can corrupt more than it repairs. Recovery is `git checkout -- <file>`
  and redo; keep edits small and verify each step. For a handful of call
  sites, prefer the `patch` tool over scripts.

**dotnet format aftermath**: script rewrites can leave mixed CRLF/LF —
`dotnet format <sln> whitespace --no-restore` fixes ENDOFLINE diagnostics;
strip trailing blank lines (`text.rstrip('\n') + '\n'`) for "new blank line at
EOF" diffs; re-run the test suite after whitespace normalization.

## Verification Checklist

- [ ] Plan document exists in `docs/refactoring/` with all required sections (quality standards, phase goals, change lists, verification criteria, dependency diagram)
- [ ] User has explicitly approved the plan before any code changes begin
- [ ] Each phase passes `dotnet build`, `dotnet test`, and `dotnet format --verify-no-changes` independently
- [ ] Each phase is committed as a separate, isolated git commit
- [ ] The correct approach was routed based on technology stack (.NET → stack-specific patterns, other → language-agnostic methodology)
