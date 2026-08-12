---
name: ada-blazor-wasm-api-integration
description: "Use when Blazor WASM calls backend API: auth, URL, verify."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, wasm, dotnet6, api, integration, pitfalls]
    related_skills: [ada-blazor-interaction-pitfalls, ada-dotnet-verification]
    trigger_keywords: ['Blazor WASM API', 'apiBaseUrl', 'Authorization', 'DelegatingHandler', 'login', 'CORS', 'dev server cache', 'relative path api']
---

# Blazor WASM ↔ Backend API Integration Pitfalls

## Overview

A catalog of failures when a Blazor WASM frontend (net6.0) talks to a separate ASP.NET Core API backend. All pitfalls here were caught in a real browser or by real users; several were missed by unit/contract tests until an actual interaction was performed. The unifying discipline: **every cross-backend request must go through one URL-resolving service, and browser verification must actually execute the critical path.**

## When to Use

Use when:
- Adding auth (login/register/me, JWT) or CRUD calls from Blazor WASM to a backend API
- The site runs in two modes: static JSON (GitHub Pages demo) and API mode (cloud server), switched by a runtime config file
- The mode config file is committed and shared across deployment forms (local dev / GitHub Pages / cloud server) — each form needs a different value, and hand-editing it breaks one of the forms (Pitfall 3b)
- Debugging "comment load failed", "username or password error" on a valid credential, or startup crash right after wiring HttpClient
- Writing net6.0 tests for frontend services that call a backend

## Pitfall 1: Manual `DelegatingHandler` Crashes WASM at Startup

**Symptom**: app never renders — browser error page; console shows
`System.AggregateException: ... The inner handler has not been assigned` with a stack through your `DelegatingHandler.SendAsync`.

**Root cause**: `new HttpClient(handler)` where `handler` is a `DelegatingHandler`. Server-side `HttpClientFactory.AddHttpMessageHandler` chains `InnerHandler` automatically; WASM manual construction does not. The handler's `base.SendAsync` throws because `InnerHandler` is null.

**Fix**: don't hand-roll an auth handler chain. Have the auth service manage the shared HttpClient's `DefaultRequestHeaders` directly (singleton HttpClient; header applies to all API calls, public endpoints ignore it):

```csharp
private void ApplyToken(string? token)
{
    _http.DefaultRequestHeaders.Authorization = string.IsNullOrEmpty(token)
        ? null
        : new AuthenticationHeaderValue("Bearer", token);
}
```

## Pitfall 2: Relative API Paths Resolve to the Frontend Itself

**Symptom**: API mode works for content but a specific call fails — comments "加载失败", login always "用户名或密码错误" even with valid credentials. Backend log shows **no request** arriving (or the frontend dev server logs 404 for `/api/...`).

**Root cause**: `HttpClient.BaseAddress` is the frontend origin (e.g. `http://localhost:5035`). A relative path `api/posts/...` resolves to the **frontend**, which has no such endpoint. This bug recurred twice in one project (comment list, then auth login) — the second time only caught because a user actually tried to log in.

**Fix**: all cross-backend requests go through one resolver:

```csharp
// apiBaseUrl empty → return relative path (same-origin Nginx proxy);
// otherwise prefix the absolute backend URL.
_config.ResolveApiUrl($"api/posts/{slug}/comments")
```

**Regression test**: a FakeHandler that matches routes by `PathAndQuery` (no host) will pass even when the request hits the wrong host. Record `request.RequestUri` on the handler and assert the host prefix:

```csharp
Assert.StartsWith("http://api.example.com", handler.LastRequestUri!.GetLeftPart(UriPartial.Path), StringComparison.Ordinal);
```

## Pitfall 3: Dev Server ETag-Caches wwwroot Config

**Symptom**: you edit `wwwroot/config.api.json` to switch mode, restart nothing, reload the browser — behavior unchanged (frontend still reads the old config; backend log silent).

**Root cause**: ASP.NET Core dev server serves wwwroot static files with ETag; the browser reuses the cached response for the same URL.

**Fix**: after changing a wwwroot runtime config, restart the dev server (or hit the URL with a cache-busting query to confirm the served content). Production Nginx reads the file directly — no issue. Verify what the browser actually receives, not what curl sees.

## Pitfall 3b: Mode-Switch Config Is a Committed File Shared Across Deployment Forms — Never Hand-Edit

**Symptom**: local API-feature debugging requires hand-editing `wwwroot/config.api.json` to api mode; the edit can't be committed (it would flip the GitHub Pages deploy to api mode and break the static demo); the cloud-server publish script, if it doesn't explicitly generate the api version, leaves the server frontend running static data — the backend API is dead weight.

**Root cause**: one committed, hand-edited file is shared by three deployment forms that need different values:

| form | value |
|---|---|
| GitHub Pages / local pure-frontend | `{"mode":"static"}` (safe default) |
| cloud server main site | `{"mode":"api","apiBaseUrl":""}` — empty = same-origin, nginx proxies `/api/` |
| local API-feature debugging | `{"mode":"api","apiBaseUrl":"http://localhost:5210"}` |

Key fact: **pure frontend debugging (static default) does NOT need the backend running**. Only login/comments/admin features need frontend+backend up together plus api mode. The sln has no multi-startup-project config (stored in `.suo`, not committed); VS users set "Multiple startup projects" once.

**Fix (engineering)**: make the config a **build-time artifact generated per form** — each deploy path explicitly writes it to the publish output, the repo keeps only the static default: Pages workflow generates static; the cloud publish script overwrites to api same-origin after `dotnet publish`; local scripts write the **bin output directory** (`bin/Debug/<tfm>/wwwroot/config.api.json`) — note `dotnet build` copies wwwroot from source and overwrites it, so the order must be build → generate → start. The repo file is never hand-edited, git status stays clean. Add a CI assertion that the Pages artifact config is static, to prevent a future accidental api-mode commit.

### 形态决策：引流站 API 优先 vs 纯静态快照（真实项目用户确认）

用户方向：**云服务器为主站（内容主源 = DB），GitHub Pages 仅为引流**。引流站三形态：
A 纯壳+API（API 挂则白屏） / **B 混合（选定）：API 优先 + 构建期 JSON 降级** / C 纯静态快照。
B vs C 的核心差异在**谁承担内容一致责任**：C 的双内容源（DB + XML 快照）一致性是每天的
认知税——每次内容变更必须记得一键同步，忘同步 = 引流站静默陈旧（不报错）；B 让主站 API 与
引流站 API 同读 DB，改完即所见，一键同步退化为"刷 SEO + 降级快照"（忘了不影响内容可见性）。
B 的代价是前期一次性投入：fallback 代码/测试面、CORS 白名单、读端点限速；演进向上兼容
（未来可删 fallback 简化构建）。

设计时省事的三个已核实事实（本仓库）：
1. **API 模式只覆盖 posts**——`IContentSource`（GetPostsAsync/GetPostByIdAsync）是唯一
   切换点，profile/projects/career/skills/search 永远读构建期 JSON（后端无端点）→ fallback
   只需包 posts，面很小
2. **index.html 无 CSP meta**——Pages 无 nginx/自定义响应头，跨域调主站 API 不受 CSP 阻碍，
   只需 CORS 白名单加 Pages 域名（生产经环境变量注入，不入库）
3. **Admin 一键同步已存在**（`POST /api/admin/sync/github` + Dashboard sync 面板 +
   GitHubSyncService 导出 DB→content/posts.xml + 增量传媒体 → push main 触发 deploy.yml）——
   B 形态下不新增功能，**职责重定义为降级快照 + SEO 刷新**

Fallback 实现：`FallbackContentSource : IContentSource` 装饰器包 Api + Static，先 API、
捕获 `ContentLoadException` 降级静态；**熔断**：API 连续失败 2 次 → 本会话切静态（避免每请求
等超时），成功一次即恢复。config.api.json 加可选 `fallbackStatic`（默认 true）；api 模式 +
fallbackStatic 时 DI 注册 Fallback，否则裸 ApiContentSource（本地调试 API 可设 false 看真实错误）。
配套：读端点限速（RateLimiter 现有策略只有 Login/Register/Comment/Media，GET /api/posts 无限速）；
内容维护习惯从"改 content/*.xml 提交"迁移到 **Admin 后台写内容**（主站 API 只认 DB），
XML 退化为 SEO/降级数据源；本地一键 scripts/dev.ps1（build → 写 bin 输出目录 api-local config
→ 同起 API+前端），纯前端调试仍不需要后端（static）。

## Pitfall 4: Browser Automation Must Blur Inputs to Trigger `@bind`

**Symptom**: you type into a Blazor input via browser automation, but the submit button stays disabled and nothing happens.

**Root cause**: `@bind` updates the C# field on the `change` event (blur), not on every keystroke. Typed text alone doesn't commit the value.

**Fix**: after `type`, send Tab (or click elsewhere) to blur the field, then re-snapshot and click submit.

## Pitfall 5: Render Smoke Is Not Proof of the Interaction Path

**Symptom**: browser verification "passed" (pages render, console clean) yet a real user hits a functional failure on login/comment/submit.

**Root cause**: rendering a form proves the component renders, not that submitting it calls the right endpoint with the right headers. Pitfall 2's auth bug survived exactly this way.

**Fix**: browser verification must **perform** the critical-path operation — submit the form, delete the item, change the mode — and assert the backend log received the request (plus expected status). Console-clean rendering is smoke, not interaction evidence.

## Pitfall 6: net6.0 Tests Cannot Use C# 11 Raw String Literals

