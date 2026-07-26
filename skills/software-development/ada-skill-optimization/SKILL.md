---
name: ada-skill-optimization
description: "Use when auditing, optimizing, or maintaining Hermes agent-created skills — frontmatter fixes, description compression, content dedup, memory migration, curator setup, and cross-machine skill export."
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, skills, audit, optimization, maintenance, curator, memory]
    related_skills: [ada-hermes-agent-skill-authoring]
---

# Hermes Skill Optimization

Audit and optimize user-side (agent-created + local) skills for quality,
token efficiency, and maintainability.

## Overview

This skill covers the full maintenance lifecycle for user-side Hermes skills: inventory
discovery (cross-referencing `hermes skills list` with `.usage.json`), diagnostic
classification (premature creation, duplicate content, missing frontmatter, verbose
descriptions >120 chars, content bloat >14K chars, stale/unused), frontmatter
standardization (license, tags under `metadata.hermes.tags`, related_skills),
description compression to ≤120 chars in "Use when <trigger>" format, cross-skill
content deduplication (replacing duplicated prose with one-line pointers), memory-to-
skill migration (removing procedural rules from memory that duplicate a skill), curator
setup for automated lifecycle management, and cross-machine export via zip. The skill
also detects and handles external tool skill injection (e.g., CC Switch writing
directly to `~/.hermes/skills/` without `.usage.json` entries).

## When to Use

- User asks to audit, review, or optimize skills
- After discovering skill quality issues (missing frontmatter, description bloat)
- When preparing skills for export to another machine
- After memory fills up and needs migration to skills
- **When `hermes skills list` shows unexpected local skills** — suspect external tool injection
- User says "这些 skill 有什么优化空间" or asks about skill quality


Don't use for: creating new skills — follow standard skill authoring conventions. One-off skill fixes — this skill is for systematic batch audits. Skill deletion decisions — this skill audits and recommends, but deletion requires user confirmation.

## Workflow

### 1. Inventory — full picture, not just `.usage.json`

```bash
hermes skills list          # breakdown: builtin / hub / local
```

Parse `.usage.json` for agent-created skills:

```python
import json
with open(".hermes/skills/.usage.json") as f:
    usage = json.load(f)
agent_skills = {k: v for k, v in usage.items() if v.get("created_by") == "agent"}
```

### 2. Diagnose — classify every issue

Cross-reference `hermes skills list` (canonical source) with `.usage.json` (usage
data). Skills appearing in the list but NOT in `.usage.json` are either:

- **Never used** — recently created or hub-installed but not loaded
- **External-tool injected** — CC Switch, etc., write directly to `~/.hermes/skills/`
  without updating `.usage.json`. Check file modification times with
  `ls -lt ~/.hermes/skills/*/SKILL.md` to spot recent injections.

| Problem | Signal | Fix |
|---------|--------|-----|
| Premature creation | `use_count == 0` | Delete via `skill_manage(action='delete')` |
| Duplicate content | Same prose in two skills | Replace with cross-reference, keep authoritative source |
| Missing frontmatter | No `license`, no `metadata.hermes.tags` | Patch to add both |
| Verbose description | >120 chars or not "Use when..." | Compress to trigger-focused ≤120 chars |
| Content bloat | File >14K chars | Split bulky sections to `references/` |
| Stale / unused | No use in 14+ days | Let curator auto-archive |

### 3. Frontmatter Standard

Every agent-created skill must end its frontmatter with:

```yaml
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [relevant, tags, here]
    related_skills: [other-skill]  # if applicable
```

Common gaps: `tags:` at top level instead of under `metadata.hermes.tags`;
missing `license: MIT`; description using YAML folded `>` instead of simple string.

### 4. Description Compression

Descriptions are injected into every turn's `<available_skills>` block — each
character costs tokens. Target: ≤120 chars, "Use when <trigger>" format.

