---
name: ada-dotnet-verification
description: "Use after editing .NET/C#/Blazor projects or when dotnet build/test/format/pack gates matter. Covers build-graph completeness, focused-to-full evidence, stale packages and generated assets, Windows MSB3021/MSB3027 locks, and isolated artifact verification."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [dotnet, testing, verification, packaging, refactoring, windows]
    related_skills: [ada-test-driven-development]
---

# .NET Verification

Use this skill when a .NET repository phase needs evidence-backed verification: focused TDD checks, full build/test gates, `dotnet format`, `git diff --check`, or a temporary ad-hoc verifier script.

## Agent Execution Contract

Inputs to identify first:
- Solution/project files (`.sln`, `.slnx`, `.csproj`) and touched test projects.
- Whether the task is focused TDD, module regression, full phase verification, or lock recovery.
- Repository-specific build/test/format commands.

Default workflow:
1. Run a focused test for the touched behavior when one exists.
2. Run a focused regression set for the touched module.
3. Run the project gate: build, tests, format, and `git diff --check` when feasible.
4. If Windows output locks block verification, use isolated artifacts before claiming failure.

Stop conditions:
- Required SDK or dependencies are missing and need installation.
- Test failures are unrelated to the change and cannot be triaged quickly.
- Locks require closing the user's IDE or killing ambiguous processes.

Output contract:
- Verification tier used.
- Exact commands run.
- Pass/fail results.
- Lock workaround used, if any.
- Whether evidence is focused or full-suite.

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
   - Typical Lib-style gate:
     ```sh
     dotnet build -v q && dotnet test --no-build -v q
     dotnet format --verify-no-changes
     git diff --check
     ```

4. **Ad-hoc verifier script**
   - For handoff/review evidence, create a temp script that prints the exact commands it runs.
   - Delete the script after it runs.
   - Call it **ad-hoc** or **focused** verification unless it truly runs the full suite.

## Build Graph and Artifact Freshness

Before trusting a green command, reconstruct the repository's build graph from
solution/project files, CI, package configuration, frontend manifests, and
consumer samples. A solution may omit independent package consumers, browser
fixtures, generated JS/CSS, pack checks, or custom test projects.

For each gate record both command coverage and artifact provenance:

- build the project that owns the changed source before dependents;
- after TS/JS/CSS changes, run the declared bundle command before packing;
- after package changes, pack, clear only the consumer's approved local package
  cache, restore the consumer, and verify its resolved version/artifacts;
- distinguish source-project tests from packed-package consumer tests;
- verify the running process/browser loaded the new assembly and static asset,
  rather than relying on restart assumptions or HTTP cache;
- inspect current SDK/template/tool help before applying version-specific rules
  such as `.sln` versus `.slnx` or a test framework API migration.

Never delete global NuGet caches or user-wide tooling as a routine fix. Prefer
repository-local or isolated temporary artifacts and report exactly what was
cleared.

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

## Cross-SDK `obj` contamination

When the same working tree is restored or published by different major SDKs, generated NuGet imports under `obj/` can retain SDK-specific package references. A later build with the target SDK may then fail while loading tasks from another runtime (for example, SDK 6 loading `Microsoft.NET.ILLink.Tasks` built for .NET 7). `dotnet restore --force` is not sufficient evidence that the generated imports are clean.

Before changing project properties or package versions:

1. Reproduce the exact CI command, including whether `publish` performs its own restore or uses `--no-restore`.
2. Verify in a clean source copy with `bin/` and `obj/` excluded, or move only the ignored `obj/` directory to a reversible temp backup and let the target SDK recreate it.
3. Inspect `obj/project.assets.json` for unexpected SDK-pack or linker versions.
4. Treat success in the clean target-SDK environment as proof of cache contamination; do not disable trimming, change dependencies, or alter framework settings to work around a stale `obj` tree.

## Verification Checklist

- [ ] Focused RED test confirms the new test fails for the expected missing behavior before implementation
- [ ] Focused GREEN test confirms the fix passes the same filter after implementation
- [ ] Full regression set for the touched class/module passes (not just the new test)
- [ ] `dotnet build -v q && dotnet test --no-build -v q` passes project-wide
- [ ] `dotnet format --verify-no-changes` and `git diff --check` pass with zero violations
- [ ] Any ad-hoc evidence is clearly labeled as "focused" or "ad-hoc" — never conflated with full-suite results
- [ ] Temp artifacts (verifier scripts, isolated artifact directories) are cleaned up
