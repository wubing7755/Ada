# Full Statistical Self-Consistency Audit — Example

This is a worked example from an actual verification session where all 7 statistical
items in a code quality report were verified for self-consistency. Unlike the
sampling approach in `session-verification-example.md`, this is an exhaustive
audit of every quantitative claim in the report.

## Report Under Audit

- **Report**: `docs/reports/code-quality-2026-07-22-full.md` (Lib project)
- **Scope claim**: "src/Lib/（47 个文件，5,510 行）+ tests/（12 个文件，1,907 行）"
- **Coverage claim**: "8/30 源类有直接测试覆盖（27%）"
- **Test claim**: "130 个测试（123 [Fact]/[Theory] + 7 个结构验证）"
- **Previous report citation**: "前次报告覆盖 3 个文件，908 行"

## Verification Results

### 1️⃣ Source file count & lines (47 files, 5,510 lines)

**❌ 不一致**

| Metric | Report | Actual | Delta |
|--------|--------|--------|-------|
| src/ file count | 47 | 50 | +3 |
| src/ line count | 5,510 | 5,519 | +9 |
| Header claim | "48 个源文件" | 50 | — |

Root cause: Report excluded `src/Lib/_Imports.razor` (4 lines), and its
subdirectory breakdowns are systematically off (see item 4).

### 2️⃣ Test file count & lines (12 files, 1,907 lines)

**✅ 一致**

| Metric | Report | Actual | 
|--------|--------|--------|
| File count | 12 | 12 |
| Line count | 1,907 | 1,907 |

Subdirectory breakdowns have errors but the totals match.

### 3️⃣ Coverage 8/30 (27%)

**✅ Percentage correct, ⚠️ Coverage list incomplete**

- 8/30 = 26.67% → 27% ✅
- But actual source code has ~45 public/internal classes. Report's "30 源类"
  selectively excludes interfaces, enums, internal DTOs, and multi-class files.
- **Missing covered classes**: `DomainModelTests.cs` tests DockPanelModel + TabModel
  (6+3=9 [Fact] tests) — both listed as "uncovered" in the report.
- `DockResultTests.cs` tests DockResult (5 [Fact]) — DockResult not even in the
  report's class list.
- Actual covered source classes: at least 11, not 8.

### 4️⃣ Subdirectory breakdown sums

**❌ Internal arithmetic inconsistency + factual errors**

Subdirectory sums from report's own table:
```
1,484 + 806 + 1,755 + 419 + 97 + 98 + 437 + 470 = 5,566
```
Report claims total: **5,510** ← off by 56 lines

Per-directory comparison:

| Subdirectory | Report files | Actual files | Report lines | Actual lines |
|-------------|-------------|-------------|-------------|-------------|
| Components/ | 11 | 11 ✅ | 1,484 | 1,229 ❌ |
| Domain/ | 12 | 11 ❌ | 806 | 639 ❌ |
| Services/ | 13 | 16 ❌ | 1,755 | 2,135 ❌ |
| Services/Commands/ | 6 | 6 ✅ | 419 | 410 ❌ |
| Interop/ | 1 | 1 ✅ | 97 | 97 ✅ |
| Results/ | 2 | 2 ✅ | 98 | 98 ✅ |
| ClientScripts/ | 1 | 1 ✅ | 437 | 437 ✅ |
| wwwroot/ | 1 | 1 ✅ | 470 | 470 ✅ |

### 5️⃣ Test method counts (130 = 123 [Fact]/[Theory] + 7 结构验证)

**❌ [Fact]+[Theory]=123 ✅, but "7 结构验证" not found**

- Actual [Fact]: 121
- Actual [Theory]: 2
- Total: 123 (matches report's "123")
- Report claims 7 additional "结构验证" tests → total 130. No such tests or
  markers exist in any test file. All test methods are [Fact] or [Theory] annotated.

### 6️⃣ Random spot checks (3 files)

Report doesn't provide per-file line counts in the full report appendix,
only subdirectory totals. Spot-checked against subdirectory totals:

| File | Subdir report lines | Actual file lines | Verdict |
|------|-------------------|-------------------|---------|
| LayoutState.cs (Domain/) | 806 (domain total) | 158 | N/A — only subdir total available |
| DragService.cs (Services/) | 1,755 (services total) | 225 | N/A — same |
| lib.css (wwwroot/) | 470 | 470 | ✅ matches |

### 7️⃣ Cross-report consistency (prior report = 908 lines)

**✅ 一致**

- Prior report (`code-quality-2026-07-22.md`): ToolBar.razor 395 + LayoutStyleAdapter.cs 42 + lib.css 471 = 908 ✅
- Current working tree has modified ToolBar.razor (+20 lines) and lib.css (-1 line) making them 415 and 470 respectively, but the cited 908 refers to the prior report's own totals at its generation time, not the current file state.

## Summary

| # | Check | Result | Key Finding |
|---|-------|--------|-------------|
| 1 | src file count & lines | ❌ | 47→50 files, 5,510→5,519 lines |
| 2 | test file count & lines | ✅ | 12 files, 1,907 lines ✅ |
| 3 | coverage 8/30 (27%) | ⚠️ | Calc ✅, list missing 2+ covered classes |
| 4 | subdir breakdown sums | ❌ | Self-inconsistent: 5,566 ≠ 5,510; per-dir values also off |
| 5 | test method counts | ❌ | 123 = 121+2 ✅; "7 结构验证" unsubstantiated |
| 6 | spot checks | — | No per-file data to compare |
| 7 | prior report 908 lines | ✅ | Self-consistent |
