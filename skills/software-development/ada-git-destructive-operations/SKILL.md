---
name: ada-git-destructive-operations
description: "Use when deleting local commits or resetting a branch."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [git, reset, branch, destructive, safety, recovery]
    related_skills: [ada-git-history-preserving-moves, ada-hermes-operations, github-pr-workflow]
---

# Git Destructive Operations

Safe handling of branch resets, local-commit deletion, and diverged-branch sync.
Trigger phrases: 删除本地提交 / 拉取最新 / 重置到 origin / 放弃这些提交 / discard local commits.

## Core Principle

> **Before destroying anything, know whether it can be recovered — and confirm the user's actual intent.**

"删除本地提交" is ambiguous. It can mean: hard-reset to a remote (discard N commits),
abort an in-progress merge, or rebase onto the remote. Always disambiguate with options.

## Workflow (verified)

### 1. Detect state before touching anything

```bash
git status            # diverged? (ahead N, behind M) / unmerged paths / staged changes?
git branch -vv        # which remote does each branch track?
```

- Unmerged paths + MERGE_HEAD ⇒ an in-progress merge is blocking the branch.
- Staged changes + conflicts will ALL be destroyed by `reset --hard` — warn explicitly.

### 2. Fetch and check for a remote backup

```bash
git fetch origin
git log --oneline origin/<branch> -N          # does the remote carry the same commits?
git rev-list --left-right --count <local>...origin/<branch>   # 0 0 ⇒ identical ⇒ full backup
```

If local commits exist on a remote branch, deletion is **recoverable** (`git reset --hard
origin/<branch>` or `git checkout -B` restores them). If they were never pushed, deletion
is irreversible — escalate confirmation.

### 3. Clarify intent with concrete options

Use `clarify` with distinct choices, never a bare yes/no:

1. Hard reset to `origin/main` — discard local N commits AND all worktree changes (recoverable only if pushed).
2. Abort the merge, keep the N commits, merge the remote in (conflicts to resolve).
3. Abort the merge, then rebase onto the remote (linear history, conflicts to resolve).

State the facts first: how many commits, whether they're pushed, what worktree changes exist.

### 4. Execute after confirmation

```bash
git reset --hard origin/main      # also clears the in-progress merge state
```

### 5. Verify

```bash
git status        # clean, "up to date with 'origin/main'"
git log --oneline -5
```

## Branch cleanup after Rebase-and-merge PRs

When a PR was merged with **Rebase and merge**, the local feature branch's
commits were rewritten onto `main` (new SHAs). Consequences:

- `git branch --merged main` will NOT list the feature branch — git compares
  SHAs, and the local tip SHA no longer exists in `main`'s history. The branch
  looks unmerged even though its content is fully merged.
- Same applies to squash merges (content merged, SHAs differ).

Safe cleanup sequence:

```bash
# 1. Confirm the content actually landed on main (do not trust --merged)
git log main --oneline | grep -iE "feature-title|PR-topic"
# 2. Delete merged branches; -D only for SHA-rewritten ones
git branch -d feature/content-catalog        # git confirms merged → safe
git branch -D feature/dock-zone-preview      # SHA rewritten by rebase → force
# 3. List remaining branches; keep unmerged ones (may hold in-progress work)
git branch -v
```

- Verify the main-side merge commit/topic exists BEFORE `-D`; a force-deleted
  branch whose work was never merged is unrecoverable.
- Leave unmerged branches (experiments, in-flight work) alone unless the user
  explicitly names them.

## Pitfalls

- **Never `git reset --hard` directly on a "delete commits" request.** The user may not know
  the commits were already pushed (then the branch work survives on the remote and reset is
  safe) — or may actually want to keep the work and only clear the merge mess. `clarify` with
  options costs one round-trip and prevents an irreversible mistake.
- **`reset --hard` silently kills unmerged paths + staged changes.** If `git status` shows
  conflicts or staged files, say so in the options before executing.
- **A clean branch after reset ≠ remote parity for other branches.** Verify which remote the
  branch tracks (`git branch -vv`); after resetting to `origin/main`, the local branch may
  still track a different remote branch.
- **Local-only commits have no recovery path.** Check `rev-list --left-right --count` BEFORE
  presenting options; if the count shows local-only commits, mark that option as destructive.

## Verification Checklist

- [ ] `git status` + `git branch -vv` captured before any destructive command
- [ ] `rev-list --left-right --count` confirmed whether local commits have a remote backup
- [ ] Options presented via `clarify`; user's choice recorded
- [ ] `reset --hard` executed only after explicit confirmation
- [ ] Post-reset `git status` clean and aligned with the intended remote
