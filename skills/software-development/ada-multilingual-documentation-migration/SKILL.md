---
name: ada-multilingual-documentation-migration
description: "Use when migrating docs into language pairs (en/zh)."
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [documentation, i18n, migration, translation, markdown, manifest]
    related_skills: [ada-docs-revision, ada-doc-traceability-audit, ada-srs-revision]
---

# Multilingual Documentation Migration

Use when the user asks to restructure a documentation tree into language
directories (`docs/en/`, `docs/zh/`), establish one language as canonical per
language pair, translate documents, and atomically switch authority. This is
the class of work behind the 项目 multilingual docs plan (P0–P6).

## Core Model

- English is the default language and the canonical version of every pair.
- Chinese (or any secondary language) lives in `docs/zh/`; English in
  `docs/en/`; same relative path and filename in both.
- A machine-readable **manifest** (`docs/documentation-manifest.json`) is the
  single source of truth for document roles, authority paths, migration
  phases, blob integrity, legacy routes, and mirror exceptions.
- A human-readable **status table** (`docs/translation-status.md`) records
  per-pair state; CI checks manifest and status do not contradict.
- Canonical states: `Legacy Canonical` → `English In Review` →
  `English Ready for Cutover` → `English Canonical`; Chinese: `Synchronized`
  or `Outdated`. A file under `docs/en/` is NOT canonical unless the manifest
  says so.

## Lightweight Bilingual Migration (small consumer repo, no manifest)

When the user asks to make docs bilingual following the 项目 convention
("参考 项目/docs，文档中/英两份") for a SMALL repo (a handful of docs, no SRS
audit machinery, no `documentation-manifest.json`), do NOT drag in the
phase-gated manifest machinery below. The lightweight pattern (worked on
某项目):

1. `git mv docs/x.md docs/en/x.md` — history-preserving move (see
   `ada-git-history-preserving-moves`); then write `docs/zh/x.md` as the
   mirror.
2. **Update stale content during migration** — before translating, diff the
   doc against the CURRENT implementation. The doc may describe pre-refactor
   state (某项目's architecture.md still said "512x512 canvas, four-pane
   layout" after the canvas went dynamic-size and the workspace became
   six-region). Migrating a stale doc doubles the drift; fix en first, then
   translate.
3. Keep the `## ` section structure identical across the pair — same count,
   paired headings (en `Overview` ↔ zh `概述`, `Layers` ↔ `分层`, etc.).
   Table columns/IDs/commands stay byte-identical; only prose is translated.
4. Update entry points: README.md + README.zh.md with the language switcher
   line (`English | [简体中文](README.zh.md)`), a mirrored doc-links table
   pointing at `docs/en/...` and `docs/zh/...`, and the parent-project style
   (feature list, project table, dev commands, license).
5. Verify (cheap, scriptable): en/zh `## ` count equality + paired heading
   presence; `grep` the repo for stale references to the OLD path
   (`docs/architecture.md`) in `.md`/`.yml`; resolve every README doc link to
   a real file; docs-only change → `dotnet build` (or repo gate) is the only
   build gate needed.
6. Ship on a branch off current `origin/main` (user's standing rule: switch
   to main + pull before new work), one commit, PR with the repo's template.

The manifest/status-table/validator machinery below is for 项目-scale
migrations with normative documents and cutover audits; skip it for a small
consumer repo unless the user explicitly asks for the full apparatus.

## Manifest Schema (stable contract)

Each document entry needs:

```json
{
  "documentId": "srs",
  "role": "normative-requirements",
  "migrationPhase": "P5d",
  "targets": {"en": "docs/en/SRS.md", "zh": "docs/zh/SRS.md"},
  "authority": {"path": "docs/SRS.md", "language": "zh", "state": "Legacy Canonical"},
  "integrity": {"translatedFromBlob": null, "reviewedCandidateBlob": null, "canonicalBlob": null},
  "mirrorRequired": true
}
```

- `translatedFromBlob`: Legacy source Git blob OID the translation was made from.
- `reviewedCandidateBlob`: blob the bilingual reviewer actually approved.
- `canonicalBlob`: filled only at cutover and MUST equal the final reviewed blob.
- `legacyRoutes[]`: structured `{sourcePath, targetDocumentId, kind, activeFromPhase, removeAfterPhase, removalCondition, reason}` — only three core compatibility pointers stay permanent.
- `mirrorExceptions[]`: `{path, reason, lifetime, removalCondition}` for the language selector, manifest, status table, and (during migration) the plan doc.
- `mirrorRequired`: true for every real language pair; false only for control files/exceptions.

