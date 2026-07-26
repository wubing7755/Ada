---
name: ada-code-quality-pipeline
description: "Use when running the full code quality pipeline — three-phase unified entry point from analysis through verification to QA gate. Produces, validates, and delivers structured code quality reports."
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [code-quality, pipeline, audit, qa, umbrella]
    related_skills: [ada-code-quality-analysis, ada-code-quality-report-verification, ada-quality-report-qa]
    sub_skills: [code-quality-analysis, code-quality-report-verification, quality-report-qa]
---

# 代码质量流水线

端到端的代码质量保障流程——分析代码库产生报告，独立验证报告中的结论，最终 QA 门禁后交付用户。

## Overview

This skill provides a unified three-stage gated pipeline for end-to-end code quality
assurance. It chains three specialized skills — `code-quality-analysis` (Stage 1:
multi-dimension audit), `code-quality-report-verification` (Stage 2: independent
verification), and `quality-report-qa` (Stage 3: QA gate with four extra checks) —
into a sequential workflow where each stage blocks the next if issues are found.
The pipeline enforces a strict no-skip rule: analysis → verification → QA, in order.
If verification finds ≥3 false positives or QA finds statistical drift, the pipeline
sends the report back for correction before delivery.

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

## When to Use

- User wants a complete code quality workflow spanning analysis through delivery
- User says "full pipeline", "end-to-end quality", "完整流水线", or "全流程质量"
- User wants a code quality report that has been independently verified and QA-gated before acting on it
- When the cost of delivering an inaccurate quality report is high (e.g., mandatory compliance, team-wide action items)
- User needs to chain the three quality skills together with enforced stage gating

## Common Pitfalls

- **Skipping stages**: Each stage is a mandatory gate. Skipping verification or QA because "the analysis looks fine" defeats the purpose — the ~10% error rate in first-draft reports is exactly what these stages catch.
- **Tolerating false positives**: The verification stage (Stage 2) must send the report back for correction if ≥3 false positives are found. Passing through with known inaccuracies erodes trust in the final deliverable.
- **Statistical drift across stages**: The file counts and line counts in Stage 1 may drift by the time Stage 2 runs if the codebase changes between stages. Run all three stages on the same commit.
- **QA gate as rubber stamp**: Stage 3 is not a formality — it catches statistical inconsistencies, test-coverage false negatives from aggregated test files, and security omissions that the other two stages routinely miss.

## Verification Checklist

- [ ] Stage 1 produced a complete quality report with all 7 dimensions covered and report file written to disk
- [ ] Stage 2 independently verified ≥5 sampled issues (truth, completeness, consistency) with concrete file:line evidence
- [ ] Stage 3 QA gate passed all 4 checks (statistical consistency, aggregated test files, file count header match, subdirectory boundary clarity)
- [ ] No stage was skipped — all three stages completed in strict order (1 → 2 → 3)
- [ ] Final delivered report has Appendix C (verification record) and no known inaccuracies remaining
