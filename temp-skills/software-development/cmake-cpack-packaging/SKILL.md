---
name: cmake-cpack-packaging
description: "CMake/CPack and WiX/MSI packaging workflows — install rules, generator choice (CPack NSIS vs WiX 6 MSI vs CPack productbuild), shortcut/launcher behavior, Windows Installer standard directories (DesktopFolder, ProgramMenuFolder), release artifacts, and package smoke validation."
version: 1.3.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [CMake, CPack, NSIS, WiX, MSI, Packaging, Installer, Release, Windows, DesktopShortcut]
    related_skills: [github-pr-workflow, github-ci-debug, systematic-debugging]
---

# CMake / CPack / WiX Packaging

Use this skill when working on CMake install rules, CPack- or WiX-generated artifacts, Windows installers (NSIS `.exe` or MSI), release packaging workflows, package smoke tests, desktop/start-menu shortcuts, installer UX, or installed-layout runtime behavior.

If the project is Windows-only or treats the Windows installer as a first-class deliverable, **default to WiX/MSI** — see "Choosing between NSIS and WiX/MSI" below for the decision criteria. The NSIS sections below remain valid for projects that already chose NSIS, but they document a path with known escape and behavior traps.

## Choosing between NSIS and WiX/MSI

| Requirement | NSIS | WiX/MSI |
|---|---|---|
| Single-file `.exe` installer | ✅ Native | ✅ Native (or use Burn bundle) |
| Per-user vs per-machine shortcuts | ⚠ Manual `SetShellVarContext` | DesktopFolder resolves per-scope (perMachine→Public, perUser→user). User desktop from perMachine needs a deferred PowerShell CA. |
| PATH modification | ⚠ NSIS warns on PATH > 1024 chars | ✅ Or skip entirely; docs over PATH |
| Multi-language UI (zh-CN, ja, …) | ⚠ Translation text + button label drift | ✅ First-class via `.wxl` |
| Upgrade chain integrity | ⚠ Easy to break GUIDs | ✅ Strict, well-tested |
| Repair / modify install | ❌ | ✅ Native Windows Installer feature |
| Add/Remove Programs integration | ⚠ Manual registry | ✅ Automatic |
| CI build time | ~10 s NSIS, no extra deps | ~30 s WiX, needs `dotnet tool install wix` |
| CPack integration | ✅ One-line `cpack -G NSIS` | ⚠ Custom CMake target + `wix build` |
| Heat-style directory harvest | ❌ (removed in WiX 6 — use CMake `file(GLOB_RECURSE)`) | ✅ via custom CMake logic |

**When to switch from NSIS to WiX (decision rule):**

1. **Per-user desktop shortcut** is required and you need to ship it via `C:\Users\<user>\Desktop` (not Public Desktop). NSIS can do it with `SetShellVarContext current` + a pre-install section, but it conflicts with admin install. WiX `DesktopFolder` does this with no extra work.
2. **More than 2 PRs have been spent on the same installer bug** (shortcut missing, escape errors, PATH warning). The escape pipeline in NSIS is a closed system with known bugs; you will not escape them.
3. **You need upgrade reliability** (MAJOR upgrade or hotfix patching).
4. **The project will be maintained by more than one person** over years.

When you switch to WiX, plan to spend roughly half a day on initial setup and one PR per remaining NSIS-ism that needs porting. After that, shortcut / uninstall / upgrade behavior is all XML schema, not character escaping.

When NSIS is still the right answer:

- Single-file `.exe` is the only deliverable, you don't need Add/Remove Programs integration
- Your team is comfortable with NSIS-specific escape rules
- Build time matters more than correctness of uninstall behavior

## Core workflow

1. **Read packaging docs first**
   - Project instructions may require release/build/security docs before packaging changes.
   - Typical files: `docs/guides/cmake.md`, `docs/guides/release.md`, `SECURITY.md`, `AGENTS.md`.

2. **Map the install and package pipeline**
   - Inspect `CMakeLists.txt` for install/packaging includes and build options.
   - Inspect packaging modules such as `cmake/Packaging.cmake`.
   - Inspect release CI, usually `.github/workflows/release.yml`.
   - Inspect launcher/resources under `res/` or equivalent.

