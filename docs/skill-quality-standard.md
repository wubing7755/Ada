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

## Review Checklist

- [ ] `name` matches the directory.
- [ ] `description` is under 1024 characters and describes when to use the skill.
- [ ] Main `SKILL.md` is under 500 lines or has a clear split plan.
- [ ] Direct `references/` and `scripts/` links exist.
- [ ] Related skill names use actual installable names.
- [ ] The skill has activation, stop conditions, validation, and output contract when it guides agent development work.
- [ ] Large examples or templates live in `references/`.
- [ ] Important skills have trigger and output evals.
