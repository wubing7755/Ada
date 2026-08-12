---
name: ada-blazor-wasm-runtime-pitfalls
description: "Use for Blazor WASM runtime state, query navigation, interop, fragments, metadata, and section fault isolation."
version: 1.3.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, wasm, interop, navigation, headcontent, pitfalls]
    related_skills: [ada-blazor-interaction-pitfalls, ada-blazor-interop-pitfalls, ada-blazor-wasm-github-pages]
---

# Blazor WASM Runtime Pitfalls

Verified pitfalls from a production Blazor WASM static-site project (no SSR, GitHub Pages). Each entry: symptom, root cause, verified fix.

## Pitfall 1: JS interop silently no-ops on first render

**Symptom**: `OnAfterRenderAsync(firstRender)` calls JS (`JS.InvokeAsync`/`InvokeVoidAsync`) that should scroll/focus/measure, but nothing happens — no exception, no console error. Later manual invocation of the same JS works.

**Root cause**: On WASM startup, the *first* component render's `OnAfterRenderAsync` can fire before JS interop is reliably ready; the call silently no-ops. A component that only acts on `firstRender` never retries.

**Fix**: gate on data-ready, not `firstRender`:
```csharp
private bool _dataLoaded;   // set true at end of OnInitializedAsync
private bool _fragmentHandled;
protected override async Task OnAfterRenderAsync(bool firstRender)
{
    if (!_dataLoaded || _fragmentHandled) return;   // data-loaded gate + one-shot flag
    _fragmentHandled = true;
    var hash = await JS.InvokeAsync<string>("app.scroll.currentHash");
    ...
}
```
`OnAfterRenderAsync` re-fires on every render; the data-loaded gate moves the interop call to a later render when interop is ready. (Batch 9 fix.)

## Pitfall 2: `NavigationManager.Uri.Fragment` unreliable on direct initial load

**Symptom**: Directly loading `/page#section` (fresh navigation, e.g. `/#latest`, `/projects#project-002`) does not scroll; SPA navigation to the same URL does. `Navigation.Uri.Fragment` reads empty on initial load.

**Root cause**: Blazor WASM initialization can drop the URL fragment; only SPA (client-side) navigation preserves it.

**Fix**: read the fragment from the browser via a tiny JS helper instead of `NavigationManager`:
```js
// storage.js
window.app.scroll = {
    currentHash: function () { return window.location.hash || ''; },
    toFragment: function (id) {
        var el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: 'auto', block: 'start' });
    }
};
```
```csharp
var hash = await JS.InvokeAsync<string>("app.scroll.currentHash");
var id = hash.TrimStart('#');
if (targetExists) await JS.InvokeVoidAsync("app.scroll.toFragment", id);
```
Combined with Pitfall 1's data-ready gate this works for both direct load and SPA navigation. (Batch 9 fix.)

## Pitfall 3: static `<head>` metadata wins over runtime `HeadContent`

**Symptom**: Adding `<link rel="canonical" href=".../">` statically in `index.html` (intended for the homepage) plus per-page canonical via Razor `HeadContent` results in **every** SPA page carrying the homepage canonical first; `document.querySelector('link[rel=canonical]')` returns the static one.

**Root cause**: `HeadContent` appends to `<head>`; static tags from `index.html` persist across SPA navigation and precede runtime-injected ones.

**Fix**: do NOT put route-specific metadata (canonical) statically in `index.html`. Inject all per-route canonical/meta via `HeadContent` (homepage included). Keep only language-neutral static tags in `index.html` (OG/Twitter/JSON-LD for the homepage preview are fine — they are same across routes, and OG preview reads raw HTML before WASM runs). (Batch 11 fix.)

## Pitfall 4: V4A patch injects LF into CRLF Razor files

**Symptom**: After a `patch(mode='patch')` multi-hunk edit on a CRLF `.razor` file, `git diff` shows mixed line endings (new lines LF, rest CRLF) — noisy diff.

