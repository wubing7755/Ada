[English](README.md) | 简体中文

> **状态：** Synchronized（与英文主版本同步维护；如有冲突，以英文版为准）

# Ada — Hermes Profile Distribution

Ada 是一个可分发的 Hermes Profile：偏软件工程、重正确性与可验证性的 agent。名字来自 Ada Lovelace——第一位看见机器不仅能够计算数字，也能够表达思想的人。

Ada 帮助开发者理解、设计、构建、调试和演进软件系统。它的价值不在于知道多少术语，而在于看清问题、作出判断，并把事情推进到可运行、可验证的结果。它不是只提供术语答案的聊天角色，而是有工程判断的技术搭档。

人设与工程原则由 [SOUL.md](SOUL.md) 统一定义，64 个分发技能位于 [skills/](skills/)。

当前版本：`0.3.0`，要求 Hermes `>=0.19.0`。

## 适合谁

Ada 适合需要需求分析、工程设计、实现与调试、审计与验证、工程级重构的开发者与团队，也适合重视证据、最小修改、兼容现有系统和长期维护成本的团队。

Ada 不是通用生活助手。生活、情感和非技术日常事务不是 Ada 的主要方向，这类问题更适合 Thea。

## Ada 如何工作

Ada 用「事实 → 假设 → 验证 → 修改 → 复验」的方式工作：

1. 先分清事实、假设和未知；优先相信可观察证据——实际代码、错误与堆栈、编译与测试结果、配置与官方文档；
2. 面对故障先缩小问题空间，再选择信息增益最高的验证方式；修改追求最小化，验证以可运行、可复现为准；
3. 不伪造确定性：不知道就承认，并给出最直接的验证路径。

工程原则：正确性优先于便利，清晰优先于巧妙，可验证优先于听起来合理，可维护优先于短期炫技。完整规范见 [SOUL.md](SOUL.md)。

## 快速开始

### 1. 安装 Hermes Agent

Ada 要求 Hermes `>=0.19.0`。按平台安装：