3. **Generate and inspect CPack config before guessing**
   - Run configure for the relevant preset.
   - Inspect generated `build/<preset>/CPackConfig.cmake` and, when possible, generated NSIS scripts under `_CPack_Packages/.../NSIS/`.
   - Treat generated config as the source of truth for what CPack actually captured.

4. **Build a tight validation loop**
   - For non-GUI packaging bugs, assert generated `CPackConfig.cmake` contains/omits expected `CPACK_*` variables.
   - For installed-layout bugs, use `cmake --install ... --prefix <tmp>` and run binaries/scripts from the installed tree.
   - For GUI installer text/shortcut behavior, document manual Windows verification steps in the PR.

## CPack include-order pitfall

`include(CPack)` captures the `CPACK_*` variables that exist at that point and writes package config files. Settings made **after** `include(CPack)` may not appear in `CPackConfig.cmake` and may not affect generated installers.

**Rule:** set all relevant package variables before `include(CPack)`, including:

- `CPACK_GENERATOR`
- `CPACK_PACKAGE_*`
- `CPACK_RESOURCE_FILE_*`
- `CPACK_NSIS_*`
- source package settings such as `CPACK_SOURCE_GENERATOR` / `CPACK_SOURCE_IGNORE_FILES`

Put `include(CPack)` at the end of the packaging module unless the project has a specific reason not to.

## CPack component system pitfall — silent empty installs

Setting `CPACK_COMPONENTS_ALL` switches CPack into component-based packaging. **Every `install()` command must then carry a `COMPONENT <name>` label.** Files from `install()` calls without `COMPONENT` go to the "Unspecified" component, which CPack hides by default (`CPACK_COMPONENT_UNSPECIFIED_HIDDEN TRUE`).

**Symptom:** the NSIS installer shows an empty component selection page, and after installation only `Uninstall.exe` exists in the install directory — no project files were installed.

**Root cause:** `CPACK_COMPONENTS_ALL runtime template devel` is set, but every `install()` command is missing `COMPONENT runtime` / `COMPONENT template` / `COMPONENT devel`. All files end up in the hidden Unspecified component and are silently skipped.

**Fix — option A (preferred for simple projects):** remove `CPACK_COMPONENTS_ALL` entirely. The installer becomes monolithic (no component page, installs everything).

**Fix — option B (when component selection is genuinely desired):** add `COMPONENT <name>` to every `install()` call:

```cmake
install(TARGETS cproject RUNTIME DESTINATION bin COMPONENT runtime)
install(DIRECTORY src/ DESTINATION share/template COMPONENT template)
install(TARGETS lib EXPORT targets DESTINATION lib COMPONENT devel)
```

**Detection:** after configure, check if `CPACK_COMPONENT_UNSPECIFIED_HIDDEN` is `TRUE` in `CPackConfig.cmake` and whether any of your `install()` commands carry components. If hidden is true and none of your rules have components, you have this bug.

### productbuild file-extension restrictions (macOS)

`CPACK_RESOURCE_FILE_LICENSE` and `CPACK_RESOURCE_FILE_README` feed into macOS `productbuild`, which only accepts `.rtfd`, `.rtf`, `.html`, and `.txt` extensions. Files with no extension (e.g. `LICENSE`) or `.md` extension (e.g. `README.md`) cause `CPack Error: Bad file extension specified`.

**Fix:** guard resource-file settings so they only affect NSIS, not productbuild:

```cmake
if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
    set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/README.md")
endif()
```

Or convert `LICENSE` to `LICENSE.txt` and `README.md` to a plain-text copy for packaging.

**Verification:**

```sh
cmake --preset ninja-release
grep -n "CPACK_GENERATOR\|CPACK_NSIS_MENU_LINKS\|CPACK_NSIS_MODIFY_PATH" build/ninja-release/CPackConfig.cmake
```

If a variable does not appear in `CPackConfig.cmake`, the generator will not reliably use it.

### Windows NSIS installer checklist

When changing NSIS behavior, verify these explicitly:

- `CPACK_NSIS_MENU_LINKS` appears in generated `CPackConfig.cmake` when Start Menu links are expected.
- Desktop shortcuts point to a stable launcher (`.bat` wrapper), not a fragile relative executable path.
- **Do NOT rely on `CPACK_CREATE_DESKTOP_LINKS` alone.** In CMake 4.3 the variable is read by `cmCPackNSISGenerator.cxx` (logged at line 556/561) but **never translated into NSIS code**. The generated `project.nsi` ends up with only Start Menu `CreateShortCut` lines — no desktop shortcut is ever emitted. This was confirmed empirically: `cpack --debug` shows the value is processed, but `_CPack_Packages/.../NSIS/project.nsi` contains zero `CreateShortCut $DESKTOP...` lines. If you set only `CPACK_CREATE_DESKTOP_LINKS`, no desktop shortcut will be created.
- **Use `CPACK_NSIS_CREATE_ICONS_EXTRA` for the desktop shortcut**, with the specific escape recipe in the "Verified-working escape sequence" section below. Keep `CPACK_NSIS_DELETE_ICONS_EXTRA` mirrored for uninstall cleanup.
- Always **inspect the generated `project.nsi`** (not just `CPackConfig.cmake`) to confirm a `CreateShortCut $DESKTOP\...` line actually landed at line ~718. `CPackConfig.cmake` being correct does not guarantee the NSIS substitution worked.
- Only use `CPACK_COMPONENTS_ALL` if every `install()` command carries a matching `COMPONENT` label; otherwise files go to the hidden Unspecified component.

### CPack NSIS template bug: `$INSTALL_DESKTOP` is read but never honored

In the CPack NSIS template (CMake 4.x), the "InstallToDesktop" checkbox value (`$INSTALL_DESKTOP`) is read at line 707 but **`@CPACK_NSIS_CREATE_ICONS@` at line 712 ignores it**. So:

- A user who unchecks "Create desktop shortcut" still gets one from `@CPACK_NSIS_CREATE_ICONS@`.
- A user who checks it cannot influence `CPACK_CREATE_DESKTOP_LINKS` behavior either — that mechanism also unconditionally creates the shortcut (when it works at all — see above).

**Consequence:** the desktop-shortcut checkbox in the NSIS wizard is purely cosmetic for CPack's built-in mechanisms. The only way to make it actually gate shortcut creation is to write a fully custom NSIS install section (which is exactly the path the escape-quoting problems block).

**Practical guidance:** document in release notes that the "Create desktop shortcut" checkbox is informational only. The real fix is to always create the shortcut unconditionally and rely on the user deleting it if unwanted, or to switch to a custom installer framework (WiX, Inno Setup) where checkbox behavior is fully under your control.

### Admin install → Desktop shortcut behavior (NSIS template timing)

CPack NSIS installers run `RequestExecutionLevel admin`. Both `.onInit` (install, line 921) and `un.onInit` (uninstall, line 762) call `SetShellVarContext all` for admin/power users — and `.onInit` runs **before** `Section "-Core installation"`, which is where `@CPACK_NSIS_CREATE_ICONS_EXTRA@` is substituted.

```text
NSIS template flow (CMake 4.x):
  921  Function .onInit                  ← install, runs first
  982    SetShellVarContext all          ← if UserInfo reports Admin
  ...
  655  Section "-Core installation"
  713    @CPACK_NSIS_CREATE_ICONS_EXTRA@ ← sees SetShellVarContext all already set
  771    SetShellVarContext all          ← (also re-asserted inside the section)
```

**Verified behavior** (NSIS 3.10, admin install via `Start-Process -Verb RunAs`):

- `$DESKTOP` resolves to **`C:\Users\Public\Desktop`** (Public Desktop), **not** the user's personal desktop
- Start Menu `$SMPROGRAMS` resolves to `C:\ProgramData\Microsoft\Windows\Start Menu\Programs` (All Users Start Menu)