**Fix**: prefer `replace`-mode patches (they preserve CRLF). If V4A was used, normalize the file back to CRLF afterwards:
```python
data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
```

## Pitfall 5: one-shot scroll flag blocks same-route fragment re-scroll

**Symptom**: `_fragmentHandled` makes the first anchor scroll work (`/#skills`), but changing the hash on the same route (`/#skills` → `/#latest`, e.g. `window.location.hash = '...'` or an in-page anchor) never scrolls again — the one-shot flag stays true.

**Fix**: subscribe `NavigationManager.LocationChanged` and reset the flag on every navigation (Blazor fires it for same-route hash changes too):
```csharp
protected override void OnInitialized()
{
    base.OnInitialized();                      // preserve LocalizableComponentBase language subscription
    Navigation.LocationChanged += OnLocationChanged;
}

public override void Dispose()
{
    base.Dispose();                            // LocalizableComponentBase.Dispose is virtual
    Navigation.LocationChanged -= OnLocationChanged;
}

private void OnLocationChanged(object? sender, LocationChangedEventArgs e)
{
    _fragmentHandled = false;
    InvokeAsync(StateHasChanged);
}
```

**Lifecycle rule**: if the base class (`LocalizableComponentBase`) subscribes in `OnInitialized` and unsubscribes in `Dispose`, an overriding component MUST call `base.OnInitialized()` and `base.Dispose()` or the language-change re-render silently stops (and the event subscription leaks). (B-group fix.)

## Pitfall 6: marking a fragment handled before interop succeeds

**Symptom**: fragment scrolling fails once during startup or a transient render, but every later render skips it because `_fragmentHandled` was set before reading the hash or calling `scrollIntoView`.

**Fix**: make the interop boundary return whether the attempt completed, and assign the flag from that result:

```csharp
_fragmentHandled = await FragmentScroller.TryScrollCurrentAsync(
    JS,
    id => id is "skills" or "latest");
```

The helper returns `true` for an empty hash, an intentionally unsupported target, or a successful scroll. It returns `false` for recoverable interop failures (`JSException`, temporarily invalid render state), preserving eligibility on a later render. If the component must force an immediate retry, schedule a bounded re-render; never create an unbounded `StateHasChanged` loop while interop is unavailable.

## Pitfall 7: query-only navigation leaves a reused component stale

**Symptom**: `/search?q=first` works on initial load, but changing only the query string leaves the input or results stale. Reading `Navigation.Uri` in `OnInitializedAsync` cannot fix this because Blazor reuses the routable component instance.

**Fix**: two options, prefer the manual one — `[SupplyParameterFromQuery]` was observed UNRELIABLE in .NET 6 WASM (a routable component sometimes never binds it on initial load, even when another component in the same app binds it fine; Search worked, Archive did not, same pattern):

```csharp
// Option A (robust, verified): parse Navigation.Uri + subscribe LocationChanged.
// Router does NOT fire OnParametersSetAsync for same-route query-only navigation,
// so the LocationChanged subscription is mandatory for in-page type switches.
@inject NavigationManager Navigation

protected override void OnInitialized()
{
    base.OnInitialized();
    Navigation.LocationChanged += OnLocationChanged;   // handles ?type= changes
}

public override void Dispose()
{
    base.Dispose();
    Navigation.LocationChanged -= OnLocationChanged;
}

protected override async Task OnParametersSetAsync() => await ReloadAsync();

private void OnLocationChanged(object? sender, LocationChangedEventArgs e)
    => _ = ReloadAsync();

private async Task ReloadAsync()
{
    _type = ParseType(Navigation.Uri);
    ...await load + filter...
    await InvokeAsync(StateHasChanged);
}

private static string? ParseType(string uri)
{
    if (!Uri.TryCreate(uri, UriKind.Absolute, out var parsed)) return null;
    var pairs = parsed.Query.TrimStart('?').Split('&', StringSplitOptions.RemoveEmptyEntries);
    foreach (var pair in pairs)
    {
        var parts = pair.Split('=', 2);
        if (parts.Length == 2 && string.Equals(parts[0], "type", StringComparison.OrdinalIgnoreCase))
            return Uri.UnescapeDataString(parts[1]);
    }
    return null;
}
```