## Canonical State Machine & Blob Integrity

`Legacy Canonical` → `English In Review` → `English Ready for Cutover` →
`English Canonical`; Chinese side: `Chinese Synchronized` / `Chinese
Outdated`. **Never declare canonical just because a file lives under
`docs/en/`** — the manifest state is the source of truth.

Blob integrity rules:
- `translatedFromBlob` = Legacy source blob the translation was made from.
- `reviewedCandidateBlob` = blob the bilingual reviewer actually approved.
- `canonicalBlob` = blob after cutover; MUST equal the FINAL reviewed
  candidate. **Recompute after any link rewrite and have the reviewer
  re-approve the final blob** — do not reuse pre-rewrite review records.
- Before cutover, verify the current legacy blob still equals
  `translatedFromBlob`; any drift rolls the doc back to `In Review`.

## Workflow (phase-gated, one independent commit per phase)

0. **Plan + baseline**: get the approved plan; verify its SHA-256; record the
   plan doc itself as a tracked document. Commit the plan first.
1. **P0 infrastructure**: manifest, status table, language-neutral validator
   script, refactor path-hardcoded tests to read the manifest, add stable
   markers (e.g. `<!-- 项目:requirements-index:start/end -->`) so tests do
   not depend on natural-language section titles. Do NOT move any content.
2. **Entry points**: root README (canonical English + `README.zh.md`), docs
   language selector, guides, security. Use `git mv` to preserve history.
3. **History docs**: development/ work packages and remediations. Preserve
   every historical fact (dates, branches, test counts, delegation IDs,
   paths) — translate prose, never facts.
4. **ADR**: index + ADR-0001..N. Preserve ADR tuple: IDs, status, dates,
   decision makers, related requirement/design IDs, supersession relations.
5. **Evidence**: historical verification records. Facts, measurements,
   instance IDs, SHA-256 values must be byte-identical across languages.
   A document that was already English stays the English baseline; write the
   Chinese translation.
6. **Normative docs (SRS/HLD/traceability)**: create English candidates in
   `docs/en/` but DO NOT move the legacy Chinese yet; record
   `translatedFromBlob`; run automated tuple checks; then a **bilingual
   reviewer** must approve the candidate (this is a human gate if the task
   spec requires it — STOP and report source/candidate blobs, tuple
   comparisons, reviewer findings, and the planned cutover paths).
7. **Atomic cutover**: verify legacy blob still equals `translatedFromBlob`;
   recompute the candidate blob after any link rewrites; reviewer must
   re-approve the final blob (never reuse a pre-rewrite review record);
   `git mv` the legacy Chinese to `docs/zh/`; replace old paths with
   English pointer stubs; switch manifest authority to
   `English Canonical` with `canonicalBlob == reviewedCandidateBlob`.
8. **Cleanup + archive**: check mirror sets are identical, no undeclared
   legacy routes, no cross-language mislinks; archive the plan doc into
   `docs/zh/development/` + reviewed English mirror, no root stub.