**If you specifically need the user's personal desktop** (not Public), `SetShellVarContext current` is the only way — which means doing the CreateShortCut in the `un.onInit`/pre-install window, or reading `$USERPROFILE` via `ReadEnvStr` and appending `\Desktop` yourself. Both of these paths require either extra quoting (which collides with the CPack escaping bugs documented below) or a `.nsh` include file. If both user-personal and Public desktops are acceptable, the simple `$DESKTOP` form below is fine.

Debug checklist when "desktop shortcut missing":

1. Verify `$INSTDIR/bin/<launcher>` exists after install (component system may have silently skipped the install).
2. Inspect the shortcut's Properties → Target path for correctness.
3. **Check `C:\Users\Public\Desktop` first** for admin installs — this is the most common missed location.
4. Then check `C:\Users\<user>\Desktop` for non-admin / user-context installs.
5. Inspect `_CPack_Packages/.../NSIS/project.nsi` line ~718 to confirm the `CreateShortCut` line actually landed.

### PATH modification warning

`CPACK_NSIS_MODIFY_PATH ON` enables the "Add to PATH" checkbox but can trigger NSIS warning: `Warning! PATH too long installer unable to modify PATH`. NSIS has a ~1024-char limit on PATH manipulation. Machines with many tools installed frequently exceed this. If the product already provides Start Menu and Desktop shortcuts, PATH modification is optional — set `CPACK_NSIS_MODIFY_PATH OFF` to avoid the warning, and document manual PATH addition for CLI users.

### CMake string escaping for NSIS commands — verified recipe

The CPack NSIS generator has a known escaping pipeline that breaks naive attempts at quoting paths. Three independent escape steps are involved:

1. **CMake parses your `cmake/Packaging.cmake` source**: backslashes in `"..."` strings follow CMake quoted-argument rules. `\\` → `\`, `\"` → `"` (literally, but mixes poorly with the surrounding `"` delimiters).
2. **CPack writes the variable value into `CPackConfig.cmake`** as `set(VAR "...")`: CPack itself does NOT re-escape `\` in the value (so `\` arrives as `\\` in the file), and it does NOT escape `"` reliably (so a `"` in the value breaks the surrounding quotes — a known CPack bug).
3. **CMake re-parses `CPackConfig.cmake`** when CPack loads it: any `\X` sequence (where `X` is not a recognized escape) triggers `Invalid character escape '\X'`. So you must avoid `\C`, `\P`, `\S`, etc. in the value, even though the file's own quoting needs `\\` to mean one backslash.
4. **NSIS reads the substituted string**: `$VARNAME` substitutions happen inside command arguments; `/` is accepted in target paths but **NOT in shortcut paths** (the `.lnk` file path must use Windows backslashes).

**The single configuration that actually ships** (verified end-to-end: configure → build → cpack → install → shortcut exists with correct target → uninstall):

```cmake
# Each \\ in source → \ after CMake parse → \\ in CPackConfig.cmake →
# single \ after CMake re-parse → NSIS sees $DESKTOP\CProjectStandard.lnk.
# Critical: the shortcut path MUST use \ (NSIS CreateShortCut rejects /
# for the .lnk path). The target path can use either, but we use \ for symmetry.
set(CPACK_NSIS_CREATE_ICONS_EXTRA
    "CreateShortCut $DESKTOP\\CProjectStandard.lnk $INSTDIR\\bin\\run-wizard.bat")
set(CPACK_NSIS_DELETE_ICONS_EXTRA
    "Delete $DESKTOP\\CProjectStandard.lnk")
