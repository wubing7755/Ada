---
name: ada-powershell-from-bash
description: Run PowerShell commands and scripts from git-bash/MSYS on Windows without path/variable mangling.
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

## Pitfalls

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
