# Scenario Guides — Detailed Prompts & Outputs

This reference contains expanded versions of the five workflows from SKILL.md,
with exact user prompts, agent actions, and expected output formats. Use it
when the user needs step-by-step hand-holding through a workflow.

---

## Bug Fix — Full Script

### Prompt 1: Reproduce

```
先别急着修。帮我写一个能复现这个 bug 的最小测试用例。
确认测试确实失败（RED）。不要动任何业务代码。

Bug: [症状描述]
复现步骤:
1. [步骤1]
2. [步骤2]

相关文件: [文件路径列表]
```

**Agent should:**
1. Read relevant source files
2. Write a minimal test case
3. Run test → confirm RED
4. Report: "测试 `[TestName]` 已创建，确认失败。错误信息: [error]"

### Prompt 2: Root Cause

```
现在分析根因。用 systematic-debugging 流程:
1. 追溯数据流，从症状点一直追溯到源头
2. 检查最近改动（git log -5）
3. 输出分析报告，包含:
   - 根因定位（文件:行号）
   - 为什么会出现这个 bug
   - 修复方案（最小改动）
   - 风险评估
   - 影响范围
先别改代码。
```

**Expected output format:**
```
根因分析报告
═══════════════════════════════════
文件: [文件路径]:[行号]
函数: [函数名]
根因: [一句话描述]
修复方案: [具体改动描述 + 估计行数]
风险等级: LOW / MEDIUM / HIGH
影响范围: [受影响的模块/功能]
```

### Prompt 3: Fix

```
方案确认。只修复根因，不要动其他代码。
只改 [具体方法/文件]，改完跑测试验证。
```

### Prompt 4: Sub-Agent Review

```
现在用子 agent 独立审查这次修复。
加载 requesting-code-review 技能，走完整流程:
静态扫描 → 独立 reviewer → 输出审查报告。
```

**Expected output format:**
```
审查报告 (独立 reviewer)
═══════════════════════════════════
变更文件: [文件] (+N 行)
审查结果: ✅ 通过 / ❌ 不通过

安全检查: [通过/发现问题]
  [具体项目]

逻辑检查: [通过/发现问题]
  [具体项目]
  边界情况: [检查结果]

建议（非阻塞）:
  - [建议1]
  - [建议2]

风险等级: SAFE / CAREFUL / RISKY
```

### Prompt 5: Final Report

```
汇总成修复报告，中文输出:
- Bug 描述
- 根因分析
- 修复内容（diff 摘要）
- 审查结果
- 测试结果
```

---

## Feature Implementation — Full Script

### Prompt 1: Align & Plan

```
实现 SRS [REQ-F-XXX]: [需求简述]。

先对照 docs/SRS.md 确认需求理解无误。然后:
1. 检查是否和其他 REQ 冲突
2. 读相关源文件了解当前结构
3. 输出实现方案:
   - 改动文件清单（新增/修改）
   - 新增类/方法列表
   - 估计改动量（行数）
   - 实施顺序（先 Domain → 再 Service → 再 Component → 再 Test）
```

**Expected output format:**
```
实现方案: [REQ-F-XXX] [需求名称]
═══════════════════════════════════
SRS 原文: [引用]
当前状态: [已实现/未实现/部分实现]

改动清单:
  新增:
    [文件路径]  (~N 行)  [说明]
  修改:
    [文件路径]  (+N 行)  [说明]
  测试:
    [文件路径]  (~N 行)  [说明]

冲突检查: [无冲突 / 与 REQ-F-XXX 重叠: ...]

实施顺序:
  ① [步骤1] → ② [步骤2] → ③ ...
估计总改动量: ~N 行
```

### Prompt 2: Phased Implementation

```
方案确认。按顺序逐步实施，每步跑 build + test 验证。
先从 ① [第一步] 开始。
```

After each step, agent runs verification. Say "继续下一步" or give feedback.

### Prompt 3: Review

```
全部实施完毕。并行开 3 个子 agent 审查:
1. 安全性 + 逻辑错误
2. SRS 合规性（是否满足所有 AC）
3. 代码质量 + 效率
输出合并审查报告。
```

### Prompt 4: Traceability

