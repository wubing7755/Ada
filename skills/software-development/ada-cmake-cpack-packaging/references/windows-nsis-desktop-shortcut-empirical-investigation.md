# NSIS Desktop Shortcut — Empirical Investigation Transcript

A real-world investigation into why `CPACK_CREATE_DESKTOP_LINKS` and `CPACK_NSIS_CREATE_ICONS_EXTRA` both fail to produce a working desktop shortcut on Windows, and the exact configuration that finally works. Recorded so the next agent who hits this doesn't redo the 20-PR cycle.

**Environment:** CMake 4.3.3, NSIS 3.10, GCC 15.2 (MSYS2 ucrt64), Windows 10, project `wubing7755/c-project-standard` (C11+CMake+Ninja+CPack NSIS).

## Symptom

After `cpack -G NSIS` builds `MyApp-1.0-win64.exe` and the user installs it (admin via `Start-Process -Verb RunAs`):

- ✅ `$INSTDIR\bin\run-wizard.bat` exists
- ✅ Start Menu has `MyApp\Project Setup Wizard.lnk` and friends (in `C:\ProgramData\...\Start Menu\Programs\MyApp`)
- ❌ **No** `MyApp.lnk` on either `C:\Users\Public\Desktop` or `C:\Users\<user>\Desktop`

The installer exit code is 0. No NSIS errors logged. Silent failure.

## Phase 1 — Verify what CPack actually emitted

The most important diagnostic move is to look at what NSIS actually compiles, not just what CPack *thought* it generated:

```sh
cmake --preset ninja-release
cmake --build --preset ninja-release -t <your-target>
cd build/ninja-release
cpack -G NSIS
sed -n '710,725p' _CPack_Packages/win64/NSIS/project.nsi
```

Expected `project.nsi` content around the shortcut section (CMake 4.x):

```
  CreateDirectory "$SMPROGRAMS\$STARTMENU_FOLDER"
  CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Project Setup Wizard.lnk" "$INSTDIR\bin\run-wizard.bat"
  CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Template Files.lnk" "$INSTDIR\share\..."
  @CPACK_NSIS_CREATE_ICONS_EXTRA@         ← was substituted to empty here
  CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
```

If `@CPACK_NSIS_CREATE_ICONS_EXTRA@` is replaced with empty, **no desktop CreateShortCut line was ever generated**. Confirms `CPACK_CREATE_DESKTOP_LINKS` is a no-op in CMake 4.3.

## Phase 2 — Confirm `CPACK_CREATE_DESKTOP_LINKS` is dead

Run `cpack --debug` and grep for the variable:

```sh
cpack -G NSIS --debug 2>&1 | grep -E 'CPACK_CREATE_DESKTOP|CreateShortCut'
```

Output (CMake 4.3.3):

```
C:\glr\builds\cmake\cmake ci\Source\CPack\cmCPackNSISGenerator.cxx:556 CPACK_CREATE_DESKTOP_LINKS: bin/run-wizard.bat
C:\glr\builds\cmake\cmake ci\Source\CPack\cmCPackNSISGenerator.cxx:561 CPACK_CREATE_DESKTOP_LINKS: bin/run-wizard.bat
```

Note: lines 556/561 read the variable but **no subsequent line emits a `CreateShortCut` to the desktop**. The variable is parsed and discarded. This is the root cause of the original symptom — nothing in the generated NSIS code ever creates a desktop shortcut.

## Phase 3 — Test what `CPACK_NSIS_CREATE_ICONS_EXTRA` actually allows

CPack has a known bug where it serializes the variable value into `CPackConfig.cmake` with broken escaping for `"` and `\`. Tested each alternative systematically:

| Source in `cmake/Packaging.cmake` | Result in `CPackConfig.cmake` | NSIS compile |
|---|---|---|
| `"CreateShortCut $DESKTOP/foo.lnk $INSTDIR/bin/foo"` | unchanged | ✅ compiles, runs, **but** `.lnk` not created (NSIS rejects `/` in shortcut path) |
| `"CreateShortCut \\\"$DESKTOP/foo.lnk\\\" \\\"$INSTDIR/bin/foo\\\""` | `"CreateShortCut "$DESKTOP/foo.lnk" "$INSTDIR/bin/foo""` (4 quotes) | ❌ `CreateShortCut expects 2-9 parameters, got 0` — CPack broke the value's quoting |
| `[==[CreateShortCut "$DESKTOP/foo.lnk" "$INSTDIR/bin/foo"]==]` | same broken quoting | ❌ same failure |
| `"CreateShortCut $DESKTOP\\CProjectStandard.lnk $INSTDIR\\bin\\run-wizard.bat"` (the working form) | `"CreateShortCut $DESKTOP\\CProjectStandard.lnk $INSTDIR\\bin\\run-wizard.bat"` (correct) | ✅ compiles, runs, shortcut created |
| `"!include \"${CMAKE_CURRENT_BINARY_DIR}/foo.nsh\""` | `"!include \;\C:/.../foo.nsh\""` (escape broken) | ❌ `!include: could not find: "\;C:/.../foo.nsh""` |
| `"!include foo.nsh"` (no quotes, relative) | unchanged | ⚠️ would work if `foo.nsh` colocated with `project.nsi`, but CPack provides no hook to copy it there |

**The escape sequence that actually works** (verified end-to-end including install):

```cmake
# In cmake/Packaging.cmake:
set(CPACK_NSIS_CREATE_ICONS_EXTRA
    "CreateShortCut $DESKTOP\\CProjectStandard.lnk $INSTDIR\\bin\\run-wizard.bat")
set(CPACK_NSIS_DELETE_ICONS_EXTRA
    "Delete $DESKTOP\\CProjectStandard.lnk")
```

