---
name: ada-contract-consistency-review
description: 'Frozen-contract consistency review, read-only PASS/FAIL.'
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [audit, contract, specification, consistency, srs, hld, adr, review, read-only]
    related_skills: [ada-doc-implementation-audit, ada-pre-implementation-audit, ada-srs-review, ada-library-public-api-review]
---

# Frozen-Contract Consistency Review

Read-only verification that a set of normative documents — SRS requirements,
HLD design entries (DES-*) plus the normative public-API manifest section
(e.g. HLD §10.2), accepted ADRs, and the implementation plan — agree with
each other on every frozen contract property, producing a PASS/FAIL
implementability verdict. No source code, no git diff, no fixes unless asked.

The question answered: **"Do the contracts tell one consistent story, and is
every frozen property stated everywhere it should be?"**

## When to Use

- "Final read-only review of Phase-N contracts — return PASS if no actionable
  High/Medium remains"
- Verifying a frozen API manifest (namespaces, nullability, enum values,
  constructor visibility, generic constraints) against the ADR and plan
- Cross-checking SRS acceptance criteria against HLD design entries and an
  implementation plan before implementation starts
- Pre-release contract freeze validation
- "对 X 功能做 spec-compliance 独立审查（只读），对照 SRS AC / ADR / HLD
  清单逐项验证实现与测试，输出 PASS/FAIL" — implementation+tests compliance
  mode, see the dedicated section below

**Skip for:** docs-vs-code audits (ada-doc-implementation-audit), writing or
reviewing requirement quality (ada-srs-review), pre-plan code verification
(ada-pre-implementation-audit), comparing two doc versions (ada-doc-comparison-analysis).

## Workflow

1. **Locate and size the docs.** `ls -R` to find them (HLD, SRS, ADR,
   `.hermes/plans/`), then `wc -l` each — plan read offsets; a 5000-line SRS
   is read by grep-range, not whole-file.
2. **Batch independent reads in one turn.** Read the HLD design entries,
   the normative API manifest section IN FULL (it is the tie-breaker
   document), the ADR decisions, the plan's target-API section, and the SRS
   requirement blocks together. Never serialize independent reads.
3. **Build the checklist** from the user's frozen items, or derive it from
   the ADR's Verification section when the user just says "verify the
   contracts". One item per contract property.
4. **Trace every item through every document that should state it**, citing
   `doc:line` evidence for each occurrence. A property frozen in only one
   place is a gap; a property stated consistently everywhere is confirmed.
5. **Grep-verify negative claims and numeric freezes over the WHOLE docs
   tree**, not one file: forbidden IDs (`grep -rn "REQ-F-157" docs/` must be
   empty), removed-API names must appear only as removal statements,
   additive enum values must state `= N` plus "existing values unchanged",
   nullability and generic constraints must match char-for-char between the
   manifest and the plan's API sketch.
6. **Classify findings — omission is NOT contradiction.** A plan that omits
   restating a value frozen by the normative section (and defers to it) is
   informational, not actionable — especially when the plan has an
   independent spec-compliance gate in its final phase. Only a direct
   contradiction (different namespace, different nullability, conflicting
   semantics, a forbidden API still promised) is actionable.
7. **Verdict format:** `PASS`/`FAIL` first; per-item evidence table;
   a separate "Informational only" list for non-actionable gaps; an
   "Issues encountered" note for tooling fallbacks. Stay read-only unless
   fixes were explicitly requested.

## Spec-Compliance Implementation Review Mode

When the user asks to verify implementation AND tests against frozen contracts
("对照 SRS AC / ADR / HLD §10.2 逐项验证实现与测试"), the
review gains an evidence pass over the code. Same read-only discipline, same
PASS/FAIL + `file:line` verdict shape — but the checklist items become ACs and
the evidence is source lines + test names + executed test output.

1. Read the normative docs in parallel (Workflow above), then read the
   feature's implementation files FULLY. Deviations hide in the 20-line render
   paths (placeholder markup, static DiagnosticIds, ordering of resolver vs
   catalog lookup) — do not skim.
2. Grep-verify negative claims over the WHOLE repo, not just docs/: removed
   API names (`grep -rn "ContentTemplate" src/ samples/`), forbidden symbol
   names (`GetComponent|SetContentParameters|FallbackContent`), and scope
   exclusion (`git diff --name-only origin/main..HEAD` must show zero hits in
   core / persistence when the plan freezes them).
3. Map every AC to a test by NAME: `grep -n "public void|public async Task"`
   per test file. Prove ABSENCE by grepping the registration/usage pattern
   (`grep -rn "AddContent" tests/ samples/` — if no test registers the
   same Kind twice, the composition-fatal duplicate-DI AC is UNTESTED even
   though the ctor throws). "Implementation throws but zero coverage" is a
   FAIL on the AC's verification, not a PASS with a note.
4. RUN the focused suites as execution evidence:
   `dotnet test tests/<proj>/<Proj>.Tests.csproj --filter "FullyQualifiedName~CatalogTests|FullyQualifiedName~BindingTests" --no-restore`
   plus the consumer-sample tests (coordination/lifetime often live there).
   Report real pass counts in the verdict — static reading is not evidence
   that tests pass.
5. Diff the frozen API manifest symbol-by-symbol against
   `PublicAPI.Unshipped.txt` (namespaces, sealed, generic constraints,
   enum `= N`, EditorRequired) — the baseline file is the machine-readable
   freeze and catches drift the prose review misses.