```csharp
// Option B (works when it binds): [SupplyParameterFromQuery] + parameter lifecycle.
[Parameter]
[SupplyParameterFromQuery(Name = "q")]
public string? Query { get; set; }

protected override async Task OnParametersSetAsync()
{
    var query = Query ?? "";
    if (query == _appliedQuery) return;
    _appliedQuery = query;
    _keyword = query;
    await RunSearchAsync();
}
```

Let the input event update the URL; let `OnParametersSetAsync` own the search. Guard result commits with a monotonically increasing request version so an older request cannot overwrite a newer result. Invalidating the gate when the query becomes blank prevents an in-flight request from repopulating cleared results. Ignore an old exception only after proving its request version is stale; current-request exceptions must still surface.

## Pitfall 8: one content request blanks an entire page

**Symptom**: profile, projects, skills, and posts are loaded by sequential assignments in one `OnInitializedAsync`; one HTTP/JSON failure aborts the method and every later section disappears.

**Fix**: place a recoverable fault boundary around each independent source and return an empty value for only that section. Keep expected content failures narrow (`HttpRequestException`, `JsonException`, unsupported serialization, invalid empty content, timeout) so programming errors still surface.

Do not automatically use `Task.WhenAll`: first inspect the service cache. A plain `Dictionary` cache is unsafe for concurrent writes, so sequential-but-independent loads can be the correct minimal fix.

See `references/spa-state-and-fault-isolation.md` for testable request-gate, query lifecycle, and failure-injection patterns.

## Pitfall 9: offline content data makes sort/count features look broken

**Symptom**: user reports "star sort does nothing", "view-count sort has no effect", "stars missing". The Razor/C# sort logic is correct and unit-tested.

**Root cause**: the site's data is build-time enhanced by the content converter — external view counts and GitHub star counts are fetched during conversion. Local verification with enrichment disabled (or without a token) produces all-zero values: stars never render (gate `Stars > 0`), and sorting by stars/views is a no-op over identical values. This is NOT a UI bug.

**Debug path**: inspect generated `wwwroot/data/posts.json` / `projects.json`; all zeros ⇒ enrichment was skipped. Re-run conversion WITHOUT offline mode and WITH a token to confirm real data (external view counts are usually anonymous-fetchable; GitHub needs a token, and brand-new repos legitimately have 0 stars).

**Fixes that work**:
- Local/dev parity: make the GitHub enricher attempt the anonymous API when no token is present (rate limit 60/hr is fine for one owner) instead of skipping.
- UI perception: render star counts unconditionally (including `★ 0`) so the field and sort basis are visible even when values are zero.
- Never conclude "sort button broken" from an offline-generated dataset; check the JSON first.

## Pitfall 10: fragment-only anchors (`href="#..."`) navigate to the site root

**Symptom**: footer "back to top" (`<a href="#main-content">`) and the skip-link, clicked on any page except the homepage, take the user to the *homepage top* — not the current page's `#main-content`. Live-browser evidence on `/projects`: URL becomes `/#main-content`, `scrollY=0`.

**Root cause**: Blazor WASM intercepts every `<a>` click for SPA navigation and resolves relative links against `<base href="/">` — the site root, NOT the current page URL. `#main-content` → absolute `https://site/#main-content` → path `/` (homepage); Blazor then scrolls to the homepage's `main-content`. Applies to ANY fragment-only anchor: back-to-top, skip-link, in-page jump links.

