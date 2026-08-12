---
name: ada-github-pages-static-site
description: "Use when building or deploying any static site on GitHub Pages: architecture constraints, no-server limits, content publishing paths, and generated-artifact verification."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github-pages, static-site, blazor-wasm, deployment, github-actions, architecture]
    related_skills: [ada-blazor-wasm-github-pages, ada-dotnet-blazor-library, ada-dotnet-verification, ada-requirements-authoring]
---

# GitHub Pages 静态站点（架构约束与内容方案）

静态托管的架构约束与内容方案，适用于任何"部署在 GitHub Pages 上、无服务端"的网站。**先讲清楚约束再谈方案**。

## 硬约束（先讲清楚再谈方案）

1. **GitHub Pages 无服务端运行环境**：无进程、无数据库、无文件写入。发布后的页面没有任何"写文件"能力。
2. **GitHub Actions 不是常驻服务**：只在触发时（push、定时、issue 事件、workflow_dispatch）运行一次，结束即销毁。不能充当"等你提交内容的在线后端"。
3. **客户端不能持有凭据（红线）**：静态站 JS 对所有人可见，token/密钥放进客户端 = 公开凭据。任何"把 GitHub token 写进网页"的方案直接否决。

推论：**"在网页上直接上传内容"在纯静态站上不可实现**——缺一个能接收写入的服务端。

## 内容发布三路径（静态站"写内容"的可行方案）

| 路径 | 机制 | 代价 | 适用 |
|------|------|------|------|
| **1. Git 工作流（推荐）** | 内容源文件进仓库 → push → Actions 构建部署 | "上传"发生在 Git 层，不在网页上 | 网站所有者本人维护；与 CI 全自动闭环 |
| **2. GitHub Issues 中转** | 网页跳转 `issues/new?title=...&body=...` 预填模板，Actions 监听 issues 事件构建 | 内容写在 GitHub 页面而非本站；公开仓库任何人可开 issue，需审核 | 想要"网页可发起发布"的轻量升级 |
| **3. 第三方 CMS（Decap CMS 等）** | GitHub OAuth 在网页端编辑仓库文件 | 引入认证基础设施 + 外部依赖 | 多人内容维护 |

## 构建期内容转换（内容源管理）

区分两个问题——"内容源放哪"与"发布产物里有什么"：

- **方案 A**：内容源进仓库，构建期转换为静态页面 + 索引，发布产物不含原始源（如 XML）。CI 全自动。✅ 推荐
- **方案 B**：内容源仅存本地、不进仓库。GitHub Actions 拿不到源 → CI 无法从源构建，只能本地构建后提交产物（CI 中断）或私有仓库/Secret 中转。仅当内容必须保密且仓库公开时才考虑

**必须向用户问清"不发布"的确切含义**：是不进发布产物（方案 A，可行）还是不进仓库（方案 B，CI 含义完全不同）。

## GitHub API（公开只读）

- 匿名接口限流约 **60 次/小时/IP**；数据量大 → 构建期预取生成静态数据，或静态配置兜底，避免运行时逐次调用
- 只读公开接口（仓库列表、描述、Star 数）不携带凭据即可用；**任何会暴露凭据的调用一律不用**
- 需要写操作（建 issue 等）→ 走"用户自己登录 GitHub"的跳转/中转，不在本站持凭据

## Blazor WASM 部署要点

- **SPA 子路由刷新**：直接刷新 `/blog/xxx` 会 404 → 需 `404.html` 兜底（复制 index.html 内容或 JS 重定向）
- **用户级站点（`username.github.io`）根路径部署**，无 base href 子路径问题；**项目站点（`user.github.io/repo/`）必须处理 Base Href / 相对路径**
- 首次加载成本：IL 裁剪（PublishTrimmed）、gzip/brotli 压缩、合理缓存策略
- CSR 对 SEO 有限制：基础索引可用静态元数据、预渲染或静态生成缓解
- 无服务端 → 联系表单无接收方：第三方表单服务（外部依赖）或邮件链接降级；不推荐 Issues API（需凭据）

## 生成产物验证（分层源 → 生成产物的仓库）

审查/验证时必须证明**源与产物一致**，不能只信提交的文件：

- **生成 CSS bundle 的仓库**：可编辑源在 `wwwroot/css/{base,layout,home,pages,interactions,responsive}.css`，bundle 是生成文件（头部注释注明生成器）。新增样式必须改分层源再重新打包；契约测试用 `StyleBundleBuilder.Compose(cssDirectory)` 重组各分层源后与 bundle 逐字节比对——直接手改 bundle 会挂测试。验证：重新生成后 diff 提交版本，diff 为空 = 一致
- **i18n 资源键一致性**：`Language.T("...")` 使用键必须同时存在于两种语言的资源文件；删除文案键前先 grep 确认无 razor 引用（易误判死键）。一键扫描脚本见 `scripts/resource-key-check.py`
- **`sitemap.xml` 既是提交基线又是生成产物**：内容路由变化后同步生成产物到源位置并更新契约测试
- **`packages.lock.json` 随新 NuGet 依赖自动变更**：CI 用 `--locked-mode`，新增依赖后必须让 lock 文件进提交
- **global.json SDK 锁定**：仓库锁旧 SDK 而本机只有新 SDK 时，验证技巧：临时移走 `global.json` → 用已装 SDK 跑 build/test → 移回 → `git status --short` 确认干净（验证过程改动的生成文件 `git checkout --` 恢复）。旧 TFM 在新 SDK 下仅 NETSDK1138 EOL 警告，0 错误即可视为通过

## 陷阱

1. **`pwsh` 不在 git-bash PATH**：跑 PowerShell 脚本用 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <script>` 替代
2. **net6.0 测试项目不支持原始字符串 `"""`**（C# 10，报 CS8652）：多行字符串用 `$"..."` + `\n` 拼接或 `@"..."` 逐字字符串
3. **命名空间与库静态类冲突**：共享库命名空间若叫 `Portfolio.Markdown` 会遮蔽 Markdig 的 `Markdown` 静态类（CS0234）。用别名：`using MarkdigMarkdown = Markdig.Markdown;`
4. **构建期 Markdown 渲染的安全边界**：站内正文用构建期 Markdig → HTML + 白名单消毒，客户端 `MarkupString` 只渲染构建期消毒后的 HTML。**安全边界永远在构建期/服务端，不在浏览器**；明确否决"客户端渲染 Markdown"（客户端消毒不可靠）
5. **外部图片防盗链（Referer 403）**：站内正文外链图床图片可能因防盗链不显示。构建期下载到本地 `wwwroot/media/...` 并改写相对路径；失败保留外链 + 警告，构建不失败
6. **需求文本必须与已批准决策一致**：功能升级改写需求文档时，把批准的取舍写进去；修订后主动核对"需求文本 ↔ 批准决策 ↔ 实际代码"三方一致，不一致时改需求文本对齐决策，而非改实现

## 验证清单

- [ ] 与用户确认"内容源进不进仓库 / 进不进发布产物"，不默认
- [ ] 任何方案不含客户端凭据
- [ ] 用户级站点确认根路径部署；SPA 404 兜底方案已设计
- [ ] GitHub API 调用限流有兜底（构建期预取/静态数据）
- [ ] 联系表单、评论、上传等"写功能"已明确取舍路径
