---
name: ada-dotnet-verification
description: "Use when verifying .NET builds, tests, and code formatting during refactoring phases — focused TDD checks, ad-hoc verifier scripts for Windows IDE/testhost locks, and isolated artifact verification. Triggered by: MSB3021/MSB3027 DLL lock errors on Windows, dotnet test failures after refactoring, need for isolated artifact verification when default output path is locked by IDE/testhost."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [dotnet, testing, verification, refactoring, windows]
    related_skills: [ada-test-driven-development]
---

# .NET Verification

Use this skill when a .NET repository phase needs evidence-backed verification: focused TDD checks, full build/test gates, `dotnet format`, `git diff --check`, or a temporary ad-hoc verifier script.

## Overview

This skill defines a four-tier verification ladder for .NET refactoring phases: (1) focused RED/GREEN TDD checks on a single behavior, (2) focused regression sets for the touched module, (3) full project gates (build + test + format + diff), and (4) ad-hoc verifier scripts for handoff/review evidence. It also covers Windows-specific pitfalls — IDE/testhost DLL locks under `bin/Debug/`, isolated artifacts directories as a workaround, and reporting discipline that distinguishes focused evidence from full-suite claims.

The core principle: never claim "verified" on weak evidence. Separate RED, GREEN, full-suite, format, and diff results. When a lock blocks the default output path, report it explicitly and use `--artifacts-path` instead of silently skipping verification.

## When to Use

Use when:
- A .NET refactoring phase needs formal verification evidence before proceeding to the next phase
- The user or reviewer requests proof that changes are correct (build, test, format, diff)
- Windows IDE locks prevent default `dotnet test` from running (MSB3021 / MSB3027 errors)
- A temporary ad-hoc verifier script is needed to produce focused evidence for a specific change
- TDD is being applied: write a failing test, implement the fix, verify the test passes

Do **not** use for: running the full CI pipeline, performance benchmarking, or security scanning.

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

## Common Pitfalls

- **Claiming "verified" on focused evidence.** Running a single test filter is not a full-suite pass. Always label focused/ad-hoc results explicitly and run the full suite before claiming completion.
- **Killing the user's IDE to resolve DLL locks.** On Windows, `MSB3021` / `MSB3027` errors are output-tree locks from stale `testhost.exe` processes. Never kill the user's IDE — use `--artifacts-path` to an isolated temp directory instead.
- **Forgetting to clean up temp verification artifacts.** Ad-hoc verifier scripts and isolated artifact directories under `$TEMP` must be deleted after use. Leaving them accumulates stale evidence.
- **Using deprecated `dotnet-format` global tool.** The global tool conflicts with the SDK built-in `dotnet format` command. Always use `dotnet format` (no hyphen) for .NET 6+ projects.
- **Running `dotnet test` without `--no-build` after a separate build.** This triggers an unnecessary rebuild. Use `dotnet build -v q && dotnet test --no-build -v q` for the project gate.
- **Inflating ad-hoc verification into a full quality gate.** If a reviewer/user challenges ad-hoc evidence, rerun with an OS-safe temp script — do not defend prior output.

## Verification Checklist

- [ ] Focused RED test confirms the new test fails for the expected missing behavior before implementation
- [ ] Focused GREEN test confirms the fix passes the same filter after implementation
- [ ] Full regression set for the touched class/module passes (not just the new test)
- [ ] `dotnet build -v q && dotnet test --no-build -v q` passes project-wide
- [ ] `dotnet format --verify-no-changes` and `git diff --check` pass with zero violations
- [ ] Any ad-hoc evidence is clearly labeled as "focused" or "ad-hoc" — never conflated with full-suite results
- [ ] Temp artifacts (verifier scripts, isolated artifact directories) are cleaned up
