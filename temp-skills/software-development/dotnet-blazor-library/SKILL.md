---
name: dotnet-blazor-library
description: Use when structuring, developing, or publishing .NET Blazor component libraries — RCL setup, public API naming conventions, demo app separation, and NuGet packaging considerations.
version: 1.0.0
platforms: [windows, linux, macos]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [dotnet, blazor, rcl, library, component, naming]
---

# .NET Blazor Component Library

Structuring and developing a Blazor component library as a Razor Class Library
(RCL) with a companion demo app.

## Trigger

- "Create a Blazor component library"
- "Split this Blazor app into a library + demo"
- "Structure this as a NuGet package"
- "Add Atlas prefix to all public types"

## Project Structure

```
src/
├── <Library>/                     ← Razor Class Library (RCL)
│   ├── <Library>.csproj           ← Sdk="Microsoft.NET.Sdk.Razor"
│   ├── _Imports.razor             ← @using for Domain/Services/Interop
│   ├── package.json               ← TypeScript build (if JS interop)
│   ├── Domain/                    ← Data models, enums
│   ├── Services/                  ← Business logic services
│   ├── Interop/                   ← JS interop (IJSRuntime wrappers)
│   ├── Results/                   ← Result types, error codes
│   ├── Components/                ← Razor components
│   │   └── _Imports.razor         ← @namespace for components
│   ├── ClientScripts/             ← TypeScript source (if any)
│   └── wwwroot/                   ← Static assets (CSS, compiled JS)
│
└── <Library>.Demo/                ← Blazor WebAssembly demo app
    ├── <Library>.Demo.csproj      ← Sdk="Microsoft.NET.Sdk.BlazorWebAssembly"
    ├── _Imports.razor             ← @using for library namespaces
    ├── App.razor
    ├── Program.cs
    ├── Pages/                     ← Demo pages
    ├── Shared/                    ← Demo layouts
    └── wwwroot/                   ← Demo static assets (bootstrap, etc.)

tests/
└── <Library>.Tests/               ← xUnit test project
    └── <Library>.Tests.csproj     ← ProjectReference to RCL
```

## RCL .csproj Template

```xml
<Project Sdk="Microsoft.NET.Sdk.Razor">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <RootNamespace>Atlas</RootNamespace>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.Components" Version="6.0.36" />
    <PackageReference Include="Microsoft.AspNetCore.Components.Web" Version="6.0.36" />
  </ItemGroup>
</Project>
```

## Demo .csproj Template

```xml
<Project Sdk="Microsoft.NET.Sdk.BlazorWebAssembly">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <RootNamespace>Atlas.Demo</RootNamespace>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.Components.WebAssembly" Version="6.0.36" />
    <PackageReference Include="Microsoft.AspNetCore.Components.WebAssembly.DevServer" Version="6.0.36" PrivateAssets="all" />
  </ItemGroup>
  <ItemGroup>
    <ProjectReference Include="..\Atlas\Atlas.csproj" />
  </ItemGroup>
</Project>
```

## Public API Naming Convention

When every public type in the library is developer-facing, use the project name
as prefix on all types. Distinguish categories by suffix:

| Category | Pattern | Example |
|----------|---------|---------|
| Razor components | `<Name><Purpose>` | `AtlasLayout`, `AtlasDockPanel` |
| Domain models | `<Name><Purpose>Model` | `AtlasLayoutState`, `AtlasDockPanelModel` |
| Services | `<Name><Purpose>Service` | `AtlasDragService` |
| Enums | `<Name><Purpose>` | `AtlasRegionKind`, `AtlasDedupMode` |
| Results | `<Name>Result<T>` | `AtlasResult<string>` |
| Error codes | `<Name>ErrorCode` | `AtlasErrorCode` |
| Events | `<Name><Event>EventArgs` | `AtlasLayoutChangedEventArgs` |
| Interfaces | `I<Name><Purpose>` | `IAtlasActivationStrategy` |

**Key rule**: Domain models and Razor components MUST NOT share the same name.
The `Model` suffix on domain types prevents clash. The component name stays
clean because that's what developers type in markup.

## Pitfalls

### Domain Model / Component Name Clash

When adding a common prefix to all types:

1. Rename all types (both domain models and components get the prefix)
2. This creates identical names for paired types (e.g., both `DockPanelModel`
   and `DockPanel` component become `AtlasDockPanel`)
3. Fix: add `Model` suffix to domain types (`AtlasDockPanel` → `AtlasDockPanelModel`)
4. In `.razor` `@code` blocks, use the `Model`-suffixed name for domain references
5. Component tags stay clean (`<AtlasDockPanel>`)

### Regex for Fixing Component Tags

When reverting component tag names after a Model-suffix pass, the regex MUST
distinguish HTML/XML tags from generic type parameters:

- **Correct**: `<AtlasDockPanelModel ...>` (HTML tag) → `<AtlasDockPanel ...>`
- **Incorrect**: `List<AtlasDockPanelModel>` must NOT be matched

