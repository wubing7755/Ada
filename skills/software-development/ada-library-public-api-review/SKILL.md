---
name: ada-library-public-api-review
description: "Use when reviewing a library's public API, compatibility surface, extension model, factory validation, immutable boundaries, or consumer usability. Requires normative contract evidence and, when source inspection is insufficient, a temporary external-consumer compile/run probe rather than privileged in-repo tests alone."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [library, public-api, compatibility, consumer, review]
    related_skills: [ada-requesting-code-review, ada-dotnet-verification]
---

# Library Public API Review

Review a library as an external consumer sees it. Same-assembly tests, friendship, and successful internal builds can hide an unusable or overly permissive public contract.

## Activation

Use for package API reviews, compatibility gates, closed or extensible hierarchy design, public factories/validators, API baseline changes, immutable snapshot surfaces, and consumer-facing documentation.

## Do Not Use When

- The target is an application with no supported library API.
- The task is general code quality without compatibility or consumer boundaries.
- A public contract has not been defined and alternative interpretations materially change severity; obtain a decision first.

## Inputs

Identify the production library/package, requirements/ADRs/API baseline, supported compatibility policy, exact diff or release range, test friendship/privileges, and representative consumer scenarios.

## Workflow

### 1. Establish the normative contract

Read requirements, ADRs, compatibility policy, generated API baseline, XML docs, and package examples before judging implementation details. Separate intended extension points from accidental accessibility.

### 2. Inventory the public surface

Inspect public and protected types, constructors, interfaces, records, delegates, factories, validators, events, options, collection exposure, serialization shapes, and generated members. Include compiler-generated record behavior and default value-type states.

### 3. Test extension and construction boundaries

Check whether abstract bases are intentionally open or closed, whether constructors express that intent, and whether unsupported implementations fail deterministically. Distinguish `protected`, `protected internal`, and `private protected`; modifiers are contracts, not style.

### 4. Audit validation and failure behavior

Public factories and normalizers must handle unsupported inputs exhaustively. Reject silent defaults, unchecked fallback casts, and incidental null/index/cast exceptions when the contract promises a typed result or argument error.

### 5. Audit immutability and ownership

Read-only interfaces are insufficient if they expose caller-owned mutable collections or mutable elements. Verify defensive copies, authoritative state ownership, mutation methods, caches/indexes, `init`/copy behavior, and serialization round trips.

### 6. Run an external-consumer probe

When accessibility or package behavior is non-obvious:

1. create the smallest temporary project outside the repository;
2. reference the packed package or production project as a normal consumer;
3. compile/run the disputed use case;
4. capture the exact success, compiler diagnostic, or typed failure;
5. remove the probe and confirm the repository is unchanged.

Prefer a packed-package probe when packaging/build assets affect the contract.

### 7. Reconcile baselines and docs

Every API baseline delta must correspond to an intended reviewed symbol. Confirm docs and examples compile against the shipped surface, not internal helpers or unshipped source.

## Mandatory Checks

- Same-assembly or `InternalsVisibleTo` tests are not treated as consumer proof.
- Closed hierarchies enumerate current same-assembly subtypes before unchecked exhaustive dispatch is accepted.
- Collection and element mutability are both reviewed.
- Public failure modes are deterministic and documented.
- Temporary probes leave no repository artifacts.
- Findings use current source lines and current package/API evidence.

## Stop Conditions

Stop when the public contract is genuinely unspecified, a probe requires unapproved installation/publication, credentials are needed, or changing the API requires a compatibility/ADR decision.

## Output Contract

Report findings by severity with normative contract evidence, source `file:line`, exact consumer behavior, remediation, and regression guidance. State whether evidence came from source, project reference, packed package, or runtime probe, and provide PASS/BLOCKER when requested.
