---
name: ada-git-pr-delivery
description: "Use when uncommitted work becomes a PR on a fresh branch."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [git, pr, delivery, branching, gates]
    related_skills: [ada-continuous-phased-delivery, ada-requesting-code-review]
---

# Git PR Delivery

Turn a worktree full of uncommitted changes (possibly mixed user edits + agent work)
into a clean PR on top of an updated main, without losing or mis-committing anything.

## Trigger

- User asks: "切到 main / 拉最新 / 新开分支 / 把这个修改都带过去 / 提交 PR" (or the
  English equivalent), and the worktree has uncommitted changes based on an older branch.

## Steps

1. **Fetch and inspect first**: `git fetch origin`, then
   `git log --oneline <old-branch>..origin/main`. Squash-merged PRs make main's content
   identical to the old branch but with different commits — expect this.
2. **Do NOT checkout main while the local main pointer is stale.** `git checkout main`
   will be rejected with *"Please commit your changes or stash them"* — the refusal here
   is about the stale target pointer conflicting with the worktree, NOT a dirty-worktree
   policy. Fix the pointer from the current branch: `git branch -f main origin/main`
   (safe when main has no uncommitted changes), then `git checkout main`. Uncommitted
   changes carry over automatically.
3. **Confirm the full set survived**: `git status --short | wc -l` before/after; the
   count should be identical.
4. **Create the work branch** (`git checkout -b feat/...`) and stage everything, but
   first exclude local tooling dirs (e.g. `.qwen/` IDE/plugin config) by appending them
   to `.gitignore`. Verify before committing:
   - `git check-ignore -v <path>` matches the excluded path;
   - `git diff --cached --name-only | grep -cE "(^|/)(bin|obj)/|\.db$|TestResults"` is 0
     (no build artifacts / databases / test output staged).
5. **Commit** with a conventional message summarizing the actual content (scope bullets,
   test counts, coverage) — a PR whose message matches reality is easier to review.
6. **Re-run gates in CI order** before opening the PR (restore --locked-mode → content
   conversion → CSS bundle → Release build → full test suite → format), not just the
   tests. The PR body's Validation checklist must match what was actually run — never
   tick boxes the run didn't cover.
7. **Fill the repo PR template** exactly (`.github/pull_request_template.md`, sections
   like Summary / SRS Coverage / Validation / Impact / AI Assistance). Write the body to
   a temp file, `gh pr create --base main --head <branch> --title ... --body-file <tmp>`,
   then delete the temp file.
8. **Verify the PR actually opened cleanly**:
   `gh pr view <n> --json state,mergeable,baseRefName,headRefName,url,statusCheckRollup`
   — confirm OPEN / MERGEABLE and CI checks started.

## Commit Conventions & PR Base Determination

- Conventional Commits (`fix:`, `feat:`, `docs:`, ...) in **English** (user
  preference: chat in Chinese, code and commit messages in English). One
  logical change per commit.
- Frontend tooling varies by repo: some repos have no `package.json` (tsc
  unavailable — do not npm-install without asking); others DO have one for
  TS→JS compilation (`npm ci && npm run build:js` before dotnet build). Check
  the repo's actual state before assuming.
- Pre-commit verification: `git status` + `git diff --stat` for scope; for
  renames, search the whole repo for the OLD symbol name to confirm no stale
  callers remain; if no compiler is available, state explicitly that
  verification was static (search-based), not compiled.
- **PR base determination (branch topology)**: Do NOT trust
  `refs/remotes/origin/HEAD` — it may point at a stale branch (e.g. master =
  one-shot initial import). Map the topology before choosing the base:
  `git branch -a`, `git symbolic-ref refs/remotes/origin/HEAD`,
  `git merge-base dev <candidate-base>`, `git log --oneline <candidate-base>..dev`
  (exactly what the PR would contain), `git diff --stat dev <candidate-base>`.
  Pick the base whose `..dev` log contains ONLY the intended commits. Common
  pattern: `master` = initial import, `main` = real dev line → PR base is
  `main`, not `master`.

## User PR Conventions

- **Local commits also require user review** — do NOT `git commit` (even
  locally, unpushed) without explicit confirmation. Present the staged change
  list and wait for approval; `git add` is fine to stage, `git commit` is not.
- Linear history; new PRs merged with **Rebase and merge**. Never rewrite
  already-merged public history.
- **Before starting any new work, switch to main and pull the latest** —
  `git checkout main && git pull --ff-only origin main`; `--ff-only` surfaces
  a diverged local main immediately instead of forking from a stale base.
- User often performs merge/publish in the web UI themselves — pushing +
  opening the PR is usually the deliverable.
- **PR body format follows the repo's `.github/pull_request_template.md`**:
  sections `## Summary` (What changed / Why), `## Validation` (checklist of
  build/test/format + manual smoke, or "Not run; reason:"), `## Impact`
  (public API / NuGet dependency / documentation), `## AI Assistance`
  (disclose AI usage). Drop sections the repo doesn't support; adapt the
  Validation checklist to the repo's actual commands. GitHub only
  auto-prefills from the **target** branch's template, so the template lands
  in the repo first, then future PRs pre-fill.
- **Branch names and PR titles must be semantic and self-explanatory**: no
  meaningless phase codes like `phase1-4`. Use `feat/backend-integration`
  not `feat/backend-integration-phase1-4`; if a phase number adds real
  meaning, pair it with semantics (`feat/backend-integration-phase1`).

## Pitfalls

- `git branch -f main origin/main` while ON main is dangerous (moves the branch you are
  standing on); only run it from a different branch.
- If checkout is rejected and `git status` shows legitimately conflicting changes, do NOT
  `stash`/`reset` — resolve the pointer first (step 2) before considering stash.
- PR templates with AI-disclosure sections: mark the disclosure checkbox truthfully; the
  validation checklist is a promise about what was run.
- Unit suites often do not read runtime config files (e.g. `config.api.json`). If such a
  file was flipped for manual/browser testing, restore its committed default before
  committing, and verify the restored file with a targeted ad-hoc check, not the suite.
- **Windows gitignore matching is case-insensitive.** A lowercase pattern like
  `src/Api/media/` silently ignores a source directory `Media/` (different
  case), leaving source files untracked — the local build passes (files exist on disk),
  but a fresh clone fails to compile. Symptom: `git add <source-file>` says "paths are
  ignored by one of your .gitignore files" for a file that should be committed.
  Mitigation: before committing a new source directory, verify the on-disk source set
  equals the tracked set (`git ls-files --others <dir>` shows untracked incl. ignored),
  and confirm `git check-ignore -v <source-file>` does NOT match. Fix the pattern to the
  precise runtime path (e.g. `.../media/uploads/` instead of `.../media/`).
