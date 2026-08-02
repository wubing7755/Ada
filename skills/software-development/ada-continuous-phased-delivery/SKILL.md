---
name: ada-continuous-phased-delivery
description: "Use after a user has approved a multi-phase implementation plan and explicitly wants continuous autonomous execution through bounded phases. Enforces authorization envelopes, per-phase verification, independent review, recoverable checkpoints, Git discipline, and stop conditions without asking for routine confirmation after every green phase."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [delivery, orchestration, phased-execution, verification, git]
    related_skills: [ada-agent-assisted-development, ada-requesting-code-review, ada-test-driven-development]
---

# Continuous Phased Delivery

Execute an already approved plan continuously while preserving safety, reviewability, and truthful evidence. “Continuous” removes routine pauses; it does not expand permissions or waive gates.

## Activation

Use only when all are true:

- an implementation plan or equivalent task breakdown exists;
- the user explicitly approved execution;
- the work has multiple bounded phases;
- routine progress can continue without product decisions between phases.

## Do Not Use When

- The task is still discovery or planning.
- Requirements or architecture choices remain materially ambiguous.
- The user requested review after every phase.
- Work requires credentials, publication, release, destructive migration, payment, or other unapproved side effects.
- A single focused change does not need phased orchestration.

## Authorization Envelope

Before changing files, record:

| Dimension | Required decision |
|---|---|
| Goal | observable final outcome |
| Scope | allowed repositories, modules, and documents |
| Mutations | file edits, branch/commit/PR permissions |
| Exclusions | secrets, private state, unrelated refactors |
| Gates | tests, format, package, browser, review |
| Escalation | conditions that require the user |

Never infer authority for push, merge, release, credential use, destructive commands, or external publication from authority to edit code.

## Phase Loop

For each phase:

1. **Freeze scope** — identify owning files, requirement, and expected behavior.
2. **Establish baseline** — read current state and run the narrowest meaningful check.
3. **Implement one coherent slice** — avoid mixing unrelated cleanup.
4. **Verify locally** — run focused checks, then the phase gate.
5. **Review the live diff** — re-read changed files and check scope, safety, and evidence.
6. **Checkpoint** — record result and create a coherent commit only when authorized.
7. **Continue automatically** — proceed when the phase is green and remains inside the envelope.

Only one phase is in progress at a time. Failed phases are repaired or explicitly stopped; they are never silently carried forward.

## Evidence Ladder

Label evidence precisely:

- **Focused** — one behavior or module.
- **Phase** — all work in the current slice.
- **Repository** — documented full project gates.
- **Distribution/Package** — packed or installed artifact.
- **Runtime** — actual browser/service/device behavior.

Do not promote lower-tier evidence into a higher-tier completion claim.

## Independent Review

Use a fresh read-only reviewer after high-risk or multi-file phases and before PR completion. Supply the requirement, exact diff, tests, prior findings, and known residuals. Verify reviewer claims against the live worktree before acting.

## Git Discipline

When Git delivery is authorized:

- start from an updated default branch and create a named work branch;
- make each commit coherent, buildable, and conventionally named;
- re-run affected gates before each commit;
- push only the work branch;
- create a PR with scope, decisions, evidence, risks, and AI disclosure;
- merge only after required CI/review passes and merge authority is clear;
- treat tags and releases as separate publication operations.

## Automatic Continuation Conditions

Continue without asking only when:

- the next step is explicitly in the approved plan;
- no new product or architecture decision is required;
- permissions and data boundaries are unchanged;
- verification is green or a local, reversible fix is clear;
- the action is recoverable and does not publish externally beyond approved Git delivery.

## Stop Conditions

Stop and report immediately when:

- evidence contradicts the plan or requirement;
- scope must expand materially;
- the same gate fails repeatedly without a grounded root cause;
- user-owned changes conflict with the phase;
- a secret, permission prompt, destructive operation, or irreversible migration appears;
- release/merge authority is missing;
- a required environment or dependency cannot be obtained safely.

## Output Contract

Maintain a phase ledger with status, files, verification, commit/PR handle when applicable, and residual risk. Final reporting must distinguish completed execution from planned or blocked work and include the exact artifact and verification results.