9. **Post-migration control-layer removal (optional, user-dependent)**:
   the manifest, status table, language selector page, validator script,
   and CI docs job are MIGRATION-TIME artifacts, not a permanent contract.
   After the migration lands, the maintainer may direct their removal
   ("删除多余文件", "移除这些引用"). When that happens:
   - `git rm` the control files AND every reference: the validator script,
     the CI `docs:` job, the `--phase`/`currentPhase` machinery, and any
     test that resolves paths through the manifest.
   - Refactor contract tests BACK to direct paths
     (`docs/en/SRS.md`, `docs/en/evidence/p8-requirement-audit.md`) — but
     KEEP the stable markers (`<!-- 项目:requirements-index:start/end -->`);
     the markers are the durable part, the manifest was the indirection.
   - Replace manifest-driven authority wording in AGENTS.md/CONTRIBUTING.md
     /PR/issue templates with a simple prose rule ("English under
     `docs/en/` is the authority for each pair"), and re-point any
     `docs/README.md` index link to `docs/en/README.md`.
   - Before committing a deletion the agent did not initiate, verify the
     worktree state is intended (a `D` status on core files is a
     concurrency signal — clarify attribution with the user first), then
     sweep the repo for the removed identifiers to prove zero references
     remain (archive/history docs are the allowed exception).
   - The validator that was manifest-driven dies with the manifest; do not
     keep a broken script around.

## Translation Rules

Classify fenced blocks into three kinds and treat them differently:

1. **Structured normative prose** (SRS requirements, HLD DES/OI): translate
   the natural language; KEEP IDs, Actor, Priority, Source, AC count and
   order, requirement/DES references, code identifiers, numeric constraints,
   must/should/may strength, failure semantics.
2. **Machine/executable content** (code, commands, API signatures, JSON/XML,
   schema, config): keep byte-identical, including the JSON manifest example.
3. **Diagram/mixed** (Mermaid, ASCII, examples): translate human labels,
   comments, notes; keep Mermaid keywords, node IDs, edge topology, numbers,
   code identifiers.

Never translate: `REQ-F-*`, `REQ-NF-*`, `DES-*`, `OI-*`, `ADR-*` IDs,
C#/TypeScript/CSS symbols, paths, commands, dates, versions, SHAs,
measurements, error codes, enum values.

## Delegated Translation + Bilingual Review Pattern

For large docs (2k–5k lines), split by stable section boundaries into 3
parallel subagents, each writing `docs/en/<doc>.partN.md`, then `cat` them
into the final file and delete the parts. Each subagent gets the glossary
and hard rules in `context`. After merging:

- Automated tuple checks (see below) must pass BEFORE the review.
- Dispatch an independent bilingual reviewer whose gate is contract
  semantics, not language fluency: must/should/may strength, failure
  semantics, AC boundaries, numeric constraints, security promises.
- The reviewer's verdict (APPROVE / NEEDS-FIX) is what upgrades a candidate
  to Ready for Cutover.

## Validation Gates (per phase)

A single validator script (`scripts/validate-docs.py`) should be phase-aware:

- manifest schema: documentId unique == key, targets complete, authority
  exists, integrity state constraints, legacyRoutes/mirrorExceptions fields.
- phase-aware path existence: authority always exists; legacy route source
  exists once `activeFromPhase` reached; a `mirrorRequired` target exists
  once its document's state says it should (P6: ALL mirrorRequired targets
  exist).
- Markdown link + anchor checks that skip fenced blocks and
  `.packages/artifacts/obj/bin` dirs; skip anchor validation for non-.md
  targets (avoids UnicodeDecodeError on images).
- SRS/HLD/ADR tuple checks that resolve paths FROM THE MANIFEST, never
  hardcoded `docs/SRS.md` — otherwise the cutover stub breaks the gate.
- bidirectional manifest↔status consistency: both ID sets equal AND the
  status table's authority path/state column matches the manifest per row.
- mirror-set check: only documents whose authority state is
  `English Canonical` are required to have both targets (before that phase,
  en-only is legal).
- `--phase` should default to a machine-readable `currentPhase` field in the
  manifest so CI phase-gated checks advance with the migration instead of
  always running P0.

Run `dotnet build/test/format` + `git diff --check` at P0, cutover, and final
gates. If TypeScript is untouched, do not rebuild `wwwroot` bundles.

## Pitfalls

- **read_file misreads UTF-8 Chinese files as "binary"** (large CJK docs):
  use `sed -n 'X,Yp'` via terminal or Python `open(..., encoding='utf-8')`
  instead; do not trust the binary flag.
- **GitHub CJK anchors**: GitHub's slugger removes full-width punctuation
  WITHOUT inserting a separator. `附录 D：SRS—HLD 完整设计追溯矩阵` →
  `附录-dsrshld-完整设计追溯矩阵` (the `：` and `—` vanish, gluing
  `D`+`SRS`+`HLD`). A hand-written `#附录-dsrs-hld-...` is broken. Verify
  against the real rendered anchor in a browser (`scrollY` > 0 after
  navigating to the fragment) before fixing pre-existing anchors. See
  `references/github-slugger-cjk-anchors.md`.
- **A script file with a hyphen (`validate-docs.py`) cannot be imported** as
  a Python module; load it with `importlib.util.spec_from_file_location`.
- **HLD duplicate-DES check**: count only *definition rows* (line whose
  first token is `DES-xxx-###`), not every textual occurrence — DES IDs
  legitimately appear in the appendix matrix and tables.
