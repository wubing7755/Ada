---
name: ada-hermes-operations
description: "Use when operating Hermes Agent itself — slash commands, evidence standards, context handoff, approval boundaries, Windows-specific tool behavior, and delegation patterns. Load before any complex multi-session or multi-agent workflow. Triggered by: complex multi-session workflows, multi-agent delegation, or any task requiring context management across /new boundaries. Defines evidence standards and approval boundaries that all agent tasks depend on. Should be preloaded for every non-trivial session."
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, operations, context, commands, delegation, workflow]
    related_skills: [ada-agent-assisted-development]
---

# Hermes Agent 操作规范

Hermes Agent 自身的操作知识——命令、工具选择、证据标准、上下文管理、审批边界。这些是 Ada 执行任何复杂任务的"基础设施"知识。

## Slash Commands

| 命令 | 用途 | 使用时机 |
|------|------|----------|
| `/new` | 重置会话 | 从分析切换到实现，或从实现切换到审查 |
| `/compress` | 压缩上下文 | 会话过长（>50 轮）但任务不变 |
| `/snapshot` | 保存状态 | 大范围编辑或架构变更前 |
| `/rollback` | 恢复快照 | 编辑失败或实验不可逆后 |
| `/goal` | 跟踪多轮目标 | 需要多步推进的复杂目标 |
| `/background` | 后台运行 | 慢扫描或报告不阻塞主会话 |
| `/steer` | 引导运行中 agent | 在下一个 tool boundary 修正行为 |
| `/queue` | 排队指令 | 当前指令之后的下一个指令 |

## 工具选择原则

- **terminal**：构建、测试、git、脚本、包管理。首选。
- **文件工具**（read_file、search_files、patch）：精确读写。search 优先于 broad reading。
- **browser/web**：仅当依赖当前外部信息、在线文档或交互式网站。
- **delegate_task**：独立审查、并行调查、降低不确定性。不要用于简单机械任务。
- **execute_code**：需要循环/解析/聚合的重复性本地分析。

## 证据阶梯

优先使用强证据：

| 证据类型 | 强度 |
|----------|:----:|
| 通过的测试/构建/检查命令 | 强 |
| 已渲染或打开的文件检查 | 强 |
| 直接源码引用或当前官方文档 | 强 |
| 静态扫描 + file:line 证据 | 中 |
| 从本地代码的推理 | 中 |
| 用户报告但未复现 | 弱（有用但仅作起点） |

只有弱证据时，明确说明，不要过度肯定。

## 上下文移交

好的移交应包含：
- 目标和当前阶段
- 已更改或检查的文件
- 关键结论及证据
- 下一步和约束
- 已运行的命令及其结果

保持移交简短——新 agent 无需重读整个对话即可行动。

### 何时重置上下文

| 信号 | 操作 |
|------|------|
| 从分析切换到实现 | `/new` |
| 开始审查（任何审查） | `delegate_task`（独立子 agent） |
| Agent 表现明显下降 | `/compress` 或 `/new` |
| 会话超过 ~50 轮 | 考虑拆分 |
| 失败的方法后重试 | `/new`——不要让失败的推理污染重试 |

### 子 Agent 隔离规则

1. **审查者 ≠ 实现者**。新上下文发现实现者遗漏的问题。
2. **修复者 ≠ 审查者**。修复者只拿到问题列表，不拿审查推理。
3. **最多 2 轮自动修复**。2 轮不能解决所有问题→升级给用户。

## 审批与安全

以下操作前需确认：
- 破坏性操作（递归删除、强制推送）
- 大范围文件系统写入
- 凭据或密钥变更
- 外部安装或网络依赖
- 工作区外的操作

请求审批时，说出命令目的和影响的路径或系统。

## Windows 注意事项

- git-bash/MSYS 下 PowerShell：`$` 变量被 bash 吃掉→写入 `.ps1` 文件后 `MSYS_NO_PATHCONV=1 powershell.exe -File` 执行
- MSYS 路径转换：`C:\Users\...\file` 变为 `C:Users...file`→用正斜杠 `C:/Users/.../file`
- CMake from MSYS：用 `cygpath -w` 转换 Unix→Windows 路径
- 递归删除或移动：先解析验证目标路径

详见 PowerShell-from-bash documentation 和 CMake/CPack packaging documentation。

## Common Pitfalls

- **自我审查盲区**：实现者审查自己的工作会错过新上下文能发现的问题。始终用 `delegate_task` 做审查。
- **跳过复现**：没有红色测试就声称"我知道怎么修"=赌博。先建立紧反馈循环。
- **捆绑修复**："顺便"改进与 bug 修复或功能实现无关→引入无关风险。一次改一个，一次验证一个。
- **单点报告**：一份质量报告是快照。3 个月以上的趋势才讲真故事。
- **信任子 agent 输出不验证**：子 agent 的"测试通过"是声明不是事实。自己跑命令确认。

## Verification Checklist

- [ ] 阶段切换时上下文已重置（`/new` 或 `delegate_task`）
- [ ] 审查使用了独立子 agent，不是自我审查
- [ ] 所有子 agent 声明（测试通过、文件写入）已独立验证
- [ ] 破坏性操作前已请求并获批准
- [ ] Windows 操作使用了正确的 shell 路径处理