**Fix**: page-internal actions are not navigation — don't use fragment anchors at all. Scroll via JS interop:
```js
// storage.js
window.app.scroll.toTop = function () {
    var reduce = false;
    try { reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { }
    window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
};
```
```razor
<button type="button" class="footer-back-to-top" @onclick="ScrollToTop">@Language.T("footer.backToTop")</button>
@code {
    private async Task ScrollToTop()
        => await JsInteropRetry.TryInvokeAsync(() => Js.InvokeVoidAsync("app.scroll.toTop"));
}
```
- Prefer `<button type="button">` (zero navigation semantics) over `<a @onclick:preventDefault>` for pure scroll actions — no dependency on Blazor's interceptor honoring preventDefault, no race. Reset button default styles (background/border/padding/font) to match the link look, keep the visible focus ring.
- The skip-link must keep `<a>` semantics, but handle the click with JS: `scrollIntoView` + `main.focus()` (`main` has `tabindex="-1"`, so focus matches native fragment behavior) instead of `href="#main-content"`.
- Respect `prefers-reduced-motion` in smooth-scroll helpers (project a11y baseline; existing `toFragment` uses `behavior:'auto'` — be consistent per action).
- Regression guard: contract test asserting the component no longer contains `href="#main-content"` (InformationArchitectureContractTests pattern reads the .razor as embedded resource).

## CSS contract tests must respect cascade scope

When an embedded CSS contract validates a base selector that is also redefined inside `@media`, do not aggregate every matching rule from the entire stylesheet. A correct mobile declaration can otherwise hide a broken desktop declaration.

- Extract a brace-balanced root scope with all `@media` blocks removed before asserting base declarations.
- Extract and assert each media-query scope separately.
- Aggregate repeated selectors only within the same cascade scope.
- Prove the guard with an exact selector-scoped mutation: first show the normal rule passes, then change the intended base selector (for example `height:auto; aspect-ratio:16/9` to `height:540px; aspect-ratio:4/3`) and require that specific test to fail.
- Assert the mutation matched exactly once. A broad first-occurrence replacement can mutate an unrelated rule and produce a false conclusion about test strength.
- If a browser-verification harness later fails because of a wrong DOM selector or mutation target, treat the whole run as failed, correct the harness from the actual markup, and rerun; earlier partial measurements are diagnostic evidence, not a PASS.

See `references/css-contract-scope-and-mutation.md` for a compact extraction and mutation recipe.

## Browser-verification timing notes

- Playwright over a local static server: `npx playwright` does NOT expose a require()-able module — install into a scratch dir (`npm i playwright@1.48.2`) and run `node script.js` from it. If the installed revision is absent from the ms-playwright cache (e.g. cache has chromium-1228 but playwright 1.48 wants 1140), launch with `channel: 'chrome'` to use the system Chrome instead of downloading a new build. Kill stray node.exe before deleting the scratch dir, or `rm` fails with "Device or resource busy".
- After clicking a language switch in puppeteer, wait for the *effect*, not a fixed delay: `await page.waitForFunction(() => document.documentElement.lang === 'en')`. The switch is async (`LoadSavedLanguageAsync`); typing immediately can search with the old language index.
- Language preference persists in localStorage across pages in the same browser session. A second test that clicks `.lang-switch` again toggles **back** — check current `documentElement.lang` first, or assert the expected end state.
- 403 console errors from rate-limited third-party APIs (e.g. `api.github.com`) are expected; confirm the URL, don't treat as a regression.

## Pitfalls That Were Investigated and Resolved (not defects)

- A static `<html lang="zh-CN">` in `index.html` is fine as a default; `LanguageService` + a tiny JS `lang.set` updates it after WASM boots.

## Native Library Linking (DllNotFoundException)

### When to use
- Browser console shows `DllNotFoundException: <libName>` (e.g. `libSkiaSharp`) inside `TypeInitializationException` when a component touches a native-backed library.
- Blazor WASM app works when started with `dotnet run` but fails when started from Visual Studio (error stack often contains `receiveHotReload` frames).
- Suspicion that `wwwroot/_framework/dotnet.wasm` does not contain expected native symbols.

