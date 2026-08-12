---
name: ada-dotnet-nuget-packaging
description: "Use when publishing or preparing .NET NuGet packages."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [dotnet, nuget, packaging, release, msbuild, cpm]
    related_skills: [ada-dotnet-blazor-library, ada-dotnet-verification]
---

# .NET NuGet Packaging and Release

Publishing a .NET library as a NuGet package: single-package distribution,
central version management, package metadata/README, and the MSBuild targets
that keep pack artifacts fresh. Covers the class of work where the deliverable
is a nupkg that external consumers will install — not building the library
itself (see `ada-dotnet-blazor-library` for RCL structure).

## When to Use

- "How do I publish / how do consumers install this package?"
- Deciding between multiple packages vs a single package that embeds a dependency
- Editing package versions when the repo uses Central Package Management
- Writing the README that nuget.org will auto-render on the package page
- Packing a library whose nupkg must include freshly built JS/CSS assets
- Verifying a consumer (Demo) resolves the exact package being published

## Single-Package Distribution (embed a referenced assembly)

Publish ONE package while keeping two independent source projects (pure-C#
domain + RCL). Embed the domain DLL into the RCL nupkg:

```xml
<ItemGroup>
  <!-- PrivateAssets=all removes Lib.Core from the nuspec dependency list -->
  <ProjectReference Include="..\Lib.Core\Lib.Core.csproj" PrivateAssets="all" />
</ItemGroup>
<ItemGroup>
  <None Include="$(OutputPath)Lib.Core.dll"
        Pack="true"
        PackagePath="lib\$(TargetFramework)" />
</ItemGroup>
```

Result: consumers install one package and get both assemblies at compile and
run time; the nuspec declares no dependency on the embedded project; consumers
keep using the embedded namespace unchanged. This is a packaging decision, not
an architecture merge — the domain project stays independent with no Blazor
reference.

### PITFALL: `PrivateAssets="all"` requires a CLEAN restore before pack

A stale `obj/` keeps the old dependency graph, so the generated nuspec still
lists Lib.Core even though the csproj says `PrivateAssets="all"`. The FIRST
pack after adding PrivateAssets often still shows the dependency; `rm -rf
<RCL>/obj <Core>/obj && dotnet restore && dotnet pack` fixes it. ALWAYS verify
the nuspec dependency list after packing (see Verification).

### Ripple effects on test projects

- Source-level test projects inside the repo (not NuGet consumers) that use
  both projects need an explicit `ProjectReference` to the domain project,
  because `PrivateAssets="all"` hides the transitive reference from them.
- Package-boundary tests that assert the Demo references both packages must
  be flipped to assert it references ONLY the RCL package.
- CI pack job: pack only the RCL project; remove the domain pack step.
- **PITFALL: packing without consuming proves nothing.** A pack job that only
  runs `dotnet pack` stays green even when the embed topology, dependency
  graph, or bundled assets break — the nupkg is never exercised. Add a
  consumer-verification step to the SAME CI pack job (restore the Demo with
  its own NuGet.Config so it resolves the local feed, build, test). The
  Demo verification steps in AGENTS.md are otherwise only run manually
  locally, so a packaging regression ships green.

  Verified shape (Lib `ci.yml` pack job): pack with
  `-p:PackageVersion=<demo-pinned-version>` in the same job, then a
  "Verify Demo consumes the packed package" step running
  `dotnet restore Demo.sln --configfile NuGet.Config` → `build` →
  `test` → `format`. Keep the packed version in sync with the demo's CPM
  props: if the pack job emits the dev default while the demo pins the
  release version, restore fails on the missing package — the check catches
  it, but pinning the pack version to the demo's makes the check exercise the
  exact artifact the demo resolves. The same flow as a local one-shot script
  is the fastest developer loop: `scripts/republish-demo.sh` (pack → `rm -rf
  samples/<Demo>/.packages/<pkg>` → restore `--configfile` → build/test/
  format) — the `.packages` clear is mandatory or the cached nupkg shadows
  the fresh one.
- Update AGENTS.md / CONTRIBUTING / docs that list "pack both packages".

## Central Package Management (CPM) Overrides

With CPM (`Directory.Packages.props` at repo root,
`ManagePackageVersionsCentrally=true`):

- Versions live in the props file, NOT in `PackageReference` attributes.
  Writing `Version=` on a PackageReference under CPM fails restore with NU1008.
- A **subdirectory can have its own `Directory.Packages.props` that OVERRIDES
  the root one** for projects under it. Multi-solution repos (main sln +
  standalone consumer sln) commonly carry a second
  `samples/<Demo>/Directory.Packages.props` pinning the local package version.
- To change the version a demo consumes, edit THAT file. Editing the root one
  has no effect on the demo. Symptom of editing the wrong file: restore
  succeeds but resolves the old version.