- **ADR status markers vary**: Chinese ADRs use `- **状态**：`, English
  translations use `- **Status**:` or `## Status`; the validator must accept
  both.
- **Blob recompute after link rewrites**: any link-depth fix after review
  changes the blob; update `reviewedCandidateBlob`/`canonicalBlob` and have
  the reviewer re-confirm the final blob. After ANY bulk recompute, run a
  sweep asserting no English Canonical document has an empty
  `canonicalBlob` — a naive `integrity` rewrite can silently blank all 17
  ADR blobs while `translatedFromBlob` stays correct.
- **`sed -i` on shared paths**: after `git mv` to `docs/zh/`, relative link
  depths change; re-scan inbound links each phase and fix depths
  (`./zh/...` → `../zh/...` → `../../zh/...`) rather than assuming prior
  replacements still hold.
- **Pre-existing doc inconsistencies** (e.g. audit says 48 Verified, header
  says 49): preserve original numbers in translation; record the discrepancy
  in the final report; do not silently "fix" contract numbers.
- **Translated table cells must not keep Chinese punctuation**: in a wide
  bilingual table (traceability/audit), the Requirement/DES/Phase/Owner
  columns stay byte-identical with the source (including `、` separators),
  but translated cells (Test evidence, Notes) must use ASCII punctuation
  (`[ADR-0002](...), [ADR-0003](...)`), not `、`/`：`. Reviewers flag `、` in
  a translated cell as Low residue; fix and keep key-column parity at
  zero-diff.
- **Machine-consumed tables have a format contract, not just content**:
  `RequirementsBaselineTests` matches appendix rows with
  `^\| (REQ-...) \|` — exactly one space after the ID. Translation
  subagents often pad cells for visual alignment (`| REQ-F-001   | 🔴       |`),
  which breaks the regex (150-row index silently drops to 0 matches). After
  merging parts, normalize machine-consumed tables to the compact
  `| REQ-F-001 | 🔴 | ... |` form and re-run the contract test; also keep the
  `<!-- 项目:requirements-index:start/end -->` markers verbatim.
- **Duplicate headings at parallel-translation merge seams**: when parts are
  `cat`-ed, the same `## N Section Title` can appear at both part1 tail and
  part2 head (`## 5 Interaction Architecture` twice), or a subagent can emit
  a heading twice. After merge, grep for consecutive duplicate heading lines
  (`grep -n '^## ' file | uniq -d`-style) and dedupe before review — the
  bilingual reviewer will flag it as Low but it is trivial to catch earlier.
- **Translation subagents drift on prose style even when tuples are exact**:
  reviewers may find `tool window` vs glossary `Tool Panel`, `Dock region`
  vs `Dock Region`, or `must forbid` where source says 应 (should). These are
  Low but worth a batch fix pass before cutover; use the glossary as the
  single authority and `grep` for known variant spellings across the merged
  file.
- **Async review results arrive late and reference a stale tree**: review
  subagents finish after later commits, so their findings may already be
  fixed. Re-verify each item against the current worktree
  (`grep`/`git hash-object`/`git status`), classify already-fixed /
  still-open / stale-snapshot, commit only still-open items, and state in
  the commit message which listed findings earlier commits resolved. See
  the "Late-arriving async review results" section in
  `references/multilingual-migration.md` 中的逐 Phase 配方。

## Post-Migration Remote Merge (PR already squash-merged)

A long-lived migration branch that gets pushed and PR'd can be squash-merged
into `main` while the branch keeps gaining commits (e.g. new worked-example
guides added after the PR snapshot). When the user says "先在本地合并远程最新
提交" (merge remote latest locally first) before pushing more work:

1. **Probe before merging**: `git fetch origin`, then
   `git show -s --format="parents: %P" origin/main` — a single parent means
   the PR was squash-merged, so `main`'s history is NOT your branch history.
   `git ls-tree origin/main docs/en/guides/` shows whether the merged main
   already contains files you added after the PR snapshot (it will not).
2. **Expect a near-clean merge**: because the squash content is byte-identical
   to your migration commits, `git merge origin/main` typically conflicts ONLY
   on shared index files both sides edited (e.g. the Developer Guides list in
   `docs/en/README.md` → add/add conflict). Resolve by keeping the HEAD side
   (your new entries); there is no content loss on either side.
