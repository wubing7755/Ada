# VS 18 (2026) workload SDK import workaround for .NET 6 Blazor WASM

Verified on: VS Enterprise 2026 (18.6.2), .NET SDK 6.0.428, runtime 6.0.36, SkiaSharp 2.88.9.
Result: VS-style build (`-p:BuildingInsideVisualStudio=true`) links `dotnet.wasm` (20,435,455 bytes, 67 `SkiaSharp` symbol hits), CLI build unaffected, page loads with `mono_wasm_runtime_ready` and zero console errors.

## Exact csproj block (append before `</Project>`)

```xml
<PropertyGroup Condition="'$(BuildingInsideVisualStudio)' == 'true'">
  <UsingBrowserRuntimeWorkload>true</UsingBrowserRuntimeWorkload>
  <UsingBlazorAOTWorkloadManifest>true</UsingBlazorAOTWorkloadManifest>
  <DisableAutoWasmBuildApp>true</DisableAutoWasmBuildApp>
  <WasmGenerateAppBundle>false</WasmGenerateAppBundle>
  <_WasmSdkPacksRoot Condition="'$(DOTNET_ROOT)' != ''">$(DOTNET_ROOT)\packs</_WasmSdkPacksRoot>
  <_WasmSdkPacksRoot Condition="'$(_WasmSdkPacksRoot)' == ''">$(ProgramW6432)\dotnet\packs</_WasmSdkPacksRoot>
  <_WasmEmscriptenSdkProps>$(_WasmSdkPacksRoot)\Microsoft.NET.Runtime.Emscripten.2.0.23.Sdk.win-x64\6.0.36\Sdk\Sdk.props</_WasmEmscriptenSdkProps>
  <_WasmNodeSdkProps>$(_WasmSdkPacksRoot)\Microsoft.NET.Runtime.Emscripten.2.0.23.Node.win-x64\6.0.36\Sdk\Sdk.props</_WasmNodeSdkProps>
  <_WasmRuntimeSdkProps>$(_WasmSdkPacksRoot)\Microsoft.NET.Runtime.WebAssembly.Sdk\6.0.36\Sdk\AutoImport.props</_WasmRuntimeSdkProps>
  <_WasmRuntimeSdkTargets>$(_WasmSdkPacksRoot)\Microsoft.NET.Runtime.WebAssembly.Sdk\6.0.36\Sdk\Sdk.targets</_WasmRuntimeSdkTargets>
  <_WasmMonoTargetsSdkProps>$(_WasmSdkPacksRoot)\Microsoft.NET.Runtime.MonoTargets.Sdk\6.0.36\Sdk\Sdk.props</_WasmMonoTargetsSdkProps>
  <_WasmAotCrossSdkProps>$(_WasmSdkPacksRoot)\Microsoft.NETCore.App.Runtime.AOT.win-x64.Cross.browser-wasm\6.0.36\Sdk\Sdk.props</_WasmAotCrossSdkProps>
  <_WasmMonoTargetsSdkTargets>$(_WasmSdkPacksRoot)\Microsoft.NET.Runtime.MonoTargets.Sdk\6.0.36\Sdk\Sdk.targets</_WasmMonoTargetsSdkTargets>
</PropertyGroup>
<Import Project="$(_WasmEmscriptenSdkProps)" Condition="'$(BuildingInsideVisualStudio)' == 'true' and Exists('$(_WasmEmscriptenSdkProps)')" />
<Import Project="$(_WasmNodeSdkProps)" Condition="'$(BuildingInsideVisualStudio)' == 'true' and Exists('$(_WasmNodeSdkProps)')" />
<Import Project="$(_WasmRuntimeSdkProps)" Condition="'$(BuildingInsideVisualStudio)' == 'true' and Exists('$(_WasmRuntimeSdkProps)')" />
<Import Project="$(_WasmMonoTargetsSdkProps)" Condition="'$(BuildingInsideVisualStudio)' == 'true' and Exists('$(_WasmMonoTargetsSdkProps)')" />
<Import Project="$(_WasmAotCrossSdkProps)" Condition="'$(BuildingInsideVisualStudio)' == 'true' and Exists('$(_WasmAotCrossSdkProps)')" />
<Import Project="$(_WasmRuntimeSdkTargets)" Condition="'$(BuildingInsideVisualStudio)' == 'true' and Exists('$(_WasmRuntimeSdkTargets)')" />
<Import Project="$(_WasmMonoTargetsSdkTargets)" Condition="'$(BuildingInsideVisualStudio)' == 'true' and Exists('$(_WasmMonoTargetsSdkTargets)')" />
```

