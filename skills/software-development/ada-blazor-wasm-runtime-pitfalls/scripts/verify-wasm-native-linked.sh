#!/usr/bin/env bash
# Verify a Blazor WASM output contains a dotnet.wasm with linked native symbols.
# Usage: verify-wasm-native-linked.sh <wwwroot/_framework dir> [symbol-pattern]
#   symbol-pattern defaults to SkiaSharp. Pass e.g. 'libSkiaSharp' or another lib name.
# Exit 0 if the served dotnet.wasm contains native symbols; 1 otherwise.
set -uo pipefail
FW="${1:?usage: $0 <wwwroot/_framework dir> [symbol-pattern]}"
PATTERN="${2:-SkiaSharp}"
WASM="$FW/dotnet.wasm"
[ -f "$WASM" ] || { echo "FAIL: $WASM not found"; exit 1; }
SIZE=$(stat -c%s "$WASM" 2>/dev/null || stat -f%z "$WASM" 2>/dev/null || echo 0)
HITS=$(grep -c "$PATTERN" "$WASM" 2>/dev/null || echo 0)
echo "dotnet.wasm size=$SIZE bytes, pattern '$PATTERN' hits=$HITS"
if [ "$HITS" -gt 0 ]; then
  echo "PASS: native symbols linked into dotnet.wasm"
  exit 0
fi
echo "FAIL: no '$PATTERN' symbols in served dotnet.wasm."
echo "Likely the build copied the runtime-pack original. Compare size/timestamp with:"
echo "  C:\\Program Files\\dotnet\\packs\\Microsoft.NETCore.App.Runtime.Mono.browser-wasm\\<ver>\\runtimes\\browser-wasm\\native\\dotnet.wasm"
echo "For VS 18 + .NET 6 projects see skill references/vs18-workload-sdk-imports.md (csproj workaround)."
exit 1
