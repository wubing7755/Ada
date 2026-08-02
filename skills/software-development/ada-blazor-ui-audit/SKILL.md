---
name: ada-blazor-ui-audit
description: "Use when auditing a Blazor or Razor component library across component rendering, state notifications, CSS/markup contracts, JavaScript interop, disposal, packaged assets, demos, and real-browser reachability. Produces severity-ranked file:line findings; use narrower Blazor pitfall Skills for an already isolated bug."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, razor, audit, css, js-interop, browser]
    related_skills: [ada-blazor-component-library, ada-blazor-interaction-pitfalls, ada-blazor-interop-pitfalls]
---

# Blazor UI Source Audit

Audit the complete behavioral chain of a Blazor UI. Compilation and service-level tests do not prove that rendering, DOM reachability, CSS, interop, cleanup, packaging, and browser behavior agree.

## Activation

Use for read-only component-library audits, UI architecture reviews, package/demo discrepancies, and interaction paths that span Razor/C#, CSS, JavaScript or TypeScript, and state services.

## Do Not Use When

- The defect is already isolated to pure Blazor lifecycle/rendering; use `ada-blazor-interaction-pitfalls`.
- The defect is already isolated to JS interop lifetime/events; use `ada-blazor-interop-pitfalls`.
- The task is a general repository health review with no UI depth requirement.
- The user asked to implement rather than audit; complete the audit first, then route the fix.

## Inputs

Identify authored source roots, generated/vendor exclusions, component host and demo, state owner, CSS entry points, JS/TS source and bundle, package topology, test projects, and governing requirements or ADRs.

## Workflow

### 1. Freeze authored scope

Enumerate tracked Razor, C#, CSS, JS/TS, project, host, demo, and test files. Exclude `bin`, `obj`, vendor assets, and generated bundles from authored line counts, but inspect generated bundles when verifying packaging.

### 2. Reconstruct the component tree

For each component, map parameters, callbacks, child components, local caches, lifecycle hooks, JS registrations, and disposal ownership. Flag identity parameters consumed only during initialization when the component may be reused with a different object.

### 3. Build mutation continuity

Trace each visible operation:

```text
DOM/Razor event -> handler -> state mutation -> domain notification
-> projection/cache rebuild -> render request -> persistence/side effects
```

A render request does not prove projections were refreshed or persistence observed the change.

### 4. Trace interop end to end

For each interaction, follow element reference → C# wrapper → exported JS function → event branch → target discovery → typed callback → state operation → cleanup. Definitions without production call sites are not integrated behavior.

Pair attach/detach, add/remove listener, map set/delete, object-reference create/dispose, observer start/stop, and animation-frame schedule/cancel.

### 5. Audit RenderTree identity

For hand-written `BuildRenderTree`, identify state-dependent element, attribute, and collection cardinality. Shared advancing sequence counters across variable siblings can corrupt later frames. Verify A→B→A or Undo/Redo transitions, stable keys/regions, node IDs, classes, and sentinel content—not only initial markup.

### 6. Compare markup, CSS, and hit testing

Check component class/data attributes against selectors, specificity, source order, global style leakage, semantic HTML, ARIA relationships, focus/keyboard behavior, and target geometry. DOM presence is not operability: hidden, zero-sized, covered, or unreachable targets must complete the real operation.

### 7. Verify package and demo topology

Determine whether the demo consumes source, a package, or copied assets. Rebuild generated bundles, pack/restore when required, and prove the browser loaded the current artifact. A green source test with a stale package or cached bundle is not runtime evidence.

### 8. Reconcile requirements and evidence

Separate **Designed**, **Implemented**, **Reachable**, and **Verified**. Search status-bearing documents for contradictory completion claims when the rendered controller path is missing.

## High-Value Probes

- parameter identity replacement and subscription cleanup;
- mutable collection count changes across distant render regions;
- empty and non-empty drop targets completing commit plus Undo/Redo;
- producer/consumer source-kind × target-kind matrix;
- nested hosts or competing overlay roots;
- bundle marker and package-consumer smoke test;
- browser console, mutation, focus, and geometry evidence.

## Stop Conditions

Stop when source scope cannot be enumerated, requirements materially conflict, browser/package evidence is required but unavailable, or a proposed fix crosses an unapproved public API or architecture boundary.

## Output Contract

Return severity-ranked findings with claim, `file:line` evidence, runtime consequence, recommended remediation, and missing regression proof. State exact scope, commands run, evidence tier, files modified (normally none), and an explicit verdict when requested.

## Verification Checklist

- [ ] Authored source inventory is complete and exclusions are explicit.
- [ ] Component, mutation, interop, and cleanup chains are mapped.
- [ ] Render transitions, not just initial markup, are tested.
- [ ] CSS selectors and hit-test geometry match emitted DOM.
- [ ] Package/demo/browser evidence identifies the exact artifact.
- [ ] Findings were rechecked against the final live diff.
