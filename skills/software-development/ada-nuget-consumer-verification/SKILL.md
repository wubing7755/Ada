---
name: ada-nuget-consumer-verification
description: "Verify NuGet consumer samples against local library source."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [dotnet, nuget, packaging, consumer, verification]
    related_skills: [ada-blazor-bunit-testing, ada-test-driven-development]
    trigger_keywords: ['NuGet consumer', 'packed package', 'local feed', '.packages', 'PackageVersion', 'PublicAPI.Unshipped', 'RS0016', 'HintPath']
---

# NuGet Consumer Verification

Verifying an independent NuGet consumer sample (a portable demo app + its
tests that reference the library by PACKAGE, not ProjectReference) against
local source. This is the classic library-repo gate: source changes mean
nothing to the consumer until the local feed carries a matching package.

## When to Use

Use when:
- A consumer sample (e.g. `samples/Demo`) must exercise NEW library
  source APIs, and its tests fail with `CS1061 ... does not contain a
  definition for 'X'` after restore.
- The consumer resolves the RELEASED package from nuget.org instead of the
  local feed.
- Focused `dotnet test tests/<App>.Tests` silently runs old app code.
- Adding public API to a library triggers RS0016 PublicAPI analyzer errors.

## The Dev Loop (pack → clear cache → restore → verify)

```sh
# 1. Pack with the consumer's PINNED version, not the repo default.
#    Directory.Build.props <Version>0.0.0-dev</Version> otherwise produces a
#    version the consumer never selects. Central package management pins a
a concrete version (e.g. <PackageVersion Include="Lib" Version="0.1.0" />).
dotnet pack src/Lib/Lib.csproj -c Release -o artifacts/packages -p:PackageVersion=<pinned>

# 2. Clear ONLY the consumer's local package cache, then restore.
#    The consumer's NuGet.Config sets globalPackagesFolder=.packages, so the
#    cache lives inside the consumer directory.
rm -rf <consumer>/.packages/<pkg>
dotnet restore <consumer>/<Consumer>.sln --configfile <consumer>/NuGet.Config

# 3. Verify the restore resolved from the LOCAL feed, not nuget.org.
#    .nupkg.metadata records the source used:
cat <consumer>/.packages/<pkg>/<version>/.nupkg.metadata   # expect the local path, not https://api.nuget.org
#    Or grep the new API symbol bytes in the extracted DLL:
python -c "d=open('<consumer>/.packages/<pkg>/<version>/lib/net6.0/Lib.dll','rb').read(); print(b'NewApiName' in d)"
```

## Critical Details

- **Version match is everything.** The consumer pins ONE version via central
  package management. The local feed must contain that exact version or the
  restore pulls the released one from nuget.org. Pack with
  `-p:PackageVersion=<pinned>` — the repo's default `<Version>` is often a
  `0.0.0-dev` placeholder the consumer never selects.
- **Feed order decides equal-version winners.** nuget.org may already host
  the pinned version. The local feed must be listed FIRST in the consumer's
  `NuGet.Config` so an equal-version local package wins.
- **The packed local package is dev-only state** (typically under gitignored
  `artifacts/`). It shadows the published version only for that consumer's
  restores — never confuse it with a release, and don't push it.
- **Only clear the consumer's local cache**, never the global NuGet cache.

## Staleness Traps

### HintPath-referenced app DLL

A test project that references the app assembly via
`<Reference Include="App"><HintPath>..\..\bin\$(Configuration)\net6.0\App.dll</HintPath></Reference>`
(no ProjectReference) does NOT rebuild the app. Focused
`dotnet test tests/App.Tests --filter ...` runs against the STALE DLL — a
"green" focused run can silently exercise old code. Run the solution
(`dotnet test App.sln`) or build the app project first so the HintPath DLL
is rebuilt. The app csproj and the test project are two layers that must
BOTH be refreshed (pack → clear cache → restore → build app → test).

### PublicAPI analyzer baseline (RS0016)

Adding public types/members to a library with
`Microsoft.CodeAnalysis.PublicApiAnalyzers` triggers RS0016 "symbol is not
part of the declared API" errors. Fix by updating `PublicAPI.Unshipped.txt`
(baseline maintenance, NOT test weakening). Entry format follows the
analyzer's exact expected text — generic methods look like
`Lib.Content.IStateScope.GetOrCreate<TState>(Lib.Items.ContentReference reference, System.Func<TState!>! factory) -> TState!`;
`out` parameters and nullable returns keep their annotations
(`out TState? state) -> bool`, `-> TState?`). When unsure, write a
best-guess entry and let the build error supply the exact string.

## Consumer-Sample Gap Review Mode（从消费者示例找库缺口）

A library/framework review that reads its own consumer sample (a `samples/`,
`examples/`, or demo project referencing the packed package) as a **friction
report**. A sample that compiles and runs but fights the API is the cheapest,
most honest evidence of what the library does not support well — more reliable
than privileged in-repo tests, because the sample is the only code written from
the consumer's side.

**Activation**: evaluate a library's developer experience / NuGet consumer
experience; find framework shortcomings from a consumer perspective; assess
whether library X can host a team's model reuse; review a component library's
architecture and data passing. Skip for: applications with no library API, or
general code quality without a consumer boundary.

**Workflow**:
1. Read the sample as a consumer would: DI/startup wiring, host component
   usage, panel definitions, cross-panel data flow, and the sample's own tests
   (they expose workarounds the author needed).
2. Read the normative docs (SRS/ADRs) for the content/state model BEFORE
   judging — a documented app-owned responsibility turns "missing API" into
   "missing guidance"; say so precisely.
3. Inventory the library's public surface for the seams the sample needed.
4. Hunt friction patterns (verify each against library source + docs):
   - **Ignored framework contexts**: a per-item `Context` parameter named but
     never used; panels bind `[Parameter] Model` from host closure instead of
     the framework's per-instance context.
   - **Per-kind singleton state vs per-item model**: one host-owned ViewModel
     per Kind breaks when two items of the same Kind exist.
   - **Cross-panel communication through the host**: content only receives
     item-scoped commands, never Open/subscribe → panels cannot drive
     navigation themselves.
   - **Stringly-typed kinds duplicated across declaration surfaces**: renaming
     one yields a runtime "not registered", not a compile error.
   - **Local UI state clobbered by parent re-render**: `OnParametersSet`
     copies from a model while the host re-renders → unsaved edits silently
     lost.
   - **Slot parameters forcing hand-built RenderTreeBuilder**: plain
     `RenderFragment` slots push consumers into `builder.OpenComponent<T>(0)` +
     magic sequence numbers.
   - **Undemonstrated modes**: a sample using only one content-declaration
     path hides the other paths' rough edges.
5. Report severity-ranked, `file:line`-cited findings, split into
   framework-fix vs sample-fix, with a prioritized table. A sample workaround
   may be the author's taste — verify before claiming a gap; attribute
   findings as framework deficiency vs demo usage problem.

## Verification Checklist

- [ ] Packed the local feed with the consumer's PINNED version
- [ ] Cleared only the consumer's `.packages/<pkg>` cache
- [ ] Restored with `--configfile <consumer>/NuGet.Config`
- [ ] `.nupkg.metadata` source field shows the local feed path
- [ ] App DLL (HintPath) rebuilt before focused tests
- [ ] `PublicAPI.Unshipped.txt` updated for new public API
- [ ] Full consumer suite green; framework suite re-run after packing
