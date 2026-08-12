# Batch Audit: Layer-by-Layer Evidence Techniques

Generalized evidence recipes for read-only batch audits (see
`ada-continuous-phased-delivery` → Batch Audit Gate). Each layer's recipe
cites what to prove, the exact commands, and the false-positive traps.
For a site with content XML → converter tool → wwwroot/data JSON → models →
services → components → pages → tests → resources → CSS:

## XML source
- `grep -n 'featured' content/*.xml` → count exact attribute occurrences
  (must equal the required count); `grep -n '<status\|<tags\|<highlight'`
  must exit 1 (no fabricated elements).
- Whole-file well-formedness gate (escaping, `&amp;`, encoding):
  `python -c "import xml.dom.minidom; xml.dom.minidom.parse('content/skills.xml'); print('XML OK')"`.
- For attribute-added-to-every-element claims, `git diff <file>` showing ONLY
  the attribute addition on each line is positive evidence the original
  attribute values were preserved.

## Converter
- Verify parse lines: attribute vs element extraction (`p.Attribute("x")` vs
  `p.Element("x")`), list building (`Elements("tag")`), localization reuse,
  and that `[JsonPropertyName]` names match the consumer model.

## Regenerate + verify JSON (prefer temp dir)
- Run the converter into a scratch dir, never into the worktree, to keep the
  audit strictly read-only. Only regenerate in place when the checklist
  explicitly demands comparing regenerated vs committed artifacts.
- Verify programmatically: record count, route patterns, key presence per
  record, empty-value serialization for missing fields. Clean up the scratch
  dir at the end.
- MSYS trap (Windows/git-bash): native Windows processes (dotnet) do NOT
  resolve bash's `/tmp/...` — passing `/tmp/x` lands the output at
  `C:\tmp\x`. Pass an explicit Windows-style scratch path (`C:/tmp/<audit-dir>`)
  or read the tool's own `生成:` stdout lines to discover where files landed.

## Models / Services
- Models: cite each property line and its CLR type.
- Services: Clone() must deep-copy collections — `new List<T>(src)` and
  `new Dictionary<K,V>(src)` — cite each line; confirm no new field was dropped.

## Components (.razor)
- Optional-UI guards (`@if (!string.IsNullOrEmpty(...))`), `@foreach` over
  lists, localization calls, and the `@inherits ...Base` line.
- For a heading-component refactor: usage inventory grep counts; residual
  bare-heading grep must respect the qualifier (bare unnumbered headings on
  dynamic pages = out of scope, 备注 not FAIL); single-source proof = the CSS
  class renderer grep hits ONLY the component; orphan-CSS check = every
  touched class has one definition line AND one component renderer line.

## Pages
- The two-branch foreach (featured / !featured) lines; the exact data-source
  field; absence of stale `.Take(3)` or old-filter logic.

## Tests
- New tests must assert non-default values AND missing-field defaults; cite
  assertion lines per field.
- For CSS source-contract tests: do not equate `flex-wrap: nowrap` with
  one-line rendered text or `min-width` with a fixed rendered width. A
  selector helper that aggregates every matching rule in the whole stylesheet
  can let a mobile declaration satisfy a desktop assertion; scope base/media
  rules explicitly and mutation-test the original bug back in — the focused
  test must fail.
- If a test discovers repository assets by walking upward from
  `AppContext.BaseDirectory`, copy the complete test output outside the repo
  and re-run with `dotnet vstest`; a relocated `DirectoryNotFoundException`
  proves output-topology dependence.
- For an embedded-resource fix, match `<EmbeddedResource LogicalName>` to the
  test constant, prove `GetManifestResourceStream` under the declared SDK, and
  require the relocated focused test to pass.

## Resources (bilingual)
- Keys exist in BOTH languages; flatten both JSON key trees (python) and diff
  — must be identical (only-zh / only-en both empty).
- Lighter bash variant: `diff <(grep -o '^\s*"[^"]*"' ui-zh.json | sort) <(... ui-en.json ...)`.
- PITFALL: `grep -o '"[a-z.]*"'` misses camelCase keys (nav.openMenu,
  common.newWindow) — use `[^"]*` for key inventories.

## CSS
- Each class is defined (line) AND referenced by a component (line); note
  styling intent as supporting evidence.

## External links & a11y
- Inventory with `grep -rn 'target="_blank"' --include=*.razor --include=*.html`
  — scope to source; minified JS in bin/obj matches otherwise.
- Verify every rel is exactly `noopener noreferrer`; absence-grep
  `rel="noopener"` (without `noreferrer`) must exit 1.
