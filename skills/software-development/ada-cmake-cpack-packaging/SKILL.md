---
name: ada-cmake-cpack-packaging
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

## Overview

This skill is the definitive reference for CMake/CPack packaging and Windows installer generation, born from a real migration that survived 20+ PR cycles of escape-character debugging. It covers the full pipeline: CMake install rules, CPack generator choice (NSIS vs WiX 6 MSI vs productbuild), CPack include-order and component-system pitfalls, Windows NSIS escape-character recipe (the single verified configuration that actually ships), installer UX (desktop shortcuts, Start Menu links, PATH modification, finish-page auto-run), installed-layout launcher behavior, and regression tests for packaging config. The skill also documents a complete WiX 6 MSI migration path with every schema change from v3, `file(GLOB_RECURSE)` pitfalls on Windows, graceful CI fallback, and per-user desktop shortcut patterns via PowerShell deferred custom actions.

The core lesson: CPack NSIS has a four-stage escape pipeline (CMake source → CPackConfig.cmake → CMake re-parse → NSIS substitution) where every naive quoting approach fails in a different way. The verified recipe uses quadruple-backslash escaping and explicitly avoids `!include` of `.nsh` files. When NSIS becomes unmaintainable, the decision framework guides the switch to WiX/MSI.

## When to Use

Use when:
- Setting up CMake install rules for a C/C++ project with `install(TARGETS ...)`, `install(DIRECTORY ...)`, or `install(FILES ...)`
- Generating Windows installers via CPack (NSIS `.exe`) or WiX 6 (MSI)
- Debugging missing desktop shortcuts, Start Menu entries, or silent empty installs in CPack-generated installers
- Implementing per-user desktop shortcuts from a per-machine MSI installer
- Adding or modifying CPack NSIS variables (`CPACK_NSIS_MENU_LINKS`, `CPACK_NSIS_CREATE_ICONS_EXTRA`, `CPACK_NSIS_MODIFY_PATH`, etc.)
- Validating CPack packaging config with CTest regression tests
- Migrating from CPack NSIS to WiX 6 MSI
- Testing installed-layout behavior (launcher working directory, template/data discovery)
- Handling CPack component-system pitfalls (silent empty installs from Unspecified component)
- Cross-platform packaging (NSIS on Windows, DEB/RPM/TGZ on Linux, productbuild on macOS)

Do **not** use for: configuring CI runners (use GitHub Actions docs), writing application code, or general CMake build system design (use CMake documentation).

## Choosing between NSIS and WiX/MSI

| Requirement | NSIS | WiX/MSI |
|---|---|---|
| Single-file `.exe` installer | ✅ Native | ✅ Native (or use Burn bundle) |
| Per-user vs per-machine shortcuts | ⚠ Manual `SetShellVarContext` | DesktopFolder resolves per-scope. User desktop from perMachine needs a deferred PowerShell CA. |
| PATH modification | ⚠ NSIS warns on PATH > 1024 chars | ✅ Or skip entirely |
| Multi-language UI (zh-CN, ja, …) | ⚠ Translation text + button label drift | ✅ First-class via `.wxl` |
| Upgrade chain integrity | ⚠ Easy to break GUIDs | ✅ Strict, well-tested |
| Repair / modify install | ❌ | ✅ Native Windows Installer feature |
| Add/Remove Programs integration | ⚠ Manual registry | ✅ Automatic |
| CI build time | ~10 s NSIS, no extra deps | ~30 s WiX, needs `dotnet tool install wix` |
| CPack integration | ✅ One-line `cpack -G NSIS` | ⚠ Custom CMake target + `wix build` |

**When to switch from NSIS to WiX (decision rule):**

1. **Per-user desktop shortcut** is required and you need to ship it to `C:\Users\<user>\Desktop` (not Public Desktop). NSIS can do it with `SetShellVarContext current` but conflicts with admin install. WiX `DesktopFolder` does this with no extra work.
2. **More than 2 PRs have been spent on the same installer bug** (shortcut missing, escape errors, PATH warning). The escape pipeline in NSIS is a closed system with known bugs; you will not escape them.
3. **You need upgrade reliability** (MAJOR upgrade or hotfix patching).
4. **The project will be maintained by more than one person** over years.

When you switch to WiX, budget ~½ day for initial setup and one PR per remaining NSIS-ism that needs porting. After that, shortcut / uninstall / upgrade behavior is all declarative XML schema, not character escaping. See `references/wix-msi-guide.md` for the full migration reference.

