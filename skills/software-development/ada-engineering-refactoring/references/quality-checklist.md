# 重构工程质量验证清单

每次重构 Phase 完成后逐项检查。

## 类设计
- [ ] 所有新增类声明 `sealed`（除非明确为继承点）
- [ ] 实现细节用 `internal`，仅消费者需要的用 `public`
- [ ] 抽象基类构造函数 `protected`
- [ ] 无 `#region` 指令
- [ ] 值类型声明 `readonly struct`

## 成员设计
- [ ] 无 `public`/`protected` 字段——用自动属性
- [ ] 值类型实现 `IEquatable<T>` + `==`/`!=`
- [ ] 单行方法/属性用表达式体 `=>`
- [ ] 统一 `is null`/`is not null`（不用 `== null`）

## XML 文档
- [ ] 所有 `public`/`protected` 成员有 `<summary>`
- [ ] 新增类型的 `internal`/`private` 成员在意图不明显时有文档
- [ ] 参数和返回值有 `<param>`/`<returns>`（语义不明显时）

## 参数验证
- [ ] 引用类型参数：`if (x is null) throw new ArgumentNullException(nameof(x))`
- [ ] 字符串参数：`if (string.IsNullOrWhiteSpace(x)) throw new ArgumentException(...)`
- [ ] 不在方法入口重复验证构造函数传入的 readonly 字段

## 异常处理
- [ ] 不使用 `catch (Exception)`（仅日志+重抛可接受）
- [ ] 异常消息包含上下文（哪个 ID/名称导致失败）
- [ ] 不静默吞异常

## 测试（Phase 涉及测试时）
- [ ] 命名: `Method_Scenario_ExpectedBehavior`
- [ ] AAA 模式（Arrange→Act→Assert，空行分隔）
- [ ] 单一断言概念
- [ ] 覆盖错误路径
- [ ] 测试类 `sealed`
