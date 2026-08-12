---
name: ada-agent-delivery-audit
description: "用于审核长任务/委托 Agent 的多 Phase 交付：核对方案覆盖、数据迁移，重跑门禁，不信交付报告。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [audit, delivery, agent-review, verification, phased-execution]
    related_skills: [ada-continuous-phased-delivery, ada-requesting-code-review, ada-code-quality-analysis]
---

# Agent Delivery Audit（长任务交付审核）

审核另一个 Agent（或长时间运行的自己）声称完成的大型多 Phase 方案产出。**核心原则：不信交付报告，重取证**——"migrated"、"tests pass"、"done" 都是 claim，不是事实。

## 触发条件

- 长任务/委托 Agent 声称完成整个多 Phase 计划（代码、迁移、部署脚本、文档）
- 用户问"怎么审核这个 Agent 的产出 / 是否跑偏 / 代码质量如何"
- 大型方案交付后、合入/上线前的独立验证

## 审核流程（按序）

1. **取证**：`git log --oneline` + `git status` + 逐 commit `git show --stat`。核对：commit 是否一一对应方案 Phase；有无 scope creep（改计划外文件）；"实现时定"的决策是否有记录；工作树是否干净。
2. **不可逆闸门检查（最高优先）**：方案/提示词里要求"用户确认后才执行"的删除、迁移、覆盖动作是否被提前执行。实测：执行 Agent 未经确认删除 `content/*.xml`（git 可恢复，但流程违规）——立即向用户报告并让其决策追认/恢复，不要自行处置。
3. **数据/迁移核对**：声称 "migrated to DB" 必须 DB 直查验证（`SELECT COUNT(*) FROM 各表`）。实测：Posts 21 条是**早期旧数据**（CreatedAt=PublishedAt=XML 日期，而非导入工具写的 now），4 张新表全空——ContentImporter 实际从未在正确库运行。常见根因：一次性工具默认连接串是**相对路径**，CWD 不同会静默创建全新空库。数据完整性是这类审核最易翻车处。
4. **门禁重跑**：自己跑全量测试 + format + 安全扫描（新增行密钥模式），不信 Agent 报告的数字。
5. **复现 CI/脚本的确切命令，不发明"等价"命令**：命令参数（尤其 `-o` 目标路径）不同会产出不同结构。实测：用 `-o publish/wwwroot` 演练 route-shells 失败，误判为 SDK/CI bug——实际方案用 `-o publish`（站点根在 publish/wwwroot）是正确的。验证命令与 CI/发布脚本**逐字一致**，假阳性会浪费整轮审查。
6. **独立子 Agent 审查可并行**：派只读 reviewer 对照方案文档逐 Phase 核对 + 查遗漏 + 审质量，与门禁并行跑（reviewer 的 NOTE 说"修改了文件"要 `git status` 核实，常是误报）。
7. **测试回归语义**：新增保护/校验逻辑破坏既有测试时，先理解调用方语义再修。实测：空表保护放在导出服务层，导致 dryRun 预览测试全挂——dryRun 是预览不推送，保护应只在非 dryRun 实际执行时生效。保护逻辑要放在语义正确的层。
8. **修复后补回归测试**：每个修复的行为必须有测试断言（实测 P0 修复"空 markdown 保留 BodyHtml"最初无测试，补测试后证明修复真实有效）。

## 输出契约

- 问题分级表：严重/中/低，每条带 文件:行 证据
- 修复方案（按优先级）+ 验证结果（全量测试计数、格式、ad-hoc 脚本性质标注）
- 明确区分：已验证通过 vs 需修改 vs 被阻塞
- 遗留事项（用户操作项：域名配置、环境变量、浏览器验收）

## 独立只读子 Agent 与复现纪律

- **独立只读子 Agent 审查可并行**：派 fresh-context 的只读 reviewer 对照方案文档
  逐 Phase 核对 + 查遗漏 + 审质量，与门禁并行跑。要求 `file:line` 证据；reviewer 的
  NOTE 说"修改了文件"要 `git status` 核实，常是误报。
- **复现 CI/脚本的确切命令，不发明"等价"命令**：命令参数（尤其 `-o` 目标路径）
  不同会产出不同结构。实测：用 `-o publish/wwwroot` 演练失败，误判为 SDK/CI bug——
  实际方案用 `-o publish` 是正确的。验证命令与 CI/发布脚本**逐字一致**，假阳性会
  浪费整轮审查。
- **修复后补回归测试**：每个高严重度修复的行为必须有测试断言，且该测试在旧代码上
  失败、修复后通过。
- **警惕审查期间的新提交**：执行 Agent 可能在审查时继续工作——`git log` 里最后已知
  commit 之后的新 commit 按新 scope 处理。

## 实测陷阱（每项都真实耗过时间）

- **相对连接串的迁移工具**：`Data Source=app.db` 按 CWD 解析 → 静默创建全新空库，
  "migration succeeded" 但数据不存在。要求显式/绝对连接串、逐表进度日志、幂等 upsert、
  结束自检行数。
- **导入数据的时间戳签名**：看起来是导入的行却保留旧时间戳（导入工具写 now，种子/
  从源导入保留源日期）→ 证明导入工具从未在该 DB 上运行。
- **幂等 vs JSON 列**：EF 无法把字典/JSON 列查询翻译成 SQL——加载到内存匹配。
- **守卫条件必须匹配运行时语义**："拒绝空快照"守卫破坏了 dryRun 预览（dryRun 不推送，
  不能被拦）。只守卫有副作用的路径。
- **导入正文可为 `BodyMarkdown=""` + `BodyHtml=HTML`**；无条件 `RenderToHtml(BodyMarkdown)`
  的更新端点会在任意编辑时清空正文——markdown 为空且既有 html 非空时保留 BodyHtml。
- **运行中 dev server 锁 exe**：`dotnet build` 失败，而 `dotnet run --no-build`
  静默跑旧二进制（看起来"修复没生效"）。停服务、重建、重跑。

## 验证

- 全量 `dotnet test`（或对应工具链）+ format 必须自己跑
- ad-hoc 验证脚本（Temp 目录 `hermes-verify-*.sh`）标注证据性质（targeted vs full suite），跑完清理
- 不可逆操作的恢复路径先确认（git 历史/备份）再报告

## 参考案例

本技能无独立 references：审核协议（取证快照、不可逆闸门、DB 直查、门禁重跑、逐字命令复现）均在正文。