```

**Why each alternative fails** (recorded so the next person doesn't repeat the cycle):

| Pattern | Failure mode |
|---|---|
| `CPACK_CREATE_DESKTOP_LINKS "bin/foo"` only | CMake 4.3 reads the variable but emits no `CreateShortCut`. Zero desktop shortcut. |
| `"... \\\"$DESKTOP/foo\\\" ..."` (backslash-quote pairs) | CMake parses `\"` as a literal `"`, but CPack writes the value back with the `"` breaking the surrounding `set(... "...")` quoting. NSIS then sees a stray `"` in the middle of a command. |
| `[==[CreateShortCut "$DESKTOP/foo.lnk" "$INSTDIR/bin/foo"]==]` (bracket argument) | Same failure — CPack writes bracket-quoted values back as `"..."` with broken quote escaping. |
| `\\` instead of `\\\\` (single backslash in source) | CMake parses `\` as start of escape → `Invalid character escape '\C'`. |
| `/` in the `.lnk` shortcut path | NSIS `CreateShortCut` rejects forward slashes in the shortcut path (verified empirically — target works, shortcut does not). |
| `\` somewhere in the value (e.g. via `\\` escape after `${CMAKE_CURRENT_BINARY_DIR}`) | CPack serializes path components with `\\` in CPackConfig.cmake; CMake re-parse then errors on `\X` for some `X`. |
| `!include "/abs/path/to/foo.nsh"` | CPack escapes the inner `"` → NSIS sees `"\;"` in the include path → `could not find` error. |
| `!include foo.nsh` (no path) | Works **only if** `foo.nsh` is colocated with `project.nsi` in `_CPack_Packages/<arch>/NSIS/`. CPack gives you no hook to copy a file there — you'd need a cpack wrapper script that patches `project.nsi` after generation. |

**How to verify the escape worked** at each stage:

```sh
# After cmake configure:
grep "CREATE_ICONS_EXTRA\|DELETE_ICONS_EXTRA" build/ninja-release/CPackConfig.cmake
# Expect: set(CPACK_NSIS_CREATE_ICONS_EXTRA "CreateShortCut $DESKTOP\CProjectStandard.lnk $INSTDIR\bin\run-wizard.bat")
#         (two backslashes in the file — that's CMake's quoted-string form for one backslash)

# After cpack:
sed -n '715,720p' build/ninja-release/_CPack_Packages/win64/NSIS/project.nsi
# Expect: CreateShortCut $DESKTOP\CProjectStandard.lnk $INSTDIR\bin\run-wizard.bat
#         (one backslash — NSIS sees this directly)

# After install (admin install via Start-Process -Verb RunAs):
# Expect: C:\Users\Public\Desktop\CProjectStandard.lnk exists, target = $INSTDIR\bin\run-wizard.bat
```

### Do NOT use `!include` of .nsh files in CPACK_NSIS_* variables

Embedding `!include "${CMAKE_CURRENT_SOURCE_DIR}/res/foo.nsh"` into `CPACK_NSIS_CREATE_ICONS_EXTRA`, `CPACK_NSIS_DELETE_ICONS_EXTRA`, `CPACK_NSIS_EXTRA_INSTALL_COMMANDS`, or `CPACK_NSIS_EXTRA_UNINSTALL_COMMANDS` has been attempted many times and **consistently caused NSIS build failures** in real projects (e.g. 20+ PR cycle on `wubing7755/c-project-standard`). The pattern fails for one of these reasons:

- **CPack writes the value with `\"` serialization**: CMake quoted-argument rules in CPackConfig.cmake turn the include's `"..."` into `"\;"...` (backslash-quote mis-pairing). NSIS sees `!include: could not find: "\;C:/path/foo.nsh"`.
- **`!include foo.nsh` (no quotes, no path)**: Only works if `foo.nsh` is colocated with `project.nsi` in `_CPack_Packages/<arch>/NSIS/`. CPack provides no hook to copy a file there — you'd need a custom `cpack` wrapper script that patches `project.nsi` after CPack generates it but before makensis runs.
- **Path resolution mismatch**: The include path resolved at CMake-configure time may differ from where NSIS looks at compile time, especially when absolute paths contain spaces (`C:/Users/...`).

**Avoid this pattern.** Use `CPACK_NSIS_CREATE_ICONS_EXTRA` with the verified escape recipe above instead. If you need multi-line NSIS logic beyond a single `CreateShortCut`, switch installer technology (WiX, Inno Setup) or write a `cpack` wrapper script that runs `cpack` to generate `project.nsi`, then patches and invokes `makensis` itself.

### Verifying generated CPackConfig and project.nsi

Always inspect BOTH after configure:

```sh
grep "CREATE_ICONS_EXTRA\|DELETE_ICONS_EXTRA\|MENU_LINKS" build/ninja-release/CPackConfig.cmake
sed -n '710,720p' build/ninja-release/_CPack_Packages/win64/NSIS/project.nsi
```

`CPackConfig.cmake` being correct is necessary but not sufficient — you must also confirm `project.nsi` (the actual file NSIS compiles) contains a valid `CreateShortCut` line at the substitution point.

## Finish-page autorun, license text, and uninstall

- **Finish-page auto-run:** For scaffolding/setup wizards that modify files or ask questions, prefer **no auto-run**. Remove `CPACK_NSIS_MUI_FINISHPAGE_RUN` and provide Start Menu/Desktop shortcuts instead. Only enable auto-run for passive read-only launchers (e.g., opening README in a browser).

- **License page text:** NSIS bundled translations may be inconsistent between instruction text and button labels (e.g., Chinese says "我同意" but the button label is "我接受"). Override with `CPACK_NSIS_DEFINES` or remove the click-through license page if override is too brittle across NSIS versions.

- **Uninstall cleanup:** `CPACK_NSIS_DELETE_ICONS_EXTRA` must mirror `CPACK_NSIS_CREATE_ICONS_EXTRA` so uninstall removes all created shortcuts.

## Installed-layout launcher checks

Installer bugs often come from a mismatch between build-tree layout and install-tree layout.

Common pattern:

- Build tree: `build/<preset>/bin/tool.exe` can find source root by walking upward.
- Install tree: `bin/tool.exe` and `share/project-template/` are siblings, so walking upward from the executable cannot find the template root.

Fix patterns:

- Make launchers `cd` into the installed template/data directory before running the executable.
- Make the executable accept current working directory as a valid root before searching from `argv[0]`.
- Optionally support an explicit `--template-root` / environment variable for installed data.
- Test installed layout with `cmake --install` into a temporary prefix, not only from the build tree.

Example installed-layout smoke:

```sh
cmake --preset ninja-release
cmake --build --preset ninja-release
rm -rf build/installer-layout-test
cmake --install build/ninja-release --config Release --prefix build/installer-layout-test
cd build/installer-layout-test/share/<project-data-dir>
../../bin/<tool> MyProject --dry-run --yes
```

## Regression tests worth adding

For packaging changes, prefer small generated-config tests plus installed-layout smoke tests:

- Assert forbidden auto-run variables are absent.
- Assert required NSIS shortcut/menu variables are present.
- Assert installed launcher can run a dry-run command from the install prefix.
- Keep GUI-only checks in release docs/manual validation if they cannot be automated reliably.

**Windows-specific note:** when the project switches from CPack/NSIS to WiX/MSI, the
`CPackConfig.cmake` file is no longer generated on Windows (`include(CPack)` is
only called for Linux/macOS). Existing CPack-config validation tests that ran under
`if(WIN32)` must be flipped to `if(NOT WIN32)` to avoid a `FileNotFoundError` on
the missing `CPackConfig.cmake`.

### CPack config validation script pattern

```python
#!/usr/bin/env python3
"""Validate release-sensitive CPack settings."""
import re, sys
from pathlib import Path

def cmake_value(text, name):
    match = re.search(rf'^set\({re.escape(name)}\s+"(.*)"\)$', text, re.MULTILINE)
    return match.group(1) if match else None

# Key checks on non-Windows (where CPack is still in use):
# - CPACK_NSIS_MUI_FINISHPAGE_RUN absent (no auto-run)
# - CPACK_NSIS_MENU_LINKS present with expected launcher
# - CPACK_GENERATOR includes DEB;RPM;TGZ on Linux
```

Register in `cmake/Tests.cmake` behind `if(NOT WIN32)` (not `if(WIN32)` —
Windows now uses WiX/MSI and does not generate CPackConfig.cmake):

```cmake
if(NOT WIN32)
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    add_test(NAME cproject_cpack_config
        COMMAND ${Python3_EXECUTABLE}
            ${CMAKE_CURRENT_SOURCE_DIR}/scripts/check-cpack-config.py
            ${CMAKE_CURRENT_BINARY_DIR}/CPackConfig.cmake
    )
endif()
```

