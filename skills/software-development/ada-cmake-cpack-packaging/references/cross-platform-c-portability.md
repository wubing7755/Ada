# C11 Cross-Platform Portability Pitfalls

Lessons from CProjectStandard installer development that broke CI in non-obvious ways.

## `S_ISDIR` macro — exists on POSIX, not on MSVC

```c
// Wrong — S_ISDIR not available on MSVC; causes LNK2019 unresolved external:
return stat(path, &st) == 0 && S_ISDIR(st.st_mode) != 0;

// Correct — platform-conditional:
#ifdef _WIN32
    return (st.st_mode & _S_IFDIR) != 0;
#else
    return S_ISDIR(st.st_mode) != 0;
#endif
```

**Symptom:** `error LNK2019: unresolved external symbol S_ISDIR` on MSVC builds.
**Root cause:** `S_ISDIR` is a macro on POSIX but doesn't exist in MSVC's CRT.
**Detection:** GCC/clang builds pass; MSVC linker fails with unresolved external.

## `getcwd` buffer-size argument — `int` on Windows, `size_t` on POSIX

```c
// Wrong on POSIX — implicit conversion 'int' to 'size_t' flagged by clang-tidy:
if (!getcwd(out, (int)size)) { ... }

// Correct — platform-conditional cast:
#ifdef _WIN32
    if (!getcwd(out, (int)size)) {
#else
    if (!getcwd(out, size)) {
#endif
```

**Symptom:** clang-tidy `-warnings-as-errors` flags `implicit conversion changes signedness: 'int' to 'size_t'`.
**Root cause:** `#define getcwd _getcwd` on Windows maps to `_getcwd(char*, int)`; POSIX `getcwd` takes `(char*, size_t)`.

## `strcpy` flagged by clang-analyzer

```c
// Wrong — clang-analyzer flags as insecure CWE-119:
strcpy(tmp, path);

// Correct — use strncpy with manual null termination:
strncpy(tmp, path, sizeof(tmp) - 1);
tmp[sizeof(tmp) - 1] = '\0';
```

**Symptom:** `Call to function 'strcpy' is insecure ... CWE-119` treated as error with `-warnings-as-errors`.
**Fix:** Replace with `strncpy` + explicit null termination. The project may already have `_CRT_SECURE_NO_WARNINGS` for MSVC but clang-analyzer on Linux CI still catches these.

## `clang-format` for CI fixes

When clang-format isn't installed on the dev machine but CI enforces it:
```sh
pip install clang-format
export PATH="$HOME/AppData/Roaming/Python/Python313/Scripts:$PATH"  # Windows
clang-format -i src/main.c
```

The pip package provides `clang-format.exe` in the user's Python Scripts directory.

## `productbuild` (macOS) rejects non-standard resource file extensions

macOS CPack productbuild generator requires `CPACK_RESOURCE_FILE_LICENSE` and `CPACK_RESOURCE_FILE_README` to have extensions `.rtfd`, `.rtf`, `.html`, or `.txt`. Files with `.md` extension or no extension (`LICENSE`) are rejected.

```cmake
# Wrong — .md and extensionless files break productbuild:
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/README.md")

# Correct — restrict to Windows/NSIS:
if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
    set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/README.md")
endif()
```

**Symptom:** `CPack Error: Bad file extension specified: . Currently only .rtfd, .rtf, .html, and .txt files allowed.`

## Windows console UTF-8 for Chinese/multibyte output

When a C program outputs UTF-8 text on Windows, the console defaults to a legacy code page (GBK on Chinese Windows, CP437 on English). UTF-8 bytes display as garbled characters (mojibake).

```c
// Add at the top of main(), using __declspec to avoid <windows.h> conflicts:
#ifdef _WIN32
    {
        typedef unsigned int UINT;
        #ifndef CP_UTF8
        #define CP_UTF8 65001
        #endif
        __declspec(dllimport) int __stdcall SetConsoleOutputCP(UINT);
        __declspec(dllimport) int __stdcall SetConsoleCP(UINT);
        SetConsoleOutputCP(CP_UTF8);
        SetConsoleCP(CP_UTF8);
    }
#endif
```

**Why not `#include <windows.h>`?** `<windows.h>` pulls in macro definitions (`NEAR`, `FAR`, `ERROR`, etc.) that clash with C11 designated initializers and enum values commonly used in this project's message tables. Using `__declspec(dllimport)` declares only the two needed functions directly.

**Symptom:** Chinese characters in `printf` output appear as garbled/gibberish on Windows, but display correctly on Linux/macOS.
**Root cause:** Windows console uses system code page (e.g. GBK), not UTF-8.
**Alternative:** Use wide-character API (`wprintf`, `_setmode`) but that complicates the bilingual message tables.
