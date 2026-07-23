# CPack Config Check Script

A minimal Python script that validates key CPack settings in generated
`CPackConfig.cmake`. Runs as a CTest test on Windows to catch NSIS
configuration regressions before release.

## Full example

```python
#!/usr/bin/env python3
"""Validate release-sensitive CPack settings."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def cmake_value(text: str, name: str) -> str | None:
    match = re.search(rf'^set\({re.escape(name)}\s+"(.*)"\)$', text, re.MULTILINE)
    return match.group(1) if match else None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check-cpack-config.py <CPackConfig.cmake>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    text = path.read_text(encoding="utf-8", errors="replace")

    generator = cmake_value(text, "CPACK_GENERATOR") or ""
    is_nsis = "NSIS" in generator or cmake_value(text, "CPACK_BINARY_NSIS") == "ON"
    if not is_nsis:
        print("CPack config checks skipped: NSIS generator is not enabled")
        return 0

    errors: list[str] = []

    # No finish-page autorun
    if "CPACK_NSIS_MUI_FINISHPAGE_RUN" in text:
        errors.append("finish-page autorun must be disabled")

    # Start Menu links include launcher
    menu_links = cmake_value(text, "CPACK_NSIS_MENU_LINKS")
    if not menu_links or "bin/run-wizard.bat" not in menu_links:
        errors.append("CPACK_NSIS_MENU_LINKS must include bin/run-wizard.bat")

    # Desktop shortcut with quoted paths
    shortcut = cmake_value(text, "CPACK_NSIS_CREATE_ICONS_EXTRA")
    if not shortcut or "run-wizard.bat" not in shortcut or '"' not in shortcut:
        errors.append("desktop shortcut must point to quoted bin/run-wizard.bat")

    # PATH modification enabled
    modify_path = cmake_value(text, "CPACK_NSIS_MODIFY_PATH")
    if modify_path != "ON":
        errors.append("CPACK_NSIS_MODIFY_PATH must be ON")

    # ZIP also generated on Windows
    if "ZIP" not in generator and cmake_value(text, "CPACK_BINARY_ZIP") != "ON":
        errors.append("Windows packages must include ZIP alongside NSIS")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("CPack config checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

## CTest registration

```cmake
if(WIN32)
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    add_test(NAME cproject_cpack_config
        COMMAND ${Python3_EXECUTABLE}
            ${CMAKE_CURRENT_SOURCE_DIR}/scripts/check-cpack-config.py
            ${CMAKE_CURRENT_BINARY_DIR}/CPackConfig.cmake
    )
endif()
```

## Running manually

```sh
cmake --preset ninja-release
python scripts/check-cpack-config.py build/ninja-release/CPackConfig.cmake
```