- Opening `<a>` tags can span lines — the anchor body may start on the NEXT
  line; confirm companion spans sit between `>` and `</a>` by reading the
  file, never by single-line grep alone.
- If a browser-verified link count differs from the source count, dedupe
  first: the same links render from multiple cards — count difference is
  rendering dedup, a 备注, not a FAIL.
- Touch-target claims: cite the `min-width`/`min-height: 44px` lines per class
  plus a referencing component line.

## Head/SEO metadata
- Static global meta (theme-color, og:*, twitter:*, JSON-LD) lives in
  `index.html <head>` — cite each meta line; per-route canonical lives in page
  `<HeadContent>`.
- Render-outlet check FIRST: `HeadOutlet` is registered in Program.cs
  (`RootComponents.Add<HeadOutlet>("head::after")`), NOT in any .razor — a
  HeadOutlet grep over pages returns nothing and must not be read as
  "canonical unreachable".
- Sensitive-field absence = whole-file grep exit 1 (profile data may legally
  contain an email; only the JSON-LD blocks must not).
- Image dimension proof = PIL `Image.open(...).size` PLUS `file` output as
  cross-check.
- New wwwroot assets proven in the build by their route entries in
  `*.staticwebassets.endpoints.json` (Content-Length must match source bytes)
  plus the deploy workflow uploading the whole publish output.

## Doc-sync / term-removal sweeps
- A clean diff is NOT sufficient — the batch usually updates some mentions of
  a term and misses others. Workflow: (a) list every term being removed or
  changed; (b) per term, `grep -n` the CURRENT file state (not just the diff)
  and classify EVERY hit as updated-ok / acceptable-semantics / residual;
  (c) sweep every doc layer: glossary rows, actor/constraint tables,
  architecture diagrams, per-feature design sections, security/NFR
  constraints, CI workflow descriptions, appendices. Residuals that contradict
  the new scheme are FAIL-level; glossary terms as neutral definitions are 备注.
- Batch attribution: `git status` shows cumulative uncommitted work from
  MULTIPLE batches — prove a residual belongs to THIS batch with
  `git diff -- <file> | grep -n '<term>'`: absent from the diff but present in
  the file = pre-existing (report as issue, don't blame the batch).
- Bilingual README parity: align feature-list lines line-by-line plus the
  content-file inventory block.

## Fix re-audit (复核批次修复)
- The fix typically touched ONLY the lines the first audit cited — re-grep the
  WHOLE repo with the exact forbidden-phrase list against CURRENT file state
  and expect same-topic residuals at UNCITED lines.
- Classify each stale hit by ACTIVE status: a requirement still counted in its
  section tally, still sourced by a design entry, and still mapped in the
  traceability matrix = FAIL + real contradiction; one marked 已移除 =
  acceptable.
- Phrase-family judgment: judge by context (runtime vs build-time), never by
  substring — e.g. "客户端不携带凭据" in a RUNTIME context is old residue,
  while "构建期令牌仅存在于 CI 环境变量" is the approved wording.
- Severity-tag findings: 【高】 blocking residuals/contradictions,
  【低】 marker/wording nits.

## Cross-domain CI / Pages / security release audit
- Do not let a pass under the host's newest SDK substitute for the workflow's
  declared SDK — reproduce that SDK in a scratch copy.
- Conversely, do not let a publish failure against `obj/project.assets.json`
  restored by a newer SDK prove that the declared SDK is incompatible.
- When the claim is that the project defaults to trimming, the final clean
  publish must omit any `-p:PublishTrimmed=...` CLI override; require an
  `Optimizing assemblies for size` signal.
- Distinguish a browser-rendered SPA route from its raw HTTP status (a copied
  404.html can render successfully while every deep link remains 404).
- Audit workflow permissions per job and scan the final artifact for
  credentials.

## Git hygiene
- `git check-ignore <generated-file>` explains why regenerated JSON doesn't
  appear in `git status` — absence from status is NOT evidence of a stale
  build.
- Untouched-file claims ("only reused, not modified") → prove with empty
  `git diff` for that path PLUS a grep showing the reused symbol still exists,
  PLUS the page that loads it if the JS interop name must resolve at runtime.

## Baseline vs batch regression (judgment gate)
- When a checklist item seems to fail because "data is missing", first prove
  whether the batch caused it: `git diff HEAD -- <data-source>` empty = source
  untouched; `git show HEAD:<data-source> | grep -c <pattern>` shows the
  pre-batch state. Pre-existing emptiness → observation (备注), NOT a FAIL.
