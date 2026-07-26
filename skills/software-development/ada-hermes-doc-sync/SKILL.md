---
name: ada-hermes-doc-sync
description: "Use when keeping Hermes project documentation in sync with a live Hermes installation — skill inventory diffing, command reference updates, version upgrade checklists, and periodic maintenance audits."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, documentation, maintenance, skills, version-sync]
    related_skills: [ada-hermes-agent-skill-authoring]
---

# Hermes 文档同步

当 `hermes-agent` skill 版本升级或定期维护 Hermes 项目文档时，系统性同步技能清单、命令引用和功能描述。

## When to Use
## 适用时机

- `hermes-agent` skill 版本号变化
- 定期（月度）项目文档巡检
- `hermes skills list` 输出与文档声称数量不一致
- 发现文档中有过时或失效的技能引用

## 流程

### Step 0: 确认文件结构

项目现为五文件三层架构（v2.4+）。同步前确认目标文件：

| 文件 | 定位 |
|------|------|
| `hermes-best-practices.md` | 入口——场景 + 技能链表格 |
| `hermes-built-in-capabilities.md` | 基础设施——工具/命令/机制。**不含技能** |
| `hermes-acquired-skills.md` | 技能手册——全部已安装技能，来源标注 |
| `hermes-self-evolution.md` | 进化引擎 |
| `EVOLUTION.md` | 进化日志 |

> 技能手册不区分"内置/习得"——全部技能加载方式相同。`hermes skills list` 输出全部已安装技能（~135），其中 `skills/` 目录部署的约 62 个标记为 local。

### Step 1: 技能差分分析

`hermes skills list` 使用 Unicode box-drawing 表格输出，grep/sed 对这类字符不可靠。使用 `execute_code` + Python 解析：

```python
from hermes_tools import terminal

result = terminal("hermes skills list")
lines = result["output"].split('\n')

# 提取技能名（跳过表头和分隔线）
skills = set()
for line in lines:
    if line.strip() and not any(line.startswith(c) for c in ['┌','├','└','│ Name','Installed']):
        parts = line.split()
        if parts:
            skills.add(parts[0])

print(f"Total: {len(skills)}")
```

然后与文档中已列出的技能做集合差运算：
- `new = actual - documented` → 新增但未文档化
- `removed = documented - actual` → 文档有但未安装
- 名称差异 → 手动对比（如 `c-project-template-v2` → `c-project-template`）

### Step 2: 全文档计数同步

发现计数不一致后，在以下位置统一更新：

| 位置 | 文件 | 搜索关键词 |
|------|------|-----------|
| 头部统计 | hermes-acquired-skills.md | 技能总数 |
| 全景图 | hermes-acquired-skills.md | 技能 (Skills) |
| 自动加载说明 | hermes-acquired-skills.md | tokens 估算 |
| 去重检查 | hermes-acquired-skills.md | 个技能中，有些功能重叠 |
| 来源清单 | hermes-acquired-skills.md §6.1 | 本项目 skills/ 部署 |
| 部署验证 | hermes-acquired-skills.md §6.3 | grep local |
| setup-skills.sh | setup-skills.sh | 源目录计数注释 |

### Step 3: 技能清单增删改

**删除未安装技能**: 从 §6.2 各分类表中移除条目
**新增未文档化技能**: 补充到对应分类表
**重命名**: 修正技能名并确认分类数

### Step 4: 残留引用清理

全局搜索已移除技能名，逐处修正：

```bash
# 对每个已移除技能
grep -rn "skill-name" *.md | grep -v "移除\|未安装"
```

三类处置：
- **可替换** → 替换为已安装替代技能（如 `multi-bug-batch-debugging` → `bugfix-architecture-root-cause`）
- **标注未安装** → 保留引用但加「（未安装）」标记
- **完全移除** → 删除过时条目

### 工作流 B: 外部文档对照审计

当 Hermes 官方文档发布新版本，或怀疑项目文档遗漏了重要原生能力时，执行此流程。核心思路：**下载完整权威文档 → 提取结构 → 交叉对比 → 生成差距清单 → 分 Phase 落地**。

#### Step B1: 获取完整文档

官方文档提供 LLM 上下文注入版（单文件，全部章节拼接）:

```bash
# 获取中文版（或替换 /zh-Hans/ 为 /en/）
curl -sL 'https://hermes-agent.nousresearch.com/docs/zh-Hans/assets/files/llms-full-<hash>.txt'
```

> 文件通常 3-4 MB。如果 curl 在 Windows 上遇到 SSL 错误（exit code 35），用 `browser_navigate` + `browser_console` 的 `fetch()` 作为备选。

#### Step B2: 提取文档结构

用 Python 提取源文件标记和 H1 标题，构建分区索引:

```python
from hermes_tools import read_file

text = read_file(path)['content']
for i, line in enumerate(text.split('\n')):
    if line.strip().startswith('<!-- source:'):
        print(f"L{i+1}: {line.strip()}")  # 源文件标记
    elif line.startswith('# ') and not line.startswith('## '):
        print(f"L{i+1}: {line.strip()}")  # 一级标题
```

#### Step B3: 交叉对比

