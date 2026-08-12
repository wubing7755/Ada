---
name: ada-blazor-debug-verification
description: "Use when debugging or verifying .NET 6 Blazor WASM work."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, dotnet6, debugging, verification, bunit, consumer-sample]
    related_skills: [ada-blazor-interop-pitfalls, ada-blazor-interaction-pitfalls, ada-dotnet-verification, ada-systematic-debugging]
---

# .NET 6 Blazor Debug & Verification

Class-level playbook for debugging runtime/DI/rendering behavior in .NET 6 Blazor WASM
and for verifying changes end-to-end (unit, bUnit, NuGet consumer sample). Complements
the user-owned `ada-blazor-interop-pitfalls` (JS interop patterns),
`ada-blazor-interaction-pitfalls` (lifecycle/rendering), and `ada-dotnet-verification`
(.NET gates) skills; this skill carries the debug/verify workflow lessons and the
verified framework facts discovered while applying them.

## Pitfall 1: Optional `[Inject]` is impossible in .NET 6

.NET 6's `ComponentFactory.CreateInitializer` (verified against aspnetcore v6.0.0 source)
throws `InvalidOperationException` for ANY `[Inject]` property whose service is not
registered — reference types and nullable annotations included. A plan/design that says
"`[Inject] T? Optional` — fall back when unregistered" will crash component instantiation
in real apps AND in bUnit, at `Renderer.InstantiateComponent`.

**Fix**: inject `IServiceProvider` (always resolvable) and resolve manually with a fallback:

```csharp
[Inject] private IServiceProvider ServiceProvider { get; set; } = null!;
// in OnParametersSetAsync:
effectiveScope ??= ServiceProvider.GetService(typeof(IMyScope)) as IMyScope ?? new DefaultScope();
```

Verify against the actual runtime source before designing around framework behavior —
fetch `aspnetcore/<version>/src/Components/Components/src/ComponentFactory.cs` rather than
trusting "nullable [Inject] must be fine".

## Pitfall 2: bUnit stale event handler after fire-and-forget re-render

An event handler that does `_ = InvokeAsync(StateHasChanged)` (or `InvokeAsync(async () =>
{ StateHasChanged(); ... })`) leaves a pending render. The test's next click on a
freshly-queried element can dispatch a handlerId that the pending render already replaced →
`UnknownEventHandlerIdException` ("There is no event handler with ID 'N' associated with
the 'onclick' event in the current render tree"). A `WaitForAssertion` whose condition was
ALREADY true before the render (e.g. reading a textarea value that `Change()` set directly
in the DOM) returns immediately and does NOT flush the pending render.

**Fix**: flush with `cut.Render()` before the next query+click, or wait for a condition
that only becomes true after the render applies. Re-issuing `FindAll` alone is not enough —
the race is between query and dispatch.

## Pitfall 3: KeepAliveWithinGroup cache accumulates, it does not pre-fill

The kept-alive outlet list fills as items become SELECTED; on the first render only the
selected item's outlet is mounted. To assert N kept-alive outlets in bUnit, first switch
selection N-1 times, then assert — mirror the existing ContentLifetimeTests pattern.
Expecting all items mounted from the initial render produces "found 1, expected 2".

## Pitfall 4: bUnit misses module invocations made from OnAfterRenderAsync

bUnit's `WaitForAssertion` pumps renders but does NOT reliably observe
`module.InvokeVoidAsync` calls issued from inside `OnAfterRenderAsync` — even with a 5s
timeout it can report "The collection was empty" while a DIAG print proves the invocation
ran. The loose JSRuntime records the call asynchronously; `WaitForAssertion`'s render pump
does not yield long enough for the recording to land.

**Fix**: `cut.Render()` (awaits the render INCLUDING `OnAfterRenderAsync`) followed by
`await Task.Yield()`, then assert `module.Invocations["fnName"]`. A plain `Task.Delay(100)`
also works but the yield is cleaner and deterministic. This pattern is required whenever the
behavior under test is a C#→JS callback triggered by a render (e.g. the split-preview-clear
ack after a resize commit), not by a direct awaited call.

