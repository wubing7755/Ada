# Bilingual Audit Common Pitfalls

## Common Pitfalls

- **Rename diff shows as new file**: `git diff HEAD -- <new-name>` prints the
  whole file as untracked. Use `git diff HEAD -M -- <old> <new>` to see the
  real delta ("similarity index 98%, 7 changed lines") — this is how you prove
  a rename+small-edit stayed in scope.
- **`RM` status row** = rename staged (from `git mv`) but worktree edits NOT
  staged. Report as process observation: final commit needs `git add -A`.
- **Premature canonical / compat-pointer claims**: wording like "remain
  available as compatibility pointers to the canonical English documents"
  may be factually wrong mid-migration — before the plan's cutover phase the
  legacy files ARE the canonical documents (Legacy Canonical, ZH) and no
  English canonical exists yet. Compare every state claim against the plan's
  state machine and the manifest's own `authority.state`; also flag
  EN-only sentences with no ZH counterpart (asymmetry).
- **Manifest blobs drifted from disk**: a manifest may claim blobs that no
  longer match the actual files (or the reviewedCandidate ≠ canonical).
  Always recompute with `git hash-object` / `git ls-files -s`; a mismatch is
  a real finding, not a style nit. Two related traps:
  - **Validator green ≠ blobs verified**: the repo's own phase validator may
    only TYPE-CHECK the three integrity fields (null-or-string) without ever
    comparing them to `git hash-object` output — so a stale/wrong
    `canonicalBlob` passes validation silently. Read the validator's source
    to learn what it actually enforces, then cite the gap: "validator only
    type-checks integrity fields; manual hash comparison found X".
  - **`git hash-object` without `-w` leaves no object in the DB**: if a
    manifest blob was computed but never committed, `git cat-file -p <blob>`
    fails with "Not a valid object name" — you cannot inspect what that blob
    contained. Compare manifest blobs against `git hash-object <worktree
    file>` directly; do not treat cat-file failure as proof the hash was
    never a real file state.
- **`R100` vs `D`+`A`**: run `git diff --cached --name-status -M` (with `-M`)
  to prove renames preserved history; without `-M` git may split a rename
  into delete+add in the report.
- **read_file misjudges UTF-8+Chinese files as binary**: when read_file
  reports "Binary file" but `file` says UTF-8, read via python
  (`io.open(path, encoding='utf-8').read()`) instead — do not skip the file.
  On git-bash, `sed -n '<start>,<end>p' file` also works directly for
  reading a range of a CJK file (no temp copy needed).
- **Preservation-check tokens must be sourced from the source text first**:
  a "token preserved" check that lists an id from MEMORY (e.g. `REQ-F-135`)
  false-FAILs when the source actually writes `F-135` (historical-number
  style) — the translation was right, the test token was wrong. Before
  adding any token to a preservation check, `grep -n` it in the SOURCE; if
  absent, the token is wrong, not the translation.
- **git-bash grep silently returns 0 on multibyte/emoji patterns**: counting
  priority markers with `grep -c '🔴'` on a file that DOES contain 🔴 can
  return 0 (locale-dependent multibyte pattern failure). Count emoji/CJK
  with Python regex (`re.findall(r'[🔴🟡🟢]', text)` + Counter), never grep.
- **Verification scripts: evidence trail + shell hygiene**: run ad-hoc
  verification scripts from the OS temp dir with a `hermes-verify-` prefix,
  keep the output, then clean up — a repo-local script deleted after running
  leaves no reproducible evidence. Prefer a script FILE over inline
  `python -c` (double-quoted `-c` with backticks breaks bash eval via
  command substitution), and avoid shell commands whose payload contains
  XML tags (`</svg>`) or backtick-quoted patterns — the command parser can
  reject them; move the logic into the script file instead.
- **Inline comments vs commands**: only the command text must be byte-identical;
  flagging translated `#` comments is a false positive.
