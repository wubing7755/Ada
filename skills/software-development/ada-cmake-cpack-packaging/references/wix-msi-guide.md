# WiX 6 MSI Build Integration Guide

This reference covers the full NSIS→WiX migration path: toolchain setup, WiX 6 schema changes, CMake integration pitfalls, and desktop shortcut patterns. Everything below was encountered during a real migration and is documented here so the next attempt does not repeat the cycle.

See also `wix-msi-build-integration.md` (CMake skeleton), `wix-msi-desktop-shortcut-pattern.md` (static shortcuts), and `wix-msi-per-user-desktop-ca.md` (per-user desktop from perMachine).

## Toolchain

```sh
# Install once. WiX 7 charges an OSMF fee — pin to 6.x for OSS projects.
dotnet tool install --global wix --version 6.*
# CRITICAL: --global is required for version pinning. Without it, the /6.0.2
# suffix is treated as a minimum-version range and resolves to latest (7.0.0),
# which produces WIX6101 errors when used with WiX 6.
wix extension add --global WixToolset.UI.wixext/6.0.2
# Only needed if using the PowerShell CA pattern (per-user desktop shortcut):
wix extension add --global WixToolset.Util.wixext/6.0.2
```

The UI extension is **not auto-loaded**. Without `-ext path/to/WixToolset.UI.wixext.dll`, you get `WIX0200: unhandled extension element 'WixUI'`. CMake should detect the extension path automatically (see the `find_path` snippet in `wix-msi-build-integration.md`) and pass `-ext` on every `wix build` invocation.

**CI shell pitfall:** on GitHub Actions Windows runners, use `shell: bash` for the WiX install step. The default `pwsh` shell loses `~/.dotnet/tools` from PATH after `dotnet tool install --global`. bash handles this correctly. Also append `$HOME/.dotnet/tools` to `$GITHUB_PATH` so subsequent steps see `wix`.

**Extension version pinning:** `wix extension add` without `--global` and without a version defaults to the **latest** (currently v7). Even with `/6.0.2` as a version suffix, without `--global` NuGet treats it as a minimum-version constraint and resolves to 7.0.0. v7 extensions produce `WIX6101: Could not find expected package root folder wixext6` when used with WiX 6. Always use both `--global` AND an explicit version: `wix extension add --global WixToolset.UI.wixext/6.0.2`.

## WiX 6 Schema Changes from v3

The following v3 idioms are **errors in WiX 6** (silent or hard failure):

| v3 idiom | WiX 6 status | Fix |
|---|---|---|
| `Package/@SummaryCodepage` | `WIX0004: unexpected attribute` | Remove — codepage is implicit |
| `Component/@Win64="yes"` | `WIX0004: unexpected attribute` | Move to `<Package Win64="...">` |
| `<DirectoryRef Id="X"><ComponentGroup Id="Y">` | `WIX0005: ComponentGroup not allowed in DirectoryRef` | Put ComponentGroup at Fragment root; the Components themselves carry `Directory="X"` |
| `wix heat directory ...` | command not found | `heat` was removed in WiX 4+; use CMake `file(GLOB_RECURSE)` + `configure_file` instead |
| `<?define var.X = "..." ?>` (preprocessor namespace) | `WIX0150: undefined variable` | Use `<?define X = "..." ?>` — the `var.` prefix is only on the read side (`$(var.X)`) |
| `-dX=Y` (no space) | `WIX0118: unexpected argument` | Use `-d X=Y` (with space) — WiX 6 CLI requires space |
| `WixUI/@Description` | `WIX0004: unexpected attribute` | Use `<WixVariable Id="WixUIBannerString">` instead, or just drop it |

## CMake `file(GLOB_RECURSE)` Pitfalls on Windows

Two non-obvious gotchas, both hit during migration:

1. **`file(GLOB_RECURSE dir)` returns empty.** You must pass `dir/*` for it to enumerate recursively. The directory path alone is silently treated as a literal filename match.