Related: bUnit `JSRuntimeMode.Loose` also never validates that the invoked JS function
exists — a missing bundle export passes all bUnit tests and fails only in a real browser
("Could not find 'fn'"); guard with a Node test that imports the public-api surface (see
`ada-blazor-interop-pitfalls` → Public API Re-Export Trap).

## Pitfall 5: Keyboard activation on custom interactive divs (.NET 6 `preventDefault` limitation)

.NET 6's `@onkeydown:preventDefault` directive attribute can only bind a **bool constant or field** — it CANNOT be conditional on event args (`e.Key == " "`). Event-args-conditional `preventDefault` is a .NET 8+ capability. Verified against a real project's flip-card fix.

**Pitfall**: an interactive `<div tabindex="0" @onkeydown="OnFlipKeyDown">` that toggles on both Enter and Space causes a **double action** — Space's browser default is page scroll, so pressing Space flips the card AND scrolls the page (Blazor handler runs in addition to the default action; .NET 6 has no way to prevent just that key).

**Fix pattern**: Enter-only activation — leave Space for page scroll:
```csharp
private void OnFlipKeyDown(KeyboardEventArgs e)
{
    // .NET 6: cannot conditionally preventDefault on event args; Enter-only avoids scroll+flip double action
    if (e.Key == "Enter") { ToggleFlip(); }
}
```

## Pitfall 6: flip-card faces must keep symmetric tabindex (hidden face still in Tab order)

`backface-visibility: hidden` hides the inactive flip face **visually only** — its links remain in the DOM and in the Tab order. After flipping, the front-face link is invisible but still tab-focusable, while back-face buttons use `tabindex="-1"` until flipped. Asymmetric tabindex = keyboard users focus invisible elements.

**Fix pattern**: bind each face's focusability to the flip state symmetrically:
- Front-face links: `tabindex="@(_flipped ? "-1" : "0")"` (deactivate when hidden)
- Back-face buttons: `tabindex="@(_flipped ? "0" : "-1")"` (activate when visible)
- Inner links need `@onclick:stopPropagation="true" @onkeydown:stopPropagation="true"` so clicking/focusing them doesn't toggle the flip.
- Expose flip state to assistive tech (`aria-pressed` or `aria-expanded`) since both faces stay in the accessibility tree (SD-29) — SR users read all content but cannot tell which face is showing.

**Contract-test pattern**: this repo asserts razor source as embedded resources (csproj `EmbeddedResource` + `LogicalName`), so tabindex symmetry can be locked with `Assert.Contains("tabindex=\"@(_flipped ? \"-1\" : \"0\")\"", card)` and `Assert.DoesNotContain("\" \"", card)` (no Space literal).

## Pitfall 7: C# raw string literals (`"""`) unavailable in net6.0 test projects

`CS8652` fires for `"""..."""` blocks in net6.0 test projects even with `LangVersion=latest` — raw strings need C# 11 preview which the net6.0 toolchain does not enable. Write test fixture HTML/JSON as escaped normal strings joined with `\n`:

```csharp
// WRONG: CS8652 on net6.0
var html = """
    <img src="https://x/a.png" />
    """;

// RIGHT: escaped normal string
var html = "<img src=\"https://x/a.png\" />\n<img src=\"https://x/b.png\" />";
```

Same class as the .NET 6 `preventDefault` limitation (Pitfall 5): verify language-version capabilities against the actual TFM before writing test fixtures in modern syntax.

## Pitfall 8: ad-hoc verifier scripts on Windows — don't shell out to `grep` with Windows paths

A Python ad-hoc verification script that runs `subprocess.run(["grep", "-rl", pattern, r"C:\...\src"])` returns **0 matches** because grep interprets the backslash path segments as escapes. The script then reports FAIL for a behavior that is actually correct — a script defect, not a code defect.

