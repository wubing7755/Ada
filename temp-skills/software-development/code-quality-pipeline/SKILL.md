---
name: code-quality-pipeline
description: 代码质量全流水线 — 从分析、验证到 QA 门禁的三阶段统一入口。产生、验证、交付结构化的代码质量报告。
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
metadata:
  hermes:
    tags: [code-quality, pipeline, audit, qa, umbrella]
    sub_skills: [code-quality-analysis, code-quality-report-verification, quality-report-qa]
---

# 代码质量流水线

端到端的代码质量保障流程——分析代码库产生报告，独立验证报告中的结论，最终 QA 门禁后交付用户。

## 三阶段流水线

```
源代码 ──→ [Stage 1: Analyze] ──→ [Stage 2: Verify] ──→ [Stage 3: QA Gate] ──→ 交付用户
            code-quality-           code-quality-           quality-report-qa
            analysis                report-verification
```

| 阶段 | 技能 | 做什么 | 输入 | 输出 |
|------|------|--------|------|------|
| **Analyze** | `code-quality-analysis` | 多维度扫描代码库 | 源代码树 | 质量报告 (Markdown) |
| **Verify** | `code-quality-report-verification` | 抽查/全量验证报告结论 | 质量报告 + 源代码 | 验证结果 (confirmed/partial/false-positive) |
| **QA Gate** | `quality-report-qa` | 三道额外门禁 | 已验证的报告 | 放行/打回 |

## 流水线执行规则

1. **不可跳过**: 分析 → 验证 → QA，必须按顺序
2. **验证阻塞**: 验证发现 ≥3 个 false positive → 回到 Stage 1 修正
3. **QA 阻塞**: QA 发现统计偏差/遗漏 → 回到 Stage 1 补充
4. **最终交付**: 三阶段全部绿灯后交付用户

## 报告维度

Stage 1 覆盖七大维度：
- 复杂度 (Cyclomatic Complexity)
- 重复代码
- 死代码
- 安全漏洞
- 依赖健康度
- 测试覆盖率
- 代码规范

## 使用方式

加载本 skill 后，从 Stage 1 开始，依次加载对应子技能。每个阶段完成后确认输出质量再进入下一阶段。