**Symptom**: `CS8652: raw string literals are not available...` when building tests under SDK 6.0.x.

**Root cause**: SDK 6.0.x ships the C# 10 compiler; `"""..."""` and `$"""..."""` are C# 11. `LangVersion=latest` resolves to C# 10 under net6.0.

**Fix**: write test JSON as escaped interpolated strings:

```csharp
private static string SummaryJson(string slug) =>
    $"{{\"slug\":\"{slug}\",\"postType\":\"article\"}}";
```

## Pitfall 7: Session-Scoped Content Caches Go Stale After Admin Writes (drop, don't invalidate)

**Symptom**: user edits a post in Admin; save succeeds (re-opening the editor
shows the new content because the admin write path calls the API directly),
but the PUBLIC page still shows the old body and old summary until a hard
refresh (Ctrl+F5).

**Root cause**: `AddScoped` in Blazor WASM is effectively a SINGLETON for the
whole browser session. Any content source registered scoped that caches
backend responses (`_allPosts`, per-slug `_detailCache`, etc.) serves stale
data for the rest of the session after a write happens through a different
path. Backend is NOT stale (verify with hard refresh; backend response
caching/ETag is usually absent). This is a UX trap users report as "edit
didn't save".

**Fix (decision framework, verified in a real project)**:
Do NOT add `InvalidateCache()` calls to every admin write — that couples
write and read paths, pollutes the interface for sources that can't change
(static mode), and every FUTURE write operation that forgets to invalidate
re-introduces the same bug. The decisive question is the multi-user view:
**a WASM session cache can never be shared across clients, so once more than
one writer exists it has zero performance benefit and only consistency
cost.** Therefore:
- If the data can change through the backend, DON'T cache it in the session —
  read the backend every call (it is the single source of truth; a small
  list + detail fetch per navigation is fine, and the API read rate limit
  is usually generous, e.g. 120/min per IP).
- Static/immutable sources (data files that only change at deploy time) may
  keep their cache — there is no write path to invalidate.
- If real traffic ever demands caching, put it at the BACKEND
  (ETag/Last-Modified/response cache): shared across clients and
  invalidated by data change, not by a manual call site.
- TDD the no-cache contract: assert the fake handler's request count
  INCREASES on a second `GetPostsAsync`/`GetPostByIdAsync` call — the old
  "second call makes no request" test is the regression you are removing.

## Pitfall 8: Derived fallback field shadows the hand-written field (cache fix alone doesn't fix it)

**Symptom**: after the cache fix, editing the post BODY shows up on the public
page, but editing the SUMMARY/intro still appears to do nothing.

**Root cause**: two fields exist for the same display slot — a hand-authored
intro (`SummaryZh` → `Post.Intros`) and a derived excerpt (backend
`BodyExcerpt`, auto-extracted from the markdown). A list item component that
renders `if (!string.IsNullOrEmpty(Excerpt)) show Excerpt else show Intro`
will ALWAYS show the derived excerpt (non-empty for any post with a body), so
the hand-written intro is never displayed. Editing the intro "saves" (admin
path + DB + DTO all correct) but the UI never shows it — indistinguishable
from a cache bug at first glance.

**Fix (verified in a real project)**:
invert precedence — hand-written intent wins, derived field is the fallback;
make the decision a `public static` pure function so it is unit-testable
WITHOUT bUnit (repo may forbid new test frameworks):
```razor
@if (!string.IsNullOrEmpty(DisplayIntro)) { <p class="post-intro">@DisplayIntro</p> }
...
public static string SelectIntro(string? intro, string? excerpt)
    => !string.IsNullOrWhiteSpace(intro) ? intro.Trim() : (excerpt ?? "");
```
Rules:
- List cards: intro-first, excerpt-fallback. A detail page may still use
  intro only when there is no local body (a different semantic — keep it).
- When diagnosing "edit didn't show": FIRST check session cache (Pitfall 7),
  THEN check display precedence (Pitfall 8) — the two bugs share a symptom
  and were found back-to-back here.
- Full detail: `references/display-precedence-shadowing.md`.

## Verification Checklist

- [ ] Every cross-backend call goes through the URL resolver (grep the service for raw `"api/` string literals)
- [ ] Regression test asserts the request host, not just the path
- [ ] Browser test performed the actual operation (submit/delete/login) and backend log confirms the request
- [ ] After changing a wwwroot runtime config, dev server restarted and served content verified
- [ ] `dotnet test` green; ad-hoc verifier script (if used) cleaned up from temp
- [ ] Mutable content sources have NO session cache (or admin writes invalidate it); test asserts request count increases on re-read

## Reference Files

- `references/display-precedence-shadowing.md` — display-precedence bug (Pitfall 8): derived excerpt shadows a hand-written field in list cards; symptom, debug ladder, pure-function fix, test cases