**Fix**: walk directories with `os.walk` and read files in Python, or pass MSYS-style paths (`/c/Users/...`). When an ad-hoc script FAILs, first check whether the failure is in the script's own environment handling before treating it as a product finding; rerun after fixing the script, and label the rerun as corrected-script evidence.

## Pitfall 9: manual `DelegatingHandler` construction in WASM → "The inner handler has not been assigned"

`new HttpClient(myDelegatingHandler)` in Blazor WASM crashes at the FIRST request with
`System.InvalidOperationException: The inner handler has not been assigned`. Server-side
HttpClientFactory chains handlers automatically; manual construction does NOT set
`InnerHandler`. Verified in a real project's auth phase — the app booted,
rendered, then died inside `SendAsync` on the very first config fetch.

**Fix (preferred)**: skip the handler chain for auth-header injection entirely — have the
auth service write the shared (singleton) `HttpClient.DefaultRequestHeaders.Authorization`
directly. Singleton HttpClient in WASM is safe (browser fetch, no socket pool), the header
applies to every API request, and unit tests assert `http.DefaultRequestHeaders.Authorization`.
**Fix (if you must keep a handler)**: assign `InnerHandler = new WebAssemblyHttpMessageHandler()`
(the `Microsoft.AspNetCore.Components.WebAssembly.Http` type) before constructing the client.

## Pitfall 10: dual-mode frontend — relative `api/...` paths resolve to the FRONTEND origin

In a Blazor WASM site with a configurable API base (`config.api.json` mode switch), a
component that calls `Http.GetFromJsonAsync("api/posts/...")` requests the FRONTEND origin
(`/api/...` on the site itself) → 404/HTML → parse failure → "加载失败" in the UI. The
central content source used a `ResolveApiUrl()` helper correctly; the comment component
did not — and unit tests PASSED because their `HttpClient.BaseAddress` was `http://localhost/`.

**Fix pattern**: every API call in every component goes through ONE resolver
(`config.ResolveApiUrl("api/...")` — empty base → relative same-origin, else absolute).
This is browser-verification-only territory: lock it with a contract test that asserts
`Contains("Config.ResolveApiUrl")` in the component source, and verify the mode switch in a
real browser against a live backend (watch the backend's request log for the frontend's
`pageSize=100` calls — if absent, the frontend is still hitting itself).

**Recurrence record — the SAME bug hit the auth service in the same session**: after the
comment component was fixed, the login page still showed "用户名或密码错误" with correct
credentials. Root cause identical: `AuthService.LoginAsync/RegisterAsync/InitializeAsync`
used relative `"api/auth/..."` paths → requests hit the FRONTEND origin (5035 → 404; the
backend 5210 returned the correct 401). Unit tests could NOT catch it: the HTTP fake routes
on `PathAndQuery`, which is host-independent, so "wrong host" passes every test. Only a real
browser submit surfaced it.

**Escalated defenses**:
1. **Host-asserting regression test**: record `LastRequestUri` in the fake handler and add a
   test that configures an ABSOLUTE `apiBaseUrl` (`http://api.example.com`) and asserts the
   login request targets that host (`Assert.StartsWith("http://api.example.com", ...)`). A
   relative-path regression then fails deterministically.
2. **Auth flows must be browser-submitted, not just render-checked**: "login page renders"
   is not "login works". Submit real credentials in the browser and assert the auth-state
   transition (nav shows 退出 / logout button), plus check the backend request log.
3. Centralize the resolver rule: every service that touches the API (content source,
   comments, auth — and any future admin UI) goes through `AppConfigService.ResolveApiUrl`.

## Pitfall 11: `[SupplyParameterFromQuery]` is .NET 7+ — hand-parse query strings in net6.0

The attribute does not exist in .NET 6 (compile error). For `returnUrl`-style query
parameters in net6.0, parse `Navigation.ToAbsoluteUri(Navigation.Uri).Query` manually
(`Split('&')` → `Split('=', 2)` → `Uri.UnescapeDataString`), and validate the value starts
with `/` before navigating (open-redirect guard).