- **Validator coupling**: a validator may still hardcode the OLD language label
  (e.g. only `当前版本`) — check its regex; if the plan required decoupling, a
  still-hardcoded label is a real finding.
- **Untracked plan file**: the change plan may intentionally remain untracked;
  that is not scope creep.
- **Polluting the tree during gate re-runs**: compileall writes `__pycache__`
  — verify gitignore covers it, and re-freeze git status afterwards.
- **Validator no-ops after a git mv (silent green)**: validation functions
  that read the OLD path (`if not old_dir.exists(): return`) become no-ops the
  moment files move — the validator still prints PASS, but the check it was
  supposed to run (e.g. ADR tuple comparison the plan mandates) never executes.
  Before trusting a green validator in a migration audit, READ its source:
  (a) does it still reference the pre-move path, and (b) does it actually
  compare the en/zh PAIR (many "tuple" validators only check titles/status
  presence in ONE directory, not cross-language parity). Report a no-op or
  missing cross-language check as a gate-strength finding even when your own
  manual comparison passes.
- **Backtick-token comparison must strip fenced blocks first**: extracting
  `` `([^`]+)` `` without removing ``` fences first yields giant multi-line
  garbage tokens (fence content matches across triple backticks) and a
  misleading diff. `re.sub(r'```.*?```', 'FENCE', text, flags=re.S)` before
  comparing inline backticked identifiers; also strip fences before bullet/
  link extraction.
- **Tuple extraction must join wrapped continuation lines**: `- **Related**:`
  values wrapped onto 2-space-indented next lines (`DES-OP-008,\n  DES-RND-001~009`)
  look like truncation mismatches to a line-based regex. Join continuation
  lines, and normalize `、` vs `,` enumeration separators (zh `、` = en `,` —
  NOT a mismatch) plus translated parentheticals in Decision-maker fields
  before diffing tuples.
- **No-space bullets (`-成功`) are a real rendering defect**: a bullet regex
  `[-*]\s+` silently misses items with no space after the dash — the count
  discrepancy IS the finding (invalid Markdown: renders as plain text, not a
  list item). When EN fixes the spacing and ZH keeps the original, confirm
  pre-existing via `git show HEAD:<old-path>` and report as Low with the
  "preserved verbatim" context.
- **Canonical rows with EMPTY candidate/canonical blobs**: a manifest may
  declare `English Canonical` + `Chinese Synchronized` + "review approved"
  while `reviewedCandidateBlob`/`canonicalBlob` are empty strings — violating
  the plan's blob-completeness rule for canonical rows and inconsistent with
  sibling entries that fill all three. Either the blobs must be filled
  (`git hash-object <en-path>` for both) or the state downgraded to
  `English In Review`; the review-approval claim is not backed by the record.
- **subprocess shell=True quoting on Windows**: single-quoted args in
  `subprocess.run(cmd, shell=True)` break silently (cmd.exe treats `'` as a
  literal) — `git diff 'HEAD:path' 'worktree/path'` returns empty/wrong
  output. Use list-args without shell: `subprocess.run(['git','diff',f'HEAD:{p}',f'{q}'])`.
  Also prefer the two-path form over `git diff <blob> -- <pathspec>`, which
  can misfire.
- **Part-seam heading overlap in parallel part translations**: orchestrator
  line ranges for adjacent parts can overlap by exactly one line (a section
  heading — part1 ended `## 5 Interaction Architecture` and part2 started
  with the same line). Read the sibling files (`ls docs/en/`, `tail -3
  partN`, `head -3 partN+1`) before finalizing the boundary: keep the
  heading your assigned range names and flag the 1-line duplicate for
  merge-time dedupe; if the NEXT part already starts with your range's
  inclusive end heading, exclude it and state so in the summary. Never
  silently drop an assigned heading, never duplicate body content. (Corollary:
  when the orchestrator instruction EXPLICITLY includes the boundary heading
  — \"translate lines 1–950\" where 950 IS `## 5 …` — include it; dropping
  requested lines is worse than a dedupable merge-seam duplicate.)