| Before (bad) | After (good) |
|---|---|
| `Patterns for C project template development — setup wizards, bilingual C programs, build system integration, and file operations in portable C11.` | `Use when developing or extending C/CMake project templates with interactive setup wizards.` |
| `CPack multi-platform release packaging for C/CMake projects — NSIS (Windows), DEB/RPM (Linux), productbuild/TGZ (macOS), GitHub Actions CI, Windows VERSIONINFO resources...` | `Use when packaging C/CMake projects for release — CPack NSIS/DEB/RPM, GitHub Actions CI.` |

### 5. Content Dedup

When Skill A duplicates substantial content from Skill B:

1. Keep the authoritative source (Skill B) intact
2. In Skill A, replace the duplicated section with a one-line pointer:
   ```markdown
   > For CPack details, see **cmake-cpack-release** skill.
   ```
3. Keep only content **unique to Skill A's domain**

### 6. Memory → Skill Migration

Memory stores preferences + environment facts, NOT procedural knowledge.
When you find procedural rules in memory that duplicate a skill, remove them.

```python
# If memory has:
#   "CPack NSIS on MSYS2/CMake 4.x: MENU_LINKS ignored..."
# → already in cmake-cpack-release skill → remove from memory
memory(operations=[
    {"action": "remove", "old_text": "CPack NSIS on MSYS2"},
])
```

Target: keep memory under 70% capacity.

### 7. Curator Setup

```bash
hermes config set curator.consolidate true
hermes config set curator.stale_after_days 14
hermes config set curator.archive_after_days 30
```

### 8. Export for Migration

```bash
cd ~/.hermes/skills
python -c "
import zipfile, os
skills = ['skill-a', 'category/skill-b', ...]  # list local skills
out = os.path.expandvars(r'%USERPROFILE%\\Desktop\\hermes-local-skills.zip')
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
    for s in skills:
        for root, dirs, files in os.walk(s):
            for f in files:
                zf.write(os.path.join(root, f))
print(f'Done: {out}')
"
```

Import on target machine: `unzip hermes-local-skills.zip -d ~/.hermes/skills/`

## Common Pitfalls

1. **`hermes skills uninstall` only works for hub-installed skills.** For local
   skills, use `skill_manage(action='delete', name='...')`.

2. **`skill_manage(action='patch')` on bundled skills is refused.** Bundled skills
   are read-only. Create a new user-local skill or add references/ to an existing
   local umbrella instead.

3. **`memory(remove)` needs exact substring match.** Copy the text from the
   system prompt's MEMORY block directly as `old_text`.

4. **Description changes don't take effect until `/reset`.** The skill loader
   is initialized at session start.

5. **`.usage.json` may not have entries for never-used skills.** Always
   cross-reference with `hermes skills list` for the full picture.

6. **Flat vs categorized directories.** Agent-created skills may live at
   `skills/<name>/` (flat) while hub-installed ones use `skills/<category>/<name>/`.
   `hermes skills list` shows the canonical location — follow it.

7. **External tools can inject skills silently (CC Switch, etc.).** If `hermes
   skills list` shows more local skills than expected, check for recent files with
   `ls -lt ~/.hermes/skills/*/SKILL.md`. CC Switch writes directly to
   `~/.hermes/skills/` when its "share to Hermes" feature is active. Injected
   skills have no `.usage.json` entry and appear as `local` source. Delete
   unwanted ones with `skill_manage(action='delete')`. To prevent future
   injection, disable the feature in the external tool.

8. **`hermes skills list` output can be stale.** If you just deleted or added
   skills and the count didn't change, the list is cached from session start.
   Run `/reload-skills` or start a new session.

## Verification Checklist

After optimization:
- [ ] `hermes skills list` shows correct count and all local skills enabled
- [ ] No unexpected local skills from external tool injection
- [ ] Memory usage report shows <70%
- [ ] `curator.consolidate: true` in config.yaml
- [ ] Exported zip opens correctly on target machine
- [ ] No skill description exceeds 120 characters

## References

- `references/skill-provenance-audit.md` — Three-directory cross-reference technique to classify skills by source (system core / ecosystem repo / user-created)
- `references/session-example.md` — Concrete walkthrough: 12→12 local skills
  after pruning 5 unused, fixing 6 frontmatter, deduping CPack, compressing
  descriptions, cleaning memory, and detecting CC Switch injection.
