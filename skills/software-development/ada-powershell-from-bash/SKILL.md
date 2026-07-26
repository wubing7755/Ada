---
name: ada-powershell-from-bash
description: "Use when running PowerShell commands or scripts from git-bash/MSYS on Windows — avoid path mangling, encoding issues, and variable expansion problems when crossing between POSIX shell and PowerShell. Triggered by: $ variable expansion errors in bash, MSYS path mangling (backslash stripping), powershell.exe -Command failures from git-bash. Only applies on Windows with git-bash/MSYS."
version: 1.0.0
platforms: [windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [powershell, bash, msys, windows, git-bash, path]
    related_skills: []
---

# PowerShell from Bash (Windows)

When running PowerShell commands or scripts through git-bash/MSYS on Windows, two problems break nearly every attempt:

## Overview

This skill provides reliable patterns for running PowerShell commands and scripts from
git-bash/MSYS on Windows. MSYS environments cause two pervasive failures: bash `$`
variable expansion silently mangling PowerShell syntax, and automatic MSYS path
conversion stripping backslashes from Windows paths (turning `C:\Users\World\script.ps1`
into `C:UsersWorldscript.ps1`). The skill prescribes a simple two-step workflow —
write PowerShell to a `.ps1` file first via `write_file`, then execute it with
`MSYS_NO_PATHCONV=1 powershell.exe -File` — that avoids both issues entirely. Also
covers CMake/Ninja path conversion from MSYS/Unix-style to Windows-native using
`cygpath -w`.

## When to Use

- User needs to run PowerShell commands from a bash/MSYS terminal on Windows
- User encounters `$` variable expansion errors when inlining PowerShell in bash
- User encounters MSYS path conversion mangling Windows backslash paths (e.g., `C:\` paths broken)
- User needs to invoke Windows-native tools (PowerShell, CMake/Ninja) from git-bash with proper path handling
- User says "PowerShell from bash", "run ps1 from git-bash", or "MSYS_NO_PATHCONV"


Don't use for: native PowerShell sessions (not via git-bash/MSYS), Linux/macOS shell scripting, or non-Windows environments.

## Problem 1: `$` variable expansion eaten by bash

Bash treats `$` as variable expansion. Any `$env:USERPROFILE`, `$_.Name`, `$(...)` etc. in PowerShell gets mangled.

**Fix:** Never inline PowerShell commands with `$` in bash. Always write to a `.ps1` file first with `write_file`, then execute the file.

## Problem 2: MSYS path conversion mangles backslashes

MSYS auto-converts strings that look like paths. `C:\Users\World\script.ps1` becomes `C:UsersWorldscript.ps1` (backslashes stripped).

**Fix:** Use `MSYS_NO_PATHCONV=1` prefix when calling PowerShell, and use Windows-style paths in the `.ps1` file itself (not passed on the command line when possible). For the `-File` argument, forward slashes work: `C:/Users/World/script.ps1`.

## Correct invocation pattern

```bash
# Write script to file first (avoids $ expansion)
write_file("C:/Users/World/myscript.ps1", "<PowerShell code here>")

# Execute with path conversion disabled
MSYS_NO_PATHCONV=1 powershell.exe -ExecutionPolicy Bypass -File 'C:/Users/World/myscript.ps1'
```

## Rules

1. **Never inline PowerShell with `$` into `terminal()` bash commands** — bash eats the `$` variables
2. **Use `write_file` to create `.ps1` scripts**, then execute them
3. **Always set `MSYS_NO_PATHCONV=1`** before calling powershell.exe
4. **Use forward slashes** in the `-File` path argument
5. **Python `os.scandir()` is faster than `du` on Windows** for filesystem scanning — consider using `execute_code` with Python instead of shell `du`

## Common Pitfalls

- `cmd.exe //c` does NOT work from git-bash for running PowerShell inline
- `powershell.exe -Command "..."` with inline script always breaks due to `$` expansion
- The `$env:USERPROFILE` approach in `.ps1` files is fine — only the bash invocation is the problem

## Passing Windows paths from MSYS/bash to CMake/Ninja

When running CMake from git-bash/MSYS, `$(pwd)` and environment variables produce Unix-style paths (`/c/Users/...`). CMake generators like Ninja may fail to resolve these. Use `cygpath -w` to convert:

```sh
# Wrong — Unix path breaks Ninja on Windows:
cmake -G Ninja -S tests/package_smoke -B build/package-smoke \
    -DCMAKE_PREFIX_PATH="$(pwd)/install"

# Correct — Windows-native path:
PREFIX="$(cygpath -w "$(pwd)/install")"
cmake -G Ninja -S tests/package_smoke -B build/package-smoke \
    -DCMAKE_PREFIX_PATH="$PREFIX"
```

This applies to all CMake path variables: `CMAKE_PREFIX_PATH`, `CPROJECT_SOURCE_DIR`, `-S`, `-B`, and install prefixes.

## Verification Checklist

- [ ] PowerShell code was written to a `.ps1` file via `write_file` before execution — never inlined with `$` in bash
- [ ] `MSYS_NO_PATHCONV=1` prefix used on all `powershell.exe` invocations
- [ ] Forward slashes used in the `-File` path argument (e.g., `'C:/Users/World/script.ps1'`)
- [ ] CMake/Ninja paths converted with `cygpath -w` when invoked from git-bash/MSYS