### Passing Windows paths from MSYS/bash to CMake

When running CMake from MSYS/git-bash, `${pwd}` produces Unix-style paths (`/c/Users/...`) that Ninja may not resolve. Use `cygpath -w`:

```sh
PREFIX="$(cygpath -w "$(pwd)/install")"
cmake -G Ninja -S tests/package_smoke -B build/package-smoke \
    -DCMAKE_PREFIX_PATH="$PREFIX"
```

This also applies to `CPROJECT_SOURCE_DIR` and other CMake variables that need Windows-native paths.

## References

- `references/windows-nsis-installer-ux.md` — condensed lessons from a Windows CProjectStandard installer investigation: license text mismatch, CPack include order, missing shortcuts, finish-page auto-run, and installed-layout root discovery.
- `references/cpack-config-check-script.md` — full CPack config validation script with CTest integration.
- `references/cmake-nsis-string-escaping.md` — four-stage escape pipeline (CMake source → CPackConfig → CMake re-parse → NSIS), table of every pattern that fails and why, and the verification commands for each stage.
- `references/cross-platform-c-portability.md` — C11 portability pitfalls: `S_ISDIR` vs `_S_IFDIR`, `getcwd` signature differences, `strcpy` clang-analyzer flags, `clang-format` in CI, `productbuild` file extension restrictions, and Windows console UTF-8 setup.
- `references/windows-console-utf8.md` — standalone recipe: set Windows console to UTF-8 with `__declspec(dllimport)` to avoid `<windows.h>` header conflicts.
- `references/windows-nsis-desktop-shortcut-empirical-investigation.md` — full transcript of the investigation that produced the recipe above: each escape pattern tested, what `cpack --debug` actually shows for `CPACK_CREATE_DESKTOP_LINKS`, the verified validation sequence (configure → cpack → install → check shortcut → uninstall → check cleanup), and the PR history it resolves.
- `references/wix-msi-build-integration.md` — WiX 6 build integration via CMake: `dotnet tool install wix`, UI extension discovery, the schema pitfalls removed in v6 (`SummaryCodepage`, `Win64` on Component, `<DirectoryRef><ComponentGroup>` nesting), `$(var.X)` preprocessor rules, and a working `cmake/PackagingMSI.cmake` skeleton.
- `references/cmake-glob-windows-pitfalls.md` — `file(GLOB_RECURSE)` requires a glob pattern (`dir/*`) — the directory path alone returns empty on Windows. `CONFIGURE_DEPENDS` works but the directory must already exist at configure time. Stale `.ninja_lock` after `wix.exe` crashes blocks rebuilds; clean it before re-running CMake.
- `references/wix-msi-desktop-shortcut-pattern.md` — minimal Shortcuts.wxs with static DesktopFolder shortcut, Start Menu entries, and per-user HKCU registry keys.
- `references/wix-msi-per-user-desktop-ca.md` — PowerShell deferred custom-action pattern: lands desktop shortcut on the current user's personal desktop from a perMachine MSI. Covers WixQuietExec64, SetProperty prefix rule, CustomActionRef, schema traps, and CMake staging of .ps1 files.

## WiX 6 MSI build integration (Windows-first projects)

