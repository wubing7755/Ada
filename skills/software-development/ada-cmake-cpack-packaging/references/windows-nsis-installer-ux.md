# Windows NSIS Installer UX Investigation Notes

Use these notes when diagnosing CPack/NSIS Windows installer reports such as missing shortcuts, confusing finish-page launches, or installed tools failing because they cannot find template/data files.

## Observed symptoms

A Windows NSIS installer for a CMake C project template showed these issues:

1. Simplified Chinese license page said to click “我同意”, but the actual button label was “我接受”.
2. Install progress appeared less than halfway complete when the installer had effectively finished.
3. No desktop shortcut appeared; Start Menu folder contained only `Uninstall`.
4. Finish page auto-ran a setup wizard that opened a console and failed with:

```text
ERROR: Not in project root (CMakeLists.txt not found)
Run from the project root, or ensure the binary is under build/<preset>/bin/.
```

## Durable root causes

### CPack include order

If `include(CPack)` appears before platform-specific variables such as `CPACK_NSIS_MENU_LINKS`, those variables may not be captured into generated `CPackConfig.cmake`. The generated installer then behaves as if those settings do not exist.

**Probe:**

```sh
cmake --preset ninja-release
grep -n "CPACK_NSIS_MENU_LINKS\|CPACK_NSIS_MODIFY_PATH\|CPACK_GENERATOR" build/ninja-release/CPackConfig.cmake
```

Missing variables in `CPackConfig.cmake` usually mean they were set after `include(CPack)` or not set for that configure platform.

### Raw NSIS shortcut commands

Desktop shortcuts written with raw commands like:

```cmake
set(CPACK_NSIS_CREATE_ICONS_EXTRA "CreateShortCut $DESKTOP/Foo.lnk $INSTDIR/bin/run.bat")
```

are fragile because paths are unquoted and Windows install paths often contain spaces.

Prefer quoted paths:

```cmake
set(CPACK_NSIS_CREATE_ICONS_EXTRA
    "CreateShortCut \"$DESKTOP\\Foo Setup Wizard.lnk\" \"$INSTDIR\\bin\\run-wizard.bat\"")
set(CPACK_NSIS_DELETE_ICONS_EXTRA
    "Delete \"$DESKTOP\\Foo Setup Wizard.lnk\"")
```

### Finish-page auto-run is often wrong for scaffolding tools

`CPACK_NSIS_MUI_FINISHPAGE_RUN` is convenient for launching an installed app, but poor UX for a project setup/scaffolding wizard that may prompt the user or mutate files. Prefer no finish-page auto-run; create explicit Start Menu/Desktop launch points.

### Build-tree root discovery does not imply install-tree root discovery

A binary that finds the project root by walking upward from `argv[0]` may work in:

```text
build/<preset>/bin/tool.exe
```

but fail after install when data lives beside `bin`:

```text
<prefix>/bin/tool.exe
<prefix>/share/project-template/CMakeLists.txt
```

Fix by either:

- having a launcher `cd` to the data/template directory before invoking the binary, and making the binary accept current working directory as root; or
- adding explicit installed-data lookup such as `<exe-dir>/../share/<project-data-dir>`; or
- supporting a `--template-root` flag/environment variable.

### NSIS translated license text may not match buttons

NSIS bundled Modern UI translations can contain wording mismatches under localized Windows environments. If a license page is required, verify the generated installer under the target locale and override the relevant NSIS language string if needed. If overriding is brittle across NSIS versions, avoid button-name-specific wording.

## Recommended validation

### Generated config checks

Add a script or CTest step that asserts expected generated CPack variables. Examples:

- finish-page auto-run variable absent when auto-run is not desired
- `CPACK_NSIS_MENU_LINKS` present when Start Menu links are expected
- shortcut commands point to a launcher and quote paths
- `CPACK_NSIS_MODIFY_PATH` present if PATH update is expected

### Installed layout smoke

```sh
cmake --preset ninja-release
cmake --build --preset ninja-release
rm -rf build/installer-layout-test
cmake --install build/ninja-release --config Release --prefix build/installer-layout-test
cd build/installer-layout-test/share/<project-data-dir>
../../bin/<tool> MyProject --dry-run --yes
```

Expected: no “not in project root” error.

### Manual Windows GUI checks

For release candidates, manually verify:

1. License page wording matches actual button labels.
2. Finish page does not auto-run scaffolding/setup tools unless explicitly intended.
3. Desktop shortcut exists if promised.
4. Start Menu folder has tool/template/uninstall shortcuts.
5. Shortcut launches the wizard successfully from installed layout.
6. Uninstall removes custom shortcuts.
