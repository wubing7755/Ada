---
name: git-cross-platform-pitfalls
description: Git behaviors that differ between Windows and Linux causing CI failures — case-insensitive renames, line endings, Dependabot stale bases, canceled CI shadowing, and cross-platform diagnostics.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Git, CI/CD, Windows, Linux, Debugging, GitHub-Actions]
    related_skills: [github-pr-workflow, github-code-review]
---

# Git Cross-Platform Pitfalls

When local dev happens on Windows but CI runs on Linux runners, subtle git and filesystem differences cause failures that look unrelated to your changes. This skill covers the high-frequency patterns and their fixes.

## Pitfall 1: Case-Only File Renames on Windows

### Symptom

CI fails with "file not found" for a file you renamed with only a case change (e.g., `ClocConfig.cmake.in` → `clocConfig.cmake.in`). The build/config references the new lowercase name, but the file doesn't exist on the Linux runner.

### Root Cause

Windows filesystem is case-insensitive. When you `mv Foo.txt foo.txt` or use `patch` / `write_file` to change a filename's case, git treats it as a **content modification** of the original file — NOT a rename. The old uppercase filename persists in git's index. On GitHub's Linux runners (case-sensitive), the file still has the old uppercase name, but your code references the new lowercase name → "file not found".

### Detection

Check `git diff --stat origin/main...HEAD` — if you see a content modification instead of a rename:
```
# Wrong — content modification, not a rename:
 cmake/ClocConfig.cmake.in  | 4 ++--

# Correct — rename:
 cmake/{ClocConfig.cmake.in => clocConfig.cmake.in} | 0
```

Also verify on the remote: `curl -I https://raw.githubusercontent.com/<owner>/<repo>/<branch>/path/to/lowercase-file` returns 404 while the uppercase version returns 200.

### Fix

Use a two-step `git mv` through a temporary name to force git to record the rename:

```bash
# Two-step rename forces git to track the case change
git mv OldName.ext OldName.ext.tmp
git mv OldName.ext.tmp newname.ext
git commit -m "fix: record case-sensitive rename via git mv"
```

Never use `mv` directly or `write_file` to "rename" by case on Windows — it won't work on CI.

## Pitfall 2: Dependabot PRs With Stale Base

### Symptom

A Dependabot PR that only bumps a dependency version fails CI. The failure is in an unrelated job (build, lint, test) and the error references a variable or filename that was recently renamed on main.

### Root Cause

Dependabot creates PRs from a branch based on an older main commit. If a refactor/rename PR was merged AFTER the Dependabot branch was created, the Dependabot branch still has the old names. When GitHub Actions merges the PR into main for CI, the merge can produce broken code with stale references.

### Detection

```bash
# Check if the PR branch is based on a stale commit
git fetch origin pull/N/head:pr-N
git merge-base main pr-N
# If the merge-base is not the latest main commit, the branch is stale

# Compare full diff (not just the dependabot change)
git diff main...pr-N --stat
# Look for differences beyond the dependency bump — stale names, removed files, etc.
```

Real example: Dependabot PR bumped `actions/checkout@v6→@v7` but the branch also had `CODELINECALCULATOR_SOURCE_DIR` (old project name) while main had renamed it to `CLOC_SOURCE_DIR`.

### Fix

Don't try to push to the Dependabot branch (you can't). Instead:

1. Close the stale Dependabot PR
2. Create a fresh branch from the latest main
3. Apply ONLY the dependency bump changes
4. Open a new PR with proper formatting

```bash
git checkout main && git pull origin main
git checkout -b chore/bump-dependency
# Apply the dependency version change
git push -u origin HEAD
# Create PR via gh or API, close the old Dependabot PR
```

## Pitfall 3: Canceled CI Runs Shadowing Successful Ones

### Symptom

PR shows "pending" or "failure" status even though CI passed on a later commit. Multiple workflow runs exist on the same commit SHA with mixed results.

### Root Cause

When you cancel a CI run mid-flight, the cancelled check runs become the **latest** check runs for each job name. GitHub displays the latest conclusion per check name, so cancelled runs shadow successful ones from an earlier run.

### Fix

Push a new commit (even `--allow-empty`) to trigger fresh CI. Do NOT cancel mid-flight runs — let them complete or fail naturally.

## Pitfall 4: Line Ending Differences (CRLF vs LF)

### Symptom

CI lint/format checks fail with "line endings" or "trailing whitespace" errors, or scripts fail with `^M` characters. Builds pass locally on Windows but fail on Linux.

### Root Cause

Windows uses CRLF (`\r\n`), Linux uses LF (`\n`). Git's `core.autocrlf` can mask this locally. On the Linux CI runner, files checked out with CRLF cause shell scripts to fail and linters to report issues.

### Fix

Ensure `.gitattributes` exists with:
```
* text=auto
*.sh text eol=lf
*.bash text eol=lf
```

And in CI workflows, never rely on `core.autocrlf` being set correctly — use `.gitattributes`.

## Pitfall 5: General Stale Branch After Project Rename

When any PR branch (manual or automated) was created before a project-wide rename was merged to main, the branch's merge-base is an old commit. The CI merge may produce stale variable names.

### Detection

```bash
git merge-base main pr-branch
# If the merge-base is the initial commit (not latest main), the branch is stale
```

### Fix

Either close and recreate, or rebase:
```bash
git checkout pr-branch
git rebase main
git push --force-with-lease
```

## CI Diagnostics Without Log Access

When GitHub API requires auth for logs (HTTP 403), use the runs and jobs endpoints which are publicly accessible for public repos:

```bash
# List workflow runs
curl -s "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5"

# Get failed jobs for a run
curl -s "https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/jobs" \
  | python3 -c "import sys,json; [print(f'{j[\"name\"]}: {j[\"conclusion\"]}') for j in json.load(sys.stdin)['jobs'] if j['conclusion']=='failure']"
```

## Ad-Hoc CI Verification Script

When CI is delayed (free tier queue), create a local verification script to validate changes before pushing:

```bash
#!/usr/bin/env bash
set -euo pipefail
# ... numbered checks: file existence, content grep, build, test, CLI output ...
```

## Quick Diagnostic Commands

```bash
# Check what git thinks about renames vs modifications
git diff --stat origin/main...HEAD

# Verify a specific path exists on the remote branch
BRANCH=$(git branch --show-current)
curl -sI "https://raw.githubusercontent.com/$(git remote get-url origin | sed -E 's|.*github.com[:/]||;s|\.git$||')/$BRANCH/path/to/file"

# Check how stale the PR branch is
git merge-base origin/main HEAD
git log --oneline origin/main..HEAD  # commits NOT on main
```
