# Windows ad-hoc verification script pattern

Use this when a .NET refactoring phase needs a short, reproducible verifier beyond one-off terminal commands, especially in a Windows repo where Hermes `terminal` runs through Git Bash/MSYS.

## Problem this avoids

A script created from Python/`execute_code` with a native Windows path can be hard to execute reliably from Git Bash, and the path shown in logs may be ambiguous. For verification evidence, the future transcript should show:

- the Windows temp-script path,
- the MSYS path actually executed,
- each command the script ran,
- final cleanup of the script file,
- whether tests were full-suite or focused/ad-hoc.

## Pattern

Prefer capturing the exact path returned by Python instead of globbing for the newest `hermes-verify-*.sh`; globbing can accidentally pick up a stale script when several retries happen in one session.

When Visual Studio, Rider, or a leftover `testhost` may lock the normal `bin/Debug` test outputs, run the focused test with an isolated artifacts directory instead of fighting the lock or killing the user's IDE:

```bash
artifacts_win=$(python - <<'PY'
import tempfile
print(tempfile.mkdtemp(prefix='hermes-verify-artifacts-', dir=r'C:\Users\usr\AppData\Local\Temp'))
PY
)
artifacts_msys=$(cygpath -u "$artifacts_win")
trap 'rm -rf "$artifacts_msys"; echo "cleanup=removed $artifacts_win"' EXIT

dotnet build src/<Project>/<Project>.csproj --artifacts-path "$artifacts_win" -v q
dotnet test tests/<Project>.Tests/<Project>.Tests.csproj \
  --filter '<filter>' \
  --artifacts-path "$artifacts_win" \
  -v q
```

This captures the fix pattern, not an environment-specific failure: isolated artifacts make the verifier reproducible even while an IDE is open.

```bash
set -euo pipefail
script_win=$(python - <<'PY'
import os, tempfile
script = r'''#!/usr/bin/env bash
set -euo pipefail
cd /c/Users/usr/source/repos/<repo>
printf 'TEMP_SCRIPT_WINDOWS=%s\n' 'C:\Users\usr\AppData\Local\Temp\__SCRIPT_BASENAME__'
printf 'TEMP_SCRIPT_MSYS=%s\n' "$0"
echo '=== changed path: <path or phase> ==='
echo '=== optional isolated artifacts path for focused verification ==='
artifacts_win=$(python - <<'PYART'
import tempfile
print(tempfile.mkdtemp(prefix='hermes-verify-artifacts-', dir=r'C:\Users\usr\AppData\Local\Temp'))
PYART
)
artifacts_msys=$(cygpath -u "$artifacts_win")
echo "ARTIFACTS_WINDOWS=$artifacts_win"
echo "ARTIFACTS_MSYS=$artifacts_msys"
trap 'rm -rf "$artifacts_msys"; echo "cleanup=removed $artifacts_win"' EXIT

echo '=== dotnet build changed project with isolated artifacts ==='
dotnet build <path/to/project>.csproj --artifacts-path "$artifacts_win" -v q
echo '=== focused tests: <describe scope> ==='
dotnet test <path/to/tests>.csproj --filter '<filter>' --artifacts-path "$artifacts_win" -v q
echo '=== dotnet format --verify-no-changes ==='
dotnet format --verify-no-changes
echo '=== git diff --check ==='
git diff --check
echo '=== ad-hoc verification complete ==='
'''
fd, path = tempfile.mkstemp(prefix='hermes-verify-', suffix='.sh', dir=r'C:\Users\usr\AppData\Local\Temp')
os.close(fd)
script = script.replace('__SCRIPT_BASENAME__', os.path.basename(path))
with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(script)
print(path)
PY
)
msys_tmp=$(cygpath -u "$script_win")
chmod +x "$msys_tmp"
echo "RUNNING_TEMP_SCRIPT_WINDOWS=$script_win"
echo "RUNNING_TEMP_SCRIPT_MSYS=$msys_tmp"
set +e
bash "$msys_tmp"
rc=$?
set -e
rm -f "$msys_tmp"
echo "cleanup=removed $script_win"
exit $rc
```

## Reporting rule

If the script uses `--filter`, report it as **focused/ad-hoc verification**, not as full-suite verification. Only say the full test suite passed when the actual command was an unfiltered full-suite test (for example `dotnet test --no-build -v q`) and the tool output confirms the full count.

## Cleanup rule

Always remove the temp script and include the cleanup line in the evidence summary. If cleanup fails, report that directly.
