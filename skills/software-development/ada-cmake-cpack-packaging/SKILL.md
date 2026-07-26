---
name: ada-cmake-cpack-packaging
description: "Use when building CMake/CPack packaging workflows — install rules, generator selection (NSIS vs WiX MSI vs productbuild), Windows Installer standard directories, desktop shortcut patterns, cross-platform portability, and package smoke validation."
version: 1.3.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [CMake, CPack, NSIS, WiX, MSI, Packaging, Installer, Release, Windows, DesktopShortcut]
    related_skills: [github-pr-workflow, github-ci-debug, ada-systematic-debugging]
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

The full 4-step workflow (read packaging docs → map pipeline → inspect generated config → validate) with detailed commands is in `references/cmake-packaging-workflow.md#core-workflow-detailed`. Key principle: always inspect `CPackConfig.cmake` and generated `.nsi` before guessing at NSIS behavior.

## Pitfall 1: CPack include-order

`include(CPack)` captures `CPACK_*` variables at that point. Settings made after `include(CPack)` may not appear in `CPackConfig.cmake`. **Rule:** set all package variables before `include(CPack)`, and put `include(CPack)` at the end of the packaging module. Verify with `grep CPACK_GENERATOR build/<preset>/CPackConfig.cmake`. Full diagnostics and macOS `productbuild` extension rules in `references/cmake-packaging-workflow.md#pitfall-1-cpack-include-order`.

## Pitfall 2: CPack component system — silent empty installs

`CPACK_COMPONENTS_ALL` requires every `install()` to carry `COMPONENT <name>`. Unlabeled files go to the hidden "Unspecified" component and are silently skipped. **Fix:** either remove `CPACK_COMPONENTS_ALL` for monolithic installs, or add `COMPONENT <name>` to every `install()` call. Full symptom/diagnosis/fix patterns in `references/cmake-packaging-workflow.md#pitfall-2-cpack-component-system--silent-empty-installs`.

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

Build-tree vs install-tree layout mismatch is a common source of installer bugs. **Fix:** launchers should `cd` into the installed data directory, or the executable should accept CWD/`--template-root`/env var as a valid root. Test with `cmake --install --prefix <tmp>`. Full fix patterns, commands, and diagnostics in `references/cmake-packaging-workflow.md#installed-layout-launcher-checks`.

## Verification Checklist

- [ ] `grep CPACK_GENERATOR build/<preset>/CPackConfig.cmake` confirms correct generator
- [ ] Generated `.nsi` file contains `CreateShortCut` lines (desktop shortcut)
- [ ] Installed-layout smoke test passes on Windows
- [ ] Desktop shortcuts appear and resolve correctly after install
- [ ] Uninstall removes all installed files and shortcuts cleanly
- [ ] Full 5-step checklist: see `references/cmake-packaging-workflow.md#verification-checklist`

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

**Core workflow & pitfalls (this split):**
- `references/cmake-packaging-workflow.md` — **Detailed workflow, pitfalls, and verification.** Full 4-step workflow, CPack include-order diagnostics, component-system silent-empty-install fix, installed-layout launcher checks, and the complete verification checklist.

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
