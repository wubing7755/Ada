# SRS 需求条目格式参考示例

> 本文件为 `tp-to-srs-derivation` 技能的格式参考。展示了经用户验证的完整需求条目格式。

## 通用格式

每个需求条目必须用代码围栏（`````` ` ` ``` ``）包裹，围栏包含从 `###` 标题行到最后一个 AC 的全部内容：

````markdown
```
### REQ-F-XXX 🔴 [Actor: RoleName]

**Title**
<中文标题>

**Description**
<中文功能描述，说明系统应做什么行为>

**Acceptance Criteria**

AC1：<中文场景名称>

Given <英文前置条件>
When <英文触发操作>
Then <英文预期结果>
And <英文附加结果>

AC2：<中文场景名称>

Given <英文前置条件>
When <英文触发操作>
Then <英文预期结果>
```
````

## 示例一：标准功能需求（含代码围栏包裹）

````markdown
```
### REQ-F-006 🔴 [Actor: Application Developer]

**Title**
线型 .c/.h 文件生成

**Description**
线型生成工具应根据用户配置的占空比、线宽、颜色和索引值，生成 `.c` 形式的 A661 线型表资源文件和相应的资源声明 `.h` 文件。生成的源文件应可编译链接到 A661 Server 软件中，并按索引获取相应线型数据。

**Acceptance Criteria**

AC1：生成源文件

Given 用户已完成线型参数的配置
When 用户点击「生成源文件」
Then 系统应生成对应的 .c 文件和 .h 文件
And .c 文件应包含按索引组织的线型数据
And .h 文件应包含相应的外部声明和宏定义

AC2：编译兼容

Given 已生成的 .c 和 .h 文件
When 将文件添加到 A661 Server 工程中编译
Then 应能成功编译链接
And 通过索引值应能正确获取对应的线型占空比、线宽和颜色数据
```
````

## 示例二：多 Actor 需求（含代码围栏包裹）

````markdown
```
### REQ-F-001 🟡 [Actor: Application Developer, Verification Engineer, System Integrator]

**Title**
登录入口

**Description**
系统应为每个工具提供一个登录界面作为启动入口。用户输入任意非空的用户名和密码即可进入主页面，系统不执行实际的身份鉴权验证。

**Acceptance Criteria**

AC1：显示登录界面

Given 用户访问任一工具
When 系统加载完成
Then 应显示登录界面，包含用户名输入框、密码输入框和登录按钮

AC2：任意凭证可登录

Given 登录界面已显示
When 用户输入任意非空的用户名和密码并点击登录按钮
Then 系统应允许进入主页面
And 不应拒绝任何非空的用户名/密码组合
```
````

## 格式要点清单

| 要素 | 规范 |
|:----:|------|
| 编号 | `REQ-F-XXX`，三位数字全局连续 |
| 优先级 | 🔴 P0 / 🟡 P1 / 🟢 P2，放在编号后 |
| Actor | `[Actor: RoleName]`，英文，多角色用逗号分隔 |
| 标题层级 | 用 `###` 作为需求头部（Markdown 标题级） |
| 分段标题 | `**Title**` `**Description**` `**Acceptance Criteria**` 加粗段落 |
| AC 场景名 | `AC1：<中文场景名>`，不可省略或有空 |
| Given/When/Then | 英文，各自独立一行 |
| 附加结果 | 用 `And` 行衔接在 Then 之后 |