**When NSIS is still the right answer:** single-file `.exe` is the only deliverable, you don't need Add/Remove Programs integration, your team is comfortable with NSIS-specific escape rules, and build time matters more than correctness of uninstall behavior.

## Core workflow

1. **Read packaging docs first** — project instructions may require release/build/security docs before packaging changes. Typical files: `docs/guides/cmake.md`, `docs/guides/release.md`, `SECURITY.md`, `AGENTS.md`.

2. **Map the install and package pipeline** — inspect `CMakeLists.txt` for install/packaging includes and build options. Inspect packaging modules such as `cmake/Packaging.cmake`. Inspect release CI, usually `.github/workflows/release.yml`. Inspect launcher/resources under `res/` or equivalent.

3. **Generate and inspect CPack config before guessing** — run configure for the relevant preset. Inspect generated `build/<preset>/CPackConfig.cmake` and, for NSIS, `_CPack_Packages/.../NSIS/project.nsi`. Treat generated config as the source of truth for what CPack actually captured.

4. **Build a tight validation loop** — for non-GUI packaging bugs, assert generated `CPackConfig.cmake` contains/omits expected `CPACK_*` variables. For installed-layout bugs, use `cmake --install ... --prefix <tmp>` and run from the installed tree. For GUI installer behavior, document manual Windows verification steps in the PR.

## Pitfall 1: CPack include-order

`include(CPack)` captures the `CPACK_*` variables that exist at that point and writes package config files. Settings made **after** `include(CPack)` may not appear in `CPackConfig.cmake` and may not affect generated installers.

**Rule:** set all relevant package variables before `include(CPack)`:
- `CPACK_GENERATOR`, `CPACK_PACKAGE_*`, `CPACK_RESOURCE_FILE_*`
- `CPACK_NSIS_*`, `CPACK_SOURCE_GENERATOR`, `CPACK_SOURCE_IGNORE_FILES`

Put `include(CPack)` at the end of the packaging module unless the project has a specific reason not to.

**Verification:**
```sh
cmake --preset ninja-release
grep -n "CPACK_GENERATOR\|CPACK_NSIS_MENU_LINKS\|CPACK_NSIS_MODIFY_PATH" build/ninja-release/CPackConfig.cmake
```

If a variable does not appear in `CPackConfig.cmake`, the generator will not reliably use it.

> **macOS note:** `CPACK_RESOURCE_FILE_LICENSE` / `CPACK_RESOURCE_FILE_README` feed into `productbuild`, which only accepts `.rtfd`, `.rtf`, `.html`, `.txt`. Files with no extension (e.g. `LICENSE`) or `.md` cause `CPack Error: Bad file extension specified`. Guard with `if(CMAKE_SYSTEM_NAME STREQUAL "Windows")` or convert to accepted extensions.

## Pitfall 2: CPack component system — silent empty installs

Setting `CPACK_COMPONENTS_ALL` switches CPack into component-based packaging. **Every `install()` command must then carry a `COMPONENT <name>` label.** Files from `install()` without `COMPONENT` go to the "Unspecified" component, which CPack hides by default (`CPACK_COMPONENT_UNSPECIFIED_HIDDEN TRUE`).

**Symptom:** the NSIS installer shows an empty component selection page, and after installation only `Uninstall.exe` exists in the install directory — no project files were installed.

**Root cause:** `CPACK_COMPONENTS_ALL runtime template devel` is set, but every `install()` command is missing `COMPONENT runtime` / `COMPONENT template` / `COMPONENT devel`. All files end up in the hidden Unspecified component and are silently skipped.

**Fix A (preferred for simple projects):** remove `CPACK_COMPONENTS_ALL` entirely. The installer becomes monolithic (no component page, installs everything).

**Fix B (when component selection is genuinely desired):** add `COMPONENT <name>` to every `install()` call:
```cmake
install(TARGETS cproject RUNTIME DESTINATION bin COMPONENT runtime)
install(DIRECTORY src/ DESTINATION share/template COMPONENT template)
install(TARGETS lib EXPORT targets DESTINATION lib COMPONENT devel)
```

**Detection:** after configure, check if `CPACK_COMPONENT_UNSPECIFIED_HIDDEN` is `TRUE` in `CPackConfig.cmake` and whether any of your `install()` commands carry components. If hidden is true and none of your rules have components, you have this bug.

## Common NSIS traps (summary)