- For release verification, pin the demo's package version to the release
  version so restore proves the consumer resolves the exact artifact.

## Package README (nuget.org auto-renders it)

NuGet.org renders `PackageReadmeFile` content automatically on the package
page and it cannot be edited after publish. Therefore the packaged README must
be CONSUMER-focused, not repository-focused. A repo README that says "not yet
published", lists two packable projects, or contains Building-From-Source /
npm / test instructions is wrong content for a package page.

### PITFALL: the packaged README must be refreshed BEFORE every version bump

The readme is frozen at publish time. A release prep that only bumps the
nuspec version ships the OLD readme — wrong install snippet and missing new
capabilities. Before packing a new version, update in the SAME release-prep
commit:

- the Install snippet `Version="X.Y.Z"` to the new version;
- the Core Capabilities list with what the new version adds (users read the
  NuGet page to decide whether to upgrade);
- documentation links that changed (e.g. a new theming guide).

The repo pins version in FOUR places that must stay in sync on a release:
the readme Install snippet, the demo's CPM props
(`samples/<Demo>/Directory.Packages.props` → `PackageVersion Include=<pkg>`),
the republish script (`PACKAGE_VERSION=`), and — the most commonly missed —
the CI pack step (`.github/workflows/ci.yml` → `-p:PackageVersion=...`).
A bump that updates props+script+readme but NOT ci.yml makes the CI pack
job fail with `NU1102: Unable to find package Lib.Blazor with version
(>= X.Y.Z)` while build/format still pass, so the failure looks unrelated
to the bump. Before committing a release prep, grep the whole repo for the
old version (`.github samples scripts src/Lib.Blazor` at minimum) and fix
every hit. An ad-hoc check that greps the old version in these four files
catches a miss before pack.

Keep a dedicated `package-readme.md` in the library project (NOT the repo
root README):

- What it is, one-line positioning
- Install snippet (single PackageReference)
- Quick Start using real demo API calls (service registration, workspace
  creation, host rendering)
- Capabilities list
- **Documentation links as ABSOLUTE URLs** to the GitHub repo — relative
  links break on the nuget.org rendered page
- License

### PITFALL: Quick Start code must be consumer-copyable — never repo-internal types

The readme is frozen at publish time, so every identifier in the Quick Start
must exist in the PUBLISHED package and be PUBLIC. A readme example that calls
a repo demo's `internal` helper (e.g. `LibDemoWorkspaceDefinition.Create(...)`
— an `internal` class living in the samples project) compiles fine in the repo
but a consumer copying it gets CS0122/CS0246. Before packing, grep-verify the
readme: every referenced type exists, is public, and the member signature
matches (same discipline as API-signature verification for docs). Prefer the
public declaration components (or a `new LibWorkspaceDefinition(...)` shape
from the worked guide) over any sample-only helper. When in doubt, unzip the
the nupkg and read the packaged `package-readme.md` back — verify it contains the
new version snippet AND the intended new-feature bullets, not just that a
readme file exists.

### PITFALL: packaged-readme format — no soft line wraps, no trailing blank

The readme is frozen at publish AND shown in editors/reviewers before then.
Two format rules the Lib maintainer enforces (both were explicit
corrections):

