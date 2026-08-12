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

## Batch Audit Gate（批次独立审查）

Independent, read-only audit of a batch of changes ("批次 N 改动") against a
user-supplied numbered checklist. Every item gets a PASS/FAIL verdict backed by
file:line evidence. This is the "independent review" gate of phased delivery.

**Activation**: 独立审查 / 独立复核 / 审查批次 N 改动 with a numbered checklist;
a batch needs a gate review before merge or before the next batch.
**Do NOT use for**: verifying claims in an existing report
(ada-code-quality-report-verification), impact analysis of a commit/branch,
generating a quality report
(ada-code-quality-analysis), or auditing docs against the diff
(ada-doc-implementation-audit).

**Core principles**:
1. **Read-only discipline.** Never modify worktree files. Re-running
   generators/builds is allowed; if a regenerated artifact differs from the
   committed one, report it — do not "fix" it. State 未修改任何文件 in the report.
2. **Evidence = file:line + re-run tool output.** Tool claims (test runs,
   converter output, JSON contents) are re-run, never assumed.
3. **Absence checks are evidence too.** `grep -n '<pattern>'` returning exit 1
   (no match) proves "no stale logic". Document the exit code.
4. **Never fabricate.** If the source data contains no status/tags elements,
   the generated output must show empty values — that empty serialization IS
   the correct evidence that nothing was invented, not a defect.
5. **Prefer programmatic verification:** python one-liners for JSON counts and
   key-set parity, `grep -c` for counts, tests for gate status.

**Workflow**:
1. Scope the batch: `git diff --stat` — know every touched file.
2. Map checklist items to files; read each file fully.
3. Per item, gather evidence in order: source-level lines → gate-level re-runs
   → absence greps (exit 1 = evidence) → parity diffs (zh/en key sets, CSS
   class definitions vs usage).
4. Classify PASS or FAIL per item (nuances go in the item's evidence as 备注).
5. Write the report: `## 审查结论（N/N PASS, M FAIL）` summary up front →
   `## 逐项清单`（verdict first, then bullet evidence with file:line）→
   `## 发现的任何问题或遗漏`（only real observations; non-blocking notes as 备注,
   do not inflate into FAILs).

**Layer-by-layer evidence techniques** (content pipeline, CSS, tests,
bilingual resources, SEO metadata, doc-sync sweeps, cross-SDK CI, git
hygiene, baseline-vs-batch regression judgment): see
`references/batch-audit-evidence-techniques.md`.

**Key pitfalls**:
- Generated data files are often gitignored — absence from `git status` is NOT
  evidence of a stale build; use `git check-ignore` + re-run the generator.
- `grep -c` returns exit 1 on zero matches — a "no match" absence check inside
  an `&&` chain kills the remaining evidence commands silently; run as
  standalone commands and document exit 1 as the intended evidence.
- `grep -rn "Symbol" src/` also matches compiled DLLs in bin/ and obj/ —
  scope source greps with `--include=*.razor --include=*.cs --include=*.js` or
  `--exclude-dir=bin --exclude-dir=obj`.
- A newer host SDK can hide a real compiler mismatch in the workflow's
  declared SDK — re-run the gate in a scratch copy pinned to that exact SDK.
- Baseline vs batch: when "data is missing", prove whether the batch caused it
  (`git diff HEAD -- <data-source>` empty = pre-existing → 备注, not FAIL).

## Review-Gated Batch Loop（先审后改的逐批执行）

Execute a numbered-batch plan (`.hermes/plans/...` 批次 N) where the user wants
a **pre-implementation review + explicit approval** before each batch
("先输出精确改动清单和影响分析，不要立即改码；等待我批准后再实施"). Each batch is a
closed loop: **review → approval → implement → verify → independent audit →
report**. Validated over 11+ consecutive batches; framework-agnostic.

**Pre-implementation review (NO code edits)**:
- Re-read the plan section; check `git status` (prior batches stay uncommitted
  until user reviews); verify the previous batch's actual result; state
  explicitly whether the plan is stale.
- **Verify the plan's 涉及文件 list by tracing call chains — never trust the
  list alone.** Real misses: a plan renumbered routes but omitted the page file
  itself; a plan added model fields but omitted the `Clone()`/mapper on the
  data path — the clone drops unlisted fields and new data silently vanishes at
  runtime. Any Clone/mapper/copy method touching the modified type must be
  updated for new fields. Check workflow/CI steps needing env injection.
- Output contract (what the user approves): exact change list (per file, the
  concrete diff description); impact analysis (nav / routes / search / sitemap
  / resources / publish artifacts); dead-code & resource-key sweep (never
  delete keys still used by future/hidden-but-routable pages); verification &
  acceptance commands; open decision points (recommend one option with
  rationale).
- **Stop and wait for explicit approval** (「批准」/「确认」). Do not implement
  during review.

**Implement strictly per the approved list**: no batch-N+1 while doing batch-N;
no opportunistic refactors. If a fix discovered during verification is inside
the batch's acceptance scope, fix it and report it as part of the batch.

**Canonical verification chain (main agent runs all of it)**:
`dotnet build` (0 errors, no new warnings) → `dotnet test <sln> --no-build` →
`git diff --check` (+ content converter re-run if content sources or generated
data changed; expect exit 0). A subagent's "tests passed" is a claim, not
evidence — re-run yourself.

**Publish + real-browser acceptance**: `dotnet publish -c Release -o
"C:/tmp/ppN"` (quoted Windows-style path), serve publish `wwwroot` with a
Python SPA-fallback server, drive with puppeteer-core across the viewport
matrix (320/375/430/768/1024/1440). Assert the batch's behavior in the DOM
(computed styles, element counts, aria, URL state) plus no horizontal overflow
and zero console errors (403 from rate-limited third-party APIs is expected —
confirm as such).

**Independent subagent audit**: `delegate_task` with the exact batch diff
description, a `file:line` evidence contract per PASS/FAIL item, read-only.
Then the **main agent re-runs the canonical chain itself** to verify claims.

**Per-batch report (Chinese)**: 实际修改文件（表格）/ 行为变化 / 测试和浏览器
验证结果 / 独立审查结果 / 遗留问题. Never commit, push, or deploy without
explicit instruction.

**Batch-loop pitfalls**: XML content-source edits — a bare `&` in an attribute
makes the whole XML unparsable; escape as `&amp;` and re-run the converter
first. CRLF files vs patch tools: `mode='patch'` (V4A) injects LF-only lines
into CRLF files (whole-block diffs); `mode='replace'` preserves CRLF; after
V4A, normalize back to CRLF. `dotnet publish -o` MSYS path mangling: `/tmp/out`
→ `C:\tmp\out`; use quoted `"C:/tmp/ppN"` and read the `-> C:\...` line for the
real location. Terminal cwd persists across calls — `cd` back to the repo root
in the same call that runs repo commands. Puppeteer language-switch timing:
wait for `documentElement.lang` to change after clicking the toggle;
localStorage language preference persists across pages in one browser
instance. HTML static metadata vs runtime HeadContent conflict: a static
`<link rel="canonical">` in index.html persists on every SPA page and wins over
the page's dynamic canonical — remove the static one. WASM startup interop
timing: `OnAfterRenderAsync` on the first render fires before JS interop is
reliably ready — gate on data-ready, use a one-shot flag for fragment
scrolling.

## Output Contract

Maintain a phase ledger with status, files, verification, commit/PR handle when applicable, and residual risk. Final reporting must distinguish completed execution from planned or blocked work and include the exact artifact and verification results.