### Mental model (.NET 6 / net6.0 Blazor WASM)
Native libraries (SkiaSharp 2.88.x, etc.) are NOT shipped as separate .wasm files in .NET 6. `SkiaSharp.NativeAssets.WebAssembly` provides `libSkiaSharp.a`; the emscripten toolchain must link it into `dotnet.wasm` during build. This requires:
1. `WasmBuildNative=true` in the csproj (or auto-derived), and
2. the workload SDK `Microsoft.NET.Runtime.WebAssembly.Sdk` actually imported so the `_WasmBuildNativeCore` / `_WasmLinkDotNet` targets exist.

If either is missing, the build copies the **runtime-pack original** `dotnet.wasm` (small, no native symbols) into wwwroot and P/Invoke fails at runtime.

### Diagnostic path (evidence ladder, cheapest first)
1. **Check the served artifact** — `wwwroot/_framework/dotnet.wasm`:
   - Linked: large (~20 MB in Debug) and `grep -c SkiaSharp <file>` > 0
   - Unlinked: identical size+timestamp to the runtime pack's `dotnet.wasm` (~2.4 MB), zero native symbols
2. **Compare CLI vs VS build**: `dotnet build` (links; look for "Compiling native assets with emcc" / "Linking with emcc") vs the VS MSBuild invocation (silently skips the link). VS MSBuild path: find via vswhere.
3. **Check workload SDK import**: VS build diag log shows no `_WasmBuildNativeCore` / `_SetupEmscripten` execution; `blazor.boot.json` has `"libraryInitializers": null` when linking never ran.
4. Root-cause class: newer VS MSBuild cannot resolve the .NET 6 workload SDK aliases (`Microsoft.NET.Runtime.WebAssembly.Sdk.net6`, `MonoTargets.Sdk.net6`), so `UsingBrowserRuntimeWorkload` is never derived and the manifest `ImportGroup` that imports the WASM SDK never fires. `WasmBuildNative=true` becomes a no-op. This is NOT a library-usage bug.

### Fix
VS-gated manual import of the workload SDKs by absolute path in the Blazor WASM csproj. Exact block, mechanism chain, and the error cascade when pieces are missing: `references/vs18-workload-sdk-imports.md`.
The block must also set `UsingBlazorAOTWorkloadManifest=true` — without it, VS **Publish** (not Build) fails with `BLAZORSDK1002` (AOT workload check). Validate BOTH `-t:Build` and `-t:Publish` when exercising the workaround.
Reusable artifact check: `scripts/verify-wasm-native-linked.sh`.

### Build vs Publish artifacts (deployed app has no styles)
.NET 6 Blazor WASM **Build** output (`bin/<cfg>/net6.0/wwwroot`) does NOT contain NuGet package static assets — `_content/` is absent entirely (the dev server serves them from the package via the static-web-assets manifest). Only **Publish** physically copies them to `wwwroot/_content/<Package>/...`. Symptoms and diagnosis:
- Local `dotnet run` / VS F5 looks fine (dev server serves `_content`), but copying `bin/.../wwwroot` to a real machine yields HTML with zero styles — `_content/<Package>/<path>.css` (and every other package asset) 404s.
- A reference consumer with no package static assets (pure Razor) works from Build output; a consumer of a component library with CSS/JS assets does not — that difference is the tell.
- Check: `find <publish-output>/wwwroot/_content -type f` — empty/missing = wrong artifact. Compare with `dotnet publish -c Release` output, which always contains `_content`.
Fix: deploy the **Publish** output (`dotnet publish -c Release` or VS Build→Publish); never hand-copy Build `bin/.../wwwroot`. If the deploy target is a subpath (GitHub Pages project site), also rewrite `<base href>` (see `ada-blazor-wasm-github-pages`).

NOTE: artifact-correct but STILL unstyled → separate cause. A component library that ships an unstyled baseline (system-color defaults, transparent chrome) needs the consumer's own theme (palette → CSS-variable overrides → effect layer).

