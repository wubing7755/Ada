---
name: ada-blazor-wasm-github-pages
description: "Use when deploying Blazor WASM static sites to GitHub Pages: content pipeline, Actions workflow, SPA fallback, and verified deployment pitfalls."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, wasm, github-pages, static-site, content-pipeline, deployment, github-actions]
    related_skills: [ada-github-pages-static-site, ada-dotnet-verification, ada-dotnet-blazor-library, ada-srs-writing]
---

# Blazor WASM 静态站点部署到 GitHub Pages

## 触发条件

- 把 Blazor WebAssembly 站点部署到 GitHub Pages（用户级 `<user>.github.io` 或项目级站点）
- 静态站点 + 构建期内容转换（XML/Markdown 内容源 → JSON 站点数据）
- 需要 GitHub Actions 自动构建部署 + SPA 子路由刷新兜底

## 工程结构（验证过的布局）

```
repo/
├── .github/workflows/deploy.yml
├── content/                  # 内容源（仓库根，NOT wwwroot → 不进发布产物）
├── src/<App>/                # Blazor WASM 主工程
│   └── wwwroot/
│       ├── data/             # 构建期生成的 JSON（转换工具输出，gitignore）
│       └── index.html
├── tools/<Converter>/        # 构建期内容转换工具（控制台）
└── <App>.sln
```

## 核心结构决策

1. **内容源放仓库根 `content/`，绝不放 wwwroot 下** —— wwwroot 下所有文件都会进发布产物，无法满足"XML 源文件不发布"
2. 构建期转换工具（`tools/ContentConverter` 控制台）：读 `content/*.xml` → 生成 `src/<App>/wwwroot/data/*.json`
3. `wwwroot/data/` 加入 .gitignore（构建期生成物）；**本地开发先手动跑 converter 再 `dotnet run`**——否则每个 `data/*.json` 请求 404（运行时失败，不是构建失败）
4. 发布产物结构：Blazor WASM standalone 的 `dotnet publish -o publish` 输出在 **`publish/wwwroot/` 子目录**；GitHub Pages artifact 根必须是 `publish/wwwroot`

## GitHub Pages 必要条件

- artifact 根内必须有 `.nojekyll`（否则 Jekyll 丢弃 `_framework/` 等以下划线开头的目录 → 站点白屏）
- SPA 子路由刷新：`cp publish/wwwroot/index.html publish/wwwroot/404.html`（GitHub Pages 对未匹配路径返回 404.html，Blazor 启动后按地址路由）
- 工作流权限：`contents: read, pages: write, id-token: write`；deploy job 用 `environment: github-pages`
- `actions/upload-pages-artifact@v3` `path: publish/wwwroot` + `actions/deploy-pages@v4`
- 用户级站点（`<user>.github.io`）部署于根路径，无 base href 子路径问题；项目级站点需 `<base href="/<repo>/">`

## GitHub Actions 工作流要点

- **deploy 与 CI 分离**：deploy.yml 只管 main 部署；独立 ci.yml 在 feature push / PR 上做 build+test+format+converter 门禁。PR 模板含需求覆盖与 AI 协助披露；dependabot 按生态分组
- 步骤序：checkout → setup-dotnet → 内容转换 → publish → 404 兜底 → .nojekyll → upload → deploy
- **format 作业的 setup-dotnet 版本用与本地一致的 SDK，不要用 build 作业的旧版本**——format 行为随 SDK 漂移，本地绿/CI 红几乎必现
- **Dependabot 会自动 rebase 自己的分支**——报"有冲突"的 PR 常已被自动解决，先 `gh pr view N --json mergeable,mergeStateStatus` 看 CLEAN/UNSTABLE 再决定；`gh pr merge N --squash --delete-branch` 后用 `gh pr view N --json state` 确认 MERGED
- deploy.yml 的 `concurrency: cancel-in-progress` 会取消中间部署、只跑最后一个（预期行为）
- 模板见 `templates/deploy.yml`；多批交付时协作脚手架应作为 Batch 0 先于 feature 批次落地

## 内容管线（XML → JSON）