3. **Prove correctness after merge**: `git merge-base feature origin/main`
   must equal `origin/main` (history aligned), and
   `git diff origin/main feature --stat` must show ONLY your post-PR additions
   — pure new files, no deletions/rewrites of merged content.
4. Then push; the new commits appear as the branch's delta on top of the
   merged PR. If the new content must reach `main`, open a follow-up PR.

## Follow-Up PR After a Squash-Merged PR

Once PR #N (the migration) is squash-merged, do NOT open the follow-up PR
from the same long-lived feature branch. The squash made `main`'s history
disjoint from the branch, so the branch shows N+ commits "ahead" that are all
already in `main` — a PR from it is a giant noise diff. Instead:

1. Create a fresh branch from the CURRENT `origin/main`:
   `git switch -c feature/<topic> origin/main` (this also sets up tracking).
2. `git cherry-pick <sha1> <sha2> ...` only the new post-PR commits (verify
   with `git diff origin/main --stat` that the fresh branch carries exactly
   the intended delta — pure additions, no rewrites).
3. Run the same gates (build/test/format + link checks), push, and open the
   PR from the fresh branch. Base stays `main`; mergeable stays clean.
4. The fresh-branch history is the PR history — two commits, no migration
   noise. The user asked for exactly this ("新开PR") after seeing the PR #5
   squash merge.

## Linear-History Preference (do not rewrite merged public history)

项目 maintainers prefer linear history but will NOT rewrite already-merged
public history. When asked "可以令其线性合并吗?" about a PR that was merged
as a traditional merge commit (68 commits, two parents, on `main` with 5
later PRs stacked): present the two options and let the user choose —
- Path A (rewrite): rebase/re-merge to flatten; requires force-push, breaks
  every clone and the GitHub records of the later PRs. High risk.
- Path B (safe, usually chosen): keep merged history as-is; use
  **Rebase and merge** for all FUTURE PRs (`gh pr merge <n> --rebase`, or
  the GitHub "Rebase and merge" button, or local
  `git rebase main feature/x && git push`).
Never force-push a shared `main` to linearize history without explicit
user confirmation of the blast radius.

## Remote Branch Cleanup (after PRs merge)

When the user asks to review and delete obsolete remote branches
("查看远程分支情况，删除多余分支"):

1. `git fetch --prune origin` FIRST — remote-side deletions (branches
   deleted after their PRs merged) propagate here; `git branch -r` then shows
   only survivors.
2. For each survivor compute: is it an ancestor of `origin/main`? How far
   ahead/behind? Content-vs-main diff (`git diff origin/main <branch>
   --stat`) reveals whether "ahead N" is real new work or just history
   divergence from a squash merge — a branch whose diff is empty/only-reverted
   is obsolete even when `--is-ancestor` says no.
3. Present the table (branch / PR-merged? / diff vs main / verdict), then
   CONFIRM deletion scope with the user via clarify — deleting remote
   branches is irreversible. Local branches of remote-deleted branches show
   `[gone]` tracking; ask before deleting those too.
4. `git push origin --delete <b1> <b2>` (batch), then `git branch -D <b1>
   <b2>` locally. Keep `main` and any branch the user explicitly wants to
   retain (e.g. the migration branch itself, even if content is fully
   merged).

## Post-Migration Worked-Example Guides

After the migration lands, a user may say the existing guides are still too
abstract ("阅读了开发指南文档后，还是不太理解项目" — read the guide but still
don't understand). The fix is NOT another rules document; it is a pair of
CASE-DRIVEN worked-example guides: one consumer guide (how to use the
components) and one developer guide (how to make a change), each with an
English canonical + Chinese mirror, added to the top of the Developer
Guides index.

CRITICAL: verify every API signature in a worked example against the real
source (`grep` the ctor/method in `src/`) — constructor parameter order and
"service already holds the workspace" call-site shapes are the two most
common silent errors, and a wrong example is worse than no example. See
`references/worked-example-guides.md` for the full structure, the
verification loop, and the bilingual mirroring rules for new guides.

## Related Skills

- `ada-docs-revision` — terminology/restructuring within one document; this
  skill is the language-pair migration superset.
- `ada-doc-traceability-audit` — traceability matrix audits.
- `ada-srs-revision` / `ada-srs-writing` — SRS-specific lifecycle work.
