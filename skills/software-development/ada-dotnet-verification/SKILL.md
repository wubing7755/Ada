---
name: ada-dotnet-verification
description: .NET build/test/format verification for refactoring phases, including focused TDD checks, ad-hoc verifier scripts, and isolated artifacts for Windows IDE/testhost locks.
version: 1.0.0
author: Hermes Agent
platforms: [windows]
metadata:
  hermes:
    tags: [dotnet, testing, verification, refactoring, windows]
    related_skills: [systematic-refactoring, test-driven-development]
---

# .NET Verification

Use this skill when a .NET repository phase needs evidence-backed verification: focused TDD checks, full build/test gates, `dotnet format`, `git diff --check`, or a temporary ad-hoc verifier script.

## Verification ladder

1. **Focused RED/GREEN**
   - Add the smallest behavior test first.
   - Run a focused filter and confirm the new test fails for the expected missing behavior.
   - Implement the minimal production change.
   - Re-run the same focused filter and confirm it passes.

2. **Focused regression set**
   - Run all tests for the touched class/module, not just the newly added method.
   - Example:
     ```sh
     dotnet test tests/<Project.Tests>/<Project.Tests>.csproj \
       --filter 'FullyQualifiedName~MovePanelCommandTests' \
       -v q
     ```

3. **Project gate**
   - Prefer the repository's documented commands.
   - Typical Atlas-style gate:
     ```sh
     dotnet build -v q && dotnet test --no-build -v q
     dotnet format --verify-no-changes
     git diff --check
     ```

4. **Ad-hoc verifier script**
   - For handoff/review evidence, create a temp script that prints the exact commands it runs.
   - Delete the script after it runs.
   - Call it **ad-hoc** or **focused** verification unless it truly runs the full suite.

## Windows bin/Debug lock pitfall

On Windows, IDEs and stale `testhost.exe` processes can lock test output DLLs under `tests/.../bin/Debug/...`, causing `MSB3021` / `MSB3027` copy failures during `dotnet build` or focused `dotnet test`. Treat this as an output-tree lock, not a code failure.

Preferred response:

1. Do not kill the user's IDE.
2. If a stale `testhost.exe` is clearly identified and safe to terminate, terminate only that process.
3. For fresh evidence without touching default outputs, use an isolated artifacts directory:
   ```sh
   ARTIFACTS="$HOME/AppData/Local/Temp/<project>-verify-artifacts-$(date +%s)"
   rm -rf "$ARTIFACTS"

   dotnet build <solution>.slnx -v q --artifacts-path "$ARTIFACTS"
   dotnet test tests/<Project.Tests>/<Project.Tests>.csproj \
     --filter '<focused-filter>' \
     -v q --artifacts-path "$ARTIFACTS"

   dotnet format --verify-no-changes
   git diff --check
   rm -rf "$ARTIFACTS"
   ```

See `references/isolated-artifacts-verifier.md` for a reusable session-derived verifier pattern.

## Reporting discipline

- Separate **RED**, **focused GREEN**, **full suite**, **format**, and **diff whitespace** evidence.
- If a lock blocks the default output path, report the lock and the isolated-artifacts workaround explicitly.
- Do not inflate a focused/ad-hoc script into a full quality gate.
- Preserve the user's phase terminology: local implementation/verification complete is not fully completed until required independent review passes.
