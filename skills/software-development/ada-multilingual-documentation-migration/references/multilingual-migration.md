# Multilingual Documentation Migration — execution detail

Detailed playbook companion to the SKILL.md. Proven on 项目 docs
(Chinese→English, `docs/en` + `docs/zh`, English canonical), executed as
P0..P6 with 10 commits on branch `feature/multilingual-docs`.

## Typical phase/commit sequence

| Phase | Commit message prefix | Content |
|-------|----------------------|---------|
| P0 | `docs(i18n): add documentation manifest, status table and validation baseline` | manifest JSON, translation-status.md, `scripts/validate-docs.py`, stable HTML markers in SRS appendix, refactor contract test to read manifest |
| P1 | `docs(i18n): migrate root README, docs index, guides and security` | root README → English + README.zh.md; docs/README.md → docs/zh/README.md + docs/en/README.md + language-selector stub; guides/security git mv |
| P2 | `docs(i18n): migrate development records to bilingual layout` | development/ (work-packages, remediations) |
| P3 | `docs(i18n): migrate ADR index and ADR-0001 through ADR-0017` | adr/ (index + 17 ADRs) |
| P4 | `docs(i18n): migrate verification evidence to bilingual layout` | evidence/ incl. programmatic 150-row requirement audit translation |
| P5a-c | `docs(i18n): add reviewed English SRS, HLD and traceability translations` | three normative docs translated under docs/en/, marked English Ready for Cutover, blobs recorded |
| P5d | `docs(i18n): atomically cut over SRS, HLD and traceability to English` | git mv legacy bodies → docs/zh/, pointer stubs at legacy paths, manifest authority flip, link updates across repo |
| P6 | `docs(i18n): archive migration plan and complete the documentation migration` | plan doc → docs/zh/development/ + docs/en/development/, remove root stub |

After P6, expect a TAIL of review-fix commits driven by late-arriving async
reviews (subagents dispatched mid-migration finish after you committed later
phases). The 项目 run ended with 17 commits: the 10 phase commits above plus
7-8 fix commits following a predictable naming pattern:

| Commit prefix | What it fixes |
|---------------|---------------|
| `docs(i18n): restore canonical blob integrity records in manifest` | empty `reviewedCandidateBlob`/`canonicalBlob` after link rewrites (recompute all blobs == `git hash-object`) |
| `docs(i18n): address P0 review debt in manifest and validator` | manifest `currentPhase` default, bidirectional status check, HLD definition-row duplicate check, non-`.md` anchor skip |
| `docs(i18n): apply SRS bilingual review fixes` / `... HLD ...` / `... traceability ...` | reviewer Low/Nit items: duplicate headings, term-case drift (`Dock region`→`Dock Region`), prose variants (`tool window`→`Tool Panel`), must/should strength; refresh canonical blob |
| `docs(i18n): translate consumer evidence into Chinese` | canonical-language source (was already English) still needs a REAL translation on the other side |
| `docs(i18n): fix bullet spacing in Chinese ADR-0003` | pre-existing `-成功` marker-without-space bullets render as text, not list items |
| `docs(i18n): clarify docs language selector wording` | selector copy ("canonical after cutover" → "canonical") |
| `docs(i18n): remove migration control files from the branch` | maintainer-directed deletion of manifest + status table + docs/README.md language selector (control layer is migration-time, not permanent) |
| `docs(i18n): drop migration control layer references` | `git rm` validator script, remove CI docs job, refactor contract test back to direct `docs/en/...` paths (KEEP the 项目 markers), simplify AGENTS/CONTRIBUTING/templates prose rule |

Treat this tail as normal, not as scope creep: each commit is one reviewer
finding class, re-verified against the CURRENT tree (many findings were
already fixed by later phases — see "Late-arriving async review results").
The final pair of tail commits may be the maintainer deciding the migration
control layer itself (manifest/status/validator/CI docs job) is not wanted
in the permanent repo — see the SKILL.md "Post-migration control-layer
removal" step: those artifacts die with the migration, the stable
`<!-- 项目:requirements-index:start/end -->` markers and the bilingual
doc layout are the durable outputs.

## Validator design notes

- `validate-docs.py` should accept `--phase P0|...|P6` and be state-aware:
  - authority path always must exist
  - legacy route source must exist once `activeFromPhase` reached
  - target must exist once `migrationPhase` reached AND state requires it
  - P6: every `mirrorRequired` target exists
  - mirror-set check: iterate manifest docs where state == English Canonical
    and require both targets — do NOT diff directories (translations exist
    before mirrors; e.g. docs/en/SRS.md exists at P5a but docs/zh/SRS.md
    only after P5d)
