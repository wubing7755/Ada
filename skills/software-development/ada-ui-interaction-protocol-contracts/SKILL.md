---
name: ada-ui-interaction-protocol-contracts
description: "Use when pointer, keyboard, drag/drop, list, tree, tab, toolbar, or docking interactions cross a DOM/JavaScript/native boundary into a host or domain operation. Defines source/target compatibility, stable identity, named index domains, hostile/stale message validation, operation semantics, and real-path evidence."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [ui, protocol, interop, drag-drop, validation]
    related_skills: [ada-blazor-ui-audit, ada-blazor-interop-pitfalls, ada-test-driven-development]
---

# UI Interaction Protocol Contracts

A numeric position is not a semantic target. Carry source/target identity, kind, relation, and index-domain evidence together, then validate them again at the consumer boundary.

## Activation

Use when browser, desktop, or native UI geometry becomes a typed intent consumed by a component host, backend, state store, or domain operation—especially when presentation and logical orders can differ.

## Do Not Use When

- The issue is pure rendering or lifecycle with no protocol boundary.
- The UI directly mutates one authoritative list and no message crosses layers.
- The task is only visual styling or pointer animation with no semantic commit.

## Inputs

Identify source kinds and rendered elements, target kinds and target collections, stable IDs, same/cross-container semantics, producer/controller, consumer/host, operation side effects, revision/session identity, and legacy compatibility policy.

## Workflow

### 1. Define a compatibility matrix

Write the contract before implementation:

```text
source kind × target kind × same/cross container -> operation | no-change | reject
```

Branching on a shared container ID alone is insufficient.

### 2. Define the intent envelope

Include, where applicable:

- protocol version, host/session/revision;
- source kind, source container ID, and source item ID;
- target kind and target container ID;
- target item identity for relative insertion;
- relation (`before`, `after`, `inside`, `tail`) rather than an unexplained number;
- numeric slot only with an explicitly named index domain.

### 3. Name every index domain

Examples: logical model order, presentation order, filtered visible order, DOM order, and virtualized viewport order. If two legal collections can differ, their indices are not interchangeable.

When presentation drives logical reorder, resolve the target item by stable identity in both collections, derive before/after, then normalize for source removal in the destination domain.

### 4. Validate producer and consumer

- **Producer/controller:** do not preview or emit impossible combinations; re-resolve on commit when geometry can change.
- **Consumer/host:** distrust UI reachability. Reject stale, forged, mismatched, unknown, and obsolete intents; validate identity, domain, bounds, revision, and compatibility.

Keep both checks even when predicates look duplicated; they defend different boundaries.

### 5. Preserve operation semantics

Select operations from the compatibility matrix, not convenient shared fields. Presentation reorder must not accidentally change model order, selection, visibility, expansion, placement, history, or persistence. Cross-container migration may intentionally do so; assert those side effects separately.

### 6. Build TDD slices

**Producer RED:** drive the real DOM/controller event and assert emitted identity, kind, relation, and domain.

**Consumer RED:** inject the typed message with deliberately divergent presentation/logical orders and hostile identity/revision cases.

**GREEN:** add the smallest mapping and validation change at each boundary.

**REFACTOR:** centralize matrix/mapping only when it reduces real duplication without removing boundary checks.

### 7. Verify artifact and runtime

If UI source is bundled, rebuild and inspect the generated asset. Distinguish:

- **Mapped** — direct consumer injection selects the operation;
- **Reachable** — rendered UI and producer can generate the intent;
- **Implemented** — producer and consumer tests cover the contract;
- **Verified** — current built artifact has runtime evidence.

## Required Cases

- before/after geometry and tail insertion;
- same-container forward/backward and own-target no-change;
- cross-container movement in both directions;
- divergent logical and presentation orders;
- missing, foreign, stale, replayed, and mismatched identities;
- obsolete target kinds at the consumer boundary;
- pointer-up/commit re-resolution;
- operation side effects and revision/history behavior;
- nested hosts and owner/session separation where overlays or portals exist.

## Stop Conditions

Stop when product semantics for a matrix row are undecided, no stable target identity exists, the index domain cannot be named, protocol compatibility needs an architecture decision, or runtime reachability cannot be observed enough to claim verification.

## Drop-Zone Feedback Protocol（拖放目标区反馈）

Shaping and verifying what the user sees while dragging — the highlight that
tells them where a tab/panel will land. Most failures here are not detection
failures: the logic already resolves the target kinds (center / inline-start /
inline-end / block-start / block-end); the visual layer renders one
indistinguishable block.

**Diagnose before touching code** (trace in order):
1. **Kinds** — does the protocol enum already carry the zones?
2. **Detector** — does the JS geometry function return them from the rect
   (e.g. 25% edge bands)?
3. **CSS** — are there kind-specific rules? A single generic rule is the usual
   root cause: every kind renders as a whole-element block.
4. **Tests** — do tests assert the non-center kinds? A suite that only ever
   sees `document-center` cannot catch the visual collapse.

Fix is often CSS-only + tests. Do NOT rewrite a detector that is already
correct.

**Zone shape rules (CSS, no extra DOM)**: drive the shape from the element
that already carries the preview attribute via a `::before` pseudo-element.
Scope shape rules to the owning element kind (`[data-group-kind="document"]`),
exclude that kind from the generic rule with `:not(...)`, and use a kind
prefix (`^="document-"`) so the shape rules never apply to a different preview
family. Bands/stripes use physical top/right/bottom/left + width/height; the
center zone draws a 50%×50% rect. Host element needs `position: relative`;
static test fixtures must add it explicitly. Keep zone geometry identical to
the detection bands (25% band ⇔ 25% strip).

**Boundary semantics**: `localX < 0.25*width` enables start, `localX >
0.75*width` enables end; the dividing lines themselves resolve to center.
Encode the exact boundary points in tests (99/100, 300/301 at width 400).

**RTL rule**: if the detector computes from `rect.left/right` (physical), the
CSS must use physical `left/right`. `inset-inline-start` / logical properties
flip under RTL and paint the highlight on the wrong side. Rule: **the visual
feedback must use the same coordinate space as the detection function.**

**Verification**:
- Unit-test the detector as a pure function: when the Node DOM fixture cannot
  represent the real hierarchy, `export` the geometry function (keep it OUT of
  the public API entry file) and unit-test the mapping directly with boundary
  cases.
- Real-browser verification (works without a vision model): drive the WHOLE
  drag in one eval — `pointerdown` → `pointermove` past the drag threshold →
  `pointermove` to each zone → assert `getComputedStyle(element,
  '::before')` geometry (`position`, `top/left/width/height`, `zIndex`,
  `pointerEvents`) and the resolved-kind data attribute. Controllers cancel
  drags on window `blur`/`visibilitychange`, so script the drag synchronously
  within ONE eval; the page console shares scope across evals (unique `var`
  names per probe).

Report: diagnosed layer (logic vs visual), the zone-shape CSS, boundary test
evidence, real-browser geometry evidence, and which sibling preview kinds were
verified unchanged.

## Output Contract

Deliver the compatibility matrix, intent schema, index-domain mapping, validation rules, operation mapping, producer/consumer test evidence, artifact/runtime evidence tier, and unresolved product decisions. Findings and reviews use `file:line` evidence.
