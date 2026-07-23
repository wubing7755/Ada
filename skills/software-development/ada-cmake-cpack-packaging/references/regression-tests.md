# Regression Tests for Packaging Changes

This reference covers test patterns for packaging changes: CPack config validation scripts, CTest integration, MSYS/bash-to-CMake path conversion, and Windows-specific guard conditions for WiX/MSI migration.

## Test strategy

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

## CPack Config Validation Script Pattern

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

## Passing Windows Paths from MSYS/bash to CMake

When running CMake from MSYS/git-bash, `${pwd}` produces Unix-style paths (`/c/Users/...`) that Ninja may not resolve. Use `cygpath -w`:

```sh
PREFIX="$(cygpath -w "$(pwd)/install")"
cmake -G Ninja -S tests/package_smoke -B build/package-smoke \
    -DCMAKE_PREFIX_PATH="$PREFIX"
```

This also applies to `CPROJECT_SOURCE_DIR` and other CMake variables that need Windows-native paths.

## Installed-layout smoke test

```sh
cmake --preset ninja-release
cmake --build --preset ninja-release
rm -rf build/installer-layout-test
cmake --install build/ninja-release --config Release --prefix build/installer-layout-test
cd build/installer-layout-test/share/<project-data-dir>
../../bin/<tool> MyProject --dry-run --yes
```

## NSIS script verification (manual, after cpack)

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

## Manual Windows installer verification

When changing NSIS behavior, verify these explicitly:

- `CPACK_NSIS_MENU_LINKS` appears in generated `CPackConfig.cmake` when Start Menu links are expected.
- Desktop shortcuts point to a stable launcher (`.bat` wrapper), not a fragile relative executable path.
- **Do NOT rely on `CPACK_CREATE_DESKTOP_LINKS` alone.** In CMake 4.3 the variable is read by `cmCPackNSISGenerator.cxx` (logged at line 556/561) but **never translated into NSIS code**. The generated `project.nsi` ends up with only Start Menu `CreateShortCut` lines — no desktop shortcut is ever emitted. If you set only `CPACK_CREATE_DESKTOP_LINKS`, no desktop shortcut will be created.
- **Use `CPACK_NSIS_CREATE_ICONS_EXTRA` for the desktop shortcut**, with the specific escape recipe from `cmake-nsis-string-escaping.md`. Keep `CPACK_NSIS_DELETE_ICONS_EXTRA` mirrored for uninstall cleanup.
- Always **inspect the generated `project.nsi`** (not just `CPackConfig.cmake`) to confirm a `CreateShortCut $DESKTOP\...` line actually landed at line ~718. `CPackConfig.cmake` being correct does not guarantee the NSIS substitution worked.
- Only use `CPACK_COMPONENTS_ALL` if every `install()` command carries a matching `COMPONENT` label.

## Desktop shortcut debug checklist

When "desktop shortcut missing":

1. Verify `$INSTDIR/bin/<launcher>` exists after install (component system may have silently skipped the install).
2. Inspect the shortcut's Properties → Target path for correctness.
3. **Check `C:\Users\Public\Desktop` first** for admin installs — this is the most common missed location.
4. Then check `C:\Users\<user>\Desktop` for non-admin / user-context installs.
5. Inspect `_CPack_Packages/.../NSIS/project.nsi` line ~718 to confirm the `CreateShortCut` line actually landed.
