# Session Verification Example — Atlas Code Quality Report (2026-07-22)

This is a worked example from an actual verification session. Use it as reference
for the level of detail expected in each verdict.

## Sampled Issues

| # | Issue | Priority | Why sampled |
|---|-------|----------|-------------|
| 1 | P0-1: 测试覆盖严重不足 (22/30 零覆盖) | 🔴 Critical | Core metric for trustworthiness |
| 2 | P0-2: LayoutContext 5 处 ExecuteLocked + NotifyLayoutChanged 模板重复 | 🔴 Critical | Pattern defect claim |
| 3 | P1-2: UndoStack.ExecuteLocked 重载代码重复 | 🟠 High | Duplicate code claim |
| 4 | P1-1: LayoutDto.cs 格式化错误 (8 处 WHITESPACE) | 🟠 High | Tool-reproducible claim |
| 5 | P1-3: LayoutStyleAdapter 零测试 | 🟠 High | Coverage gap claim |

## Verification Results

### 1️⃣ P0-1: 测试覆盖严重不足（22/30 类零覆盖）

**⚠️ 部分正确**

- **证据**: 37 源 .cs 文件；测试文件 12 个。`DomainModelTests.cs` 包含
  `DockPanelModelTests` 和 `TabModelTests`。
- **偏差**: 报告称 22 个类零覆盖，实际 **20 个**——DockPanelModel 和 TabModel
  在 `DomainModelTests.cs` 中已有结构化测试，但报告将两者列为"未覆盖 ❌"。
- **结论**: 测试覆盖严重不足是真实问题，但报告**高估**了零覆盖数量。

### 2️⃣ P0-2: LayoutContext 5 处 ExecuteLocked + NotifyLayoutChanged 模板重复

**⚠️ 部分正确**

- **证据**: 源码中 `ExecuteLocked(() =>` 实际有 **7 处**
  (`LayoutContext.cs:208,235,275,314,353,365,400`)。
- **偏差**:
  - 报告说"5 处"，实际 7 处，另有 2 处（MoveTab:208, SplitView:235）也被忽略
  - 报告引用的行号范围 (275-407) 中的 MovePanel (line 275) **不含**
    `NotifyLayoutChanged` 调用——通知在 command 内部触发
  - 实际同时包含 `ExecuteLocked + NotifyLayoutChanged` 的是 **5 处**
    (SplitView:235, TogglePanel:314, ExpandPanel:353, CollapsePanel:365,
    EnableAutoHide:400)，但这个数字巧合匹配了报告的"5 处"
- **结论**: 重复模式确实存在，且比报告描述的更广泛，但模式定义描述有细节偏差。

### 3️⃣ P1-2: UndoStack.ExecuteLocked 重载代码重复

**✅ 确认存在**

- **证据**: `UndoStack.cs:19-29` 和 `:32-42`
  - `ExecuteLocked(Action)` vs `ExecuteLocked<T>(Func<T>)`
  - 仅 1 行不同：`action()` vs `return func()`
  - 实际重复 7 行（try/catch/finally + Wait/Release）
- **结论**: 问题真实存在，且比报告描述的更严重（报告说"4 行"，实际 7 行）。

### 4️⃣ P1-1: LayoutDto.cs 格式化错误（8 处 WHITESPACE）

**⚠️ 无法复现（可能已修复）**

- **证据**: 运行 `dotnet format --verify-no-changes` 无 LayoutDto.cs 相关输出。
  肉眼检查 line 267+ 的 `FromModel` 初始化器，缩进一致。
- **结论**: 可能是报告生成后已被修复，而非虚假报告。不能认定为误报。

### 5️⃣ P1-3: LayoutStyleAdapter 零测试

**✅ 确认存在**

- **证据**: `src/Atlas/Domain/LayoutStyleAdapter.cs`（42 行）有构造函数验证、
  `PxToRatio` 计算属性和 5 个 CSS grid 样式属性。`tests/` 下所有文件
  无任何对 `LayoutStyleAdapter` 的引用。
- **结论**: 零测试完全属实。

## Summary

| # | Issue | Severity | Outcome | Core Deviation |
|---|-------|----------|---------|----------------|
| 1 | P0-1: 测试覆盖严重不足 | 🔴 | ⚠️ | 22→20 个零覆盖（漏算 DomainModelTests） |
| 2 | P0-2: LayoutContext 重复模式 | 🔴 | ⚠️ | 7 处而非 5 处，MovePanel 不含 Notify |
| 3 | P1-2: UndoStack 重载重复 | 🟠 | ✅ | 说 4 行重复，实际 7 行 |
| 4 | P1-1: LayoutDto 格式化错误 | 🟠 | ⚠️ | 无法复现，可能已修复 |
| 5 | P1-3: LayoutStyleAdapter 零测试 | 🟠 | ✅ | 完全准确 |

**Overall**: None of the 5 sampled issues is a pure false positive. 3 are fully
confirmed, 2 have detail inaccuracies but the core problem is real. The report's
primary tendency is mild overstatement, not fabrication.