2. **The directory must exist at configure time.** A glob on an empty (or missing) directory silently returns no results. If your MSI build runs `cmake --install` to populate a staging directory, the staging dir does not exist at the first configure — so the glob is empty and the generated `TemplateTree.wxs` ships zero components. Workaround patterns:

   - Run an `execute_process` of `cmake --install` during configure (avoid — runs before ninja's build files exist)
   - Write a sentinel file (`install-staging/.stamp`) and list it in `CONFIGURE_DEPENDS` so the next configure sees a fresh mtime and re-globs
   - List the staged files as `INSTALL_DEPENDS` of the WiX target, not as a configure-time glob

3. **Stale `.ninja_lock`** after a `wix.exe` crash blocks rebuilds with "Permission denied". Delete `build/<preset>/.ninja_lock` (and sometimes `build.ninja` itself) before re-running.

## Graceful WiX Fallback for CI

When the same `CMakeLists.txt` serves both regular CI (build + test, no packaging)
and release builds (needs WiX), `FATAL_ERROR` on missing WiX breaks the CI configure
step. Use a graceful degradation pattern:

```cmake
find_program(WIX_EXECUTABLE wix PATHS "$ENV{USERPROFILE}/.dotnet/tools")
if(NOT WIX_EXECUTABLE)
    message(WARNING "WiX 6 was not found — the 'msi' target will not be available.")
    set(CPROJECT_WIX_AVAILABLE OFF)
else()
    set(CPROJECT_WIX_AVAILABLE ON)
endif()

# Extension detection + target definitions are gated:
if(CPROJECT_WIX_AVAILABLE)
    # ... find UI/Util extensions, create install-staging/msi targets ...
endif()
```

This lets `cmake --preset ninja-release` on CI succeed without WiX, while the
release workflow (which installs WiX before configure) gets the full `msi` target.
The install rules (`cmake/InstallRules.cmake`) should be included **before** the
`if(CPROJECT_WIX_AVAILABLE)` guard so `cmake --install` still works for
package-smoke tests.

## `list(SORT)` Pitfall

CMake's `list(SORT)` does **not** support `COMPARE NATURAL` — only CMake 3.18+
supports `COMPARE` at all, and the allowed values are `STRING`, `FILE_BASENAME`,
and `NATURAL` (added in 3.18). `COMPARE NATURAL ORDER` is a syntax error. For
lexicographic version sorting of WiX extension paths, plain `list(SORT _paths)`
is sufficient since the version component (`6.0.2`) in the path sorts correctly
as a string.

## Cross-compiler Static Library Pitfall

When hand-listing files in WiX `<File Source="...">` elements, avoid referencing
compiler-specific static libraries (`.a` vs `.lib`). MSVC produces `.lib`, GCC/Clang
produce `.a`. On CI (which may use MSVC), a fixed reference to `libcproject_core.a`
causes `WIX0103: Cannot find the File file`. Instead, let consumers use `find_package`
to resolve the library — the CMake config files (`CProjectStandardConfig.cmake`,
`CProjectStandardTargets.cmake`) are compiler-agnostic and should be the only
files listed under the `lib/` directory.

**Symptom:** WiX build passes locally (GCC `.a`) but fails on GitHub Actions
Windows runner (MSVC `.lib`) with `WIX0103` at the static library entry.

**Fix:** Remove the static library `<File>` entry from `Files.wxs`. Keep only
the CMake package config files in the `LibComponents` group.

## CMake Build Skeleton

```cmake
# cmake/PackagingMSI.cmake
include_guard(GLOBAL)
include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/InstallRules.cmake")  # shared with CPack path

find_program(WIX_EXECUTABLE wix PATHS "$ENV{USERPROFILE}/.dotnet/tools")
find_path(_wix_ui_ext_path NAMES WixToolset.UI.wixext.dll
    PATHS "$ENV{LOCALAPPDATA}/wix/extensions" "${CMAKE_CURRENT_SOURCE_DIR}/.wix/extensions"
    PATH_SUFFIXES "WixToolset.UI.wixext")

# Stage install to a known location, then harvest template tree.
add_custom_target(install-staging
    COMMAND ${CMAKE_COMMAND} -E remove_directory installer-staging
    COMMAND ${CMAKE_COMMAND} --build . --target cproject_core cproject  # NOT `install`
    COMMAND ${CMAKE_COMMAND} --install . --prefix installer-staging
    COMMAND ${CMAKE_COMMAND} -E touch installer-staging/.stamp
    VERBATIM)

# Generate installer/generated/TemplateTree.wxs from staged files via configure_file.
# See wix-msi-build-integration.md for the GLOB_RECURSE+XML template.

add_custom_target(msi
    COMMAND ${WIX_EXECUTABLE} build
        installer/Product.wxs installer/Files.wxs installer/Shortcuts.wxs
        installer/generated/TemplateTree.wxs
        -arch x64
        -bindpath installer-staging
        -out msi/${PROJECT_NAME}-${PROJECT_VERSION}-win64.msi
        -d CPROJECT.Version=${PROJECT_VERSION}        # note: space, not =
        -d CPROJECT.SourceDir=${CMAKE_CURRENT_SOURCE_DIR}
        -d CPROJECT.StagingDir=${CMAKE_CURRENT_BINARY_DIR}/installer-staging
        -d CPROJECT.StagingDirTemplate=${CMAKE_CURRENT_BINARY_DIR}/installer-staging/share/c-project-standard
        -pdbtype none
        -ext ${_wix_ui_ext_path}
    DEPENDS install-staging installer/Product.wxs ...
    VERBATIM)
```

Then `cmake --build build/ninja-release --target msi` produces the `.msi`. CI does the same with `dotnet tool install wix --version 6.*` and `wix extension add WixToolset.UI.wixext` before configure.

## MSI Icon (Explorer + Add/Remove Programs)

Without `<Icon>` + `ARPPRODUCTICON`, the `.msi` file shows the default Windows
generic icon. Add inside `<Package>`:

```xml
<Icon Id="AppIcon" SourceFile="$(var.CPROJECT.SourceDir)\res\cproject.ico" />
<Property Id="ARPPRODUCTICON" Value="AppIcon" />
```

The `SourceFile` path must be resolvable at `wix build` time. Use a WiX
preprocessor variable (`-d CPROJECT.SourceDir=...`) passed from CMake. The
icon file is embedded in the MSI binary — no separate `.ico` needed at runtime.

## Desktop Shortcut (the whole reason for switching)

**For perMachine MSI (`Scope="perMachine"`):** `StandardDirectory Id="DesktopFolder"` resolves to `C:\Users\Public\Desktop` — the All Users / Public desktop. This is standard Windows Installer behavior; VS Code, Node.js, and Git for Windows all behave this way. If Public Desktop is acceptable, the static `<Shortcut>` element below is sufficient.

**For user's personal desktop** from a perMachine MSI: use a deferred PowerShell custom action (from `WixToolset.Util.wixext`, `WixQuietExec64`) with `Impersonate="yes"`. The full pattern — `.ps1` files, `SetProperty`, `CustomAction`, `CustomActionRef`, schema traps — is in `wix-msi-per-user-desktop-ca.md`.

### Static shortcut (lands on Public Desktop for perMachine; user desktop for perUser)

```xml
<!-- installer/Shortcuts.wxs -->
<Fragment>
  <ComponentGroup Id="ShortcutsComponents">
    <Component Id="Shortcut_Desktop"
               Guid="A1B2C3D4-2222-2222-2222-000000000001"
               Directory="DesktopFolder">       <!-- Public Desktop for perMachine; user desktop for perUser -->
      <Shortcut Id="Shortcut_Desktop_Wizard"
                Name="CProjectStandard"
                Target="[#File_bin_run_wizard]"  <!-- key-path reference, not a literal path -->
                WorkingDirectory="INSTALLDIR" />
      <RemoveFolder Id="RemoveDesktopFolder" Directory="DesktopFolder" On="uninstall" />
      <RegistryValue Root="HKCU" Key="Software\\CProjectStandard"
                     Name="DesktopShortcutInstalled" Type="integer" Value="1" KeyPath="yes" />
    </Component>
    <!-- Start Menu entries use Directory="ApplicationProgramsFolder" under ProgramMenuFolder. -->
  </ComponentGroup>
</Fragment>
```

The custom-action alternative path is `wix-msi-per-user-desktop-ca.md`.
No `SetShellVarContext`, no quoting dance. Replace 22 PRs of NSIS escape attempts with a single declarative XML fragment.