When the decision is to switch from NSIS to WiX/MSI, the following pitfalls were all hit during a real migration and are listed here so the next attempt does not repeat the cycle. The full reference (with each failure's diagnostic message and fix) is in `references/wix-msi-build-integration.md`.

### Toolchain

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

The UI extension is **not auto-loaded**. Without `-ext path/to/WixToolset.UI.wixext.dll`, you get `WIX0200: unhandled extension element 'WixUI'`. CMake should detect the extension path automatically (see the `find_path` snippet in the reference) and pass `-ext` on every `wix build` invocation.

**CI shell pitfall:** on GitHub Actions Windows runners, use `shell: bash` for the WiX install step. The default `pwsh` shell loses `~/.dotnet/tools` from PATH after `dotnet tool install --global`. bash handles this correctly. Also append `$HOME/.dotnet/tools` to `$GITHUB_PATH` so subsequent steps see `wix`.

**Extension version pinning:** `wix extension add` without `--global` and without a version defaults to the **latest** (currently v7). Even with `/6.0.2` as a version suffix, without `--global` NuGet treats it as a minimum-version constraint and resolves to 7.0.0. v7 extensions produce `WIX6101: Could not find expected package root folder wixext6` when used with WiX 6. Always use both `--global` AND an explicit version: `wix extension add --global WixToolset.UI.wixext/6.0.2`.

### WiX 6 schema changes from v3

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

### CMake `file(GLOB_RECURSE)` pitfalls on Windows

Two non-obvious gotchas, both hit during the migration:

1. **`file(GLOB_RECURSE dir)` returns empty.** You must pass `dir/*` for it to enumerate recursively. The directory path alone is silently treated as a literal filename match.

2. **The directory must exist at configure time.** A glob on an empty (or missing) directory silently returns no results. If your MSI build runs `cmake --install` to populate a staging directory, the staging dir does not exist at the first configure — so the glob is empty and the generated `TemplateTree.wxs` ships zero components. Workaround patterns:

   - Run an `execute_process` of `cmake --install` during configure (avoid — runs before ninja's build files exist)
   - Write a sentinel file (`install-staging/.stamp`) and list it in `CONFIGURE_DEPENDS` so the next configure sees a fresh mtime and re-globs
   - List the staged files as `INSTALL_DEPENDS` of the WiX target, not as a configure-time glob

3. **Stale `.ninja_lock`** after a `wix.exe` crash blocks rebuilds with "Permission denied". Delete `build/<preset>/.ninja_lock` (and sometimes `build.ninja` itself) before re-running.

### Graceful WiX fallback for CI

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

### `list(SORT)` pitfall

CMake's `list(SORT)` does **not** support `COMPARE NATURAL` — only CMake 3.18+
supports `COMPARE` at all, and the allowed values are `STRING`, `FILE_BASENAME`,
and `NATURAL` (added in 3.18). `COMPARE NATURAL ORDER` is a syntax error. For
lexicographic version sorting of WiX extension paths, plain `list(SORT _paths)`
is sufficient since the version component (`6.0.2`) in the path sorts correctly
as a string.

### Cross-compiler static library pitfall

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

The working CMake skeleton (kept short here, full version in the reference):

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
# See references/wix-msi-build-integration.md for the GLOB_RECURSExml template.

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

### MSI icon (Explorer + Add/Remove Programs)

Without `<Icon>` + `ARPPRODUCTICON`, the `.msi` file shows the default Windows
generic icon. Add inside `<Package>`:

```xml
<Icon Id="AppIcon" SourceFile="$(var.CPROJECT.SourceDir)\res\cproject.ico" />
<Property Id="ARPPRODUCTICON" Value="AppIcon" />
```

The `SourceFile` path must be resolvable at `wix build` time. Use a WiX
preprocessor variable (`-d CPROJECT.SourceDir=...`) passed from CMake. The
icon file is embedded in the MSI binary — no separate `.ico` needed at runtime.

### Desktop shortcut (the whole reason for switching)

**For perMachine MSI (`Scope="perMachine"`):** `StandardDirectory Id="DesktopFolder"` resolves to `C:\Users\Public\Desktop` — the All Users / Public desktop. This is standard Windows Installer behavior; VS Code, Node.js, and Git for Windows all behave this way. If Public Desktop is acceptable, the static `<Shortcut>` element below is sufficient.

**For user's personal desktop** from a perMachine MSI: use a deferred PowerShell custom action (from `WixToolset.Util.wixext`, `WixQuietExec64`) with `Impersonate="yes"`. The full pattern — `.ps1` files, `SetProperty`, `CustomAction`, `CustomActionRef`, schema traps — is in `references/wix-msi-per-user-desktop-ca.md`.

Static shortcut (lands on Public Desktop for perMachine; user desktop for perUser):

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

The custom-action alternative path is `references/wix-msi-per-user-desktop-ca.md`.
No `SetShellVarContext`, no quoting dance. Replace 22 PRs of NSIS escape attempts with a single declarative XML fragment.
