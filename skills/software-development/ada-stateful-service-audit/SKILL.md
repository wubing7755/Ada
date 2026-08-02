---
name: ada-stateful-service-audit
description: "Use when auditing a mutable service, store, context, or facade that owns commands, persistence, events, concurrency, interop callbacks, undo/redo, or duplicated state. Reconstructs real mutation paths and verifies transaction, invariant, history, restore, notification, and failure-atomicity contracts."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [audit, state, persistence, concurrency, undo-redo]
    related_skills: [ada-code-quality-analysis, ada-systematic-debugging, ada-project-audit]
---

# Stateful Service Audit

Audit behavior and mutation topology, not only class shape. The central question is whether every production entry point preserves the same invariants, transaction semantics, notification coverage, persistence behavior, and history rules.

## Activation

Use when a service/store/context/facade owns several of: mutable aggregate state, commands, save/load, import/export, events, async guards, interop callbacks, drag/resize handlers, caches, undo/redo, or duplicated authoritative representations.

## Do Not Use When

- The target is a stateless transformation or CRUD wrapper with no aggregate invariants.
- The request is broad security/complexity grading without mutation-depth requirements; use the code-quality pipeline.
- Only one already isolated bug needs debugging; use `ada-systematic-debugging` first.

## Inputs

Freeze source scope, external callers, mutable models, event/interop adapters, persistence schema, tests, and claimed architecture boundaries. Enumerate in-scope files before claiming a full audit.

## Workflow

### 1. Reconstruct production call paths

Trace each operation family:

```text
UI/API/interop -> facade -> validation/guard -> operation
-> state commit -> events -> history -> persistence/projection
```

A command, lock, validator, or event type is not integrated merely because it exists. Confirm actual callers.

### 2. Build a mutation-boundary matrix

For every state-writing route record:

| Route | Validated | Serialized | Atomic | Undoable | Event | Persisted |
|---|---:|---:|---:|---:|---:|---:|
| Public command | | | | | | |
| Interop callback | | | | | | |
| Restore/import | | | | | | |
| Direct model mutation | | | | | | |

Any bypass is assessed against the same aggregate invariants.

### 3. State invariants

Check execute, no-op, failure, undo, and redo for identity, parent/child membership, ordering, selection/current IDs, duplicated flags, derived indexes, capabilities, and retained callbacks/policies. When state is represented twice, synchronization is a first-class invariant.

### 4. Persistence as transaction and round trip

Verify:

- export/import field parity and type fidelity;
- validation before commit and unchanged state on failure;
- ordering and identity preservation;
- history invalidation or revision barriers after restore;
- deterministic migration and version handling;
- explicit repair limits—repair is not rollback or validation.

Prefer shadow-state validation plus swap or explicit snapshot/rollback when apply can fail mid-flight.

### 5. Concurrency, guards, and events

Identify linearization point, revision model, lock scope, cancellation semantics, disposal/drain behavior, and stale-operation policy. Synchronous events raised inside non-reentrant locks require a reentrancy probe. Map every persisted mutation to the event/auto-save path and identify misleading no-op events.

### 6. History and coalescing

Verify operation/patch algebra is closed enough for undo/redo, failure ordering is explicit, no-op behavior is intentional, coalescing keys separate independent gestures, and restore removes stale undo targets even when restored state is semantically equal.

### 7. Run adversarial probes

High-value cases include:

- active/current item moved across parents then undo/redo;
- failed import after partial-looking input;
- stale async guard after an intervening commit;
- last waiter cancellation while underlying callback continues;
- disposal while callbacks are draining;
- event-handler reentrancy;
- duplicated logical/presentation orders deliberately diverging.

## Mandatory Checks

- Every claimed mutation boundary has production call-site evidence.
- Tests instantiate real paths, not isolated helpers only.
- Passing tests are baseline evidence, not proof of untested invariants.
- Each finding names the violated invariant and missing regression test.
- Proposed replacement architectures define revision, commit, failure, history, restore, migration, and side-effect boundaries—not only data nouns.

## Stop Conditions

Stop when complete scope cannot be enumerated, authoritative invariants are missing, concurrent behavior requires unavailable instrumentation, or remediation would change an unapproved public/persistence contract.

## Output Contract

Report exact scope and exclusions, call-path and mutation matrices, severity-ranked `file:line` findings, violated invariants, tests/builds run, missing adversarial probes, files modified (normally none), and an explicit verdict when requested.