- **CJK-residual scans must cover the punctuation ranges**: bare
  `[\u4e00-\u9fff]` misses `、` (U+3001) and full-width parens （） — the
  two most common survivors in translated parts because they live in
  ID-list cells (`F-069、F-140`) and code-adjacent parentheticals
  (`LayoutNode（SplitNode / GroupNode）`, `WorkArea 的子 SplitNode`). Scan
  `[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]`; convert `、`→`, ` and
  （）→() in table cells and prose.
- **ASCII box diagrams need rebuilt widths, not label swaps**: CJK labels
  are double-width so the source diagram's alignment cannot survive
  translation, and English labels outgrow the old boxes. Rebuild box widths
  for the English labels, GENERATE borders programmatically
  (`'┌' + '─'*D + '┐'`, rows `'│' + text + ' '*(D-len(text)) + '│'`), and
  assert every diagram line has the same length before splicing — a
  hand-counted border produced a 72-vs-88 mismatch caught only by the
  assertion. `//` comment columns in pseudo-code blocks
  (`WorkspaceSnapshot = {…}`) are also structure: preserve the source
  block's alignment column and verify per block with `l.index('//')`.
- **`wc -l` counts newlines**: a `write_file` output without a trailing
  newline reports N−1 (python `split('\n')` said 973, `wc -l` said 972).
  Append `printf '\n' >> target` before reporting the deliverable's line
  count.
- **Modal-scan false positives (SRS contract audits)**: ZH must-class regex
  missing 不可 flags F-078's correct "must not" as strengthening; ZH
  may-class missing 可能 flags NF-008's "may produce" as drift. Include both
  tokens, restrict the EN may-class to may/allow (bare "can" over-matches),
  and hand-verify every class-absence flag before reporting it. A genuine
  but benign deviation is 应禁止→"must forbid" in a Description while all
  ACs use "should not" — Nit, not a finding.
- **AC-label scan catches Description references**: searching a whole REQ
  block for `AC\d*[：:]` matches "REQ-F-140 AC2:" inside a Description text
  (the only "AC mismatch" on a 150-block audit was exactly this false
  positive). Match labels only on label-shaped lines
  (`^\s*(AC\d*)\s*[：:]`), never on the whole block.
- **Windows python path mangling**: `python /c/Users/.../script.py` on
  git-bash fails with `C:\c\Users\...` — pass the quoted Windows path
  (`python 'C:\Users\...\script.py'`). Complex `for` loops with `;` or
  backticks can trip the command parser (hardline block) — move the logic
  into a script file. search_files on absolute Windows paths can also fail
  (os error 3) — the FIX is to pass a RELATIVE path from the repo root
  (e.g. `docs` or `docs\en\SRS.md`); relative paths resolve reliably, while
  absolute `C:\...` paths get mangled to `/c/...` before ripgrep runs.
  python `io.open(..., encoding='utf-8')` regex scans also work every time
  for large CJK files.
- **read_file "Binary file" is content-dependent, not per-file**: a dump
  file may be flagged binary while an identical-format sibling reads fine
  (s4.txt vs s37.txt in the same session) — do not retry; fall back to
  `sed -n` or python immediately.
- **Appendix table column parity**: row counts can match while the EN
  translation drops a whole column (Appendix B: ZH 4 cols incl. 推迟原因 →
  EN 3 cols). Compare column COUNT per table, not just rows; a dropped
  rationale column is a Medium content omission even though the deferred
  IDs/priorities/titles are intact. Also: index-row counts may exceed the
  doc's official count (158 vs 150) because summary rows contain REQ-
  tokens — that is expected, do not flag.
- **`来源：` vs `Source: ` footer prefix**: strip `(Source:|来源：)\s*` (note
  the `\s*`!) before comparing DES-block Source footers — the ASCII colon is
  followed by a space while the full-width one is not, so a bare prefix-strip
  leaves ` X` vs `X` and false-flags every single footer.
