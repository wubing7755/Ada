# Stale Dependabot PR After Project Rename

Real example from the Cloc repo (wubing7755/Cloc).

## Scenario

1. Dependabot opened PR #1: `chore(deps): bump actions/checkout from 6 to 7`
2. After the PR was created, PR #2 was merged: `refactor: rename project from CodeLineCalculator to Cloc`
3. PR #2 renamed `CODELINECALCULATOR_SOURCE_DIR` → `CLOC_SOURCE_DIR` in ci.yml line 187
4. PR #1's branch still had the old variable name — its merge-base was the initial commit

## Symptoms

- CI: `build (ubuntu-latest, ninja-debug)` — Build step failed with exit code 1
- Static Analysis: `cppcheck` — Clang-tidy step failed
- All other CI jobs passed
- Main branch CI passed fine

## Root Cause

The raw file comparison revealed:

```
Line 187:
  main:  -DCLOC_SOURCE_DIR=${{ github.workspace }}
  pr-1:  -DCODELINECALCULATOR_SOURCE_DIR=${{ github.workspace }}
```

The PR only changed `actions/checkout@v6` → `@v7` (5 occurrences in ci.yml, 1 in static-analysis.yml),
but it inherited the stale variable name from its base commit. GitHub's CI merge
preserved the PR's version of line 187, causing the build to reference a non-existent
CMake variable.

## Fix

1. Checked merge-base → `a704b41` (initial commit, 1 commit behind main at `1944ee8`)
2. Created fresh branch from main: `chore/bump-actions-checkout-to-v7`
3. Applied same `@v6` → `@v7` changes (now on correct base with `CLOC_SOURCE_DIR`)
4. Closed PR #1 via API, opened PR #3 with proper PR template

## Key Insight

`git diff main...pr-1` only showed the checkout version changes — **not** the stale
variable name on line 187. That's because `git diff` compares the PR's changes against
their merge-base, and line 187 was the same as the merge-base (both had the old name).
The stale reference was only visible by comparing raw file contents between branches.
