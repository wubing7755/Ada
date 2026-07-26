# CMake / CPack Packaging — Detailed Workflow & Pitfalls

This reference contains the full detailed workflow steps, pitfall diagnostics, and verification procedures extracted from the main SKILL.md. Return here when the compact summaries in the skill are insufficient.

---

## Core Workflow (Detailed)

1. **Read packaging docs first** — project instructions may require release/build/security docs before packaging changes. Typical files: `docs/guides/cmake.md`, `docs/guides/release.md`, `SECURITY.md`, `AGENTS.md`.

2. **Map the install and package pipeline** — inspect `CMakeLists.txt` for install/packaging includes and build options. Inspect packaging modules such as `cmake/Packaging.cmake`. Inspect release CI, usually `.github/workflows/release.yml`. Inspect launcher/resources under `res/` or equivalent.

3. **Generate and inspect CPack config before guessing** — run configure for the relevant preset. Inspect generated `build/<preset>/CPackConfig.cmake` and, for NSIS, `_CPack_Packages/.../NSIS/project.nsi`. Treat generated config as the source of truth for what CPack actually captured.

4. **Build a tight validation loop** — for non-GUI packaging bugs, assert generated `CPackConfig.cmake` contains/omits expected `CPACK_*` variables. For installed-layout bugs, use `cmake --install ... --prefix <tmp>` and run from the installed tree. For GUI installer behavior, document manual Windows verification steps in the PR.

---

## Pitfall 1: CPack Include-Order

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

---

## Pitfall 2: CPack Component System — Silent Empty Installs

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

---

## Installed-Layout Launcher Checks

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

---

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

---

## See Also

- **NSIS escape pipeline:** `references/cmake-nsis-string-escaping.md`
- **WiX/MSI migration:** `references/wix-msi-guide.md`
- **Regression tests:** `references/regression-tests.md`
- **CPack config check script:** `references/cpack-config-check-script.md`
