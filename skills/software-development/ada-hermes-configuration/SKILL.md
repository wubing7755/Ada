---
name: ada-hermes-configuration
description: "Use when configuring Hermes Agent — SOUL.md design, memory and profile optimization, personality tuning, and deciding what goes where (SOUL vs AGENTS.md vs skill). Also covers batch memory operations and configuration best practices."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, configuration, soul, memory, personality, optimization]
    related_skills: [hermes-agent]
---

# Hermes 配置与人格设计

## Overview

This skill covers Hermes Agent configuration patterns including SOUL.md personality
design (what belongs vs. what doesn't — identity only, not operational instructions),
memory and profile optimization (batch atomic operations, identifying stale references,
target <70% capacity), and the configuration layering model (SOUL.md for identity,
AGENTS.md for project rules, skills for workflows, memory for persistent preferences).
It also provides concrete guidance for curator setup (auto-consolidation and archival)
and cross-machine skill export.

## When to Use

- User wants to configure or tune Hermes Agent's personality, communication style, or behavior
- User asks about SOUL.md design, memory optimization, or profile management
- User needs to decide where configuration rules belong (SOUL vs AGENTS vs skills)
- User encounters memory capacity issues (>80% full) or wants to batch-update memory entries
- User asks "how do I configure Hermes", "优化 memory", "配置 Hermes personality", or "curator setup"


Don't use for: skill authoring — use skill authoring workflows directly. Runtime debugging of Hermes itself — load `hermes-agent` (built-in).

## SOUL.md 编写

**SOUL.md = 身份标识，不是操作手册。** 占据系统提示词第 1 个槽位。

### ✅ 应该写

| 维度 | 示例 |
|------|------|
| 语气 | "直接坦诚"、"结论在前" |
| 沟通风格 | "效率优先但不冷淡" |
| 直接程度 | "不确定就直说" |
| 风格禁忌 | "不写小作文"、"不用'叭、捏、嗷'" |
| 不确定性应对 | "遇到歧义先澄清，不猜测意图" |

### ❌ 不该写（去哪）

| 错误 | 应该去哪 |
|------|---------|
| 操作指令（"删文件前先确认"） | skill 或 AGENTS.md |
| 回复格式规则 | 不写——让模型自主判断 |
| 记忆策略、工作流步骤 | 独立 skill |
| 泛泛之词（"有用"、"要清晰"） | 不写——模型本来就会 |

### 判断原则

> 随用户到处适用 → SOUL.md  
> 只属某个项目 → AGENTS.md  
> 教 Agent 怎么做某类事 → skill

### 结构建议

三段式即可，不需要标题但标题有助组织:
```
你是 <角色名>，<一句话定位>。

## 你是谁
- 性格特质、核心原则

## 风格
- 具体语气规则、避免的写法

## 边界
- 不确定性处理、安全/道德底线
```

### 部署

SOUL.md 放在 `$HERMES_HOME/SOUL.md`（全局）或 `$HERMES_HOME/profiles/<name>/SOUL.md`（按 Profile）。Hermes 启动时自动读取，替换内置默认身份。不覆盖已有文件。

## 记忆与 Profile 优化

### 批量操作

Hermes memory 支持 `operations` 数组批量原子操作:

```
memory(target="user", operations=[
  {action:"remove", old_text:"unique substring"},
  {action:"replace", content:"new", old_text:"old substring"},
  {action:"add", content:"new entry"},
])
```

一次调用完成增删改，按最终结果检查字符上限。比逐条调用安全——不会被中间状态的字符上限卡住。

### 优化时机

- memory 占用 > 80%
- 条目数 > 5 条
- 发现过时引用（文件名/版本号/数字与实际不一致）
- 发现重复内容（两条说同一件事）

### 优化流程

1. 用 `operations` 数组一次性执行全部改动
2. 先 remove 过时/重复，再 replace 修正，最后 add 新合并条目
3. 每条 remove 的 old_text 用最短唯一子串（避免转义问题）
4. 目标: 占用率 < 60%，条目数 ≤ 5

### 识别过时引用

- 文件名变更: `hermes-skills-guide.md` → `hermes-acquired-skills.md`
- 版本号: `v2.0.0` → `v2.1.0`
- 数字统计: `14 场景` → `16 场景`、`71 个技能` → `62 个`
- 进度标记: `R24 进行中` → 已完成

## 配置分层模型

| 层级 | 文件 | 作用域 | 内容 |
|------|------|--------|------|
| 身份 | `SOUL.md` | 全局/Profile | 语气、风格、性格 |
| 项目规则 | `AGENTS.md` / `.hermes.md` | 项目目录 | 编码规范、路径、命令 |
| 操作流程 | skill | 按需加载 | 工作流步骤、陷阱、验证 |
| 持久偏好 | memory(user) | 跨会话 | 语言、工具偏好、约定 |
| 环境笔记 | memory(memory) | 跨会话 | 项目结构、部署方式、经验教训 |

## Common Pitfalls

- **Putting operational instructions in SOUL.md**: SOUL.md is identity only (tone, style, personality). Operational rules like "confirm before deleting files" or "run tests after every change" belong in skills or AGENTS.md. The litmus test: "Does this rule apply everywhere I use this profile?" → SOUL.md. "Does this rule only matter for this project?" → AGENTS.md.
- **Memory capacity overload**: Memory should stay under 70% capacity; above 80% is critical. Batch-optimize by removing stale entries first (outdated file names, old version numbers, completed progress markers), then replace inaccurate entries, and finally add new merged entries — all in one `operations` array call.
- **Single operations on memory instead of batch**: Using separate `memory(action='add')` calls when an `operations` array could do it all at once risks hitting character limits between calls. The batch approach is atomic — the entire operation succeeds or fails as one.
- **Forgetting that config changes need session reset**: SOUL.md and skill description changes only take effect after `/reset` or starting a new session. If a change doesn't seem to work, verify with `/reset` before debugging further.

## Verification Checklist

- [ ] SOUL.md contains only identity/communication style content (no operational instructions, no formatting rules, no workflow steps)
- [ ] Memory usage is under 70% capacity with ≤5 entries; no stale references (old filenames, version numbers, progress markers)
- [ ] Configuration layering is correct: identity in SOUL.md, project rules in AGENTS.md/.hermes.md, procedures in skills, preferences in memory
- [ ] Curator settings are active (`curator.consolidate: true` with `stale_after_days` and `archive_after_days` configured)
- [ ] `hermes config list` confirms all settings match intended configuration
