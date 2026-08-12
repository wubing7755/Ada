---
name: ada-git-history-preserving-moves
description: 'Use when git history must survive renames: git mv, --follow.'
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [git, rename, history, migration, documentation]
    related_skills: [repository-documentation, ada-docs-revision]
---

# Git History-Preserving Moves

Use when moving or renaming files in a git repository and the pre-move history
must remain traceable via `git log --follow <new-path>`. Classic triggers:
README language cutover (`git mv README.md README.zh-CN.md` + new English
`README.md`), doc tree restructuring, file renames with a same-path replacement.

## Core Rules

1. **Use `git mv`** for the rename so the intent is explicit, then verify the
   staged diff actually records a rename.
2. **Verify rename detection BEFORE committing**:
   ```bash
   git diff --cached --name-status HEAD
   # want:  R###  old/path  new/path   (similarity score, e.g. R098)
   # bad:   M     old/path            +  A  new/path
   ```
3. **Verify history AFTER committing**:
   ```bash
   git log --oneline --follow -- new/path
   # must show the rename commit AND all commits from before the move
   ```

## Pitfall: one commit cannot record a rename when a same-path replacement exists

Moving `README.md` → `README.zh-CN.md` while also adding a NEW `README.md`
(English) in the SAME commit produces `M README.md + A README.zh-CN.md`, not a
rename — even if you used `git mv` first.

Why: git pairs HEAD's old `README.md` (Chinese) with the index's new `README.md`
(English) as a same-path "modified pair". That consumes the rename source, so the
old Chinese blob can never be paired as a rename into `README.zh-CN.md`
(`diff.breakRewrites` defaults to false, so modified pairs are never broken).
Result: `git log --follow -- README.zh-CN.md` loses the original history.

**Fix — split into two commits**:
- commit 1: pure `git mv` rename, plus any small edits to the moved file.
  Staged diff MUST show `R###`.
- commit 2: add the new same-path file (the replacement) + any validator/test
  changes that depend on the new layout.

Intermediate commit 1 may fail validators/CI by itself — acceptable when CI only
runs on the PR merge result (pull_request event) or on protected branches.

## Recovery: index already staged wrong

Working-tree files are intact; only the staged state is broken. Do NOT re-add
blindly — the modify pair persists. Rebuild the rename:

```bash
mkdir -p /tmp/rename-fix
cp NEW_FILE /tmp/rename-fix/new.bak                      # backup replacement
cp MOVED_EDIT /tmp/rename-fix/moved.final.bak            # backup edited moved file
git reset -q                                             # unstage (working tree untouched)
git checkout -- OLD_PATH                                 # restore HEAD version to worktree
rm -f NEW_PATH                                           # git mv target must not exist
git mv OLD_PATH NEW_PATH                                 # staged rename
cp /tmp/rename-fix/moved.final.bak NEW_PATH              # restore the edits
git add NEW_PATH                                         # → commit 1
cp /tmp/rename-fix/new.bak OLD_PATH
git add OLD_PATH scripts/...                             # → commit 2
```

Key details: `git reset` does NOT restore working-tree files; `git mv` fails
with "destination exists" if the target is still in the working tree.

## Session-verified example

A README bilingual cutover using the two-commit fix produced
`R098 README.md README.zh-CN.md` in the staged diff and a full `--follow`
history — the exact commands are in the recovery recipe above.

## Related Tool Quirks

`read_file` may flag UTF-8 Markdown containing Chinese (especially CRLF files)
as "Binary file - cannot display as text". Read such files with:
```bash
python -c "print(open('file.md', encoding='utf-8').read())"
```
`patch` (replace mode) still works normally on those files.

## Verification Checklist

- [ ] Rename staged as `R###` (checked via `git diff --cached --name-status HEAD`)
- [ ] `git log --oneline --follow -- <new-path>` shows pre-move commits
- [ ] New same-path file committed separately from the rename
- [ ] Validator/tests updated atomically with the layout change
