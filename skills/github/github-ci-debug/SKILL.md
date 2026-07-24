---
name: github-ci-debug
description: Diagnose and fix GitHub Actions CI failures — stale branches, bot PRs, runner queuing, workflow misconfigurations, and cross-platform pitfalls.
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, CI/CD, Debugging, Pull-Requests, Dependabot, Automation]
    related_skills: [github-pr-workflow, github-code-review, git-cross-platform-pitfalls]
---

# GitHub CI Debugging

Systematic approach to diagnosing and fixing CI failures on GitHub PRs — especially automated PRs from Dependabot or similar bots.

## Rule 1: Check Staleness First

Before debugging any individual CI failure, verify the PR branch is based on a recent main. Dependabot and other bot PRs are frequently created on stale commits.

```bash
# Fetch the PR
git fetch origin pull/<N>/head:pr-<N> && git checkout pr-<N>

# Is the PR stale? If merge-base isn't HEAD~0–2, it's behind.
git merge-base main pr-<N>

# What commits is the PR missing from main?
git log pr-<N>..main --oneline
```

If the PR branch is stale (merge-base is more than a couple commits behind main), **skip individual failure debugging** and go straight to the replacement workflow (Rule 2).

## Rule 2: Replace Stale Bot PRs

Dependabot branches are owned by the bot — you can't force-push to them. Instead:

### 2a. Diff raw files, not git diff

A `git diff` only shows what the PR changed. To find stale references left behind by renames or refactors on main, compare raw file contents:

```bash
# Compare workflow files directly from GitHub raw URLs
curl -s "https://raw.githubusercontent.com/<owner>/<repo>/main/.github/workflows/ci.yml" \
  | diff - <(curl -s "https://raw.githubusercontent.com/<owner>/<repo>/<pr-branch>/.github/workflows/ci.yml")
```

Stale references to look for:
- Old project/variable names (e.g. `CODELINECALCULATOR` → `CLOC`)
- Deprecated preset names, build flags, or workflow syntax
- Missing or renamed files referenced by the workflow

### 2b. Create a fresh branch from main

```bash
git checkout main && git pull origin main
git checkout -b chore/bump-<dep>-to-v<N>
```

Apply the **same changes** the bot PR intended, then commit:

```bash
git add <files>
git commit -m "chore(deps): bump <dep> from <old> to <new>

- <what changed>

Closes #<old-pr-number>"
git push -u origin HEAD
```

### 2c. Close the old PR, open a new one

```bash
# Close the old PR
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/<OLD_NUMBER> \
  -d '{"state": "closed"}'

# Create the new PR (follow repo PR template if one exists)
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{\"title\": \"chore(deps): bump ...\", \"body\": \"...\", \"head\": \"<branch>\", \"base\": \"main\"}"
```

## Rule 3: Common Root Causes After Project Renames

When the base had a rename refactor between the bot fork point and main HEAD:

- **CMake**: `project()` name, export targets, config file names, install paths, namespace aliases
- **CI workflows**: CMake variable names passed via `-D` flags
- **Docs**: `find_package()` calls, import paths in README/examples
- **Path references**: `add_subdirectory(path/to/OldName)` → new name

Always diff the bot branch's modified files against main's versions of those same files — NOT against the bot's merge-base.

## Rule 4: Read Annotations When Logs Are Protected

GitHub requires sign-in to view raw job logs via browser. But **annotations are public** and often contain the error messages:

1. Navigate to the failed job's check run page
2. Click "Open job annotations"
3. Read the error table — it shows the failed step and exit code
4. If available, click "Show more" for stack traces

## Rule 5: Diagnose via API When Logs Are Protected

When GitHub requires auth for logs (HTTP 403), use the runs and jobs endpoints:

```python
import json, urllib.request

run_id = <run_id>
req = urllib.request.Request(
    f"https://api.github.com/repos/<owner>/<repo>/actions/runs/{run_id}/jobs",
    headers={"User-Agent": "HermesAgent", "Accept": "application/vnd.github.v3+json"}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

for job in data.get('jobs', []):
    if job.get('conclusion') == 'failure':
        print(f"FAILED: {job['name']}")
        for step in job.get('steps', []):
            if step.get('conclusion') in ('failure', 'cancelled'):
                print(f"  Step: {step['name']} ({step['conclusion']})")
```

## Rule 6: Runner Queuing Issues

On free-tier GitHub, CI runs can remain "queued" for extended periods.

### Check if CI is running or stuck

```bash
TOKEN=$(git credential fill <<< 'protocol=https
host=github.com
' | grep password | cut -d= -f2)

# Check run status
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs/<run_id>" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'], d.get('conclusion'))"

# Check individual jobs
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs/<run_id>/jobs" \
  | python3 -c "
import sys, json
for j in json.load(sys.stdin).get('jobs', []):
    print(f'{j[\"name\"]}: {j[\"status\"]} / {j.get(\"conclusion\",\"?\")}')
"
```

### Unblock stuck CI

If CI is stuck in "queued" for >5 minutes:
1. Cancel the stuck run: `curl -X POST -H "Authorization: token $TOKEN" ".../actions/runs/<id>/cancel"`
2. Re-trigger by pushing an empty commit:
   ```bash
   git commit --allow-empty -m "chore: re-trigger CI"
   git push
   ```

## Rule 7: Branch Names vs. Workflow Triggers

Workflows often restrict `push` triggers to specific branch patterns:

```yaml
on:
  push:
    branches: [main, master, 'feature/**', 'fix/**', 'refactor/**']
```

A branch named `chore/...` or `deps/...` won't trigger CI on `push`. This is fine — the `pull_request` trigger fires when the PR is opened. Just don't wait for CI to run before creating the PR.

## Rule 8: PR Template Compliance

Some repos have `.github/pull_request_template.md` that Dependabot PRs won't follow:

```bash
curl -s "https://raw.githubusercontent.com/<owner>/<repo>/main/.github/pull_request_template.md"
```

When replacing a dependabot PR, fill in the template:
- **Summary** — what changed and why
- **Validation** — local checks run or CI coverage
- **Impact** — API, build, docs impact
- **AI Assistance** — disclosure checkbox

## GitHub Token Extraction

When `gh` CLI isn't available and `$GITHUB_TOKEN` isn't set, extract the token from the git credential helper:

```bash
# Works on Windows (git-bash), macOS, Linux
TOKEN=$(git credential fill <<< 'protocol=https
host=github.com
' | grep password | cut -d= -f2)
```

Use this token in curl commands: `-H "Authorization: token $TOKEN"`

## Pitfalls

- **Don't debug individual failures for stale PRs.** A PR based on a months-old commit that fails CI almost certainly has a stale-base problem. Replace it.
- **Compare raw files, not just `git diff`.** Stale references that weren't touched by the PR's changes won't appear in the diff.
- **Dependabot PR bodies never follow the repo's PR template.** When replacing one, check for `.github/pull_request_template.md` and fill it in.
- **Python urllib SSL on Windows**: Python 3.11 on Windows sometimes gets `ssl.SSLEOFError` when making rapid successive API calls. Use `curl` in terminal for reliability.
- **Case-insensitive filesystem**: When renaming files that differ only in case on Windows, use `git mv` (two-step through temp name). See `git-cross-platform-pitfalls` skill for details.

## References

- `references/stale-dependabot-after-rename.md` — Worked example: stale Dependabot PR after project rename
- `references/stale-dependabot-example.md` — Additional stale PR example with diagnostics
- `scripts/verify-rename.sh` — Verification script for post-rename repo checks