Version pins (`2.0.23`, `6.0.36`) must match the machine's runtime pack: read them from
`C:\Program Files\dotnet\packs\Microsoft.NET.Runtime.Emscripten.*.Sdk.win-x64\<ver>\` and
`...\Microsoft.NETCore.App.Runtime.Mono.browser-wasm\<ver>\`.

## Mechanism chain
- `sdk-manifests\6.0.400\microsoft.net.workload.mono.toolchain\WorkloadManifest.targets` derives `UsingBrowserRuntimeWorkload=true` when `RuntimeIdentifier=browser-wasm` AND (`RunAOTCompilation` or `WasmBuildNative` or non-Blazor project), then in an `ImportGroup` (condition `RuntimeIdentifier=browser-wasm and UsingBrowserRuntimeWorkload=true`) imports by SDK alias:
  1. `Microsoft.NET.Runtime.MonoTargets.Sdk.net6` Sdk.props
  2. `Microsoft.NET.Runtime.WebAssembly.Sdk.net6` Sdk.targets
  3. `Microsoft.NETCore.App.Runtime.AOT.Cross.net6.browser-wasm` Sdk.props
  4. `Microsoft.NET.Runtime.MonoTargets.Sdk.net6` Sdk.targets
- VS 18 MSBuild resolves only the plain emscripten manifest imports (`microsoft.net.workload.emscripten`); the `.net6`-aliased WASM/Mono imports fail silently, so `WasmApp` targets are undefined → `_BlazorWasmNativeForBuild` (6_0.targets, condition `UsingBrowserRuntimeWorkload==true`) never runs `WasmBuildApp` → no emcc link → runtime-pack `dotnet.wasm` copied to wwwroot.
- Each manually imported package provides one piece:
  - Emscripten Sdk.props → `EmscriptenSdkToolsPath` (+PATH prepends)
  - Emscripten Node Sdk.props → `EmscriptenNodeToolsPath`
  - WebAssembly.Sdk AutoImport.props → `WasmNativeWorkload=true`
  - MonoTargets Sdk.props → `JsonToItemsTaskFactoryTasksAssemblyPath` (task factory used by `ReadEmccProps` UsingTask)
  - AOT Cross Sdk.props → `MonoAotCrossCompiler` item (`mono-aot-cross.exe`)
  - WebAssembly.Sdk Sdk.targets → WasmApp props/targets (the link chain incl. `_WasmBuildNativeCore`)
  - MonoTargets Sdk.targets → `RuntimeComponentManifest.targets`

## Error cascade when pieces are missing (each missing import = next error)
1. Only Emscripten+Wasm imported: `_SetupEmscripten` → "Emscripten from the workload is missing some paths: $(EmscriptenNodeToolsPath)= ..." → add Node props.
2. Manual imports without `UsingBrowserRuntimeWorkload`: "WasmAssembliesToBundle item is empty. No assemblies to process" (WasmApp.targets `_BeforeWasmBuildApp`). Because `DisableAutoWasmBuildApp` is set by 6_0.targets AFTER the csproj-body import, `WasmBuildAppAfterThisTarget` wrongly defaults to `Build` and `WasmBuildApp` auto-fires without `_GatherWasmFilesToBuild` having run. Fix: set `UsingBrowserRuntimeWorkload=true` (so `_BlazorWasmNativeForBuild` → `_GatherWasmFilesToBuild` → `WasmBuildApp` in the right order) and `DisableAutoWasmBuildApp=true` BEFORE the imports.
3. "MSB4036: ReadEmccProps task not found" → import MonoTargets Sdk.props + Sdk.targets.
4. "Could not find AOT cross compiler at $(_MonoAotCrossCompilerPath)=" → import AOT Cross Sdk.props.
5. VS **Publish** (not Build) → `BLAZORSDK1002: Publishing with AOT enabled requires the .NET WebAssembly AOT workload to be installed` — `_EnsureWasmRuntimeWorkload` needs `UsingBlazorAOTWorkloadManifest=true`, which the workload manifest sets but VS never evaluates. Fix: add `<UsingBlazorAOTWorkloadManifest>true</UsingBlazorAOTWorkloadManifest>` to the block.
6. Done: "Compiling native assets with emcc. This may take a while ..." appears; `dotnet.wasm` ~20 MB with symbols. Build AND Publish both succeed.

## MSB4011 warnings
`WorkloadManifest.targets(23/24,5): warning MSB4011: cannot import again ... Emscripten ... Sdk.props` — expected and harmless (VS DOES import the emscripten manifest; only the aliased WASM/Mono SDKs fail). Treat as acceptable; do not chase them.

## Field check for a broken build (no build needed)
```bash
ls -la <proj>/bin/Debug/net6.0/wwwroot/_framework/dotnet.wasm
grep -c SkiaSharp <proj>/bin/Debug/net6.0/wwwroot/_framework/dotnet.wasm   # >0 = linked
```
Compare size/timestamp with the runtime-pack original under
`C:\Program Files\dotnet\packs\Microsoft.NETCore.App.Runtime.Mono.browser-wasm\<ver>\runtimes\browser-wasm\native\dotnet.wasm`.
An identical file means the build served the unlinked runtime pack.

## Session transcript highlights (real project, 2026-08)
- Symptom: `DllNotFoundException: libSkiaSharp` at `SkiaSharp.SKImageInfo..cctor()`, thrown from `<ComponentClass>..ctor()` (line 16, `new SKImageInfo(...)`). Second error "No element is currently associated with component 52" was a renderer cascade.
- The WASM csproj already had `<WasmBuildNative>true</WasmBuildNative>` (added 19:31, file mtime). CLI build linked fine; VS build overwrote wwwroot with 2.4 MB runtime-pack `dotnet.wasm` (mtime 2024-10-15).
- Misleading artifact: `bin/Debug/net6.0/dotnet.wasm` (2.4 MB, old) vs served `wwwroot/_framework/dotnet.wasm` (20.4 MB after CLI link). Always check the served path.
- Follow-up: after the link fix, "deployed app has no styles" — user ran the VS **Build** output (`bin/.../wwwroot`) on a real machine; `_content/<Pkg>/<path>.css` was absent because Build never copies package static assets (only Publish does). VS Publish then surfaced `BLAZORSDK1002` until `UsingBlazorAOTWorkloadManifest=true` was added. User chose to keep the native + workaround route (not the SVG refactor).
