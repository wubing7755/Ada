# WiX 6 MSI Build Integration

A condensed record of the WiX 6 integration path that replaced CPack/NSIS in a Windows-first C project. Each pitfall below was hit during the migration and is documented with the exact diagnostic message that surfaced it.

## Toolchain

```sh
# WiX 7+ charges an OSMF maintenance fee — pin to 6.x for OSS projects.
dotnet tool install --global wix --version 6.*
# CRITICAL: --global is required for version pinning.
# Without --global, `/6.0.2` is treated as a minimum-version NuGet range
# and resolves to latest (7.0.0), producing WIX6101 errors at build time.
wix extension add --global WixToolset.UI.wixext/6.0.2
```

**Why `--global` matters for version pinning:**

`wix extension add` without `--global` and without a version suffix defaults to latest (currently v7). Even with `/6.0.2` as a version suffix, without `--global` NuGet treats it as a minimum-version constraint and resolves to 7.0.0. v7 extensions produce:

```
WIX6101: Could not find expected package root folder wixext6.
Ensure WixToolset.UI.wixext/7.0.0 is compatible with WiX v6.
```

Always use BOTH `--global` AND an explicit version: `wix extension add --global WixToolset.UI.wixext/6.0.2`.

**GitHub Actions Windows runner note:** use `shell: bash` for the WiX install step. The default `pwsh` shell loses `~/.dotnet/tools` from PATH after `dotnet tool install --global`. Append `$HOME/.dotnet/tools` to `$GITHUB_PATH` so subsequent steps see the `wix` command.

Extensions install under `.wix/extensions/<name>/<ver>/wixext6/<name>.dll` (project-relative) or `%LOCALAPPDATA%\wix\extensions\` (when run from a directory without write access). CMake should detect both paths.

## Required `-ext` for WixUI

The UI extension is **not auto-loaded**. Without `-ext path/to/WixToolset.UI.wixext.dll`, you get:

```
WIX0200: The Package element contains an unhandled extension element 'WixUI'.
Please ensure that the extension for elements in the
'http://wixtoolset.org/schemas/v4/wxs/ui' namespace has been provided.
```

Pass it on every `wix build`:

```cmake
-ext "${CMAKE_CURRENT_SOURCE_DIR}/.wix/extensions/WixToolset.UI.wixext/6.0.2/wixext6/WixToolset.UI.wixext.dll"
```

Or detect at configure time with `find_path(_wix_ui_ext_path NAMES WixToolset.UI.wixext.dll PATHS "$ENV{LOCALAPPDATA}/wix/extensions" "${CMAKE_CURRENT_SOURCE_DIR}/.wix/extensions" PATH_SUFFIXES "WixToolset.UI.wixext")` and pass the result via `-ext`.

## WiX 6 schema changes from v3 (every one of these was a hard failure during migration)

| v3 idiom | WiX 6 diagnostic | Fix |
|---|---|---|
| `<Package SummaryCodepage="1252">` | `WIX0004: unexpected attribute` | Remove — codepage is implicit |
| `<Component Win64="yes">` | `WIX0004: unexpected attribute` | Move to `<Package Win64="...">` |
| `<DirectoryRef Id="X"><ComponentGroup Id="Y">` | `WIX0005: ComponentGroup not allowed in DirectoryRef` | Put ComponentGroup at Fragment root; each Component carries `Directory="X"` |
| `wix heat directory ...` | `WIX0118: unexpected argument 'heat'` | Removed in WiX 4+ — use CMake `file(GLOB_RECURSE)` + `configure_file` instead |
| `<?define var.X = "..." ?>` | `WIX0150: undefined preprocessor variable '$(var.X)'` | Use `<?define X = "..." ?>` — `var.` is only on the read side |
| `-dX=Y` (no space) | `WIX0118: unexpected argument '-dX=Y'` | Use `-d X=Y` (with space) |
| `<WixUI Description="...">` | `WIX0004: unexpected attribute` | Override via `<WixVariable Id="WixUIBannerString">` or drop |

## preprocessor var passing from CMake

CMake's `VERBATIM` quoting is fragile with WiX preprocessor vars. Use the unquoted form so `-d` receives a plain `X=value` token (not `"X=value"`):

```cmake
add_custom_target(msi
    COMMAND ${WIX_EXECUTABLE} build
        ...
        -d CPROJECT.Version=${PROJECT_VERSION}
        -d CPROJECT.SourceDir=${CMAKE_CURRENT_SOURCE_DIR}
        -d CPROJECT.StagingDir=${CMAKE_CURRENT_BINARY_DIR}/installer-staging
        -d CPROJECT.StagingDirTemplate=${CMAKE_CURRENT_BINARY_DIR}/installer-staging/share/c-project-standard
        -pdbtype none
        -ext ${_wix_ui_ext_path}
    VERBATIM)
```

`PROJECT_VERSION=0.1.0` contains no spaces, so VERBATIM does not quote it. If a future version contains a space, use list-form args and rely on shell argument splitting.

## `heat` replacement via CMake

WiX 6 removed `heat`. The replacement pattern is CMake `file(GLOB_RECURSE)` followed by `configure_file` to render `<Component>` lines. Two gotchas specific to this:

```cmake
# 1. MUST include a glob pattern (e.g. "/*"). A bare directory returns empty.
file(GLOB_RECURSE _template_files CONFIGURE_DEPENDS "${CPROJECT_STAGING_DIR}/*")

