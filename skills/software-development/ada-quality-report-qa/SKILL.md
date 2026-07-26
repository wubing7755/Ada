---
name: ada-quality-report-qa
description: "Use when running the three-agent QA pipeline on a code quality report — catches statistical errors, test-coverage false negatives, and security scan omissions before delivery. Complements ada-code-quality-analysis."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-quality, qa, verification, report]
    related_skills: [ada-code-quality-analysis, ada-requesting-code-review, ada-code-quality-pipeline]
---

# Quality Report QA — 报告质量门禁

在 `code-quality-analysis` 的 Step 5 三 Agent 复核基础上，增加四道额外的质量门禁。**本 skill 专门捕获主 skill 未覆盖的常见陷阱：统计偏差、聚集测试文件遗漏、不安全的统计公式。**

## Overview

This skill adds four extra quality gates on top of the 3-agent verification built into
`code-quality-analysis`. It specifically targets failure modes that the main skill's
verification routinely misses: statistical formula inconsistency (sub-totals not
matching the unified total), aggregated test file detection (coverage miscounts from
files containing multiple test classes like `DomainModelTests.cs`), header-vs-appendix
file count mismatches, and subdirectory boundary blurring where parent directories are
double-counted. Based on empirical data, first-draft hand-written reports have ~10%
error rates — these four gates catch those errors before delivery.

## When to Use

- 完成代码质量报告撰写后、交付用户前
- 报告中包含附录 A 文件统计表
- 报告中有测试覆盖率数据
- 交互式 Agent 手工编制报告（非全自动 pipeline）


Don't use for: running the initial code quality analysis — load `ada-code-quality-analysis`. Verifying individual report claims — load `ada-code-quality-report-verification`. This is the final QA gate before delivery, not the first step.

## 四道门禁

### 门禁 1：统计公式一致性检查

不要相信 `wc -l` 累加得到的总数。必须用 **同一套 `find` 命令** 覆盖两次计算：

```
❌ 错误做法：分别计算每个目录的 wc -l，然后手工相加
✅ 正确做法：
  TOTAL=$(find src -type f (...) ! -path "*/obj/*" -exec cat {} + | wc -l)
  SUBTOTAL=$(for dir in ...; do find "$dir" ... | ...; done | awk '{s+=$1}END{print s}')
  [ "$TOTAL" == "$SUBTOTAL" ] || echo "MISMATCH: $TOTAL vs $SUBTOTAL"
```

**绝对不能容忍** 附录 A 的子目录行数和不等于用统一公式计算的总行数。偏差就是错误信息——不是"约等于"。

### 门禁 2：测试聚集文件检测

按文件名匹配 (`FooTests.cs ↔ Foo.cs`) 会漏掉包含多个内嵌测试类的**聚集文件**（如 `DomainModelTests.cs` 包含 `DockPanelModelTests` 和 `TabModelTests`）。

修复方法：用 `grep -rhoP 'class\s+\w+Tests\b'` 提取所有测试类名，然后检查它覆盖了哪些源类。

```bash
grep -rhoP 'class\s+\w+Tests\b' tests/ --include="*.cs" | sort -u
```

然后把每个测试类名去掉 `Tests` 后缀后与源类名做匹配。

### 门禁 3：可执行文件计数 vs 总文件计数

报告头部写的「审查范围」与附录 A 的文件数应一致。常见的矛盾：
- 头部写「48 个源文件」，附录 A 加起来 47 个
- 忘记计入根目录文件（如 `_Imports.razor`、`_Imports.cs`）
- 将生成文件（如 `atlas.js`）计入源码文件计数

修复方法：直接用 find 命令列出所有源文件并计数，不要目测：

```bash
find src -type f \( -name "*.cs" -o -name "*.razor" -o -name "*.css" -o -name "*.ts" \) ! -path "*/obj/*" ! -path "*/bin/*"
```

### 门禁 4：子目录边界模糊

当提取子目录行数时，必须注意 `Services/` 目录是否包含 `Services/Commands/` 子目录。如果报告将它们分列为两行，第一行必须是**仅顶层**（不含子目录），第二行为子目录。

```bash
# 仅顶层
find Services -maxdepth 1 -type f -name "*.cs" ...

# 含子目录的完整计数
find Services -type f -name "*.cs" ...  # 包含 Commands/
```

## 典型错误率

根据实践统计，手工编制的报告在第一版中约有 10% 的错误率（统计偏差 + 覆盖分类错误）。这属于可接受范围——但必须经过本 QA pipeline 修正后再交付。

## Verification Checklist

- [ ] 附录 A 子目录行数和 == 统一 find 公式的计算总数
- [ ] 报告头部文件数 == 附录 A 文件数
- [ ] 测试覆盖表已检查聚集文件（`grep -rhoP 'class.*Tests\b'`）
- [ ] 子目录行数未混入（如 Services/ 不含 Commands/ 的子目录行数）
- [ ] `obj/`、`bin/`、生成文件已排除

## Common Pitfalls

- **Trusting manual addition over unified find**: Adding per-directory `wc -l` results by hand introduces arithmetic errors. Always run a single unified `find -exec cat {} + | wc -l` command to get the true total and cross-check the sum of subdirectory counts against it.
- **Filename-matched test coverage only**: The common mapping pattern (`FooTests.cs ↔ Foo.cs`) misses aggregated test files that contain multiple test classes. Always grep for `class.*Tests\b` patterns across all test files.
- **Header vs. appendix mismatch**: The report header may claim "48 source files" while the appendix table lists 47. Always count independently with `find` and flag discrepancies between the scope statement and the detailed breakdown.
- **Subdirectory double-counting**: When `Services/` contains `Services/Commands/`, the subdirectory breakdown must explicitly clarify whether the parent count includes child subdirectories. Use `-maxdepth 1` for parent-only counts and subtract child subtotals to verify.
