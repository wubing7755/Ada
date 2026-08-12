# Worked-Example Guides (post-migration consumer/developer docs)

Trigger: after a large documentation migration lands, a user may say the
existing guides are too abstract — e.g. "阅读了开发指南文档后，还是不太理解项目"
("I read the development guide but still don't understand the project").
Do NOT respond with yet another abstract rules document. The fix is a pair of
CASE-DRIVEN worked-example guides, one for consumers (how to use the
components) and one for developers (how to make a change to the project).

## What worked (项目 run, docs/en|zh/guides/)

Two guides, each with an English canonical + Chinese mirror:

1. `using-项目.md` — "Using 项目: A Worked Example"
   Consumer walkthrough: reference packages → register services → register
   content providers → declare a workspace definition (programmatic AND
   declarative) → create workspace through factory → render Host →
   operations/queries → persistence (serialize / restore / presets).
   Rule: EVERY code snippet mirrors a real runnable consumer sample
   (`samples/Demo`), so the doc is proven to compile/run.

2. `developing-项目.md` — "Developing 项目: A Worked Example"
   End-to-end change walkthrough: start from an SRS requirement → read
   traceability → HLD DES → ADR → owning Core module → write failing test
   (TDD) → smallest owning change → full local gate → update traceability in
   same commit → cross-boundary/public-API change paths → commit conventions
   → common mistakes.

Both were added to the Developer Guides index in `docs/en|zh/README.md` at
the TOP (new readers see them first), keeping the existing abstract guides
below.

## Critical pitfall: API signatures in worked examples MUST be verified
against the actual source, not written from memory

A worked example with a wrong signature is worse than no example. In the
项目 run, the first draft of `using-项目.md` had TWO wrong persistence
examples:

- `new LayoutPresetService(store, serializer)` — the real ctor is
  `LayoutPresetService(IWorkspace workspace, ILayoutSerializer
  serializer, ILayoutPresetStore store)`.
- `presets.SaveAsync(workspace, "my-layout")` — the real signature is
  `SaveAsync(string name, CancellationToken)`; the service already holds the
  workspace.

Verification loop before committing any worked-example doc:

1. For every public type/method shown, `grep` the real signature in `src/`
   (`grep -n "public .*SaveAsync" src/.../LayoutPresetService.cs`).
2. Check constructor parameter ORDER — the most common silent error.
3. Check whether the service/facade already holds the workspace/state, so
   call sites take fewer arguments than intuition suggests.
4. Cross-check extension-method static classes too: `WorkspaceQueries`
   provides `workspace.TryGetItem(...)` extension methods; name the static
   class in prose so readers can find it.
5. After editing, re-run link/anchor checks (including the zh anchor for a
   Chinese HLD heading, which uses the CJK-slugger form) and the en/zh
   mirror-set equality.

## Structure that reads well for "I still don't understand"

- Numbered sections that follow the real build/use order (1..8), not the
  module topology.
- Short "Key types" bullet list after the first big code block (name →
  one-line responsibility), so the model lands before later sections.
- One small complete snippet per concept, then prose explaining the few
  lines that matter (ownership enums, lifecycle, barriers).
- A "Where To Go Next" footer linking the runnable sample, SRS, HLD public
  API surface, and ADR index.
- For the developer guide: a "Common Mistakes To Avoid" list; users who
  feel lost respond well to "here is what NOT to do".

## Bilingual mirroring for new guides

- Write the English canonical first, then the Chinese translation with the
  language-switch header (`> [English](../../en/guides/x.md) | 简体中文` +
  `状态：Chinese Synchronized。`).
- Keep the mirror sets identical: `diff <(find docs/en -name '*.md' | sed
  's|docs/en/||' | sort) <(find docs/zh -name '*.md' | sed 's|docs/zh/||' |
  sort)` must stay empty.
- Link depth in guides: `docs/en|zh/guides/` → `docs/` root is `../`,
  repo root is `../../`, sibling language is `../../<lang>/guides/...`.
- A zh guide linking to `docs/zh/HLD.md` must use `../HLD.md` (not
  `./HLD.md`) and the CJK anchor of the Chinese heading
  (`#102-规范性公共-api-surface-manifest`), NOT the English anchor.

## Commit shape

Land the guides as their own commits (e.g. `docs(i18n): add worked-example
guides...`), then a corrective commit if signature verification found
errors (`docs(i18n): correct API signatures in the 项目 usage guide`).
Ad-hoc verification script pattern: mirror parity, link/anchor
resolvability, required-identifier presence, glossary-term presence —
clean up the temp script after.