Escape chain audit:

| Stage | Visible form |
|---|---|
| `cmake/Packaging.cmake` source | `\\` (two backslashes, displayed) |
| After CMake parses the source | `\` (one backslash — CMake's `\\` → `\` rule) |
| In `build/.../CPackConfig.cmake` | `\\` (two backslashes — CMake quoted-string literal) |
| After CMake re-parses `CPackConfig.cmake` | `\` (one backslash — same `\\` → `\` rule) |
| In `project.nsi` (what NSIS compiles) | `$DESKTOP\CProjectStandard.lnk` |
| At NSIS runtime (admin install) | `C:\Users\Public\Desktop\CProjectStandard.lnk` |

Critical: NSIS **rejects forward slashes** in the `.lnk` shortcut path. The target path can use either separator, but the first argument to `CreateShortCut` must be a Windows-style backslash path.

## Phase 4 — Verify which desktop `$DESKTOP` resolves to

Empirical test with a standalone NSIS installer (`RequestExecutionLevel admin`, launched via `Start-Process -Verb RunAs`):

```
$0 (UserInfo::GetAccountType) = "Admin"
$DESKTOP = C:\Users\Public\Desktop
$SMPROGRAMS = C:\ProgramData\Microsoft\Windows\Start Menu\Programs
CreateShortCut $DESKTOP\DebugApp.lnk $INSTDIR\bin\app.exe → file appears in Public Desktop ✓
```

**Implication:** On admin installs, `$DESKTOP` is the **Public Desktop**, not the user's personal desktop. If the user reports "desktop shortcut missing", check Public Desktop first. This contradicts the older theory that line 713 sees `SetShellVarContext current` because of timing — it doesn't. `.onInit` runs first and sets `all` for admin users, so by the time `Section "-Core installation"` runs at line 655, `$DESKTOP` is already Public.

For user-context (non-admin) installs, `$DESKTOP` is the user's personal desktop. If you need to support both, `$DESKTOP` covers both — it's just the right path for whichever shell context is active.

## Phase 5 — Full validation recipe

After applying the fix, run all of these:

```sh
# 1. Configure
cmake --preset ninja-release

# 2. Verify CPackConfig.cmake has the expected form
grep "CREATE_ICONS_EXTRA\|DELETE_ICONS_EXTRA" build/ninja-release/CPackConfig.cmake
# Expect:
#   set(CPACK_NSIS_CREATE_ICONS_EXTRA "CreateShortCut $DESKTOP\CProjectStandard.lnk $INSTDIR\bin\run-wizard.bat")
#   set(CPACK_NSIS_DELETE_ICONS_EXTRA "Delete $DESKTOP\CProjectStandard.lnk")

# 3. Build & cpack
cmake --build --preset ninja-release
cd build/ninja-release && cpack -G NSIS

# 4. Verify the NSI script (not just CPackConfig!)
sed -n '715,720p' _CPack_Packages/win64/NSIS/project.nsi
# Expect: CreateShortCut $DESKTOP\CProjectStandard.lnk $INSTDIR\bin\run-wizard.bat

# 5. Install (admin elevation via PowerShell)
powershell -Command 'Start-Process -FilePath "build/ninja-release/MyApp-1.0-win64.exe" -ArgumentList "/S" -Verb RunAs -Wait'

# 6. Check Public Desktop (admin install)
ls "C:\Users\Public\Desktop\MyApp.lnk"
# Expect: file exists

# 7. Check shortcut target
powershell -Command "(New-Object -ComObject WScript.Shell).CreateShortcut('C:\Users\Public\Desktop\MyApp.lnk').TargetPath"
# Expect: C:\Program Files\MyApp\bin\run-wizard.bat

# 8. Test uninstall
"C:\Program Files\MyApp\Uninstall.exe" /S
ls "C:\Users\Public\Desktop\MyApp.lnk"
# Expect: file does NOT exist (CPACK_NSIS_DELETE_ICONS_EXTRA cleaned it up)
```

## Lessons (for the next agent / next PR)

1. **Always inspect `project.nsi`**, not just `CPackConfig.cmake`. CPackConfig being correct does not guarantee the NSIS substitution worked.
2. **Run `cpack --debug`** when a variable seems ignored — it shows exactly what the generator did with it.
3. **The escape recipe `\\` in source → `\` in CPackConfig → `\` in project.nsi** is the only one that survives the double CMake parse cycle for paths-with-backslashes.
4. **`CPACK_CREATE_DESKTOP_LINKS` is a dead knob in CMake 4.3.** Don't waste PRs on it. Use `CPACK_NSIS_CREATE_ICONS_EXTRA` directly.
5. **`.nsh` `!include` from `CPACK_NSIS_*` doesn't work** because CPack breaks the path quoting. If you really need multi-line NSIS logic, patch `project.nsi` post-generation via a `cpack` wrapper script.
6. **Forward slashes only work in NSIS target paths**, not in shortcut paths. Mixed `\` and `/` in one command is allowed but inconsistent — pick `\` for shortcuts and let target paths use either.

## PR history that this resolves

This investigation closes the loop on PRs #23–#44 of `wubing7755/c-project-standard`, which repeatedly tried and failed to fix the desktop shortcut. Each PR picked a different wrong assumption; the right answer turned out to be the most boring one (`CPACK_NSIS_CREATE_ICONS_EXTRA` with `\\` escaping and **no quotes at all**).