- **`、`→`,` alone is NOT enough separator normalization**: EN ID lists use
  `, ` (comma+space); `"A、B".replace('、', ',')` yields `A,B` which ≠ `A, B`.
  Normalize BOTH sides with `re.sub(r'\s*,\s*', ',')` (+ `、`→`,`) or every
  multi-ID row in a matrix table false-flags (this bit twice in one session:
  once in the audit, once in the verification re-run).
- **Error codes are backticked snake_case identifiers, not `ERR-\d+`**: an
  Appendix-B-style catalog (`LAYOUT_VERSION_INCOMPATIBLE`, `STALE_OPERATION`)
  returns ZERO hits for an `ERR-[A-Z]+-\d+` regex — extract
  `` `([A-Z][A-Z_]+)` `` tokens from the marker-bounded appendix region and
  compare the sets (16/16), plus the basis column (`F-xxx`/`DES-xxx` refs)
  per row.
- **Relative links preserved verbatim break in subdirectory translations**:
  `./zh/security/x.md` resolves fine from `docs/HLD.md` but from
  `docs/en/HLD.md` points at the non-existent `docs/en/zh/security/x.md`.
  Walk every relative link of the EN file against its OWN directory and diff
  the resolution against the ZH file's (the fix is `../zh/...`). This is the
  one link class that translation itself introduces.
- **Substring checks false-positive on line wraps and fence segmentation**:
  a phrase wrapped across two lines (`Actual collection also\nrequires the
  application...`) fails an exact-substring check even though the text is
  present, and testing a whole `split('```')` segment for a token
  (`'DES-OP-008'` segment containing `F-122` from an unrelated later row)
  produces phantom findings. Before editing on the strength of a script
  finding, re-verify with a direct line read (`grep -n` / read the specific
  lines); use anchored per-row regex parsing for table rows, never
  substring-in-segment tests.
- **Reviewer-suggested status histograms are suggestions, not facts**: an
  independent review may propose candidate counts (`Verified 47 /
  Implemented 16`) that disagree with the actual table (`46 / 17`). Always
  recompute from the table rows and report the corrected totals; copying the
  reviewer's numbers freezes a wrong baseline into the fix commit.
- **Mapping validators must expand ID ranges AND merged rows on BOTH sides**:
  comparing requirement↔DES mappings with naive string equality false-
  positives whenever either column carries a range (`F-006~008`,
  `DES-INT-001~007`) or a merged multi-ID row (`REQ-F-030, REQ-F-031,
  REQ-F-032` in one cell). Expand `~` ranges and split multi-ID cells on BOTH
  the requirement side and the design side before set-comparing (bit twice in
  one session: NF-004's `DES-INT-001~007` and a merged REQ-F-030/031/032
  row). Conversely, when a full-table validation surfaces dozens of
  pre-existing mismatches on untouched IDs (historical Actor/index drift like
  F-005/F-009/F-014), scope the phase check to the changed REQ IDs plus
  reverse mappings of the affected DES only — do not expand the phase to fix
  unrelated baseline drift.
- **Keep the implementation plan file synced with frozen contracts**: after a
  contract freeze, update `.hermes/plans/<plan>.md` too — stale instructions
  (a dropped REQ ID like a never-added REQ-F-157, old nullable signatures,
  superseded resolver ordering, old remount rules) get read as authoritative
  by the next phase. Re-run a stale-token grep over the plan after every
  contract change and fix the plan before finishing the phase.
- **V4A multi-file patch fails when one file is a large UTF-8 CJK doc**:
  `patch` mode='patch' rejects the WHOLE patch with `Binary file — cannot
  display as text` if any listed file is a Chinese markdown doc. Split into
  single-file patches; for the zh file use `execute_code` +
  `hermes_tools.patch` with exact old/new strings (the Python patch tool
  handles CJK fine). Beware fuzzy multi-hunk replaces on zh files: an
  unrelated hunk can silently rewrite the `来源：` DES footer to the EN
  `Source:` label — check the zh footer label after every multi-hunk zh
  patch and revert if swapped.

