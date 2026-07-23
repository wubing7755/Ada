---
name: ada-srs-lifecycle
description: SRS 全生命周期管理 — 从 TP 派生、编写、审查到大规模修订的统一入口。按阶段路由到对应的子技能。
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
metadata:
  hermes:
    tags: [srs, lifecycle, requirements, umbrella]
    sub_skills: [tp-to-srs-derivation, srs-writing, srs-review, srs-revision]
---

# SRS 生命周期

SRS 文档从无到有、从初稿到终稿的完整流程。根据当前所处阶段加载对应子技能。

## 生命周期四阶段

```
TP 文档 ──→ [Phase 1: Derive] ──→ [Phase 2: Write] ──→ [Phase 3: Review] ──→ [Phase 4: Revise]
              tp-to-srs-            srs-writing          srs-review            srs-revision
              derivation
```

| 阶段 | 技能 | 输入 | 输出 | 触发词 |
|------|------|------|------|--------|
| **Derive** | `tp-to-srs-derivation` | 技术协议 (TP .md/.docx) | SRS 初稿 | "基于这份协议写 SRS" |
| **Write** | `srs-writing` | 需求描述/初稿 | 结构化 SRS | "编写 SRS""优化 SRS" |
| **Review** | `srs-review` | 已有 SRS 文档 | 审查报告 | "审查 SRS""检查需求" |
| **Revise** | `srs-revision` | SRS + 变更指令 | 修订后 SRS | "改这个概念""术语统一" |

## 共享约定

### REQ-F 格式

```
### REQ-F-XXX 🔴 [Actor] 标题
> **来源**: TP §x.x

**Description**: ...

**AC**:
AC1：场景名：
Given ...
When  ...
Then  ...
```

### 文档结构

1. Introduction (§1)
2. 术语定义 (§2)
3. 功能需求 (§3, REQ-F-XXX)
4. 非功能需求 (§4, NFR-XXX)
5. 附录

### 核心原则（贯穿全部阶段）

- **文档纯粹性**: 不引用具体编辑器实现，不保留历史编辑注解
- **需求≠实现**: 描述 What，不描述 How
- **术语一致性**: 同一概念全文统一，入口在 §2 术语定义
- **可追溯性**: 每条需求标注 TP 来源

## 使用方式

加载本 skill 后，根据用户意图选择对应阶段，再加载对应子技能获取详细工作流。