NSIS via CPack has known escape-quoting and behavior bugs. The full escape pipeline (CMake source → CPackConfig serialization → CMake re-parse → NSIS substitution), verified recipe, and failure-mode table are in `references/cmake-nsis-string-escaping.md`. Key points for quick reference:

- **`CPACK_CREATE_DESKTOP_LINKS` alone emits no `CreateShortCut`** — the variable is read by CMake 4.3's `cmCPackNSISGenerator.cxx` but never translated into NSIS code. Use `CPACK_NSIS_CREATE_ICONS_EXTRA` with the verified `\\\\` escape recipe. Keep `CPACK_NSIS_DELETE_ICONS_EXTRA` mirrored for uninstall cleanup.
- **Do NOT embed `!include` of `.nsh` files** in any `CPACK_NSIS_*` variable — CPack's serialization breaks the quoting. NSIS sees `\"\;"` in the include path and fails with `could not find`.
- **Desktop-shortcut checkbox is cosmetic** — the NSIS template reads `$INSTALL_DESKTOP` but `@CPACK_NSIS_CREATE_ICONS@` ignores it. Document in release notes.
- **Admin installs land on Public Desktop** — `$DESKTOP` resolves to `C:\Users\Public\Desktop`, not the user's personal desktop. Check both locations when debugging missing shortcuts.
- **PATH modification** — `CPACK_NSIS_MODIFY_PATH ON` triggers `Warning! PATH too long` when machine PATH exceeds ~1024 chars. Set `OFF` if Start Menu/Desktop shortcuts already exist.
- **Finish-page auto-run** — remove `CPACK_NSIS_MUI_FINISHPAGE_RUN` for scaffolding/setup wizards. Only enable for passive read-only launchers.

After any NSIS change, always inspect **both** `CPackConfig.cmake` and the generated `project.nsi` — `CPackConfig.cmake` being correct does not guarantee the NSIS substitution landed:

```sh
grep "CREATE_ICONS_EXTRA\|DELETE_ICONS_EXTRA\|MENU_LINKS" build/ninja-release/CPackConfig.cmake
sed -n '710,720p' build/ninja-release/_CPack_Packages/win64/NSIS/project.nsi
```

## Installed-layout launcher checks

Installer bugs often come from a mismatch between build-tree layout and install-tree layout:

- Build tree: `build/<preset>/bin/tool.exe` can find source root by walking upward.
- Install tree: `bin/tool.exe` and `share/project-template/` are siblings, so walking upward from the executable cannot find the template root.

**Fix patterns:** make launchers `cd` into the installed template/data directory before running the executable; make the executable accept current working directory as a valid root before searching from `argv[0]`; optionally support `--template-root` / env var; test with `cmake --install` into a temporary prefix.

```sh
cmake --preset ninja-release && cmake --build --preset ninja-release
cmake --install build/ninja-release --config Release --prefix build/installer-layout-test
cd build/installer-layout-test/share/<project-data-dir>
../../bin/<tool> MyProject --dry-run --yes
```

## Verification Checklist

After packaging changes, run:

1. **CPack config integrity:**
   ```sh
   grep "CPACK_GENERATOR\|MENU_LINKS\|CREATE_ICONS_EXTRA" build/<preset>/CPackConfig.cmake
   ```

2. **NSIS script inspection** (Windows NSIS only) — confirm `CreateShortCut` lines landed:
   ```sh
   sed -n '710,720p' build/<preset>/_CPack_Packages/win64/NSIS/project.nsi
   ```

3. **Installed-layout smoke:** install to temp prefix and run the launcher from the installed tree (see above).