### Architectural alternative (prefer this for simple shapes)
For primitive drawing (circles/rects/triangles + hit-testing) a native drawing library is overkill: it drags in the whole WASM native-link problem class, a ~20MB `dotnet.wasm`, and the VS toolchain workaround. Browser-native SVG gives element-level hit-testing for free (`@onclick` on `<circle>/<rect>/<polygon>`), zero native deps, and a pure-Razor project shape that works out of the box. Rule of thumb: if the shapes are simple and countable, remove the native dependency instead of patching the build — the color-key offscreen hit buffer can be replaced by pure geometric hit-testing that stays unit-testable. The native library earns its keep only for complex/composited rendering (paths, gradients, image ops, high volume).

### Cross-platform native assets (unit tests, non-WASM)
A net6.0 test project referencing a native-backed library passes on Windows (Win32 asset restored) but its tests throw `DllNotFoundException` on a Linux CI runner (same exception family as the WASM case, different cause). Fix: add the Linux native-assets package at the same version to the project that owns the usage (add its `<PackageVersion>` to central package management too). Verify by grepping `obj/project.assets.json` for the Linux asset after restore, plus a dual-OS CI matrix (ubuntu + windows) — local Windows dev can never reproduce this. Related CI gotcha: every Actions job that restores a Blazor WASM project needs `dotnet workload install wasm-tools`; it is easy to add it to the build job but forget the format/lint job, which then fails restore with "workloads must be installed: wasm-tools".

### CI gotcha: NU1507 + Central Package Management (packageSourceMapping)
If the repo uses CPM (`ManagePackageVersionsCentrally`), a GitHub Actions run can fail restore with `NU1507: There are 2 package sources defined in your configuration...` — the runner adds a default `C:\Program Files\dotnet\library-packs` source alongside `nuget.org` (the **windows** runner hits this; ubuntu may pass single-source). Local dev never reproduces it because the repo `NuGet.Config` `<clear/>`s the source list. Fix in `NuGet.Config`, not CI:

```xml
<packageSourceMapping>
  <packageSource key="nuget.org">
    <package pattern="*" />
  </packageSource>
</packageSourceMapping>
```

The extra source then has no mappings and is ignored, satisfying NU1507's single-effective-source requirement. Verify locally with a temp dual-source `--configfile` (nuget.org + a dummy library-packs path) asserting restore exits 0 with no NU1507, then rely on the windows-latest CI leg as the real gate.

### Pitfalls (native linking)
- `grep` the **served** file (`wwwroot/_framework/dotnet.wasm`), not `bin/Debug/net6.0/dotnet.wasm` — the latter can be a stale runtime-pack copy from an old build and misleads the diagnosis.
- MSB4011 "cannot import again" warnings for the Emscripten Sdk.props are harmless: VS actually DOES import the emscripten manifest; it is the aliased WASM/Mono SDKs that fail to resolve.
- Missing pieces of the manual import surface as a cascade of MSBuild errors — import all five packages from the reference, not just the first one that silences the current error.
- After `DllNotFoundException`, the follow-up "No element is currently associated with component N" / NullReferenceException in `RenderTreeDiffBuilder` is a cascade of the crashed renderer, not an independent bug.
- If the user cannot accept a csproj workaround, `dotnet run --project <wasm-proj>` from CLI is an immediate bypass (CLI resolves the workload normally).
- Ad-hoc verify scripts on Windows/git-bash: do not pass `mktemp` `/tmp/...` paths to Windows tools (dotnet, MSBuild, NuGet `--configfile`) — they resolve as `<drive>:\tmp\...` and fail "file not found". Use explicit `C:/Users/<user>/AppData/Local/Temp/...` paths for anything a Windows executable consumes. Also assert on process exit codes, not localized banner text (`dotnet test` on a Chinese-locale host prints `已通过!`, not `Passed!`).
