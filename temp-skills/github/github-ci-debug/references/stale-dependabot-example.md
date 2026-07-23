# Stale Dependabot PR: Concrete Example

This documents an actual case from the `wubing7755/Cloc` repository.

## Scenario

Dependabot opened PR #1 to bump `actions/checkout` from v6 to v7. CI failed with:
- `build (ubuntu-latest, ninja-debug)` — Build step failed
- `cppcheck` — Clang-tidy step failed

Main branch CI passed fine on its own.

## Root Cause

The PR branch (`dependabot/github_actions/actions/checkout-7`) was created from commit `a704b41` (initial commit). Main had since moved to `1944ee8` which included a project rename from `CodeLineCalculator` to `Cloc`.

Comparing raw files revealed a stale variable:

```
# ci.yml line 187
main:  -DCLOC_SOURCE_DIR=${{ github.workspace }}
pr-1:  -DCODELINECALCULATOR_SOURCE_DIR=${{ github.workspace }}
```

The old variable name was preserved because the PR branch was never rebased.

## Diagnosis Steps

```bash
# 1. Check merge base
git fetch origin
git merge-base main dependabot/github_actions/actions/checkout-7
# → a704b41 (initial commit, not current main)

# 2. Fetch main for comparison
git checkout -b pr-1 origin/dependabot/github_actions/actions/checkout-7

# 3. Compare files beyond the intended change
curl -s "https://raw.githubusercontent.com/wubing7755/Cloc/main/.github/workflows/ci.yml" \
  | python3 -c "..."  # or use git diff main...pr-1
```

## Resolution

1. Closed PR #1 via API
2. Created new branch from latest main: `chore/bump-actions-checkout-to-v7`
3. Applied only the `@v6` → `@v7` change
4. Opened PR #3 with proper PR template
5. CI passed, merged with squash

## Key Insight

When a dependabot PR's CI fails and main's CI succeeds, the first check should be:
> Is the PR branch stale? Does it need rebasing?

Run `git merge-base main <pr-branch>` and compare raw files — the problem is often a stale reference, not the dependency bump itself.