- 多语言字段统一用**直接 lang 属性**结构：`<title lang="zh">…</title><title lang="en">…</title>`
- **坑（实测 bug）**：嵌套结构 `<field><text lang="zh">A</text><text lang="en">B</text></field>` 用 `e.Value` 取值会把子元素文本**拼接**成 `"AB"`。解析用 `parent.Elements(name)` + lang 属性做字典
- 搜索索引按语言分别生成（`search-index-{lang}.json`），条目含 id/type/title/intro/link/route
- 输出用 `JsonSerializerOptions { WriteIndented = true, Encoder = UnsafeRelaxedJsonEscaping }` 让中文直出，便于人工审查
- 转换工具输出字段级 JSON 断言是必须验证（只查文件存在查不出多语言合并 bug）
- **构建期外部数据富化（阅读量/星标等）**：静态站无服务端，外部指标在构建期于 converter 内抓取——无 CORS、无客户端延迟、每次发布刷新。**降级契约：抓取失败必须静默降级（日志 + 保留旧值），构建绝不能因外部站点不可达而失败**（用不可达代理实测 exit 0）
- **`--validate` 目标指向真实站点根**（`content <App>/wwwroot`），不要指向临时输出目录——临时目录缺 `wwwroot/media/...` 会误报"找不到站内资源"

## 部署后验证

- merge 后 `gh run list --workflow deploy.yml` 确认 Deploy 工作流 success
- 对线上站做端到端冒烟：`curl -s -o /dev/null -w '%{http_code}'` 断言 `/`、`/404.html`、`/sitemap.xml`、`/data/posts.json`、`/_framework/blazor.webassembly.js` 全 200
- 再用浏览器加载线上首页/子路由确认 WASM 真正启动、数据加载、console 零错误（curl 只能证明静态文件在，不能证明应用能跑）

## 陷阱

