# Windows Console UTF-8 for C Programs

## Problem

C programs outputting Chinese (or any UTF-8) text display garbled characters (mojibake) on Windows consoles. The Windows console defaults to the system code page (GBK on Chinese Windows, CP437 on English), not UTF-8.

## Solution

Set the console output and input code pages to UTF-8 at program startup. Avoid `<windows.h>` include conflicts with existing C11 code by using inline `__declspec(dllimport)` declarations.

```c
int main(int argc, char *argv[]) {
#ifdef _WIN32
    /* Enable UTF-8 console I/O without <windows.h> conflicts */
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
    /* ... rest of main ... */
}
```

## Why not `#include <windows.h>`?

`<windows.h>` pollutes the global namespace with hundreds of macros that can conflict with C11 code:
- `ERROR` macro conflicts with error message strings
- `NEAR`, `FAR`, `IN`, `OUT` empty macros break designated initializers
- Type name collisions with `Config`, `STATUS`, etc.

The inline `__declspec(dllimport)` approach declares only the two needed functions with zero header footprint. **Works on both MSVC and MinGW-GCC** (`__declspec` is supported by both).

## Alternatives

- `SetConsoleOutputCP(65001)` (same thing, magic number)
- Use `wprintf` with wide strings (more invasive, requires `_setmode` on stdout)
- Embed a manifest requesting UTF-8 (only works on Windows 10 1903+)