逐项对照官方文档的能力清单与项目文档:

| 对比维度 | 官方文档来源 | 项目文档目标 |
|----------|-------------|-------------|
| 核心机制 | configuration.md, features/*.md | built-in-capabilities.md §4 |
| 斜杠命令 | skills 的 Slash Commands 表 | built-in-capabilities.md §3 |
| 工具集 | skills 的 Toolsets 表 | built-in-capabilities.md §1 |
| CLI 命令 | skills 的 CLI Reference | built-in-capabilities.md §4 |
| 功能板块 | 全部 features/*.md | best-practices.md 各场景 |

**判断标准**: 官方有但项目文档无 → 差距（Gap）。按影响面分为三级:
- 🔴 P0: 影响多个核心场景的基础设施能力
- 🟡 P1: 影响特定场景的效率工具
- 🟢 P2: 锦上添花的高级功能

#### Step B4: 产出 plan.md

按 Phase 组织改动计划，每个 Phase 列出:
- 改动文件 + 具体位置（行号或插入点）
- 改动内容（新增/修改/补充）
- 工作量估计

格式参考本 skill 的 `references/audit-plan-template.md`。

#### Step B5: 分 Phase 执行

按 P0 → P1 → P2 顺序执行，每 Phase 完成验证:
1. 检查 section numbering 级联影响（新增章节会偏移所有下游编号）
2. 更新 TOC
3. 更新交叉引用（"14 个场景" → "16 个场景"）
4. 同步 EVOLUTION.md 数据面板

### Step 5: Hermes 版本升级联动

当 `hermes-agent` skill 版本号变化时，额外检查：

| 检查项 | 方法 |
|--------|------|
| 新增斜杠命令 | 对比 skill 的 Slash Commands 章节 → 更新 best-practices §16 + built-in-capabilities §2 |
| 新增工具集 | 对比 skill 的 Toolsets 章节 → 更新 built-in-capabilities §1 |
| 新增 CLI 命令 | 对比 skill 的 CLI Reference → 更新 built-in-capabilities §3 |
| 新增提供者 | 对比 skill 的 Providers 章节 |
| 新增功能板块 | 评估是否需要新增场景（如 Kanban、Curator 等） |

### Step 6: EVOLUTION.md 同步

每轮进化后更新（详见 `references/evolution-checklist.md`）。

## Common Pitfalls
## 常见陷阱

| 陷阱 | 症状 | 对策 |
|------|------|------|
| **源目标计数分歧** | setup-skills.sh 声称数 ≠ 源目录实际数 | 分别验证 `find skills -name "SKILL.md" \| wc -l` 和 `hermes skills list` 的 local 数。脚本注释标注源目录计数 |
| **Unicode 表解析失败** | grep 在 `hermes skills list` 输出上不可靠 | 用 `execute_code` + Python 逐行解析 |
| **EVOLUTION header 忘更新** | 数据面板轮次=N，header 仍显示 N-1 | header 和 panel 是独立 patch 目标，改完后额外检查 |
| **ASCII 轨迹图断裂** | patch 时截断了代码围栏中的图 | 用包含前后文的大段 old_string 确保唯一匹配 |
| **级联引用遗漏** | 改完主流程但边缘引用（引擎 6/7/cronjob）未同步 | 用 search_files 全局扫描过时数字，逐处修正 |
| **章节插入导致编号漂移** | 新增场景后 TOC、决策树、抽象模型、引擎审视范围全部偏移 | 插入新节后必须执行一次全局编号同步：TOC条目+1、所有引用该节号的 grep 结果逐条修正、EVOLUTION 数据面板更新、引擎审视范围扩展 |

## Overview

`ada-hermes-doc-sync` keeps Hermes project documentation (best-practices, built-in-capabilities, acquired-skills, self-evolution, EVOLUTION.md) in lockstep with the live Hermes installation. It provides a systematic workflow for detecting and resolving drift: skill inventory diffing (set-difference analysis of `hermes skills list` vs documented skill lists), full-document count synchronization across seven touchpoints, skill list additions/removals/renames, stale reference cleanup, external documentation cross-auditing (comparing project docs against the official Hermes docs at hermes-agent.nousresearch.com), and version-upgrade cascade checks (new slash commands, toolsets, CLI commands, providers, and feature areas). Load this during periodic project maintenance or whenever the `hermes-agent` skill version changes.

## Verification Checklist

- [ ] Skill inventory diffed: `hermes skills list` output parsed and compared against documented skill lists; new/removed/renamed skills identified
- [ ] All seven counting touchpoints synchronized: header stats, panorama counts, auto-load notes, dedup notes, source manifests (§6.1), deployment verification (§6.3), and setup-skills.sh comments
- [ ] Stale references cleaned: global `grep -rn` for removed skill names; each occurrence either replaced with an installed alternative, marked "(未安装)", or deleted
- [ ] External documentation audited: official Hermes docs fetched, structure extracted, cross-compared against project docs; gaps triaged as 🔴 P0 / 🟡 P1 / 🟢 P2
- [ ] EVOLUTION.md updated: data panel counters match current state, header rounds match panel rounds, ASCII trajectory diagrams intact