```
审查通过。更新 docs/requirements-traceability.md 中 [REQ-F-XXX] 的状态。
生成实现报告。
```

---

## Code Review — Full Script

### One-line trigger (full auto)

```
审查我最近的改动，用 requesting-code-review 流程。
```

Agent auto-executes:
1. `git diff` → get changes
2. Static scan (secrets, injection, dangerous calls)
3. `delegate_task` → independent reviewer (sub-agent with diff only)
4. Risk-tier results
5. Output report

### Fine-grained trigger

```
审查最近的改动，但:
- 只审查 [路径] 下的文件
- SAFE 级别自动修
- CAREFUL 和 RISKY 只报告不修改
- 输出中文报告
```

---

## Code Quality — Full Script

### One-line trigger

```
用 simplify-code 分析我最近的改动。
```

Agent auto-executes:
1. `git diff` → capture changes
2. `delegate_task(tasks=[3 reviewers])` → parallel review
3. Aggregate + dedup findings
4. Risk-tier:
   - SAFE → auto-apply
   - CAREFUL → apply one file at a time, verify each
   - RISKY → flag for user
5. Output report

### Dry-run variant

```
用 simplify-code 分析最近的改动，但只报告不动代码。
```

Agent runs 3 reviewers, presents findings with risk tiers, applies NOTHING.

---

## Architecture Upgrade — Full Script

### Prompt 1: Research

```
我想升级 [模块/系统] 的架构。目标:
1. [目标1]
2. [目标2]
3. [目标3]

先:
1. 分析当前架构（梳理调用链、依赖关系）
2. 调研替代方案
3. 评估可行性 + 风险
4. 输出调研报告 + 升级方案（含 Phase 拆分）
```

### Prompt 2: Phased Execution

```
方案确认。按 Phase 实施。
每个 Phase 完成后:
1. 跑 build + test
2. 你主动做 Phase 回顾，分析有没有更好的写法
3. 有则提二次优化方案，我确认后实施
4. 无二次优化则进入下一 Phase
从 Phase 1 开始。
```

### Prompt 3: Cross-Phase Review

```
全部 Phase 完成。跨阶段审视:
1. 对比升级前后的代码结构（行数、文件数、复杂度）
2. 分析整体层面有没有更好的设计
3. 检查是否所有旧代码路径都已迁移
4. 输出最终架构升级报告
```

### Prompt 4: Final Review

```
用子 agent 独立审查全部 Phase 的改动总和。
3 个 reviewer 并行: SRS 合规、安全性、代码质量。
```

---

## Common Pitfall Patterns

### Pitfall: "Just fix it" without context reset

**Wrong:**
```
User: "审查这段代码，有问题就直接修"
Agent: [reviews, finds 5 issues, starts fixing...]
      [context has 40 turns of analysis + old reasoning]
      [fix quality degrades, introduces a new bug]
```

**Right:**
```
User: "审查这段代码，有问题列出来"
Agent: [reviews, outputs issue list]
User: "修复 #2 和 #4，用子 agent 修"  ← fresh context for the fixer
Agent: delegate_task(fix only #2 and #4) ← isolated, won't drift
```

### Pitfall: Trusting sub-agent reports without verification

**Wrong:**
```
Agent: "审查通过，无问题"  ← could be hallucinated
User: "好的，提交"
```

**Right:**
```
Agent: "审查通过。报告摘要: 变更 3 个文件，SAFE 级别。建议: [具体 file:line]"
User: "验证一下: 跑 dotnet test，确认 main.razor 的改动确实在文件里"
Agent: [runs dotnet test → 15/15 pass] [read_file → confirms change]
       "验证通过。实际产出与报告一致。"
```

### Pitfall: Fixing symptoms instead of root cause

**Wrong:**
```
User: "面板消失的 bug"
Agent: "在渲染层加了 null check，面板不消失了"  ← symptom fix
Result: 面板显示了但内容是空的  ← new symptom from unfixed root cause
```

**Right:**
```
User: "面板消失的 bug，先分析根因"
Agent: [traces data flow from render → state → drag handler]
       "根因在 MovePanel() 未保留 ContentRef，不是渲染层问题"
       [fixes MovePanel() → bug truly resolved]
```
