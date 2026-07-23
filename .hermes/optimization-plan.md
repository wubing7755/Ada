# Ada Skills 优化方案

> 基于质量审查报告 (`.hermes/audit-report.md`)
> 目标: 将 45 个 `temp-skills/` 改造为可通过 `hermes profile install` 安装的标准技能

---

## 方案总览

| 阶段 | 内容 | 影响范围 | 优先级 |
|------|------|----------|--------|
| Phase 1 | 目录迁移 + 命名重铸 | 全部 45 技能 | **P0** |
| Phase 2 | Frontmatter 补全 | 24 技能 | **P0** |
| Phase 3 | 结构调整 | 全部 45 技能 | P1 |
| Phase 4 | 内容优化 (拆分/精简) | 8 技能 | P1 |
| Phase 5 | 质量门禁 + 持续治理 | 流程 | P2 |

---

## Phase 1: 目录迁移 + 命名重铸 (P0)

### 目标
将 `temp-skills/` 迁移到 `skills/`，使 `hermes profile install` 可以加载，同时所有技能加 `ada-` 前缀。

### 操作

```
temp-skills/<category>/<name>/  →  skills/<category>/ada-<name>/
```

### 命名变更清单

#### autonomous-ai-agents (5 → 5)
| 原名 | 新名 |
|------|------|
| claude-code | ada-claude-code |
| codex | ada-codex |
| coding-agent-readiness | ada-coding-agent-readiness |
| hermes-agent | ada-hermes-agent |
| opencode | ada-opencode |

#### github (8 → 8)
| 原名 | 新名 |
|------|------|
| codebase-inspection | ada-codebase-inspection |
| git-cross-platform-pitfalls | ada-git-cross-platform-pitfalls |
| github-auth | ada-github-auth |
| github-ci-debug | ada-github-ci-debug |
| github-code-review | ada-github-code-review |
| github-issues | ada-github-issues |
| github-pr-workflow | ada-github-pr-workflow |
| github-repo-management | ada-github-repo-management |

#### software-development (32 → 32)
| 原名 | 新名 |
|------|------|
| agent-assisted-development | ada-agent-assisted-development |
| blazor-component-library | ada-blazor-component-library |
| bugfix-architecture-root-cause | ada-bugfix-architecture-root-cause |
| cmake-cpack-packaging | ada-cmake-cpack-packaging |
| code-dedup-audit | ada-code-dedup-audit |
| code-efficiency-review | ada-code-efficiency-review |
| code-quality-analysis | ada-code-quality-analysis |
| code-quality-pipeline | ada-code-quality-pipeline |
| code-quality-report-verification | ada-code-quality-report-verification |
| doc-comparison-analysis | ada-doc-comparison-analysis |
| docs-revision | ada-docs-revision |
| dotnet-blazor-library | ada-dotnet-blazor-library |
| dotnet-engineering-refactoring | ada-dotnet-engineering-refactoring |
| dotnet-verification | ada-dotnet-verification |
| engineering-refactoring | ada-engineering-refactoring |
| hermes-agent-skill-authoring | ada-hermes-agent-skill-authoring |
| hermes-configuration | ada-hermes-configuration |
| hermes-doc-sync | ada-hermes-doc-sync |
| node-inspect-debugger | ada-node-inspect-debugger |
| powershell-from-bash | ada-powershell-from-bash |
| python-debugpy | ada-python-debugpy |
| quality-report-qa | ada-quality-report-qa |
| refactoring-lifecycle | ada-refactoring-lifecycle |
| requirements-authoring | ada-requirements-authoring |
| simplify-code | ada-simplify-code |
| skill-optimization | ada-skill-optimization |
| srs-documentation | ada-srs-documentation |
| srs-lifecycle | ada-srs-lifecycle |
| srs-review | ada-srs-review |
| srs-revision | ada-srs-revision |
| srs-writing | ada-srs-writing |
| tp-to-srs-derivation | ada-tp-to-srs-derivation |

### 验证标准
- [ ] `ls skills/*/ada-*/` 返回 45 个目录
- [ ] 每个 `SKILL.md` 内 `name:` 字段已更新为新名称
- [ ] 每个 `SKILL.md` 内 `related_skills` 引用已更新为新名称
- [ ] `git mv` 保留历史
- [ ] `temp-skills/` 目录已删除

---

## Phase 2: Frontmatter 补全 (P0)

### 2.1 补充 `license: MIT` (11 技能)