```bash
# Windows (PowerShell)
iex (irm https://hermes-agent.nousresearch.com/install.ps1)

# Linux / macOS
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

### 2. 安装 Ada Profile

从 GitHub 安装并创建 `ada` wrapper：

```bash
hermes profile install github.com/wubing7755/Ada --alias
```

本地开发时，也可以在仓库根目录安装：

```bash
hermes profile install . --name ada --alias
```

`--alias` 会创建 shell wrapper（`ada` → `hermes -p ada`），之后可以直接使用 `ada` 命令。

### 3. 配置模型和 API 密钥

```bash
ada setup        # 交互式配置向导（模型、终端、网关等）
ada model        # 选择默认模型和 provider
```

### 4. 启动 Ada

```bash
ada                                     # 启动交互式会话
ada chat -q "Review this repository and identify the highest-risk issue."
```

### 5. 确认安装信息

```bash
hermes profile info ada    # 查看 distribution manifest：版本、Hermes 要求、来源
hermes profile show ada    # 查看已安装 Profile 的详情
```

## 技能加载说明

Ada 的 64 个技能遵循 Agent Skills 的 progressive disclosure：discovery 阶段只加载技能名称和 `description`；任务匹配后加载对应 `SKILL.md` 获得执行协议；需要时才读取 `references/`、`scripts/`、`assets/` 和 `evals/`。

因此用户通常只需描述目标，不需要记住或手工调用 64 个技能名称；Agent 会根据任务自动加载匹配的技能。

## 技能体系 (64 skills)

所有 Ada 专属技能均以 `ada-` 为前缀。分类与顺序均以 `distribution.yaml` 为准。

### Agent 与工作流

| 技能 | 作用 |
|---|---|
| `ada-agent-assisted-development` | 结构化 agent 编排：子 agent 审查、分阶段实现、质量审计 |
| `ada-continuous-phased-delivery` | 在授权边界内连续执行已批准的多阶段计划 |
| `ada-hermes-agent-skill-authoring` | SKILL.md 编写与校验：frontmatter、生命周期、发布 |
| `ada-hermes-configuration` | Hermes 配置与人格设计：SOUL.md、记忆、Profile |
| `ada-hermes-doc-sync` | 项目文档与实况 Hermes 安装同步（技能清单、命令引用） |
| `ada-hermes-operations` | Hermes 操作规范：证据标准、上下文管理、审批边界 |
| `ada-requesting-code-review` | 提交前审查：安全扫描、质量门禁、结构化评审请求 |
| `ada-skill-optimization` | 审计与优化 Hermes 生成技能：frontmatter、去重、curator |
| `ada-systematic-debugging` | 四阶段根因调试：先理解 bug 再修复 |
| `ada-test-driven-development` | 强制 RED-GREEN-REFACTOR 的测试驱动开发 |

### SRS 全生命周期

| 技能 | 作用 |
|---|---|
| `ada-requirements-authoring` | 轻量单条需求编写与验收标准审查 |
| `ada-srs-lifecycle` | SRS 全生命周期统一入口：派生、编写、审查、修订 |
| `ada-srs-review` | SRS 质量审查：死需求、交叉引用、术语漂移 |
| `ada-srs-revision` | 大规模修订 SRS：术语替换、重编号、引用修复 |
| `ada-srs-writing` | SRS 编写：结构模式、质量规则、需求条目格式 |
| `ada-tp-to-srs-derivation` | 从技术方案（TP）派生 SRS |
| `ada-srs-to-detailed-design` | 从分层 SRS 生成详细设计条目；仅实现需求派生条目 |
| `ada-detailed-design-audit` | 审计详细设计质量：可验证性、边界、术语、HOW 深度 |
| `ada-contract-consistency-review` | 冻结契约一致性审查：SRS/HLD/ADR/计划一致，PASS/FAIL 结论 |
| `ada-adr-authoring` | 双语 ADR 编写：强制结构、源码核实的 API 形态、维护者决策工作流 |
| `ada-project-background-authoring` | SRS 前置项目背景编写：13 节结构、逐轮确认、已确认事项汇总 |
| `ada-doc-comparison-analysis` | 对比文档版本、合并 SRS 草稿 |
| `ada-docs-revision` | 大规模修订通用技术文档：术语替换、结构重构 |

### 审计与追溯

| 技能 | 作用 |
|---|---|
| `ada-code-dedup-audit` | 提交前审计新代码与现有代码的重复 |
| `ada-code-efficiency-review` | 性能审查：N+1 查询、冗余工作、热路径 |
| `ada-library-public-api-review` | 从外部消费者视角审查库的公共 API 与兼容边界 |
| `ada-doc-implementation-audit` | 验证文档与源码、测试、git diff 的一致性 |
| `ada-doc-traceability-audit` | 文档内部追溯审计：SRS 条目、矩阵、附录 |
| `ada-pre-implementation-audit` | 实现前审计：先验证计划依赖的现状声明 |
| `ada-project-audit` | 整体/遗留项目审计：实现状态、代码健康、追溯漂移 |
| `ada-stateful-service-audit` | 审计状态服务：事务、不变量、持久化、并发、历史语义 |
| `ada-traceability-audit` | 需求追溯矩阵与源码一致性检查 |
| `ada-ui-interaction-protocol-contracts` | 设计/验证跨 UI/Host 边界的交互协议契约 |

### 代码质量

| 技能 | 作用 |
|---|---|
| `ada-code-quality-analysis` | 多维度代码质量审计：复杂度、重复、死代码、安全 |
| `ada-code-quality-pipeline` | 端到端代码质量报告：分析、验证、QA 门禁 |
| `ada-code-quality-report-verification` | 独立验证质量报告中的每一条声明 |
| `ada-quality-report-qa` | 三 agent QA 管道：统计错误、覆盖率假阴性、安全遗漏 |
| `ada-simplify-code` | 并行三 agent 清理最近改动：审查、简化、验证 |

### .NET 与 Blazor

| 技能 | 作用 |
|---|---|
| `ada-blazor-component-library` | Blazor 组件库构建与维护模式 |
| `ada-blazor-interaction-pitfalls` | Blazor 生命周期与渲染行为陷阱 |
| `ada-blazor-interop-pitfalls` | Blazor JS 互操作与 DOM 事件陷阱 |
| `ada-blazor-ui-audit` | 端到端审计组件库：渲染、状态、CSS、互操作、资产 |
| `ada-blazor-wasm-api-integration` | Blazor WASM ↔ 后端 API 集成陷阱：认证头、URL 解析、模式配置、会话缓存 |
| `ada-blazor-debug-verification` | .NET 6 Blazor 调试与验证手册：运行期/DI 陷阱、bUnit 竞态、消费样例循环 |
| `ada-blazor-bunit-testing` | bUnit 1.x 组件测试编写事实：渲染、等待、事件、InputFile |
| `ada-blazor-wasm-runtime-pitfalls` | Blazor WASM 运行时陷阱：首渲染互操作、fragment、查询导航、故障隔离、原生链接 |
| `ada-dotnet-blazor-library` | .NET Blazor 组件库工程：RCL、Demo、公共 API、发布 |
| `ada-dotnet-engineering-refactoring` | .NET 工程级重构：领域原语、值类型迁移、公共 API |
| `ada-dotnet-verification` | .NET 构建/测试/格式化/打包验证 |

### GitHub Pages 与静态站点

| 技能 | 作用 |
|---|---|
| `ada-blazor-wasm-github-pages` | Blazor WASM 静态站点部署到 GitHub Pages：内容管线、Actions 工作流、SPA 兜底、已验证陷阱 |
| `ada-github-pages-static-site` | GitHub Pages 静态站点架构约束：无服务端限制、内容发布路径、生成产物验证 |

### 重构

| 技能 | 作用 |
|---|---|
| `ada-bugfix-architecture-root-cause` | 多 bug 共享根因分析：先追溯架构级问题 |
| `ada-engineering-refactoring` | 架构级重构：类型约束、接口协议、实现分离 |
| `ada-refactoring-lifecycle` | 工程级重构全流程：规划、分阶段、验证 |

### 跨平台与工具链

| 技能 | 作用 |
|---|---|
| `ada-cmake-cpack-packaging` | CMake/CPack 跨平台打包与安装器 |
| `ada-node-inspect-debugger` | Node.js `--inspect` + CDP 调试 |
| `ada-powershell-from-bash` | git-bash 中正确运行 PowerShell |
| `ada-python-debugpy` | Python debugpy/DAP 交互式调试 |

### 文档与交付物

| 技能 | 作用 |
|---|---|
| `ada-business-document-authoring` | 证据 → 面向决策者的业务文档（DOCX/PDF）
| `ada-docx-merge` | Word .docx 章节级合并保格式：XML 手术、样式重映射、SEQ 重编号、引用同步 |
| `ada-markdown-html-rendering` | Markdown->HTML 渲染管线陷阱：消毒丢子树、列表编号、页内锚点 |
| `ada-data-migration-delivery-audit` | DB 取证式验证数据迁移重构确实交付 |
 |
| `ada-document-artifacts` | DOCX/PDF/XLSX/SVG 文档与图表处理 |

### 研究与规划

| 技能 | 作用 |
|---|---|
| `ada-research-planning` | 审视计划、领域建模、大任务分解、战略阅读 |

## 典型工作流

| 场景 | 推荐技能链 | 预期产出 |
|---|---|---|
| 从技术方案形成 SRS | `ada-tp-to-srs-derivation` → `ada-srs-review` → `ada-srs-revision` | 可审查、可追溯的需求文档 |
| 复杂故障修复 | `ada-systematic-debugging` → 对应技术技能 → `ada-requesting-code-review` | 根因证据、最小修复、回归验证 |
| 工程级重构 | `ada-refactoring-lifecycle` → `ada-dotnet-engineering-refactoring` / `ada-engineering-refactoring` → `ada-dotnet-verification` | 分阶段修改与独立质量门禁 |
| 多阶段实现 | `ada-agent-assisted-development` + `ada-continuous-phased-delivery` | 连续执行、逐阶段审查与验证 |
| 文档一致性审计 | `ada-doc-implementation-audit` / `ada-doc-traceability-audit` / `ada-traceability-audit` | 带证据的差距清单 |
| 代码质量报告 | `ada-code-quality-analysis` → `ada-code-quality-report-verification` → `ada-quality-report-qa` | 经独立验证的质量报告 |
| Blazor 组件库交付 | `ada-dotnet-blazor-library` → `ada-blazor-component-library` → `ada-blazor-ui-audit` | 可发布、可验证的组件库 |

## 外部依赖

Ada 依赖 Hermes `>=0.19.0` 提供以下内置技能（随 Hermes 安装，不属于本 distribution）：

| 类别 | 技能 |
|---|---|
| 自主 AI Agent | `claude-code`, `codex`, `opencode`, `hermes-agent` |
| GitHub 工作流 | `github-pr-workflow`, `github-code-review`, `github-issues`, `github-auth`, `github-repo-management`, `codebase-inspection` |
| 通用工作流 | `plan`, `spike` |

## 文件结构

```text
Ada/
├── distribution.yaml           # Profile distribution manifest（名称、版本、技能清单）
├── SOUL.md                     # Ada 的人设与工程原则
├── README.md                   # 英文主版本（Canonical）
├── README.zh-CN.md             # 简体中文版本（Synchronized）
├── docs/                       # 质量标准（skill-quality-standard.md）
├── scripts/                    # 验证器、隔离 smoke 测试与单元测试
├── .github/workflows/          # GitHub Actions 质量门禁
└── skills/software-development/  # 64 个 ada-* 技能
```

## 质量验证

仓库通过 `Ada Profile Quality / validate-profile` GitHub Actions 检查审查所有面向 `main` 的 Pull Request，并在推送到 `main` 后再次运行。检查包括：

- validator 单元测试；`distribution.yaml`、实际技能目录与 README 技能目录/数量一致性；README 与 manifest 版本一致性；
- YAML/frontmatter、资源链接、Skill 间引用和 eval 结构检查；私有运行时状态泄漏检查（memories、sessions、凭据、`local/` 等）；
- Python `compileall` 与变更范围 `git diff --check`；
- 使用临时 `HERMES_HOME` 的隔离 install/update smoke，确认 55 个 Skills 和用户状态在更新后保留。

本地可以运行同一组门禁：

```bash
python -m unittest scripts/tests/test_validate_skill_quality.py -v
python scripts/validate_skill_quality.py
python -m compileall -q scripts
python scripts/smoke_profile_distribution.py
git diff --check
```

> 自动门禁必要但不充分：它不能证明技能在真实任务中有用、无过期假设或可合法分发。当前 validator 通过，同时保留 24 条既有 eval 建议性 warning（如触发/拒绝用例数不足），这是已知的质量债，不代表“全部质量项无警告”。

## 更新 Ada

```bash
hermes profile info ada      # 查看当前安装的版本、来源与 Hermes 要求
hermes profile update ada    # 从记录的来源重新拉取并应用更新
```

`profile update` 会覆盖 distribution-owned 内容（`SOUL.md`、`skills/`、`cron/`、`mcp.json` 等），但不会触碰 memories、sessions、auth、`.env` 等用户数据；`config.yaml` 默认保留本地覆盖，除非显式传入 `--force-config`。

## 分发边界与隐私

- 本 distribution 不携带安装者的记忆、会话、API 密钥或本地日志。
- 安装者使用自己的模型配置与凭据。
- validator 会拒绝将私有运行时路径（如 `memories/`、`sessions/`、凭据文件、`local/`）纳入分发。
- Skill 质量标准见 `docs/skill-quality-standard.md`。

## 版本

| 版本 | 说明 |
|---|---|
| `0.3.0`（当前，未打 tag） | 增加 GitHub Actions 质量门禁；吸收本地 Ada 工程技能并统一为 50 技能目录 |
| `v0.2.0`（tag） | manifest 为 0.2.2：技能触发优化、自包含技能、吸收 hermes-use 新增 3 个技能 |
| `v0.1.0`（tag） | 初始 profile distribution |

## License

MIT — 见 `distribution.yaml` 的 `license` 字段声明。
