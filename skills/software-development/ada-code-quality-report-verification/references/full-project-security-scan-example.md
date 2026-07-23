# Full-Project Security Gap Scan — Atlas 项目示例

来自 2026-07-22 独立安全复核会话的完整工作记录。作为全量安全扫描的方法论模板。

## 场景

用户要求：**独立复核：全项目安全漏洞遗漏扫描** — 不基于已有报告，而是从头扫描全部源文件。

扫描范围：C# Blazor 组件库项目 (net6.0)，82 个源文件（27 .cs, 16 .razor, 1 .ts, 4 .css, 2 .csproj, 9 .json, 其余为测试/配置文件）。

## 扫描流程

### Phase 1: 文件发现

```bash
# 列举全部源文件，排除 obj/ bin/
find src/ tests/ -type d \( -name obj -o -name bin \) -prune \
  -o -type f \( -name '*.cs' -o -name '*.razor' -o -name '*.ts' \
  -o -name '*.css' -o -name '*.csproj' -o -name '*.json' \) -print | sort
```

### Phase 2: 正则扫描（terminal grep，非 search_files）

`search_files` 工具在 Windows/MSYS 环境下可能因路径转换失败。回退方案：

```bash
cd <repo_root>
find src/ -type d \( -name obj -o -name bin \) -prune \
  -o -type f \( -name '*.cs' -o -name '*.razor' -o -name '*.ts' \) -print \
  | xargs grep -inE '<pattern>'
```

执行以下扫描，每条独立：

| # | 检查项 | grep 模式 |
|---|--------|-----------|
| 1 | 硬编码凭据 | `(password|pwd|secret|token|apikey|api.key|connection.string|connstr|jwt|bearer)\s*[:=]\s*["'"'"'][^"'"'"']{4,}["'"'"']` |
| 2 | eval() / 动态代码 | `(eval\s*\(|execScript|new Function\(|setTimeout\s*\(\s*["'\'']|setInterval\s*\(\s*["\'']` |
| 3 | XSS 风险 | `(MarkupString|Html\.Raw|InnerHtml|innerHTML|document\.write)` |
| 4 | 弱加密 | `(MD5|SHA1|DES\b|RC4|3DES|TripleDES|Rijndael|\.MD5\b|\.SHA1\b|DESCrypto|RC2)` |
| 5 | 不安全反序列化 | `(BinaryFormatter|SoapFormatter|NetDataContractSerializer|TypeNameHandling|LosFormatter|ObjectStateFormatter)` |
| 6 | 路径遍历 | `Path\.Combine` |
| 7 | 空 catch | `catch\s*\(\s*\)` |
| 8 | catch(Exception) | `catch\s*\(\s*Exception` |

### Phase 3: 全量阅读 .razor 和 .ts

这些文件是正则扫描最容易遗漏的。逐行 `read_file` 检查：

**.razor 文件检查清单：**
- `DynamicComponent` — Type 是否来自受控注册（非用户输入）
- `MarkupString`、`@(new MarkupString(...))` — HTML 编码绕过
- `html.Raw` — 直接 HTML 渲染
- `ErrorBoundary` 使用 — 安全实践，确认存在
- 事件处理中的异常处理（`@onclick` 委托中的 try/catch）

**.ts 文件检查清单：**
- `innerHTML` vs `textContent` — `textContent` 安全，`innerHTML` 危险
- `document.write` — 禁用
- `eval()` / `new Function()` — 禁用
- `setTimeout(string)` — 字符串参数 = eval
- `catch {}` 空块 — 检查日志

### Phase 4: 读取 JSON 和数据文件

- `launchSettings.json` — 检查 SSL 端口、环境变量中的凭据
- `manifest.json` — PWA 配置，无安全风险但需核实
- 示例数据文件（weather.json 等）— 检查是否有真实凭据
- `package.json` — 检查 devDependencies 中的可疑包

### Phase 5: 读取 .csproj 文件

- 检查 `PackageReference` — 是否有不安全版本的依赖
- 检查 `Target` 和 `BeforeTargets` — 是否有构建时代码执行
- 检查自定义 MSBuild 脚本

### Phase 6: 审阅每个 catch(Exception) 块

`catch(Exception)` 需要逐块阅读，分类：

| 模式 | 风险 | 判定 |
|------|------|------|
| `catch(Exception ex) { ...; throw; }` | 低 | ✅ 日志后重新抛出，安全 |
| `catch(Exception ex) { Debug.WriteLine(...); }` | 中 | ✅ Dispose 路径的优雅降级 |
| `catch(Exception ex) { }` | 高 | ❌ 静默吞异常 |
| `catch(Exception) { }` | 高 | ❌ 无变量、无日志 |

### Phase 7: 补充扫描

- `Process.Start` / `ShellExecute` — 命令注入风险
- `HttpClient` 使用 — 检查 URL 是否包含用户输入拼接
- `System.Reflection` — 动态类型加载

## 报告格式

### 零发现时

```
已验证全部源文件，零新增安全风险。

### 检查项逐条详情

**1. 硬编码凭据** — ✅ 零发现
- launchSettings.json 仅含本地开发 URL，无密钥
- ...

**N. catch(Exception) 块** — 已验证
| 位置 | 文件:行 | 行为 | 判定 |
|------|---------|------|------|
| Foo.cs | :42 | Debug.WriteLine + throw; | ✅ 安全——日志后重新抛出 |
```

### 有发现时

```
### 🔴 N. [发现标题]

**文件**: `path/file.ext:line`
**代码片段**:
```csharp
// 有问题的代码
```
**风险**: 严重/高/中/低
**说明**: 问题描述和影响
```

## 已知 Windows/MSYS 工具差异

- `search_files` 工具在处理长 Windows 路径（`/c/Users/...` 格式）或复杂正则时可能返回 "系统找不到指定的路径" 错误。回退方案：使用终端 `find | xargs grep`。
- 正则转义在 MSYS bash 中需要单引号包裹模式本身，但需要正确处理模式内的单引号（`'"'"'` 模式）。
- `grep` 的 `-E`（扩展正则）比默认基本正则更稳定。