6. Classify each AC: **PASS** (impl + test evidence), **FAIL-untested**
   (impl correct, zero coverage), **FAIL-deviant** (impl or tests contradict
   the AC wording). Separate the two FAIL classes in the verdict table.

Tests are evidence, not gospel: an assertion that pins the IMPLEMENTED
behavior can freeze a deviation (see pitfalls). Flag the frozen deviation as
its own finding; do not count the assertion as compliance.

## The 11-point frozen-contract checklist

Derived from a real contract-freeze review; adapt per contract set:

1. **Atomic source-generation commit** — one candidate generation; commit
   only after completed collection; incomplete/faulting keeps previous; no
   new/old mix observable.
2. **Complete Parameter set + structural revision** — value-only change
   preserves identity and delivers the complete bound set every render;
   type/binding-set/declaration/owner change increments revision and remounts.
3. **Fail-closed ordering** — resolver evaluated at most once per projection
   inside the outlet-owned guarded fragment; throw → typed code
   (e.g. `ContentRenderFailed`); Catalog/Binding factories NOT evaluated;
   unrelated Items unaffected.
4. **Lifetime ownership split** — library-owned vs caller-owned: DI follows
   service-provider lifetime; Host-local follows the Host; the library releases
   after outlets retire a generation; caller-owned references may extend
   capture; no unconditional-GC promise.
5. **Non-public constructors** — sealed types, no public ctor, sole
   static/`Create`/builder entry points; escaped builder/binding instances
   throw after `Create` returns.
6. **Automatic reserved-parameter injection** — base-class `Content`
   parameter auto-included in every complete set; explicit duplicate binding
   rejected.
7. **Invalid-definition error code** — blank Kind / null required content →
   `DefinitionInvalid`-style code, contributes no renderer.
8. **Additive enum freeze** — new code `= N`; "existing values 1..N-1
   unchanged" stated in every doc that lists the enum.
9. **Nullability of fragment/child parameters** — `RenderFragment<T>?`
   matches char-for-char between manifest and plan sketch.
10. **Forbidden requirement IDs** — zero grep hits across `docs/`; the plan
    must explicitly preserve the baseline count.
11. **Symbol-by-symbol plan↔manifest consistency** — namespace, sealed,
    generic constraints (`IComponent` / base-class bound), EditorRequired
    markers, renderless-collector wording.

## Common Pitfalls

- **Flagging omission as contradiction.** The most common review error.
  Plans legitimately defer to the normative freeze section; only direct
  conflict is actionable. Say so explicitly in the verdict.
- **Grepping one file for negative claims.** "No REQ-F-157" must be verified
  over the whole docs tree, or a zh/ appendix copy can hide it.
- **Reading the SRS whole-file.** 5000+ lines — grep the requirement ID
  ranges, then read only those blocks.
- **Trusting the first document's wording.** The normative manifest section
  is the tie-breaker; when plan and HLD differ, the HLD §10.2-style freeze
  wins.
- **search_files failing on Windows repo paths.** It may return 0 results or
  an IO/os error while terminal grep works. Fall back to
  `cd /c/Users/<user>/...` + `grep -n` / `ls -R` / `wc -l` in bash — the
  fallback is the pattern, not a claim the tool is broken.
- **Verdict without evidence.** Every PASS item needs at least one
  `doc:line` citation; a bare "all consistent" verdict is not verifiable.
- **Tests can freeze the deviation.** A test asserting
  `error.DiagnosticId == "CONTENT-RENDER-FAILED"` while the SRS AC
  demands a NEW opaque ID per failure occurrence and a new ID on failed Retry
  proves non-compliance: the assertion is evidence OF the gap and the suite
  itself needs changing. Before trusting ID-equality assertions, check the AC
  wording for per-occurrence/uniqueness semantics (F-128-style ACs).
- **Plan file lists drift.** The plan names
  `tests/.../ContentCoordinationTests.cs`; the implementation may put those
  tests in the consumer-sample project instead. Grep test names repo-wide
  before reporting "missing test file" — behavior coverage can be complete
  under a different file.
- **Fixed-ID diagnostics as a spec-compliance red flag.** Static
  DiagnosticIds passed to `OnError` while the AC requires per-occurrence
  correlation: grep `new HostError` / `HostError(` in src/ to list
  every ID, and check whether the error UI in the item content area actually
  renders the ID (often only the summary text is rendered).
- **Untested ≠ missing, and both are FAIL classes.** Composition-fatal
  duplicate-DI behavior can exist (ctor throws, named Kind) yet have zero
  test coverage. Keep "FAIL-untested" and "FAIL-deviant" distinct rows in the
  verdict table; reviewers fix them differently.

## Verification Checklist

- [ ] All four doc types read: SRS reqs, HLD entries + manifest, ADR, plan
- [ ] Checklist built from user items or ADR Verification section
- [ ] Each item traced with `doc:line` evidence across all docs that should state it
- [ ] Negative claims grepped over the whole docs tree (zero-hit verified)
- [ ] Numeric freezes (enum `= N`, counts) and nullability checked char-for-char
- [ ] Omission vs contradiction classified; contradictions only = actionable
- [ ] Verdict: PASS/FAIL + evidence + "Informational only" list; read-only maintained

## References

本技能无独立 references：11 点冻结契约清单、验证模板与常见坑均在正文。
