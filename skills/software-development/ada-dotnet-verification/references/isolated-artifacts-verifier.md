# Isolated artifacts verifier pattern

This pattern came from a Windows .NET refactoring session where normal `dotnet build` was correct but blocked by an IDE/stale `testhost.exe` lock on `tests/.../bin/Debug/net6.0/<Project>.dll`.

## Symptom

`dotnet build` or focused `dotnet test` fails with messages like:

```text
MSB3027: Could not copy ... exceeded retry count 10.
MSB3021: The process cannot access the file ... because it is being used by another process.
File is locked by "Microsoft Visual Studio (...), testhost (...)".
```

## Preferred verifier shape

Use `--artifacts-path` so the verifier builds and tests in a fresh temp output tree:

```sh
#!/usr/bin/env bash
set -euo pipefail
cd 'C:/Users/usr/source/repos/<Repo>'
ARTIFACTS="$HOME/AppData/Local/Temp/<Repo>-verify-artifacts-$(date +%s)"

cleanup() { rm -rf "$ARTIFACTS"; }
trap cleanup EXIT

echo '=== AD-HOC VERIFY: <phase / behavior> (isolated artifacts) ==='
echo 'Repo:' "$PWD"
echo 'Artifacts:' "$ARTIFACTS"

dotnet build <Solution>.slnx -v q --artifacts-path "$ARTIFACTS"

dotnet test tests/<Project.Tests>/<Project.Tests>.csproj \
  --filter '<focused behavior filter>' \
  -v q --artifacts-path "$ARTIFACTS"

dotnet test tests/<Project.Tests>/<Project.Tests>.csproj \
  --filter 'FullyQualifiedName~<TouchedTestClass>' \
  -v q --artifacts-path "$ARTIFACTS"

dotnet format --verify-no-changes
git diff --check

echo '=== AD-HOC VERIFY COMPLETE ==='
```

## Notes

- This is best for focused/ad-hoc verification evidence. Still run the repo's normal full gate when the default output tree is available.
- If the script runs only focused filters, report focused counts only; do not claim full-suite success.
- Clean up the temp artifacts directory even on failure.
