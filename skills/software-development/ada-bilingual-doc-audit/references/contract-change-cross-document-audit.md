# Contract-Change Cross-Document Audit

Use this after a bilingual SRS/ADR/HLD change freezes or replaces a contract. Translation parity alone is insufficient: both languages can faithfully repeat the same contradiction or stale statement.

## 0. Freeze one stable review snapshot

Inspect unstaged, staged, and untracked state; the default `git diff` is not a complete review boundary. Record hashes for every scoped contract file before semantic comparison and immediately before reporting. In a shared or multi-agent worktree, a hash change means earlier line references and conclusions may be stale: reload the changed files and rerun every affected invariant. Issue findings or `PASS` only from one stable final snapshot.

## 1. Build the dependency closure

Start from the changed REQ/ADR/DES IDs, then inspect every normative or current-status consumer even when it is outside the diff:

- SRS body, terminology table, appendix/index, and change log
- ADR decision tuple, consequences, verification, supersession, and ADR indexes
- HLD design blocks, `Source` footers, design index, full traceability matrix, decision gates, and normative public-API manifest
- current requirements-traceability summary and status-change rows
- linked dated evidence/status audits
- guides only when they claim the target-state API rather than intentionally documenting the still-shipped transitional API

A missing synchronized edit in an unchanged dependent file is a real finding.

## 2. Compare an outcome matrix, not just matching words

For contracts involving multiple sources or failure classes, construct a matrix with one row per combination, for example:

| Dimension | Values to enumerate |
|---|---|
| Source | startup DI, host-local declarative route, host-local functional map |
| Outcome | missing, duplicate/conflict, binding-factory failure, renderer failure |
| Detection phase | composition-root construction, Host composition, projection/render |
| Scope | whole application/Host, one Kind, one Item/outlet |
| Observable result | throw, typed failure, safe unavailable placeholder, ErrorBoundary |
| Preservation | Item, layout position, content identity |
| Isolation | whether unrelated Kinds/Items continue |
| Diagnostics | user-visible fields versus log-only fields |

Populate the matrix independently from the SRS ACs, ADR decisions, and HLD designs. Flag:

- a universal SRS clause (for example, “any DI/Route/Map conflict”) narrowed by a design-only exception;
- an ADR that first distinguishes one source as startup-fatal and later says all conflicts are per-Kind;
- a typed-failure/no-exception rule paired with an unspecified construction failure;
- a conflict policy that preserves Items in one section but prevents the Host from being constructed in another.

These are semantic contract conflicts even when EN and ZH say exactly the same thing.

Always evaluate the adversarial cardinality case: two Items/outlets reference the same conflicting Kind. It distinguishes a per-Kind outage from a per-Item renderer failure and catches requirements that wrongly promise all “other Items” remain functional.

For diagnostics, assign each failure to exactly one transport and namespace—composition exception, workspace result/error code, or Host diagnostic/error code—then inspect generic error-code appendices for a stale trigger that assigns the same event to another channel.

For closure-bearing descriptors, compare maximum owner lifetime, active-source lifetime, source replacement/retirement, collection after the final outlet reference, and final disposal. “Retained until Host disposal” contradicts “collectible after source replacement” unless the text explicitly distinguishes active from retired descriptors.

## 3. Enforce four-way trace equality

Normalize `REQ-` prefixes, expand compact ranges, and normalize Chinese `、` versus comma separators. Derive these sets independently:

- `S(d)`: requirements in DES block `d`'s `Source` footer;
- `C(d)`: requirements in the Appendix C/design-index row for `d`;
- `R(d)`: reverse of Appendix D.2—requirements whose row names `d`;
- `D(r)`: designs in requirement `r`'s Appendix D.2 row;
- `P(r)`: designs in requirement `r`'s current evidence/status row.

Require:

```text
S(d) = C(d) = R(d)
D(r) = P(r)
```

Scan the affected closure in both directions, not only newly edited DES blocks. Typical defects are:

- a Source range grows from `F-006` to `F-006~008`, but D.2 adds only F-008 and forgets F-007;
- D.2 removes F-122 from a design while the unchanged Source footer and Appendix C retain it;
- D.2 adds a design responsibility for F-128, F-070, or an NF requirement while the current evidence row stays stale;
- a compact range such as `F-119~124` silently adds F-120, but one reverse mapping is not updated.

Compare these relations in `HEAD` and current content. A mismatch present in both may be baseline debt; a relation equal in `HEAD` and divergent only in the worktree is a phase regression. Also derive the changed requirement-ID set from the actual diff and compare it with SRS change-log rows and decision-gate closure-evidence ID sets.

Do not treat correct row counts as proof of traceability. Validate status histograms and per-row DES-set equality independently; a table can contain exactly 150 unique rows and correct totals while several mapping cells are stale.

## 4. Revalidate status and evidence after AC changes

A previous `Verified` status does not automatically survive a requirement rewrite. For each changed requirement:

1. diff the old and new ACs;
2. identify every newly required behavior, failure source, isolation boundary, diagnostic field, and negative security promise;
3. inspect the actual linked evidence description, not just a test name or an old Phase Exit claim;
4. downgrade the current status unless existing evidence demonstrably covers every new clause.

A dated audit may remain as immutable historical evidence, but then:

- label it explicitly as a snapshot;
- stop calling it the current status source;
- maintain a current override/overlay;
- recalculate status totals from the current rows;
- update the evidence table’s DES mappings when it claims current traceability.

Compare each evidence/status row’s DES set against the current HLD D.2 row. Old design IDs that were removed and new design IDs that are absent are separate traceability findings.

## 5. Check gate-state consistency

Compare all gate declarations:

- baseline/current-summary prose;
- the gate status table;
- HLD decision-gate row;
- ADR status and approval tuple;
- implementation/remediation notes.

Statements such as “Gate 007 Closed” and “close Gate 007 before this row may become Verified” cannot coexist without an explicit distinction between decision closure and implementation completion. Either use separate states or clarify which gate is already closed.

## 6. Audit the normative API manifest

When an ADR introduces named public symbols or removes a legacy API, inspect the HLD’s normative public-API surface manifest even if it is outside the changed hunk.

Require the manifest to:

- name the new public symbol families and typed binding/builders;
- remove or explicitly deprecate the superseded API;
- update service-registration/catalog terminology and lifetime constraints;
- agree with any gate claiming the API contract is frozen.

Examples in a DES block do not substitute for a manifest that explicitly says symbols cannot be renamed arbitrarily.

## 7. Reporting

Separate these verdicts:

- **Bilingual parity**: whether EN and ZH preserve the same tuple, strength, and structure.
- **Contract coherence**: whether the synchronized pair agrees with SRS authority, ADR decisions, HLD execution contracts, and downstream current-status records.

A suitable conclusion is: “No EN↔ZH drift found; both mirrors contain the same cross-document contract defect.” Include exact `path:line`, severity, and the two conflicting statements.