1. **Each paragraph is ONE line.** Hand-wrapping prose at ~80 chars puts a
   newline in the middle of a sentence ("...and layout⏎persistence for
   IDEs..." reads as two lines in source). Merge paragraph text into a
   single line; keep code fences and list items intact. A soft-wrap check:
   no two consecutive non-blank, non-fence, non-list, non-heading lines.
2. **Exactly one final newline, no trailing blank line.** No BOM, LF only,
   no consecutive blank lines, no trailing whitespace.

Verify the PACKED copy inside the nupkg (`zipfile` read of
`package-readme.md`), not just the source file — pack can silently differ.

### Checking the package's live state before release

`web_extract`/browser on nuget.org can be blocked by network policy. The
public NuGet API works instead (curl):
- Version list: `https://api.nuget.org/v3-flatcontainer/<id-lowercase>/index.json`
  — confirms the target version is not already published (NuGet versions
  cannot be overwritten).
- Metadata: `https://api.nuget.org/v3/registration5-gz-semver2/<id-lowercase>/index.json`
  with `curl --compressed` (the endpoint is gzip) — authors, license,
  dependency groups, published date; confirms the live package matches the
  csproj metadata (single dependency, embedded core, no stale deps).

```xml
<PropertyGroup>
  <PackageReadmeFile>package-readme.md</PackageReadmeFile>
</PropertyGroup>
<ItemGroup>
  <None Include="package-readme.md" Pack="true" PackagePath="\" />
</ItemGroup>
```

## Incremental JS-Bundle Rebuild Before Pack

RCLs that compile TypeScript to a bundled `wwwroot/.../app.js` often
gitignore the bundle. A plain `dotnet build`/`dotnet pack` then silently ships
a stale or missing bundle — the fix exists in TS source but never reaches the
nupkg. Add an incremental MSBuild target:

```xml
<ItemGroup>
  <ClientScript Include="ClientScripts\**\*.ts" />
  <ClientScript Include="ClientScripts\**\*.json" />
  <ClientScript Include="package.json" />
  <ClientScript Include="package-lock.json" />
  <ClientScript Include="tsconfig.json" />
</ItemGroup>
<Target Name="EnsureLibJsBundle"
        BeforeTargets="BeforeBuild"
        Inputs="@(ClientScript)"
        Outputs="$(MSBuildProjectDirectory)\wwwroot\app-v2\app.js">
  <Exec Condition="'$(SkipJsBuild)' != 'true'"
        Command="npm run build:js"
        WorkingDirectory="$(MSBuildProjectDirectory)"
        ContinueOnError="WarnAndContinue" />
</Target>
```

### PITFALL: raw glob strings in `Inputs` never expand

`Inputs="$(MSBuildProjectDirectory)\ClientScripts\**\*.ts"` (a raw string) is
NOT expanded by MSBuild, so the target runs every build and the incremental
check never skips. Collect the files into a real ItemGroup and pass
`Inputs="@(ClientScript)"` — then the skip works (verified: unchanged
bundle stays untouched, touching a TS file triggers the rebuild).

`ContinueOnError="WarnAndContinue"` lets pure-.NET builds proceed without npm
installed; `SkipJsBuild=true` is an explicit escape hatch.

## Release Workflow (nupkg for external consumers)

### PITFALL: NuGet.Config local-feed paths must use forward slashes

A consumer's `NuGet.Config` that points at a relative local feed
(`<add key="local-feed" value="../../artifacts/packages" />`) breaks on
Linux CI if written with backslashes (`..\..\artifacts\packages`): the
backslashes are treated literally, restore fails or resolves nothing, and the
consumer-verification step you added to CI fails on ubuntu while passing
locally on Windows. Forward slashes resolve correctly on both platforms —
write the local feed path with `/` from the start.

1. **Version**: dev default (`0.0.0-dev`) cannot be published. Override at
   pack time: `-p:Version=0.1.0` (or `-p:PackageVersion=0.1.0`, both set the
   nuspec version) — do not change the dev default.
   **PITFALL: bump the version in ALL FOUR touchpoints, not just the props
   file.** A release-prep commit must update them together or CI breaks:
   - `samples/<Demo>/Directory.Packages.props` — the version the demo resolves
   - `scripts/republish-demo.sh` — the `PACKAGE_VERSION` used by the one-shot
     pack+verify loop
   - `.github/workflows/ci.yml` — the `-p:PackageVersion=` the pack job pins
     (stale here = NU1102 in the "Verify Demo consumes the packed package"
     step, because local-feed and nuget.org both only have the old version
     while the demo props demand the new one)
   - `package-readme.md` — the `<PackageReference Version="..." />` snippet
     (this one is consumer-facing, wrong version = users install the old one)
   Symptom of a missed touchpoint: PR CI pack job fails with
   `NU1102: Unable to find package Lib.Blazor with version (>= X.Y.Z)` while
   build/test/format pass. Grep the whole repo for the old version string
   before opening the release PR.
2. **Metadata**: Authors, RepositoryUrl, PackageLicenseExpression, tags,
   PackageReadmeFile (see above).
3. **Pack with clean restore** (see PrivateAssets pitfall):
   ```sh
   rm -rf src/<RCL>/obj src/<Domain>/obj
   dotnet restore src/<RCL>/<RCL>.csproj
   dotnet pack src/<RCL>/<RCL>.csproj -c Release --no-restore -o artifacts/packages -p:Version=0.1.0
   ```
4. **Verify the nupkg** — inspect inside the zip:
   - `lib/<tfm>/` contains the RCL dll AND the embedded dll
   - nuspec has NO dependency on the embedded project
   - package-readme present, repo README absent
   - license expression, repository URL present
5. **Consumer verification**: clear the demo's `.packages/<pkg>` cache and
   `obj`, restore with the demo's NuGet.Config (local feed + nuget.org), build
   and test. Confirm the resolved version equals the release version.

### PITFALL: HintPath test references run against a stale DLL

Consumer-sample test projects often reference the built library by `HintPath`
(`<Reference Include="..."><HintPath>..\..\bin\$(Configuration)\net6.0\...dll</HintPath></Reference>`)
instead of a `ProjectReference`. That means `dotnet test` on the test project
does NOT rebuild the library — it runs against the stale DLL in `bin/`. During
TDD this looks like "my edit had no effect": the focused test keeps
passing/failing against old code. Fix: always build the library (and for
package consumers, pack + clear the local package cache + `obj`) BEFORE
running the sample's tests.
6. **Publish**: `dotnet nuget push ... --source https://api.nuget.org/v3/index.json --api-key <KEY>`.
   The API key is a user secret — never type it for the user; hand them the
   command. First publish cannot be deleted or overwritten; bump patch/minor
   for follow-ups.

## GitHub Packages NuGet registry

The GitHub repository "Packages" page shows packages published to GitHub
Packages (`nuget.pkg.github.com`), NOT nuget.org. A successful nuget.org
upload does not populate the GitHub Packages page; "No packages published" on
the repo page is expected unless you also push to the GitHub Packages source
(separate token with `write:packages`). nuget.org is the official public .NET
feed and is sufficient unless private hosting is required.

### Publishing to GitHub Packages (user-executed)

- **Auth is classic PAT ONLY** (GitHub Packages does not support
  fine-grained PATs). Scope needed: `write:packages` (`read:packages` is
  implied). PAT is a user secret — hand the user the commands, never type
  the token.
- Add the source, then push with the PAT as `--api-key` (per GitHub docs —
  the api-key path does NOT require credentials in the config):
  ```sh
  dotnet nuget add source --username <OWNER> --password <PAT> \
    --store-password-in-clear-text --name github \
    "https://nuget.pkg.github.com/<OWNER>/index.json"
  dotnet nuget push artifacts/packages/<Pkg>.<Ver>.nupkg \
    --api-key <PAT> --source github
  ```
- **PITFALL: `dotnet nuget add source` run inside a repo writes to the
  REPO's `NuGet.Config`, not the user-level config** — pollutes CI
  (a `--configfile NuGet.Config` restore then hits an unauthenticated
  github source) and other contributors. Run it with an explicit
  user-level target:
  `dotnet nuget add source --configfile ~/.nuget/NuGet/NuGet.Config ...`
  After the fact, `git checkout NuGet.Config` restores the repo file; the
  PAT was never persisted when pushed via `--api-key` (transient), which
  is safe — but the source entry must exist at push time.
- `RepositoryUrl` in the csproj auto-links the package to that repo
  (OWNER must match). First publish defaults to **private** — the user
  must flip visibility to public on the GitHub Packages page.
- CI alternative: publish from a workflow with `GITHUB_TOKEN`
  (`--username <OWNER> --password ${{ secrets.GITHUB_TOKEN }}`), which
  auto-inherits repo access — best on tag push / workflow_dispatch, NOT
  every PR.

### GitHub Release with the nupkg asset

For a public library, create a GitHub Release at the same version tag and
attach the nupkg — consumers can download the package directly without a
feed, and GitHub auto-attaches source zip/tar.gz:

```sh
git tag -a 0.2.0 -m "Lib.Blazor 0.2.0" && git push origin 0.2.0
gh release create 0.2.0 --title "Lib.Blazor 0.2.0" --notes "$NOTES" \
  artifacts/packages/Lib.Blazor.0.2.0.nupkg
```

Release notes should list what changed since the previous release and link
the feeds (nuget.org / GitHub Packages). The nupkg is the standard release
asset; do not attach build byproducts that already live in the source tree.

## Live demo on GitHub Pages (release-loop step)

At major nodes, after publishing, redeploy the frozen consumer demo to
GitHub Pages so the live site reflects the officially published package.
The full technique (base-href rewrite, root 404 SPA fallback,
`publish --source nuget.org`, workflow shape, local verification recipe)
is in `references/blazor-wasm-github-pages.md`. Summary: source keeps
`<base href="/" />` for local dev; the deploy workflow rewrites it to
`/<repo>/` after publish, stages the site at that subpath with a root
404.html, and uses upload-pages-artifact + deploy-pages (manual
`workflow_dispatch` trigger — the demo is frozen, don't redeploy per push).

## Consumer app: declarative host usage

When building the WASM consumer app itself (not the deploy), the declarative
host API has several type/namespace traps that each cost a build cycle —
declaration components MUST go inside `<ChildContent>`, IDs are typed
(`WorkspaceId`/`LayoutNodeId`/`DockItemId`) not strings, item params use
`ContentKind` + `ResourceId` (not `Kind`), enums live in the core namespace,
and a missing `@using` turns a consumer component into an empty HTML element
(`RZ10012`).

## Verification

- [ ] `dotnet pack` nupkg inspected: embedded dll present, no dependency on
      the embedded project in the nuspec
- [ ] Demo references only the RCL package; its CPM props pin the release
      version; restore resolves that exact version
- [ ] Demo and full solution build/test/format pass against the packed package
- [ ] package-readme.md is the file inside the nupkg (repo README excluded)
- [ ] `git diff --check` clean; temp verification scripts cleaned up