## Pitfall 12: contract/unit assertions must match what the component ACTUALLY does

Write assertions from the real implementation, not from what you assume the design does —
in a real dual-mode phase this misfired twice in one session:
- A comment-section contract test asserted the component calls `Auth.LoginAsync`; the
  component actually routes unauthenticated users to `/login?returnUrl=…` (no direct call).
- An `AppConfigService` test asserted `LoadFailed == false` for a malformed config, while
  the correct implementation sets `LoadFailed = true` (and still falls back to static mode).

Both were one-line assertion fixes after a failed test run — cheap to fix, but the pattern
costs a cycle every time. For contract tests that read razor source as embedded resources,
skim the actual component source before writing `Assert.Contains` strings; for service
tests, check the code path (especially `catch` branches) before pinning a flag value.

## Pitfall 13: browser automation — Blazor `@bind` needs a blur/change to update C# state

when driving a real Blazor WASM form through browser automation (type into `<input
@bind="_userName">`, then click submit), the button can stay `disabled` even though the
fields show text. `@bind` updates the C# field on the `change` event, which fires on
blur/Enter — typing alone does NOT flush the bound value (verified in the real
project's login page: button stayed disabled until Tab was pressed).

**Fix**: after `browser_type`, press Tab (or click another element) to blur the input and
fire `change`, THEN re-snapshot — the disabled attribute clears and the submit click works.

Related: this is why form submission must be verified end-to-end (fill → blur → submit →
assert auth-state transition), not just "the form renders".

## Pattern: static Blazor WASM site → static/API dual-mode + auth

Add an API mode to a previously-static GitHub Pages Blazor WASM site without touching every
page:

1. **Mode switch**: `wwwroot/config.api.json` `{"mode":"static"|"api","apiBaseUrl":""}`;
   load at startup, ANY load failure silently falls back to static (Pages demo stays green).
2. **Data-source abstraction**: `IContentSource` (posts list + detail) with
   `StaticContentSource` (old logic) / `ApiContentSource` (HTTP + DTO mapping); the page-facing
   `ContentService` keeps its old public methods and delegates posts internally — pages and
   contract tests are untouched. API list endpoints return summaries (no body) and require
   `postType`; fetch detail per-slug for body, and page-loop merging keeps list semantics.
3. **Auth**: token in localStorage (reuse an existing storage wrapper),
   `DefaultRequestHeaders.Authorization` injection (Pitfall 9), `GET /api/auth/me` session
   restore with silent clear on 401. No refresh token — expired = re-login.
4. **"本人可删" comments**: backend `CommentDto` gained `IsMine` (computed from
   `ClaimsPrincipal`); existing integration tests used `JsonElement` assertions so adding a
   field broke nothing — check assertion style before extending DTOs.
5. **Dev verification gotcha**: after editing `wwwroot/config.api.json` under a RUNNING dev
   server, browser fetches can keep serving the cached/old config (curl sees the new file,
   the app still runs static mode). Restart the frontend dev server before verifying a mode
   switch; confirm via the backend request log, not the UI alone.
6. **收尾 before commit/PR**: browser-testing the API mode leaves `config.api.json` in
   `{"mode":"api",...}` — restore it to the static default (`{"mode":"static","apiBaseUrl":""}`)
   before committing, or the GitHub Pages demo build silently ships in API mode. Verify the
   restored file with a targeted ad-hoc check (JSON valid, mode=static, dev server serves
   the same content), not the test suite — the suite never reads this runtime config file.

Test-double traps for the HTTP-fake based service tests (OnJson overload, PathAndQuery
routing, pagination simulation): `references/http-fake-handler-design.md`.

Blazor `@onclick` fires through document-level event delegation (lookup by a
`blazor:onclick` attribute) — a button with missing/stale data attributes still CLICKS.
A JS-side `pointerdown` drag recognizer does NOT use delegation: it walks
`target.closest("[data-drag-kind]")` and reads `data-command-capabilities`
(canMove bit test) plus `data-item-id` from the element. If the drag metadata is absent,
or the element is not in the DOM, clicking works but dragging does nothing (no preview,
no drop highlight) while a sibling element drags fine.

Diagnostic probes (DevTools console):
```js
document.querySelectorAll('[data-toolbar-entry]').forEach(e => console.log(e.outerHTML))
document.querySelectorAll('[data-drag-kind]').forEach(e => console.log(e.dataset.itemId, e.dataset.dragKind))
document.querySelector('.workspace')?.dataset.reducedMotion // 'system'=detached, 'false'/'true'=attached
```
`entry: undefined` while a button is visibly rendered ⇒ the element's attributes are
broken or the real DOM diverges from the render output.

## Pattern: NuGet consumer sample pinned-version dev loop

When a consumer sample pins a package version (central package management,
`<PackageVersion Include="X" Version="0.1.0" />`) and `dotnet pack` defaults to another
version (`0.0.0-dev`), the sample silently resolves the RELEASED package from nuget.org
and ignores local source. To verify against local source:

1. Pack at the pinned version into the gitignored local feed:
   `dotnet pack src/...csproj -c Release -o artifacts/packages -p:PackageVersion=0.1.0`
2. Clear ONLY the consumer's isolated cache (its NuGet.Config sets a repo-local
   `globalPackagesFolder`, e.g. `.packages`) — never the global NuGet cache.