The fix: match only when `<TagName` is preceded by whitespace, `=`, `"`, or
start-of-line:

```python
re.sub(r'(^|\s|=|\")<OldName(\s|>|/)', r'\1<NewName\2', content, flags=re.MULTILINE)
```

### RCL Root _Imports.razor

The RCL needs a root `_Imports.razor` with `@using` directives for its own
Domain/Services/Interop namespaces. Without this, Razor components in the
library can't resolve types from sibling folders.

### TypeScript Interop Paths

When moving TypeScript source into the RCL, update both:
- `package.json`: `"build:js"` script paths (relative to RCL root)
- `.csproj`: `WorkingDirectory="$(MSBuildProjectDirectory)"` in the MSBuild target
- `.gitignore`: Generated JS output paths

### Ci Format Check Must Use SDK Built-In Command

The `dotnet-format` global tool (`dotnet tool install -g dotnet-format`) is
deprecated — it conflicts with the built-in `dotnet format` command included
in .NET 6+ SDK. Using the global tool causes false-positive format failures on CI.

**Fix:** Remove the global tool install step. Use the SDK built-in command:

```yaml
# GitHub Actions — correct:
- name: Check formatting
  run: dotnet format style --verify-no-changes --verbosity diagnostic
```

```yaml
# GitHub Actions — wrong (deprecated):
- name: Install dotnet-format
  run: dotnet tool install -g dotnet-format
- name: Check formatting
  run: dotnet format --verify-no-changes --verbosity diagnostic
```

Local verification before pushing:

```sh
dotnet format style --verify-no-changes --verbosity diagnostic
# "已将 0 个文件格式化" = clean, ready to push
```

### .editorconfig for Blazor Projects

Create a root `.editorconfig` that distinguishes C#/Razor from config/web files:

```ini
root = true

[*.{cs,razor}]
indent_style = space
indent_size = 4

[*.{csproj,slnx,xml,json,yml,yaml,md,config}]
indent_style = space
indent_size = 2

[*.{ts,js,css,html}]
indent_style = space
indent_size = 2
```

Without this, `dotnet format` may apply inconsistent indentation across file types.

### .gitattributes for Line-Ending Consistency

Cross-platform CI (Windows + Linux) requires explicit line-ending rules:

```gitattributes
*.cs text eol=lf
*.razor text eol=lf
*.csproj text eol=lf
*.ts text eol=lf
*.js text eol=lf
*.css text eol=lf
*.json text eol=lf
```

Without LF enforcement, `dotnet format` on Linux CI will see every file as
\"changed\" due to CRLF→LF conversion during checkout.

### RCL Static Assets Require `_content/<AssemblyName>/` Prefix

Blazor serves RCL `wwwroot/` assets under `_content/{AssemblyName}/`. **Every**
reference to an RCL static file from outside the RCL MUST use this prefix. Missing
it produces 404 at runtime:

| Asset type | Wrong path | Correct path |
|------------|-----------|--------------|
| JS module import | `"./atlas/atlas.js"` | `"./_content/Atlas/atlas/atlas.js"` |
| CSS stylesheet | `"css/atlas.css"` | `"_content/Atlas/atlas.css"` |

Check ALL of these when a demo app can't load RCL assets:
1. `IJSRuntime.InvokeAsync<IJSObjectReference>("import", path)` calls in C#/Razor
2. `<link href="..." />` tags in `index.html`
3. Any other static file references (images, fonts)

### Scoped CSS Is Project-Local

Scoped CSS bundles (`{ProjectName}.styles.css`) are generated **per project** from
`.razor.css` sidecar files. Do NOT reference an RCL's scoped CSS from the demo app:

- `_content/Atlas/Atlas.styles.css` → **404** if Atlas RCL has no `.razor.css` files
- `Atlas.Demo.styles.css` → **correct** — this is the demo project's own scoped CSS

Only the project that owns the `.razor.css` files produces the corresponding
`.styles.css` bundle.

### ContentRegistry Owned by LayoutContext

When components resolve content keys at render time, the `ContentRegistry` must
be owned by a long-lived container (`LayoutContext`), not instantiated per
component per render:

```csharp
// BROKEN — empty registry every render, no keys registered:
var registry = new ContentRegistry();

// CORRECT — uses Context's pre-populated registry:
var registry = Context?.ContentRegistry ?? new ContentRegistry();
```

Pre-register demo/fallback components in `LayoutContext`'s constructor.
See `references/content-registry-wiring.md` for the full pattern.

## Reference

- `references/atlas-rename-map.md` — Complete before/after type rename map
  from XDocker → Atlas, including the Model-suffix disambiguation pass and
  the component tag fix regex.
- `references/content-registry-wiring.md` — LayoutContext + ContentRegistry
  wiring pattern: why `new ContentRegistry()` per-render fails and how to
  own it at the context level with pre-registered fallback components.
