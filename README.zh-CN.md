[English](README.md) | 简体中文

> **状态：** Synchronized（与英文主版本同步维护；如有冲突，以英文版为准）

# Ada — Hermes Profile Distribution

Ada 是一个可分发的 Hermes Profile：偏软件工程、重正确性与可验证性的 agent。名字来自 Ada Lovelace——第一位看见机器不仅能够计算数字，也能够表达思想的人。

Ada 帮助开发者理解、设计、构建、调试和演进软件系统。它的价值不在于知道多少术语，而在于看清问题、作出判断，并把事情推进到可运行、可验证的结果。它不是只提供术语答案的聊天角色，而是有工程判断的技术搭档。

人设与工程原则由 [SOUL.md](SOUL.md) 统一定义，12 个分发技能位于 [skills/](skills/)。

当前版本：`0.5.0`，要求 Hermes `>=0.19.0`。

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

Ada 的 12 个技能遵循 Agent Skills 的 progressive disclosure：discovery 阶段只加载技能名称和 `description`；任务匹配后加载对应 `SKILL.md` 获得执行协议；需要时才读取 `references/`、`scripts/`、`assets/` 和 `evals/`。

因此用户通常只需描述目标，不需要记住或手工调用 12 个技能名称；Agent 会根据任务自动加载匹配的技能。

## 技能体系 (12 skills)

所有 Ada 专属技能均以 `ada-` 为前缀。分类与顺序均以 `distribution.yaml` 为准。

### 核心工程工作流

| 技能 | 作用 |
|---|---|
| `ada-agent-assisted-development` | 结构化 agent 编排：子 agent 审查、分阶段实现、质量审计 |
| `ada-research-planning` | 审视计划、领域建模、大任务分解、战略阅读 |
| `ada-systematic-debugging` | 四阶段根因调试：先理解 bug 再修复 |
| `ada-test-driven-development` | 强制 RED-GREEN-REFACTOR 的测试驱动开发 |

### 代码质量与重构

| 技能 | 作用 |
|---|---|
| `ada-requesting-code-review` | 提交前审查：安全扫描、质量门禁、结构化评审请求 |
| `ada-code-quality-analysis` | 多维度代码质量审计：复杂度、重复、死代码、安全 |
| `ada-simplify-code` | 并行三 agent 清理最近改动：审查、简化、验证 |
| `ada-engineering-refactoring` | 架构级重构：类型约束、接口协议、实现分离 |

### Git 交付

| 技能 | 作用 |
|---|---|
| `ada-git-pr-delivery` | 脏工作树 → 干净 PR：指针修复、提交约定、PR 模板 |
| `ada-git-destructive-operations` | 安全处理重置与删除本地提交：clarify 澄清意图 |

### Windows 环境工具

| 技能 | 作用 |
|---|---|
| `ada-windows-file-editing` | Windows/MSYS 文件编辑：CRLF、MSYS 路径、大小写目录冲突、管道退出码 |
| `ada-powershell-from-bash` | git-bash 中正确运行 PowerShell |

## 典型工作流

| 场景 | 推荐技能链 | 预期产出 |
|---|---|---|
| 复杂故障修复 | `ada-systematic-debugging` → `ada-test-driven-development` → `ada-requesting-code-review` | 根因证据、最小修复、回归验证 |
| 实现新功能 | `ada-research-planning` → `ada-agent-assisted-development` → `ada-test-driven-development` | 分解后的计划、逐阶段审查的实现 |
| 工程级重构 | `ada-code-quality-analysis` → `ada-engineering-refactoring` → `ada-requesting-code-review` | 分阶段修改与独立质量门禁 |
| 清理最近改动 | `ada-simplify-code` → `ada-requesting-code-review` | 简化并验证后的可提交 diff |
| 代码质量报告 | `ada-code-quality-analysis` | 带 file:line 证据的审计报告 |
| 以 PR 交付工作 | `ada-requesting-code-review` → `ada-git-pr-delivery` | 干净分支、约定式提交、可审查的 PR |

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
├── templates/                  # 从 SOUL.md 蒸馏的可移植 AGENTS.md 模板
├── .github/workflows/          # GitHub Actions 质量门禁
└── skills/software-development/  # 12 个 ada-* 技能
```

## 质量验证

仓库通过 `Ada Profile Quality / validate-profile` GitHub Actions 检查审查所有面向 `main` 的 Pull Request，并在推送到 `main` 后再次运行。检查包括：

- validator 单元测试；`distribution.yaml`、实际技能目录与 README 技能目录/数量一致性；README 与 manifest 版本一致性；
- YAML/frontmatter、资源链接、Skill 间引用和 eval 结构检查；私有运行时状态泄漏检查（memories、sessions、凭据、`local/` 等）；
- Python `compileall` 与变更范围 `git diff --check`；
- 使用临时 `HERMES_HOME` 的隔离 install/update smoke，确认 12 个 Skills 和用户状态在更新后保留。

本地可以运行同一组门禁：

```bash
python -m unittest scripts/tests/test_validate_skill_quality.py -v
python scripts/validate_skill_quality.py
python -m compileall -q scripts
python scripts/smoke_profile_distribution.py
git diff --check
```

> 自动门禁必要但不充分：它不能证明技能在真实任务中有用、无过期假设或可合法分发。当前 validator 通过，同时保留 8 条既有 eval 建议性 warning（如触发/拒绝用例数不足），这是已知的质量债，不代表“全部质量项无警告”。

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
| `0.5.0`（当前，未打 tag） | 精简核心：77 技能目录裁剪为 12 个通用工程技能；移除 SRS 全生命周期、审计/报告流水线、.NET/Blazor/CMake 技术栈专项、文档交付与 Hermes 自维护簇；SOUL.md 新增安全与可用性工程原则（分层立场 + 7 条硬底线）；新增供其他 agent 工具使用的可移植 AGENTS.md 模板 |
| `0.4.0` | 吸收本地/桌面 Ada profile 沉淀的 27 个自学习技能，统一为 77 技能目录；新增 SRS→设计、NuGet、安全、Git/PR 交付、双语文档、UI 审查簇 |
| `v0.2.0`（tag） | manifest 为 0.2.2：技能触发优化、自包含技能、吸收 hermes-use 新增 3 个技能 |
| `v0.1.0`（tag） | 初始 profile distribution |

## License

MIT — 见 `distribution.yaml` 的 `license` 字段声明。