3. Restore the sample with its NuGet.Config; the local feed wins equal versions when
   listed first.
4. Verify the resolved package is local before trusting results:
   `cat .packages/<pkg>/<ver>/.nupkg.metadata` → `source` must be the local feed path.

Consumer test projects often reference the app assembly by `<HintPath>` (not
ProjectReference) — `dotnet test tests/...Tests` builds only the test project and runs
against a STALE app DLL. Invoke the solution-level test (`dotnet test App.sln`) so the app
project rebuilds first.

## Verification ladder

- Focused RED/GREEN: filter to the new test class/method.
- Phase gate: `dotnet test <Solution>.sln` (no `--no-build` on this repo's net6.0 toolchain), then `dotnet format ... --verify-no-changes`.
- Consumer: `cd samples/<Sample> && dotnet test <Sample>.sln` (rebuilds the app via HintPath), plus format.
- Label evidence by tier — a filtered run is not a full-suite pass.

## Pattern: verifying a JS-preview / Blazor-commit handshake (deterministic ack)

When JS renders a transient preview (splitter drag position) and Blazor commits the real
state asynchronously, pointerup must NOT clear the preview synchronously — the DOM falls
back to the old state until the commit's render lands, producing a visible "bounce".
JS-side fixes (rAF polling + frame cap, MutationObserver + timeout) are heuristics that
cannot handle the rejected-commit case (no render ever comes; only C# knows the outcome).

The deterministic pattern to verify:
1. pointerup keeps the preview and sends the commit;
2. C# branches on `ExecuteAsync`'s result — applied: queue the id and drain in
   `OnAfterRenderAsync` (clear is then a no-op safety net); rejected: invoke a
   C#→JS clear immediately;
3. JS clear skips a split currently being dragged.

Two traps that make naive tests/implementations pass locally but break in the browser or
flake in bUnit:
- **Queue BEFORE `await ExecuteAsync`**: the `Changed` event fires inside `ExecuteAsync`
  and schedules the render; a dispatcher can process it while the await is in flight, so a
  post-await add misses the drain. This is a deterministic failure in bUnit (see the
  `Applied_resize_commit_confirms_preview_clear_after_render` test pattern) and rare in the
  browser — always order the bookkeeping before the await.
- **The C#→JS function must exist in the bundle** (see Public API Re-Export Trap).

## References

- `references/http-fake-handler-design.md` — traps when writing HttpClient fakes for
  Blazor WASM service tests: OnJson(object) serializing raw responses, PathAndQuery
  routing, pagination fixture sizing, type-discriminator fields, cache-count assertions.
