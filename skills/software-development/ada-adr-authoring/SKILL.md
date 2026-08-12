---
name: ada-adr-authoring
description: "Use when authoring an architecture decision record (ADR) for a project with bilingual docs."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [adr, architecture, documentation, bilingual]
    related_skills: [ada-docs-revision, ada-srs-lifecycle, ada-doc-traceability-audit]
    trigger_keywords: ['ADR', 'architecture decision', 'Proposed', 'Supersession', 'decision record']
---

# ADR 编写（双语）

## Overview

项目以 ADR 记录架构决策：`docs/en/adr/` 为权威（canonical），
中文翻译在 `docs/zh/adr/`。仓库有 20+ ADR 和 ADR-first 文化（公共 API / 包 / 协议 / 持久化 / 安全
变更都需要 ADR）。本技能沉淀经实测验证的编写工作流。

## Mandatory ADR Structure

Each ADR must contain: **Context, Decision, Alternatives, Consequences,
Verification, Supersession** (plus frontmatter: Status, Date, Decision maker,
Related). Changing an Accepted ADR requires a NEW ADR — never rewrite the
original decision history.

## Workflow

1. **Read existing ADRs + both READMEs first.** Mirror the format of the most
   similar recent ADR (e.g. one covering bundled contract changes). The
   README index table records Status + one-line Decision; keep the table style.
2. **Verify SRS anchors against the real file.** `docs/en/SRS.md` line numbers
   drift; grep the actual REQ-F numbers (`grep -n "REQ-F-xxx"`) and quote the
   exact requirement text. Cite line numbers only after confirming them.
3. **Verify framework API shapes against actual source — never invent
   signatures.** Before writing a candidate API, read the real contract
   (command types, workspace interface, outlet, catalog).
   Real pitfall: an update method that requires TWO parameters will not
   compile if the plan wrote a single-argument call. Also confirm internal
   vs public visibility (a context type's ctor may be internal — consumers
   cannot construct it).
4. **Write English canonical, then Chinese translation.** Preserve: decision
   IDs (D1–D5), code identifiers, enum values, error codes, numeric
   constraints, must/should/may strength, and section order. Add the language
   pair link line at the top of both.
5. **Update BOTH README indexes** (`docs/en/adr/README.md`,
   `docs/zh/adr/README.md`) with the new row (Status, one-line decision).
6. **Identifier-consistency check** between en/zh before commit:

```sh
diff <(grep -oE "IdentifierA|IdentifierB|..." docs/en/adr/00XX.md | sort -u) \
     <(grep -oE "IdentifierA|IdentifierB|..." docs/zh/adr/00XX.md | sort -u)
```

7. **Status gate.** Drafts are `Proposed` — only the maintainer approves
   `Accepted`. The README row must say `Proposed` until then. Commit with
   `docs(adr): propose ... (FR-xx/yy)`.

## Decision-writing guidance

- **Package related contract changes together** (precedent from real ADR series) instead
  of one ADR per parameter — the bundling makes the trade-off reviewable.
- **Give recommended API shape + alternatives.** Write the actual candidate
  signature in a code block, list rejected alternatives with one-line
  reasons, and flag the maintainer decision points explicitly.
- **State capability boundaries** (least privilege) when exposing new
  channels: what content MAY do vs MUST NOT do, and how the trust boundary
  (SandboxedFrame) interacts.
- **Supersession must be explicit**: say whether the ADR extends, supersedes,
  or leaves untouched each related Accepted ADR (e.g. "extends ADR-0012,
  does not change ADR-0013" — use the actual numbers).
- **Record explicit rejections** (e.g., typed Kind) so the trade-off is not
  re-litigated without new evidence.

## Maintainer decision workflow (verified in practice)

After the Proposed draft, the maintainer needs a decision, not a document.
This user's pattern:

1. **Impact analysis per decision point** — a table of (public API surface /
   architecture boundary / lifecycle / security) effects + risks, each with an
   explicit recommended default. Listing options with no recommendation gives
   the maintainer nothing to decide. Be honest about structural costs (API
   freeze, number of lifecycles, security single-points) — that is what lets
   the maintainer choose "bundle vs track-scoped".
2. **Numbered decision list** — grouped, ≤9 points, each with a recommended
   default. The user replies "按推荐执行" (accept all) or "编号+你的选择"
   (e.g. "4 用 ContentStateFactory，8 待定" — substitute the real item names).
3. **固化 decisions INTO the ADR on acceptance** — add a
   "maintainer decisions on <date>" line to the metadata block, rewrite
   confirmed shapes as confirmed (move rejected alternatives to Alternatives
   with rationale), add an **Adoption Order** section when track-scoped.
4. **Track-scoped adoption, not bundling** — core-value decisions first,
   security-heavy ones reviewed separately after consumer feedback, boilerplate
   deferred, rejected ones recorded. Adoption order ≠ approval: Status stays
   `Proposed` until implementation is approved.
5. **Implementation gate** — framework-side changes get a `.hermes/plans/`
   plan for approval first (with per-phase TDD + independent commits), even
   after the ADR decisions are confirmed.

Pitfall: `diff` returns exit 1 when files differ — a `diff ... && git add ...`
chain silently stops after the diff. Run the identifier check as a separate
command from the commit.

## Pitfalls

- Inventing API shapes instead of reading source → compile-breaking ADR.
- Citing SRS line numbers from an old review doc without re-verifying.
- Writing only English or only Chinese — the pair must stay synchronized
  (Chinese file carries the "Chinese Synchronized" header).
- Forgetting to update the README index on either side.
- Treating a Proposed ADR as approved — implementation gates on maintainer
  approval.

## Verification Checklist

- [ ] Structure: Context / Decision / Alternatives / Consequences /
      Verification / Supersession all present
- [ ] SRS anchors re-verified against `docs/en/SRS.md`
- [ ] Candidate API signatures checked against real source
- [ ] en + zh both written; identifier diff empty
- [ ] Both README indexes updated
- [ ] Status `Proposed`; commit message `docs(adr): ...`
