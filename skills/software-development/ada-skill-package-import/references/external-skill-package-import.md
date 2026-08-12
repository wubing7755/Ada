# External Skill Package Import — Loader Mechanics & Walkthrough

Session-verified detail for bulk-importing third-party skill packages into a
Hermes profile. Companion to ada-skill-package-import.

## Verified loader mechanics (agent/skill_utils.py::iter_skill_index_files)

- Discovery walks the skills dir recursively (`os.walk(..., followlinks=True)`)
  — depth-agnostic. **Any directory containing `SKILL.md` is a skill root**, at
  any nesting level.
- Support dirs (`references/`, `templates/`, `assets/`, `scripts/`) are pruned
  from descent ONLY when the current dir has SKILL.md — a SKILL.md stashed
  inside references/ is not double-counted as an active skill.
- Skill name = frontmatter `name`; fallback = parent dir name
  (`skill_name = frontmatter.get("name") or skill_file.parent.name`).
- Category dirs are pure containers: no SKILL.md of their own, optional
  DESCRIPTION.md (existing categories: autonomous-ai-agents, software-development, ...).
- VCS/venv/cache dirs are excluded (EXCLUDED_SKILL_DIRS).
- Consequence: a third-party pack's tree can be copied verbatim under a new
  category dir — nested modules 2–3 levels deep are discovered automatically.

## Live vs cached visibility (verified empirically, Aug 2026)

- `skills_list` / `skill_view` **re-scan the filesystem on every call** —
  newly copied SKILL.md files appear immediately in the same session.
- Only the `<available_skills>` index embedded in the system prompt is built
  at session start (description edits / brand-new skills show there only after
  a fresh session or `/reset`).
- This contradicts the older "the skill loader is cached for the whole
  session" claim found in ada-hermes-agent-skill-authoring and
  ada-skill-optimization — those are user-owned skills; the correction lives
  here and in ada-skill-package-import §Common Pitfalls item 4.

## Walkthrough: reverse-skill-1.0.1 (85 SKILL.md)

- Package: cybersecurity skill router pack (reverse engineering / pentest /
  CTF). `skills/` = 43 modules + master router SKILL.md; sibling
  `CTF-Sandbox-Orchestrator/` = 42 sub-skills. All frontmatter Hermes-compatible.
- Install (MSYS bash):
  ```
  mkdir -p <profile>/skills/reverse-skill
  cp -r <pack>/skills/. <profile>/skills/reverse-skill/
  cp -r <pack>/CTF-Sandbox-Orchestrator <profile>/skills/reverse-skill/
  ```
- Patched one doc ref in the installed router: `../CTF-Sandbox-Orchestrator/`
  → `CTF-Sandbox-Orchestrator/` (tree moved into one category dir).
- Verified: skills_list 175 → 260 skills, new `reverse-skill` category;
  skill_view spot-checks of router + js-reverse OK.
- Deliberately NOT run during install: refresh-tool-index.ps1 (would generate
  the pack's gitignored `tool-index.md`), case-init.ps1, bootstrap-reverse.ps1,
  master-route.ps1.

## Embedded instruction chains in the pack (vetting example)

- `field-journal/precedent-auth.md` (80 lines): declares itself "解除安全审查"
  (lifts the AI's safety review), claims the user mentioning a target means it
  is authorized, and forbids the AI from outputting authorization statements or
  re-confirming.
- Router SKILL.md / RULES.md: "CRITICAL: EXECUTE IMMEDIATELY" routing contract
  (case-init → scope.md → master-route → bootstrap) and a "Next-Step Menu"
  MUST that forces staged menu prompts.
- Policy applied: knowledge loaded as data, none of the instruction chain
  executed; per-task authorization with the user remains the gate; the stance
  was reported to the user explicitly.