# 2. The directory must already exist at configure time. If you populate it
#    via `cmake --install` in a build target, the first configure sees an
#    empty/missing directory. Workarounds:
#    a. Run execute_process(cmake --install) during configure — fragile,
#       because ninja build files don't exist yet on a fresh checkout.
#    b. Use a sentinel file (installer-staging/.stamp) touched by the
#       install-staging target and listed in CONFIGURE_DEPENDS, so the next
#       configure sees a fresh mtime and re-globs.
#    c. Build the file list at build time instead of configure time, using
#       add_custom_command(OUTPUT generated.wxs COMMAND cmake -P script).
```

A working template shape:

```cmake
set(_wxs_body "")
foreach(_f IN LISTS _template_files)
    file(RELATIVE_PATH _rel "${CPROJECT_STAGING_DIR}" "${_f}")
    string(REGEX REPLACE "[\\\\/ .]" "_" _id "${_rel}")
    file(SHA512 _sha "${_f}")
    string(SUBSTRING "${_sha}" 0 12 _hex)
    # Stable Component GUID from file path hash — keeps upgrade chains intact.
    set(_guid "B1B2B3B4-${_hex:0:4}-${_hex:4:4}-${_hex:8:4}-${_hex:12:12}")
    set(_wxs_body "${_wxs_body}      <Component Id=\"Comp_${_id}\" Guid=\"${_guid}\" Directory=\"INSTALLDIR_share_template\"><File Id=\"File_${_id}\" Source=\"\$(var.CPROJECT.StagingDirTemplate)\\${_rel}\" KeyPath=\"yes\" /></Component>\n")
endforeach()
file(WRITE "${_out}" "<?xml version=\"1.0\" encoding=\"utf-8\"?><Wix xmlns=\"http://wixtoolset.org/schemas/v4/wxs\"><Fragment><ComponentGroup Id=\"TemplateTreeComponents\">${_wxs_body}</ComponentGroup></Fragment></Wix>")
```

## install-staging target design

The target that populates the staging directory needs three things:

1. Build the install prerequisites (cproject_core, generated headers) — but **not** the `install` target itself, which would write to `CMAKE_INSTALL_PREFIX` (e.g. `C:\Program Files (x86)\CProjectStandard`) and require admin.
2. Run `cmake --install . --prefix installer-staging`.
3. Touch a sentinel file (`installer-staging/.stamp`) so the configure-time `CONFIGURE_DEPENDS` glob notices the directory was just populated.

```cmake
add_custom_target(install-staging
    COMMAND ${CMAKE_COMMAND} -E remove_directory installer-staging
    COMMAND ${CMAKE_COMMAND} --build . --target cproject_core cproject  # NOT `install`
    COMMAND ${CMAKE_COMMAND} --install . --prefix installer-staging
    COMMAND ${CMAKE_COMMAND} -E touch installer-staging/.stamp
    VERBATIM)
```

## Stale ninja lock after `wix.exe` crash

A `wix.exe` crash (or a Windows process holding the file) leaves `.ninja_lock` populated. Next build fails with:

```
ninja: error: failed recompaction: Permission denied
ninja: error: rebuilding 'build.ninja': subcommand failed
```

Fix: delete `build/<preset>/.ninja_lock` (sometimes also `build.ninja`) before re-running. If the lock recurs, check for stray `msiexec.exe` or `wix.exe` processes in Task Manager — they sometimes survive installer test runs.

## Full working target skeleton

```cmake
add_custom_target(msi
    COMMAND ${WIX_EXECUTABLE} build
        "${CPROJECT_INSTALLER_DIR}/Product.wxs"
        "${CPROJECT_INSTALLER_DIR}/Files.wxs"
        "${CPROJECT_INSTALLER_DIR}/Shortcuts.wxs"
        "${CMAKE_CURRENT_BINARY_DIR}/installer/generated/TemplateTree.wxs"
        -arch x64
        -bindpath "${CMAKE_CURRENT_BINARY_DIR}/installer-staging"
        -out "${CPROJECT_MSI_PATH}"
        -d CPROJECT.Version=${PROJECT_VERSION}
        -d CPROJECT.SourceDir=${CMAKE_CURRENT_SOURCE_DIR}
        -d CPROJECT.StagingDir=${CMAKE_CURRENT_BINARY_DIR}/installer-staging
        -d CPROJECT.StagingDirTemplate=${CMAKE_CURRENT_BINARY_DIR}/installer-staging/share/c-project-standard
        -pdbtype none
        -ext "${_wix_ui_ext_path}"
    DEPENDS install-staging
            "${CPROJECT_INSTALLER_DIR}/Product.wxs"
            "${CPROJECT_INSTALLER_DIR}/Files.wxs"
            "${CPROJECT_INSTALLER_DIR}/Shortcuts.wxs"
            "${CPROJECT_INSTALLER_DIR}/License.rtf"
    COMMENT "Building ${CPROJECT_MSI_FILENAME}"
    VERBATIM)
```

## License file format

`WixUILicenseRtf` requires a real RTF (not plain text). Minimal RTF that renders LICENSE content without formatting:

```rtf
{\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang1033
{\fonttbl{\f0\fnil\fcharset0 Calibri;}}
{\colortbl;\red0\green0\blue0;}
\viewkind4\uc1\pard\f0\fs22 <LICENSE_CONTENT_HERE>}
```

For non-ASCII text in the license (e.g. Chinese), escape each non-ASCII byte as `\uN?` where `N` is the codepoint. The `?` is a placeholder for older readers; modern MSI ignores it.