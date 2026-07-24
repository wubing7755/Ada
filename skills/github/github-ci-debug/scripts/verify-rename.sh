#!/usr/bin/env bash
# Verify a project rename was applied correctly across all config/docs.
# Usage: bash verify-project-rename.sh /path/to/repo NewName
# Checks: CMakeLists project(), packaging exports, config templates,
#          readme/docs, CLI help text, and builds+tests.

set -euo pipefail
ROOT="${1:-.}"
PASS=0; FAIL=0

check() {
    local label="$1"; shift
    printf '[%s] %s... ' "$((PASS+FAIL+1))" "$label"
    if "$@"; then echo PASS; PASS=$((PASS+1)); else echo FAIL; FAIL=$((FAIL+1)); fi
}

echo "=== Verify rename in $ROOT ==="

# Config template content
check "config template targets" grep -q "${2}Targets.cmake" "$ROOT/cmake/${2}Config.cmake.in" 2>/dev/null
check "config template components" grep -q "check_required_components(${2})" "$ROOT/cmake/${2}Config.cmake.in" 2>/dev/null

# CMakeLists.txt
check "project() name" grep -q "project(${2}" "$ROOT/CMakeLists.txt"

# Packaging
check "export targets" grep -q "${2}Targets" "$ROOT/cmake/Packaging.cmake" 2>/dev/null
check "namespace" grep -q "NAMESPACE ${2}::" "$ROOT/cmake/Packaging.cmake" 2>/dev/null
check "install path" grep -q "cmake/${2}\"" "$ROOT/cmake/Packaging.cmake" 2>/dev/null

# No stale old name in project files (excludes C type names / macros)
STRAY=$(grep -rni '\bOLD_NAME_PLACEHOLDER\b' "$ROOT/CMakeLists.txt" "$ROOT/README.md" "$ROOT/cmake/" "$ROOT/doc/" "$ROOT/tests/"/*/CMakeLists.txt 2>/dev/null || true)
check "no stray old name" test -z "$STRAY"

# Build + test
check "cmake build" bash -c "cd '$ROOT' && cmake --build --preset ninja-debug >/dev/null 2>&1"
check "ctest" bash -c "cd '$ROOT' && ctest --preset ninja-debug --output-on-failure >/dev/null 2>&1"

# CLI help
check "cli help lowercase" bash -c "cd '$ROOT' && build/ninja-debug/bin/${2}.exe --help 2>&1 | grep -q '${2} - count'"

echo "=== $PASS passed, $FAIL failed ==="
exit $FAIL
