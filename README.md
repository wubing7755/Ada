# Ada

Ada 是一个可分发的 Hermes profile：一个偏软件工程、重正确性与可验证性的 agent。

## 技能体系 (42 skills)

所有 Ada 专属技能均以 `ada-` 为前缀。以下分类列出：

### SRS 全生命周期
- `ada-srs-lifecycle` — SRS 全生命周期统一入口
- `ada-tp-to-srs-derivation` — 从技术方案派生 SRS
- `ada-srs-writing` / `ada-srs-review` / `ada-srs-revision` — 编写、审查、修订
- `ada-srs-documentation` — SRS 文档化方法论
- `ada-requirements-authoring` — 需求编写
- `ada-doc-comparison-analysis` — 文档对比分析
- `ada-docs-revision` — 文档结构化修订

### 审计与追溯
- `ada-project-audit` — 项目实现状态审计
- `ada-pre-implementation-audit` — 实现前审计
- `ada-traceability-audit` — 需求-实现追溯审计
- `ada-doc-implementation-audit` — 文档-实现一致性审计
- `ada-doc-traceability-audit` — 文档追溯审计
- `ada-code-dedup-audit` — 代码去重审计
- `ada-code-efficiency-review` — 代码效率审查

### 代码质量
- `ada-code-quality-pipeline` — 代码质量全流水线
- `ada-code-quality-analysis` — 多维度代码质量分析
- `ada-code-quality-report-verification` — 质量报告独立验证
- `ada-quality-report-qa` — 三 agent QA 管道
- `ada-simplify-code` — 并行三 agent 代码清理

### .NET & Blazor
- `ada-dotnet-blazor-library` — Blazor 组件库工程
- `ada-blazor-component-library` — Blazor 组件库模式
- `ada-blazor-interaction-pitfalls` — Blazor 交互陷阱
- `ada-blazor-interop-pitfalls` — Blazor JS 互操作陷阱
- `ada-dotnet-engineering-refactoring` — .NET 工程级重构
- `ada-dotnet-verification` — .NET 构建/测试验证

### 重构
- `ada-refactoring-lifecycle` — 工程级重构全流程
- `ada-engineering-refactoring` — 架构级重构
- `ada-bugfix-architecture-root-cause` — 多 bug 根因分析

### 工作流
- `ada-agent-assisted-development` — Agent 辅助开发工作流
- `ada-requesting-code-review` — 提交前审查
- `ada-systematic-debugging` — 四阶段根因调试
- `ada-test-driven-development` — TDD RED-GREEN-REFACTOR

### 工具链
- `ada-cmake-cpack-packaging` — CMake/CPack 跨平台打包
- `ada-powershell-from-bash` — git-bash 中运行 PowerShell
- `ada-node-inspect-debugger` — Node.js Chrome DevTools 调试
- `ada-python-debugpy` — Python debugpy 调试

### Hermes 配置
- `ada-hermes-configuration` — Hermes 配置与人格设计
- `ada-hermes-agent-skill-authoring` — Skill 编写规范
- `ada-hermes-doc-sync` — 文档与实况同步
- `ada-skill-optimization` — Skill 审计与优化

## 外部依赖

Ada 依赖 Hermes ≥0.19.0 提供以下内置技能：

| 类别 | 技能 |
|------|------|
| 自主 AI Agent | `claude-code`, `codex`, `opencode`, `hermes-agent`, `coding-agent-readiness` |
| GitHub 工作流 | `github-pr-workflow`, `github-code-review`, `github-issues`, `github-auth`, `github-repo-management`, `github-ci-debug`, `codebase-inspection`, `git-cross-platform-pitfalls` |
| 通用工作流 | `plan`, `spike` |

## 安装

```bash
hermes profile install github.com/wubing7755/Ada --alias
```

安装后可直接使用：

```bash
ada chat
```

## 更新

```bash
hermes profile update ada
```

## 说明

- 这个 distribution 不携带安装者的记忆、会话、API 密钥或本地日志。
- 安装者使用自己的模型配置与凭据。
- Ada 的 SOUL.md 定义工程判断与协作风格，skills 提供经过实战验证的工作流。