- **`currentPhase`**: add it to the manifest and make `--phase` default to
  it (`phase = args.phase or manifest.get("currentPhase")`). CI runs the
  validator without `--phase`; a P0 default would silently skip every
  phase-gated check once the migration advances. At the end of the
  migration the manifest says `"currentPhase": "P6"` and CI enforces the
  full mirror set.
- **Bidirectional status/manifest check**: `validate_status_consistency`
  must (a) require every manifest Document ID to have a status row AND flag
  status rows with unknown IDs, and (b) parse each row's
  `` `path` / State `` authority column and compare path+state against the
  manifest. Prove it with a negative test (temporarily set one row's state
  to `English In Review`, expect exit 1 and
  `status table authority state mismatch for ...`), then restore.
- **Status-table authority regex pitfall**: the role column is NOT
  backticked while the en/zh path and authority columns ARE. A regex like
  `` \| `([a-z0-9-]+)` \| `([^`]+)` \| `([^`]+)` \| `[^`]+` \| ... `` fails
  to match any row (role cell is `Normative requirements`, not
  `` `Normative requirements` ``). Correct pattern:
  `` ^\| `([a-z0-9-]+)` \| `([^`]+)` \| `([^`]+)` \| [^`|]+ \| `([^`]+)` / ([A-Za-z ]+) \| `` —
  role column matched with `[^`|]+` (no backtick). Verify the regex against
  a real row with a quick `re.match` before wiring it into the validator.
- Contract test (`RequirementsBaselineTests`) must read SRS/audit paths from
  the manifest via `JsonDocument`, and locate the appendix by stable HTML
  markers `<!-- 项目:requirements-index:start/end -->` — never by Chinese
  headings or hardcoded filenames. After cutover the test silently starts
  validating the English docs; that is the intended language-neutral path.

## Delegation pattern (translation + review)

- Large doc (4-5k lines): split by chapter boundaries into 2-4 chunks,
  dispatch parallel subagents writing `docs/en/FILE.partN.md`, each given:
  - the shared glossary file path
  - hard rules (IDs/code/numbers never translated; AC count/order preserved;
    must/should/may strength preserved; fenced-block classification)
  - the exact source line range
- Concatenate parts, then run tuple checks BEFORE merging: ID set equality,
  ID order, Priority/Actor equality, AC counts per block, appendix index
  rows. Fix table formatting to satisfy the contract test regex
  (`^\| (REQ-...) \|` needs single-space-padded cells).
- Delete part files after merge so mirror-set checks don't fire.
- Bilingual review: delegate a fresh subagent to compare EN↔ZH semantics
  (not fluency): must/should/may strength, failure semantics, AC boundaries,
  numeric constraints, security terms. Verdict APPROVE / NEEDS-FIX.
- Independent phase review: delegate a fresh subagent per phase with the
  exact checklist for that phase (git mv renames, tuple parity, manifest/
  status consistency, blob hash-object match, link depth, no product-code
  changes).

## P5d pre-cutover human review gate

Before executing the atomic cutover, present a structured report to the user
and wait for explicit confirmation. The report must include:

1. **source blob** (`translatedFromBlob`) per core document
2. **reviewed candidate blob** per document + reviewer verdict
   (APPROVE / NEEDS-FIX / checks-passed)
3. **structural tuple comparison results** — ID sets, order, Actor/Priority,
   AC counts, appendix rows, 0-diff statement
4. **reviewer findings and fixes applied**
5. **remaining contract-semantic doubts** (e.g. pre-existing number
   discrepancy between two docs that both languages preserve; term-table CJK
   is intentional)
6. **what P5d will change**: authority paths (legacy → docs/en/), the three
   compatibility stubs that stay permanent, and that Chinese bodies move to
   docs/zh/

Do NOT execute P5d or mark English Canonical until the user confirms. This
gate is a hard stop — the task instructions treat it as the only
mid-migration pause besides blocking ambiguity or irreversibility.

## Delegation summary truncation (Hermes)

`delegate_task` final summaries are truncated in the live transcript at
`+97 chars`. The FULL report is saved at
`cache/delegation/subagent-summary-<delegation>-<ts>.txt` — read that file
(via `read_file`) rather than reconstructing from the log. Also the
`task-N.log` think lines are reliable evidence of the verdict when the
summary is cut.

## Late-arriving async review results (Hermes)

Review subagents dispatched mid-migration finish AFTER you have committed
later phases, and their `[ASYNC DELEGATION BATCH COMPLETE]` messages arrive
with stale context. Treat every late report as a snapshot of an older tree:

- Re-verify each finding against the CURRENT worktree before fixing. In the
  项目 run, most late findings were already resolved by later commits:
  P5c's 18 broken `./zh/` links and the missing switcher target were fixed
  by the P5d cutover; P4's Medium blob drift was fixed by the blob-integrity
  rebuild commit; SRS M1 (appendix B "missing" column) was based on an
  earlier snapshot — the file already had the 4-column table.
- Classify each item as already-fixed / still-open / stale-snapshot. Only
  still-open items get a new commit. `grep`/`git hash-object`/`git status`
  are the first tools, not the diff of the old review.
- Commit messages for late-fix commits should state which listed findings
  were already resolved earlier (`... was already corrected by the P5d
  atomic cutover; verified ...`), keeping the audit trail honest.
- Read the full saved summary file, not just the truncated transcript; the
  tail usually carries the per-finding severity table that reveals which
  items are stale.

## Ad-hoc verification scripts (Hermes)

The platform repeatedly asks for "fresh verification evidence" after file
edits. Pattern that works:

- Write a focused verification script to the OS temp dir
  (`C:\Users\World\AppData\Local\Temp\hermes-verify-<commit>.py`), covering
  ONLY the behavior the commit changed (not a full suite).
- Run it; report `PASS/FAIL` per check.
- Delete the script and any `__pycache__` after running.
- State plainly: "ad-hoc verification, not canonical suite — suite green is
  established separately via `dotnet test`/`format`" (or repo equivalent).
- If an ad-hoc check fails because the script itself was wrong (e.g. it
  looked for English section titles in a now-Chinese file), fix the script
  and re-run — do not accept the false failure as a product defect.

## Real pitfalls (each one cost time)

1. `read_file` flags UTF-8 Chinese markdown as "binary" → use `sed -n` or
   python for reading; write with `write_file` is fine.
2. GitHub slugger on CJK: `附录 D：SRS—HLD 完整设计追溯矩阵` →
   `附录-dsrshld-完整设计追溯矩阵` (colon/em-dash removed, D SRS HLD merge
   with no separator). A pre-existing link `#附录-dsrs-hld-...` was actually
   BROKEN. Verify anchors against github-slugger + scroll position, not
   intuition. Fix pre-existing broken anchors during the move (documented as
   link repair, not contract change).
3. Contract-test table regex: pretty-aligned multi-space cells
   (`| REQ-F-001   |`) fail `^\| (REQ-...) \|`; normalize programmatically
   to `| REQ-F-001 |`.
4. CJK in term tables (§1.5 term + 中文 definition columns) is intentional;
   do not flag as untranslated residue.
5. Link depth: moving a file deeper by one dir level requires one more `../`
   on EVERY relative link inside it; sibling language dir is `../en/...`
   not `./en/...`; inbound links to the moved path must be scanned repo-wide.
6. ADR status markers: ZH `- **状态**：` (full-width colon) vs EN
   `- **Status**:`; validator must accept both.
7. After cutover the validator must resolve SRS/HLD/ADR paths from the
   manifest; if it keeps hardcoding legacy paths it validates the stub.
8. Blob fields can silently go empty after link rewrites → run a reconcile
   pass (recompute all canonicalBlob == git hash-object) and commit it
   separately (`docs(i18n): restore canonical blob integrity records...`).
9. HLD duplicate-DES check: count only definition rows
   (`^(DES-[A-Z]+-\d{3})\s*$`), NOT global `\bDES-...\b` matches — IDs
   reappear in Appendix D and cross-refs, so a global count flags all of
   them. The "set is already unique" form is dead code; either form needs
   raw matches.
10. Anchor checks on non-`.md` targets (`img.png#frag`) throw
    UnicodeDecodeError; skip when `resolved.suffix != ".md"`.
11. Reviewer L/N findings are fixable even on APPROVE:
    - duplicate heading → delete one (re-run anchor checks)
    - `Dock region` vs `Dock Region` → normalize to glossary case
    - `tool window` vs `Tool Panel` → use glossary term
    - `must forbid` vs `should forbid` for 应 → align to glossary strength
    After fixes: re-run tuple checks (must stay 0-diff vs source), refresh
    canonicalBlob in manifest+status, commit as
    `docs(i18n): apply SRS bilingual review fixes`.
12. Final: `find docs/en -name '*.md'` vs `docs/zh` identical modulo
    declared exceptions (language selector, manifest, status table).