4. **Desktop shortcut (Windows):** check `C:\Users\Public\Desktop\` for admin installs; check user desktop for per-user installs. Verify shortcut Properties → Target path is correct.

5. **Uninstall cleanup:** uninstall and confirm all shortcuts are removed; no orphaned files in `$INSTDIR`.

## Common Pitfalls

- **Setting CPACK_* variables after `include(CPack)`.** CPack captures variables at the point of `include(CPack)`. Any variable set afterward will not appear in `CPackConfig.cmake` and will not affect generated installers. Always set all `CPACK_NSIS_*`, `CPACK_PACKAGE_*`, and `CPACK_RESOURCE_FILE_*` variables before `include(CPack)`.
- **Using `CPACK_COMPONENTS_ALL` without `COMPONENT` labels on `install()` commands.** Files from unlabeled `install()` calls go to the hidden Unspecified component and are silently skipped. Either remove `CPACK_COMPONENTS_ALL` or add `COMPONENT <name>` to every `install()` command.
- **Relying on `CPACK_CREATE_DESKTOP_LINKS` alone for desktop shortcuts.** CMake 4.3 reads the variable but never emits `CreateShortCut` into the NSIS script. Use `CPACK_NSIS_CREATE_ICONS_EXTRA` with the verified quadruple-backslash escape recipe instead.
- **Embedding `!include` of `.nsh` files in CPACK_NSIS_* variables.** CPack's serialization breaks the quoting — NSIS sees broken escape sequences in the include path and fails. Use inline `CreateShortCut` / `Delete` commands instead.
- **Using forward slashes in NSIS shortcut paths.** NSIS `CreateShortCut` accepts `/` in target paths but rejects it in the `.lnk` shortcut path. The shortcut path must use Windows backslashes.
- **Forgetting to check Public Desktop for admin installs.** Admin installs via `RequestExecutionLevel admin` land shortcuts on `C:\\Users\\Public\\Desktop`, not the user's personal desktop. Always check both locations when debugging missing shortcuts.
- **Using the deprecated `dotnet-format` global tool instead of SDK built-in `dotnet format`.** The global tool conflicts with the built-in command in .NET 6+ SDK. CI pipelines using the global tool produce false-positive format failures.
- **Referencing compiler-specific static libraries in WiX File elements.** MSVC produces `.lib`, GCC/Clang produce `.a`. A fixed reference to one format breaks cross-compiler CI. Use `find_package` and CMake config files instead.
- **Using `file(GLOB_RECURSE dir)` without `/*`.** The directory path alone is treated as a literal filename — returns empty. Always use `file(GLOB_RECURSE dir/*)`.
- **Forgetting to guard `CPACK_RESOURCE_FILE_LICENSE` / `CPACK_RESOURCE_FILE_README` for non-Windows.** macOS `productbuild` only accepts `.rtfd`, `.rtf`, `.html`, `.txt` extensions. Files with no extension or `.md` cause `CPack Error: Bad file extension specified`. Guard with `if(CMAKE_SYSTEM_NAME STREQUAL "Windows")`.

## References

**WiX/MSI migration & build integration:**
- `references/wix-msi-guide.md` — **Start here for NSIS→WiX migration.** Toolchain setup, WiX 6 schema changes from v3, CMake `GLOB_RECURSE` / `.ninja_lock` pitfalls, graceful CI fallback, MSI icon, desktop shortcut patterns (static + per-user CA). All pitfalls hit during a real migration, with diagnostics and fixes.
- `references/wix-msi-build-integration.md` — WiX build integration skeleton: `dotnet tool install`, UI extension discovery, `$(var.X)` preprocessor rules, `cmake/PackagingMSI.cmake`.
- `references/wix-msi-desktop-shortcut-pattern.md` — Static Shortcuts.wxs: DesktopFolder, Start Menu entries, HKCU registry keys.
- `references/wix-msi-per-user-desktop-ca.md` — PowerShell deferred custom-action: per-user desktop shortcut from perMachine MSI.

**NSIS escape & behavior details:**
- `references/cmake-nsis-string-escaping.md` — Four-stage escape pipeline, table of every failing pattern, verification commands per stage.
- `references/windows-nsis-desktop-shortcut-empirical-investigation.md` — Full investigation transcript: escape patterns tested, `cpack --debug` output, verified validation sequence.
- `references/windows-nsis-installer-ux.md` — Condensed lessons: license text mismatch, CPack include order, missing shortcuts, auto-run, root discovery.

**Validation & testing:**
- `references/regression-tests.md` — Regression test patterns: CPack config validation script, CTest integration, MSYS-to-CMake path conversion, Windows-specific guard conditions for WiX migration.
- `references/cpack-config-check-script.md` — Full CPack config validation script with CTest integration.

**Platform portability:**
- `references/cross-platform-c-portability.md` — C11 portability: `S_ISDIR` vs `_S_IFDIR`, `getcwd` signatures, `clang-format` in CI, `productbuild` file extension restrictions, Windows console UTF-8.
- `references/windows-console-utf8.md` — Standalone recipe: Windows console UTF-8 setup.
- `references/cmake-glob-windows-pitfalls.md` — `file(GLOB_RECURSE)` requires `dir/*`, `CONFIGURE_DEPENDS` edge cases, stale `.ninja_lock`.
