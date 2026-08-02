# Ada Skill Quality Standard

This standard exists for Ada skills that are loaded by coding agents during real development work. The audience is the agent first, and the human developer second.

Ada skills should follow the Agent Skills progressive disclosure model:

1. `name` and `description` are loaded at discovery time.
2. `SKILL.md` is loaded when the task matches the description.
3. `references/`, `scripts/`, `assets/`, and `evals/` are loaded only when needed.

## Frontmatter

Every `SKILL.md` must have valid YAML frontmatter with:

```yaml
---
name: ada-example
description: Use when ...
license: MIT
metadata:
  hermes:
    tags: [...]
    related_skills: [...]
---
```

Rules:

- `name` must match the parent directory name.
- `description` is the trigger contract. It must explain when an agent should load the skill, including implicit development signals.
- `description` must stay below the Agent Skills hard limit of 1024 characters.
- Prefer 1-3 concrete sentences over a long catalog of internals.
- Use `compatibility` only when a skill has real environment requirements.
- Keep extra client-specific fields under `metadata`.

## Description Quality

A good description helps the agent decide correctly before reading the full skill.

Include:

- User intent: what the user is trying to accomplish.
- Technical signals: file types, frameworks, tools, errors, or workflow phase.
- Boundary with adjacent skills when confusion is likely.
- Pushy implicit triggers for development work. Example: use verification skills after editing matching project files, even if the user did not say "verify".

Avoid:

- Marketing summaries.
- Generic claims like "improves quality".
- Long lists of implementation details.
- Triggers that are so broad they steal tasks from neighboring skills.

## SKILL.md Body

The main file should be an execution protocol, not a long essay.

Recommended sections:

```markdown
## Activation
## Do Not Use When
## Inputs
## Workflow
## Mandatory Checks
## Stop Conditions
## Output Contract
## References
```

Keep high-value gotchas in `SKILL.md` when the agent needs them before acting. Move long examples, historical cases, templates, and platform-specific deep dives into `references/`.

## Agent Execution Contract

Skills that guide development work should tell the agent:

- What evidence to gather before editing.
- Which files or commands to inspect first.
- Which validation command proves the work.
- When to stop and ask the user.
- What final output shape to use.

For audit/review skills, every finding should include:

- Claim
- Evidence with file path and line when available
- Risk
- Recommended action
- Verification performed or still needed

For debugging skills, require a tight feedback loop before proposing fixes.

For refactoring skills, require phase boundaries and validation gates.

For document/SRS skills, require traceability and consistency checks.

## References

Use relative links from the skill root:

```markdown
Read `references/gotchas.md` when the task involves Windows packaging.
Run `scripts/verify_srs_consistency.py` after editing SRS requirement IDs.
```

Keep references one level deep. Do not create reference chains where one reference requires reading several more references before acting.

## Evals

High-value skills should include `evals/evals.json`.

Minimum useful eval set:

- 4-6 should-trigger prompts
- 4-6 should-not-trigger prompts
- 2-4 output quality assertions

Prioritize near-miss prompts. A negative prompt that shares keywords with the skill is more useful than an obviously unrelated one.

The validator reports the 4/4 trigger boundary as an advisory warning so legacy
skills can be improved incrementally instead of receiving mechanically padded
cases. A new or materially revised high-value skill must meet the boundary before
merge; existing warnings are explicit quality debt, not a passing-quality claim.

## Automated Distribution Gate

Run all commands before each commit and again before opening a pull request:

```bash
python -m unittest scripts/tests/test_validate_skill_quality.py -v
python scripts/validate_skill_quality.py
python scripts/smoke_profile_distribution.py
```

The validator uses PyYAML, which is already a Hermes runtime dependency. If it
is run from an unrelated Python environment, install PyYAML there first; the
gate deliberately fails closed rather than approximating YAML with regular
expressions.

The smoke test redirects `HERMES_HOME` to a temporary directory, installs a
temporary copy of the repository, updates distribution-owned content, and
verifies that memory, session, and `local/` markers survive. It never installs
the test Profile into the user's real Hermes home.

The validator enforces:

- exact agreement between `distribution.yaml`, the physical Skill directories,
  and the README catalog/count;
- manifest and README version agreement;
- parseable YAML manifest/frontmatter with duplicate-key rejection, an exact opening fence, a non-empty body,
  Agent Skills-compatible names, and the 500-line main-file progressive-disclosure
  limit;
- existing local `references/`, `assets/`, and `evals/` links; Markdown links to
  `scripts/` and `templates/` are always local, while backticked paths are local
  when those resource directories exist beside the Skill;
- valid references to other distributed `ada-*` Skills;
- parseable object-shaped evals with unique IDs, typed prompts/expected output,
  trigger booleans, and non-empty assertions;
- exclusion of common private runtime-state paths such as credentials, memories,
  sessions, workspaces, plans, `local/`, logs, caches, and state databases. In a
  Git top-level checkout this scans tracked and non-ignored untracked files, so
  ignored developer caches do not create false positives. A nested or non-Git
  validation root falls back to a conservative full-tree scan.

The automated gate is necessary but not sufficient. It cannot prove that a Skill
is useful, correctly scoped, legally distributable, or free from stale project
assumptions; those remain qualitative review responsibilities.

## Review Checklist

- [ ] `name` matches the directory.
- [ ] `description` is under 1024 characters and describes when to use the skill.
- [ ] Main `SKILL.md` is under 500 lines or has a clear split plan.
- [ ] Direct `references/` and `scripts/` links exist.
- [ ] Related skill names use actual installable names.
- [ ] The skill has activation, stop conditions, validation, and output contract when it guides agent development work.
- [ ] Large examples or templates live in `references/`.
- [ ] Important skills have trigger and output evals.
