# CMake String Escaping in CPack NSIS Commands

## The Problem

CPack captures `CPACK_NSIS_*` variables at `include(CPack)` time and writes them into `CPackConfig.cmake` as regular CMake `set()` calls. CMake then **re-parses** `CPackConfig.cmake` when generating packages. This double-parsing creates string escaping traps that catch almost every naive attempt to put a quoted Windows path into an NSIS command.

This reference is the technical deep-dive behind the recipe in the parent SKILL.md's "CMake string escaping for NSIS commands — verified recipe" section. Read that section first for the working configuration.

## The four escape stages

A CMake string value in `CPACK_NSIS_CREATE_ICONS_EXTRA` passes through four distinct parsers before NSIS sees it:

1. **CMake parses `cmake/Packaging.cmake`**: `\\` → `\` (single backslash). `\"` → `"` (literal quote — but consumes one of the surrounding string delimiters, often confusing things).
2. **CPack writes the variable value into `CPackConfig.cmake`** as `set(CPACK_NSIS_*_EXTRA "value")`. CPack does NOT re-escape `\` in the value (so the single backslash is written as `\\` for the file). CPack does NOT escape `"` reliably — a literal `"` in the value breaks the surrounding `set(... "...")` quoting and produces cascading parse errors downstream.
3. **CMake re-parses `CPackConfig.cmake`** when CPack loads it: `\\` → `\`. Any `\X` where `X` is not a recognized escape triggers `Invalid character escape '\X'`. This is the most common failure mode for paths like `\C`, `\P`, `\S`.
4. **NSIS reads the substituted string**: NSIS does `$VARNAME` substitution inside command arguments. NSIS accepts `/` and `\` in **target paths** but **only `\` in shortcut paths** (the first argument to `CreateShortCut` must be a Windows-style backslash path).

## What works (verified)

The single configuration that survives all four stages:

```cmake
# cmake/Packaging.cmake — source has \\ (two backslashes)
set(CPACK_NSIS_CREATE_ICONS_EXTRA
    "CreateShortCut $DESKTOP\\CProjectStandard.lnk $INSTDIR\\bin\\run-wizard.bat")
