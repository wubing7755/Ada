# CMake GLOB / Globbing Pitfalls on Windows

These gotchas were hit while harvesting a staged install directory for WiX/MSI packaging. Each one cost ~15 minutes of debugging; listed here so the next session knows to skip them.

## 1. `file(GLOB_RECURSE dir)` returns empty — you need `dir/*`

CMake's `file(GLOB_RECURSE)` on Windows requires a glob pattern in the argument. Passing a bare directory path is silently treated as a literal filename match:

```cmake
# WRONG — returns nothing on Windows.
file(GLOB_RECURSE files "${CMAKE_CURRENT_BINARY_DIR}/installer-staging")

# RIGHT — the trailing /* makes it recursive.
file(GLOB_RECURSE files "${CMAKE_CURRENT_BINARY_DIR}/installer-staging/*")
```

The Linux behaviour is the same, but most projects don't notice because their Linux development workflow doesn't depend on the glob.

## 2. The directory must exist at configure time

`file(GLOB_RECURSE)` is a configure-time command. If the directory it points to doesn't exist (or is empty), it returns an empty list and the build silently ships zero components.

If your flow is "run `cmake --install` to populate a staging directory", the staging dir does not exist on the first configure. Three workarounds:

### a. `execute_process` during configure (fragile)

```cmake
execute_process(
    COMMAND ${CMAKE_COMMAND} -E remove_directory installer-staging
    COMMAND ${CMAKE_COMMAND} --install . --prefix installer-staging
)
file(GLOB_RECURSE files CONFIGURE_DEPENDS "installer-staging/*")
```

Fragile because on a fresh checkout, ninja build files don't exist yet — `cmake --install` may fail to find `cmake_install.cmake` or may run before targets are built. Avoid this pattern.

### b. Sentinel file + CONFIGURE_DEPENDS (recommended)

```cmake
# Configure-time:
file(GLOB_RECURSE files CONFIGURE_DEPENDS
    "installer-staging/*"
    "installer-staging/.stamp")   # touch in build target to trigger re-glob

# Build target:
add_custom_target(install-staging
    ...
    COMMAND ${CMAKE_COMMAND} -E touch installer-staging/.stamp)
```

The sentinel file's mtime is updated on every build, forcing CMake to re-glob on the next configure. Reliable, but requires a two-stage configure (first one is empty; first build populates staging + touches sentinel; second configure re-globs).

### c. Build-time generation

```cmake
add_custom_command(OUTPUT generated/TemplateTree.wxs
    COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_SOURCE_DIR}/cmake/GenerateTemplateTree.cmake
    DEPENDS install-staging)
add_custom_target(template-tree DEPENDS generated/TemplateTree.wxs)
```

Generation moves from configure time to build time. CMake re-runs the script whenever `install-staging` rebuilds. Most robust but requires a separate `.cmake` script file.

## 3. CONFIGURE_DEPENDS does not watch inside hidden directories

`CONFIGURE_DEPENDS` schedules a reconfigure when matched files change. It does **not** watch subdirectory contents on its own — the glob is re-evaluated each configure. If your source adds new files to a watched directory, those will be picked up; but only on the next configure, not during an in-progress build.

## 4. Glob results differ between backslashes and forward slashes

CMake stores glob results with whatever separator is native to the build host. On Windows this means backslashes; on Linux, forward slashes. If you then pass these paths to a downstream tool that doesn't handle both, you'll get silent failures. Normalize early:

```cmake
file(GLOB_RECURSE files CONFIGURE_DEPENDS "${dir}/*")
foreach(f IN LISTS files)
    file(TO_CMAKE_PATH "${f}" f)   # always forward slashes
    list(APPEND normalized "${f}")
endforeach()
```

For WiX specifically, the source path on `<File Source="..."/>` accepts either separator; this is not usually a problem there.

## 5. Stale ninja lock after non-ninja tool crashes

If you run `wix build`, `makensis`, or any other subprocess from inside a custom target, and that subprocess crashes or is killed mid-write, ninja's `.ninja_lock` may stay populated. The next build fails with:

```
ninja: error: failed recompaction: Permission denied
ninja: error: rebuilding 'build.ninja': subcommand failed
```

Fix:

```sh
rm build/<preset>/.ninja_lock
# If that doesn't work, also delete the regenerated build.ninja:
rm build/<preset>/build.ninja
cmake --build build/<preset>
```

Check Task Manager for stray `wix.exe`, `makensis.exe`, `msiexec.exe` processes if the lock recurs — installer test runs sometimes leave them hanging.

## 6. Quote-related CMake warning obscures real errors

When CMake parses a string with embedded unquoted attributes (e.g. `<Component Id="${id}">` inside `set()`), it emits:

```
Syntax Warning in cmake code at column 53
Argument not separated from preceding token by whitespace.
```

The warning is harmless but easy to misdiagnose as the source of a downstream failure. Always check `CMakeCache.txt` and the actual generated file rather than chasing these warnings.