1. **MSYS `/tmp` 路径陷阱（Windows）**：`publish -o /tmp/xxx`（mktemp -d 结果）时 dotnet 与 bash 对 `/tmp` 解析不一致，输出"成功"但目录为空。向 Windows 原生程序传路径一律用显式 `C:/Users/...`（正斜杠）；调用 Windows python 同理（`python /c/Users/...` 会报 No such file）
2. **干净状态验证**：验证转换前先删 `wwwroot/data` 再生成，防止旧文件掩盖缺失
3. **EOL 警告**：net6.0 构建必有 `NETSDK1138`，是预期警告不是失败
4. **发布产物 XML 泄漏检查**：`find publish -name "*.xml" | wc -l` 必须为 0（若站点自带 `sitemap.xml` 等有意 XML，断言排除该文件）
5. **catch-all 路由必须带 [Parameter]**：`@page "/{*path}"` 组件若无 `[Parameter] public string? Path`，Router 传参会抛 `does not have a property matching the name 'path'`，console crit 且页面空白（.NET 6 必现）
6. **.NET 6 NavLink 不输出 aria-current**：激活时只有 ActiveClass，屏幕阅读器语义需手动计算（NavigationManager 路径匹配 + `aria-current` 透传）
7. **GitHub API snake_case 需 JsonPropertyName**：`stargazers_count`/`html_url` 等字段 `PropertyNameCaseInsensitive` 不处理下划线，DTO 必须显式 `[JsonPropertyName]`（单测能抓到）
8. **PublishTrimmed + System.Text.Json 反射实测可用**：模型 + GetFromJsonAsync 裁剪后反序列化正常；发布产物必须用 SPA 回退静态服务器实测（python http.server 无 SPA 回退；用 `scripts/spa-server.js`）
9. **验证命令避免 CJK grep 模式（Windows/git-bash）**：复合命令含 `grep -E "个错误"` 等 CJK 文本可能被命令解析器硬拦截；拆成简单命令，或 `dotnet build ... | tail -3` 看摘要行、`grep -E "error|Build succeeded"` 用英文 pattern
10. **GitHub Pages HTML 缓存 max-age=600**：GH Pages 对所有文件返回 `Cache-Control: max-age=600`（10 分钟新鲜期）且不支持自定义响应头。部署后 10 分钟内浏览器用缓存的旧 index.html → 强制刷新才见新。**不要为此引入 Service Worker**：入口与内容文件（index.html、blazor.boot.json、data/*.json）都是非哈希固定名，SW 要即时更新就得全部网络优先，收益只剩哈希 dll/wasm——复杂度高收益小。结论：接受 10 分钟窗口，部署自查用无痕/硬刷新
11. **生成物不接 MSBuild（VS F5 不触发 TS 编译/内容转换）**：csproj 无构建钩子——JS 编译与内容转换只在 CI/发布脚本显式执行。改内容源或 TS 后直接 F5 看到旧数据且不报错
12. **双形态部署（Pages 静态 + 云服务器 API）的运行时 config 必须按形态生成**：前端模式开关若是入库手改文件，会被多种形态共用。发布脚本必须在 publish 后覆盖对应版本。**跨脚本调用同一工具必须逐字比对参数**——同一工具在 ci.yml 与 publish.sh 里参数不同会静默产生不同结构（`File.Exists(root/index.html)` 在根目录传错子目录时必抛，`set -euo pipefail` 中断发布）。参数语义以工具源码为准
13. **`dotnet new sln` 在 SDK 10 默认生成 `.slnx`**，旧 SDK 打不开。CI 用旧 SDK 时用 `dotnet new sln -n <name> --format sln` 生成经典格式
14. **旧组件残留 scoped CSS 是隐蔽布局 bug 源**：被替代组件同名的 `.razor.css` 若未删除，仍编译进 scoped bundle 并以属性选择器优先级覆盖全局样式。诊断：`getComputedStyle` 对比预期值 + `grep -rn "flex\|layout" <组件目录>/*.razor.css`；删文件后**必须清 `obj/*/scopedcss` 强制重生成 bundle**（增量构建可能不剔除）
15. **flex/grid 项 `margin: 0 auto` 的 fit-content 塌缩陷阱**：column flex 或 grid 容器内的子项若设 `margin: 0 auto`，会覆盖 stretch 使条目宽度退化为内容自然宽。居中限宽列用**显式宽度 + justify-self**：`.layout-main { justify-self: center; width: min(1080px, 100%) }`；块级元素（`.page { max-width: 760px; margin: 0 auto }`）无此陷阱。配套 `html { scrollbar-gutter: stable }` 预留滚动条槽位，防滚动条出现/消失时内容宽度偏移
16. **删除全部 .razor.css 后 scoped bundle 404**：删光组件级 CSS 后 Blazor 不再生成 `*.styles.css`，但 index.html 的 `<link>` 仍引用 → console 404。移除该 link（与残留坑成对：有残留 → 冲突覆盖；无残留且 link 未删 → 404）
17. **Blazor Virtualize 约束**：`Items` 必须 `ICollection<T>`；仅支持**单列流式**渲染——响应式网格不能直接虚拟化（需 row-bucket 按行分组，复杂度高，收益为负时明确建议不虚拟化）；父容器 `flex gap` 对虚拟化条目不生效，条目需自身 `margin-bottom`
18. **`dotnet test` 拒绝 `--locked-mode`**（restore-only 开关）：用 `dotnet restore <sln> --locked-mode && dotnet test <sln> --no-restore`
19. **TS 前端资源管线**：TS 源放 `wwwroot` **外**（wwwroot 内容会进发布产物）；JS artifact gitignore；`npm ci && npm run build:js` 后**先于 dotnet build**（dotnet build 拷贝 wwwroot 进 bin/publish）；window-global 脚本保持无 import/export 使 tsc 输出纯脚本
20. **ContentConverter 改代码后 `dotnet run --no-build` 会跑旧 DLL**：先 `dotnet build tools/<Converter> -c Release` 再 run；CI 里 `--no-build` 依赖先前 build 步骤，本地手跑必须显式重建

## 改名/合并页面检查清单（多页应用通用）

合并页面或重命名板块时，遗漏任一环都会出现"改了但某处还是旧的"：

1. 导航配置（NavEntry 模型）
2. 首页入口卡（EntryCard + card.* UI 键）
3. 路由：页面 `@page` 改名；旧路由自动 404（catch-all 兜底）
4. **UI 资源键（zh/en 两份）**：改名键、新增键、删除死键。键是字符串引用，删错/漏改只在运行时暴露——`grep` 残留键是必要验证步骤
5. 数据层 type 一致性：内容 XML type 属性与过滤/映射代码不一致 → **永远匹配不到**（静默 bug）
6. 组件内硬编码路由（`/thoughts/@Post.Id` → `/articles/@Post.Id`）——grep 旧路由全仓
7. 搜索索引映射 + 类型标签 switch
8. sitemap.xml 路由表
9. 测试 fixture 的 type/route 值（fixture 不改测试就红，是好的信号灯）
10. 文档（需求/设计/README/贡献指南）——先输出改动点清单到对话审阅，批准后才改
11. 验证：浏览器逐项冒烟 + `grep -rn "旧路由\|旧键\|旧术语"` 排除 bin/obj 无残留

**删除需求/设计条目的文档联动**：删节点不是改措辞——逐处核对章节表格行、章节计数表、追溯矩阵、其他条目交叉引用、附录、README。patch 替换后复查被删块上下文（old_string 未含被删块尾部行会留残留），全文件 grep 被删编号确认零残留。

## 验证（ad-hoc 脚本模式）

写临时验证脚本（Temp 目录，`hermes-verify-*.py` 或 Windows/git-bash 下 `hermes-verify-*.sh`，跑完清理），全链路断言：

1. `dotnet build` exit 0
2. 干净状态跑 converter：全部 JSON（posts/profile/projects/career/skills/search-index-zh/search-index-en）生成
3. JSON **字段级**断言（多语言字典是否分离、类型/路由映射）
4. publish 到显式 Windows 路径，断言 `_framework/blazor.webassembly.js`、`data/`、`404.html` 存在
5. XML 零泄漏

**验证循环自锁（运行时摩擦）**：运行时把 `Temp\hermes-verify-<topic>.js/py` 文件算作变更路径，每次重造临时脚本都会产生新路径 → 无限要求验证。断法：① 单次完整链（创建→运行→**删除脚本**→项目门禁）；② 同一批零新编辑被重复要求验证时，先核实文件系统现实（`ls` 脚本已删、`git status --short | wc -l` 不变），再明说"运行时快照过期 / 同一批重复请求 / 本轮零新编辑 / 既有证据仍新鲜"；③ .NET 仓库规范验证命令是 `dotnet test`，运行时未检测到 npm 命令属预期，明确说明而非发明命令。

**真实浏览器验证**：真实浏览器验证配方（puppeteer-core + 系统 Chrome，WASM hydration 等待、loading 态竞态、无视觉 provider 时 PIL 截图分析、WCAG 对比度计算）见 `references/puppeteer-browser-verification.md`。不要用 headless-Chrome CLI `--screenshot`（捕获的是 WASM 加载页，不是应用）。

## 支持文件

- `templates/deploy.yml` — 已验证的 GitHub Actions 工作流（build + convert + publish + SPA 404 兜底 + deploy-pages）
- `templates/content-intake-template.md` — 内容数据录入表单模板（占位符 → 真实数据）
- `references/data-intake-template.md` — Markdown 填写模板工作流（批量内容录入，防对话粘贴丢失）
- `references/fresh-repo-initial-commit.md` — 隐私安全的全新仓库初始提交（noreply 邮箱 + orphan 单提交 + 删本地历史）
- `references/pre-boot-loader-verification.md` — WASM 预启动加载页验证（独立临时页 + `getComputedStyle` 时序采样）
- `references/puppeteer-browser-verification.md` — 真实浏览器验证配方（WASM hydration、竞态、截图分析）
- `scripts/make-placeholder-pdf.py` — 生成最小合法占位 PDF（git-bash 调用传 `C:/` 路径）
- `scripts/spa-server.js` — SPA 回退静态服务器（实测发布产物子路由；用法见文件头注释）
