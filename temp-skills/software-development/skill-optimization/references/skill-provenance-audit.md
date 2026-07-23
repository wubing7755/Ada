# Skill Provenance Audit — Three-Directory Cross-Reference

Classify every runtime skill by source: system core, ecosystem repo, or user-created.

## The Three Directories

| # | Directory | What It Is |
|---|-----------|-------------|
| 1 | `~/AppData/Local/hermes/hermes-agent/skills/` | **System core** — shipped with Hermes |
| 2 | `~/source/repos/hermes-use/skills/` | **Ecosystem repo** — Hermes open-source repo clone (may vary by machine) |
| 3 | `~/AppData/Local/hermes/skills/` | **Runtime** — what's actually loaded this session |

Additional external directories (not Hermes) may exist, e.g. `~/.cc-switch/skills/` (Claude Code switch tool). These are separate toolchains and should be counted but excluded from Hermes provenance analysis.

## The Technique

```bash
# 1. Extract skill names (strip path prefix, keep category/name)
find ~/AppData/Local/hermes/hermes-agent/skills/ -name "SKILL.md" | \
  sed 's|.*/hermes-agent/skills/||;s|/SKILL.md||' | sort -u > /tmp/core.txt

find ~/source/repos/hermes-use/skills/ -name "SKILL.md" | \
  sed 's|.*/hermes-use/skills/||;s|/SKILL.md||' | sort -u > /tmp/repo.txt

find ~/AppData/Local/hermes/skills/ -name "SKILL.md" | \
  sed 's|.*/hermes/skills/||;s|/SKILL.md||' | sort -u > /tmp/runtime.txt

# 2. Count totals
wc -l /tmp/core.txt /tmp/repo.txt /tmp/runtime.txt

# 3. Runtime skills NOT in system core → "acquired/installed"
comm -23 /tmp/runtime.txt /tmp/core.txt | wc -l

# 4. Acquired skills that ARE in hermes-use repo → ecosystem-installed
comm -23 /tmp/runtime.txt /tmp/core.txt | comm -12 - /tmp/repo.txt

# 5. Acquired skills NOT in system core AND NOT in hermes-use → truly user-created
comm -23 /tmp/runtime.txt <(sort -u /tmp/core.txt /tmp/repo.txt)
```

## Provenance Categories

| Category | Criteria | Count (example session) |
|----------|----------|------------------------|
| 🔵 System core | In `hermes-agent/skills/` | 72 |
| 🟢 Ecosystem (repo) | In hermes-use repo but not core | 39 |
| 🟡 User-created | Only in AppData runtime | 26 |
| **Total runtime** | | **137** |

## Caveats

- `openclaw-imports/*` skills often appear as "user-created" but are actually imported from external toolchains (OpenClaw/Microsoft Foundry). Deduct these from the truly user-created count if desired.
- The `hermes-use` repo path may differ per machine. Check with `ls ~/source/repos/*/skills/` to discover alternatives.
- Skills registered without a `SKILL.md` file (e.g. plugin-provided) won't appear in `find` output but will show in `skills_list`.