`code-quality-pipeline`, `doc-comparison-analysis`, `dotnet-engineering-refactoring`, `dotnet-verification`, `hermes-configuration`, `quality-report-qa`, `refactoring-lifecycle`, `srs-lifecycle`, `srs-review`, `tp-to-srs-derivation`

### 2.2 补充 `platforms` (8 技能)

根据技能实际用途推断平台：
- `coding-agent-readiness` → `[linux, macos, windows]`
- `git-cross-platform-pitfalls` → `[linux, macos, windows]`
- `blazor-component-library` → `[windows, linux, macos]`
- `bugfix-architecture-root-cause` → `[linux, macos, windows]`
- `doc-comparison-analysis` → `[linux, macos, windows]`
- `dotnet-engineering-refactoring` → `[windows, linux, macos]`
- `hermes-configuration` → `[linux, macos, windows]`

### 2.3 补充 `related_skills` (9 技能)

根据技能间的实际引用关系推断并补充。

### 2.4 修复 frontmatter 重复字段 (2 技能)

- `hermes-agent-skill-authoring`: 移除重复的 `license` 和 `tags`
- `skill-optimization`: 移除重复的 `license` 和 `tags`

### 2.5 统一描述规范

所有 description 改为 "Use when..." 格式，去掉外层引号。

---

## Phase 3: 结构调整 (P1)

### 目标结构

每个 SKILL.md 应包含以下章节：

```markdown
# <Title>
## Overview
## When to Use
## <Topic-specific sections>
## Common Pitfalls
## Verification Checklist
```

### 优先级

先处理 14 个完全无结构的技能（主要为伞技能和小型技能），再逐步改造其余 31 个。

---

## Phase 4: 内容优化 (P1)

### 4.1 超大规模技能拆分 (>20k chars, 6 个)

| 技能 | 当前 | 方案 |
|------|------|------|
| `ada-hermes-agent` | 52,719 | 拆为 3 个: `ada-hermes-agent` (核心操作), `ada-hermes-agent-reference` (参考), `ada-hermes-agent-contrib` (贡献) |
| `ada-cmake-cpack-packaging` | 37,951 | 主文件精简到 ~10k，技术细节保留在 10 个 references 中 |
| `ada-claude-code` | 35,033 | tmux 示例移入 references |
| `ada-tp-to-srs-derivation` | 30,210 | 方法论与操作指南分开 |
| `ada-srs-review` | 28,001 | 检查方法移入 references |
| `ada-engineering-refactoring` | 22,734 | 通用方法 + .NET 专项拆分 |

### 4.2 过小技能扩充 (<3k chars, 4 个)

| 技能 | 当前 | 方案 |
|------|------|------|
| `ada-code-quality-pipeline` | 2,033 | 补充完整流程、检查清单 |
| `ada-refactoring-lifecycle` | 2,090 | 补充阶段定义、路由规则 |
| `ada-srs-lifecycle` | 2,116 | 补充生命周期阶段图、路由决策树 |

### 4.3 内容质量改进

- 移除 no-op prose ("be careful", "be thorough")
- 为每个步骤添加可验证的完成条件
- 合并重复内容（如多个技能中重复的 SRS 基础规则）

---

## Phase 5: 质量门禁 + 持续治理 (P2)

### 5.1 提交前检查

```bash
# 新增技能时运行
python scripts/verify-skill.py skills/<category>/<name>/SKILL.md
```

检查项：
- [ ] frontmatter 完整 (name, description ≤1024, version, author, license, platforms, metadata)
- [ ] description 以 "Use when..." 开头
- [ ] 文件 ≤ 20,000 chars
- [ ] 包含 `## Overview`, `## When to Use`, `## Common Pitfalls`, `## Verification Checklist`

### 5.2 技能治理

- 新增技能必须加 `ada-` 前缀
- `related_skills` 只能引用 in-repo 技能
- 每季度做一次技能审计（去重、归档、废弃标记）

### 5.3 .gitignore 更新

确保 `skills/` 目录被 git 跟踪，同时排除非技能文件。

---

## 执行建议

| 批次 | 技能数 | 预计工时 |
|------|--------|----------|
| Phase 1 (迁移+命名) | 45 | 一次性脚本 |
| Phase 2 (frontmatter) | 24 | 1-2h |
| Phase 3 (结构调整) | 14 (优先) | 2-3h |
| Phase 4 (内容优化) | 8 | 3-4h |
| Phase 5 (门禁) | 流程 | 1h |

**建议先执行 Phase 1+2（P0），让技能可安装、frontmatter 合规，再逐步推进 Phase 3-5。**
