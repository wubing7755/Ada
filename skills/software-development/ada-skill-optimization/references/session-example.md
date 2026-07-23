# Session Example: 12 local skills → optimized

Concrete walkthrough from a real session. Numbers are illustrative of the
process, not targets.

## Step 0: Pre-check

```bash
hermes skills list
# Output: 62 builtin, 17 local, 0 hub — 79 total
```

## Step 1: Inventory — identify agent-created vs user-installed

Parse `.usage.json`:
```python
with open(".hermes/skills/.usage.json") as f:
    usage = json.load(f)
agent = {k for k, v in usage.items() if v.get("created_by") == "agent"}
# Result: 12 agent-created (2 already dead: 1 archived, 1 never used)
```

Remaining 7 local skills were user-installed (5 never used), 2 active.

## Step 2: Diagnose

| Issue found | Skills affected |
|---|---|
| Never used (user-installed) | apikey-image-gen, grok-image-to-video, hyperframes, markdown-viewer, remotion |
| Never used (agent-created) | requirements-authoring (0 uses), documentation-restructure (archived) |
| CPack content duplicated | c-project-template §Release Packaging duplicated cmake-cpack-release |
| Missing license/metadata | git-workflow, docs-restructure, c-project-template, career-transition-planning, project-rename, can-dbc-format |
| Description >120 chars | cmake-cpack-release (~300), career-transition-planning (~280), project-rename (~250), can-dbc-format (~220), c-project-template (~150) |
| Memory at 94% (2,068/2,200) | CPack rules, PR template, Word formatting, SRS principles already in skills |

## Step 3: Execute fixes (P0→P1→P2)

### P0-1: Delete 5 never-used user-installed skills
```python
# skill_manage(action='delete') for each — hermes skills uninstall only
# works for hub-installed skills
```

### P0-2: Patch frontmatter for 6 skills
Added `license: MIT` + `metadata.hermes.tags` block. For `can-dbc-format`,
moved `tags:` from top-level to `metadata.hermes.tags`.

### P0-3: Dedup CPack
Replaced 210 lines in c-project-template with 65 lines. Kept template-specific
install rules and package contents table; replaced all general CPack/NSIS/CI
content with a pointer to cmake-cpack-release.

### P1-1: Compress 5 descriptions
All descriptions now ≤120 chars, "Use when <trigger>" format.

### P1-2: Enable curator consolidation
```bash
hermes config set curator.consolidate true
```

### P1-3: Memory cleanup
Removed 4 entries already covered by skills. Memory: 94% → 58%.

### P2: Export for migration
```python
# Zip 12 local skills maintaining directory structure
# Output: Desktop/hermes-local-skills.zip (78 KB, 27 files)
```

## Step 4: Verify

```bash
hermes skills list
# Output: 60 builtin, 12 local, 0 hub — 72 total ✓ (was 62+17=79)

# Memory: 1,297/2,200 (58%) ✓
# curator.consolidate: true ✓
# No description >120 chars ✓
```

## Unexpected: CC Switch injection

After export, `hermes skills list` showed 19 local skills — 7 new ones appeared.
Cause: CC Switch's "share to Hermes" feature silently wrote 6 Microsoft Foundry
skills + 1 auto-generated `skill-optimization` skill directly into
`~/.hermes/skills/`.

Lesson: CC Switch writes to `~/.hermes/skills/` without asking. Skills appear as
`local` source with no `.usage.json` entry.