```

Trace at each stage:

| Stage | Visible form |
|---|---|
| Source file (2 backslashes per separator) | `$DESKTOP\\CProjectStandard.lnk` |
| After CMake parses source | `$DESKTOP\CProjectStandard.lnk` (one `\`) |
| Written into CPackConfig.cmake | `$DESKTOP\\CProjectStandard.lnk` (two `\`) |
| After CMake re-parses CPackConfig.cmake | `$DESKTOP\CProjectStandard.lnk` (one `\`) |
| In project.nsi (what NSIS compiles) | `$DESKTOP\CProjectStandard.lnk` |
| At NSIS runtime | `C:\Users\Public\Desktop\CProjectStandard.lnk` |

The key is that **`\\` in source is the minimum that survives the double CMake parse without becoming `\X`**. Using a single `\` in source produces `\C` at stage 3 — the failure mode that triggered this whole investigation.

## What doesn't work (and exactly why)

| Pattern | Failure |
|---|---|
| `CPACK_CREATE_DESKTOP_LINKS "bin/foo"` only | Variable is logged at `cmCPackNSISGenerator.cxx:556/561` then discarded. No `CreateShortCut` ever generated. (Verified: `cpack --debug` + inspect `_CPack_Packages/<arch>/NSIS/project.nsi`.) |
| `"...\\\"$DESKTOP/foo\\\" ..."` (escaped quotes) | CMake parses `\"` as a literal `"`, but CPack writes the value back into `CPackConfig.cmake` with the embedded `"` breaking the surrounding `set(... "...")` quoting. Result: NSIS sees a stray `"` mid-command. |
| `[==[CreateShortCut "$DESKTOP/foo.lnk" "$INSTDIR/bin/foo"]==]` (bracket arg) | CPack strips the bracket syntax when writing `CPackConfig.cmake`, writing the value as a regular quoted string. Embedded `"` then breaks the surrounding `set(... "...")` quoting — same failure as the backslash-quote form. |
| Single `\` in source (e.g. `"...$DESKTOP\CProject..."`) | Stage 3: `Invalid character escape '\C'`. |
| `/` in the shortcut path (`CreateShortCut $DESKTOP/foo.lnk ...`) | Stage 4: NSIS rejects forward slashes in the `.lnk` shortcut path. Target path accepts `/`, shortcut path does not. (Verified empirically — see empirical investigation reference.) |
| `!include "/abs/path/to/foo.nsh"` | CPack escapes the inner `"` → NSIS sees `"\;"` in the include path → `!include: could not find: "\;C:/path/foo.nsh"`. |
| `!include foo.nsh` (no quotes, no path) | Would work if `foo.nsh` is colocated with `project.nsi` in `_CPack_Packages/<arch>/NSIS/`. CPack gives you no hook to copy a file there — requires a `cpack` wrapper script. |
| `${CMAKE_CURRENT_BINARY_DIR}` (with `${...}` expansion that contains `\`) | The `${...}` expands during stage 1 with CMake converting each `\` to `\\` for the file. Stage 3 then sees `\\` → `\`, but if any path component starts with a backslash letter, `\X` triggers the escape error. |

## Why the "use forward slashes" advice was wrong

This reference previously recommended `CreateShortCut $DESKTOP/MyApp.lnk $INSTDIR/bin/foo` on the grounds that NSIS accepts `/` and forward slashes avoid CMake escape errors. That advice was correct about CMake but **wrong about NSIS**: `CreateShortCut` rejects `/` in the shortcut path (the `.lnk` file path). The symptom was silent — NSIS compiles the command fine but does not create the `.lnk`, leading to the "shortcut missing after install" failure that started the whole investigation.

Forward slashes ARE still safe for **target paths** (`$INSTDIR/bin/foo` works fine). The rule is:

- **Shortcut path (1st argument):** must use `\` (Windows backslash)
- **Target path (2nd argument):** `/` or `\` both work

For consistency with what CMake produces reliably, just use `\` everywhere in these two arguments.

## `CPACK_NSIS_EXTRA_INSTALL_COMMANDS` — unreliable for shortcuts

`CPACK_NSIS_EXTRA_INSTALL_COMMANDS` runs during the file-install phase, not the shortcut-creation phase. NSIS `CreateShortCut` commands placed here may fail silently because:

- The target file may not yet be fully installed when the command runs.
- The install section's working context differs from the shortcuts section.

**Prefer `CPACK_NSIS_CREATE_ICONS_EXTRA` for desktop shortcuts.** It runs in the dedicated shortcut section alongside `CPACK_CREATE_DESKTOP_LINKS` and Start Menu creation, with the correct NSIS context.

**Symptom:** `CPack Error: Problem running NSIS command` in CI, or desktop shortcut missing after install despite the command being present in `CPackConfig.cmake`.

## Verification commands

```sh
# After cmake configure — expect two backslashes in the file:
grep "CREATE_ICONS_EXTRA" build/ninja-release/CPackConfig.cmake
# Expect: set(CPACK_NSIS_CREATE_ICONS_EXTRA "CreateShortCut $DESKTOP\CProjectStandard.lnk $INSTDIR\bin\run-wizard.bat")

# After cpack — expect one backslash in the NSIS script:
sed -n '715,720p' build/ninja-release/_CPack_Packages/win64/NSIS/project.nsi
# Expect: CreateShortCut $DESKTOP\CProjectStandard.lnk $INSTDIR\bin\run-wizard.bat
```

If you see single backslashes in `CPackConfig.cmake` (e.g. `\C` not `\\C`), your source had single backslashes — go back and double them.

If you see forward slashes in `project.nsi`, NSIS will compile fine but the `.lnk` will not be created at install time — change the shortcut path to use `\`.