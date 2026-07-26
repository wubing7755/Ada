# Verification Pitfalls

> Extracted from ada-code-quality-report-verification for progressive disclosure.

## Common Pitfalls

- **Don't trust the report's table without reading source**: The report may list
  "8/30 covered" when the actual count is 10/30 because it missed aggregated tests.
  Or it may claim 30 source classes when the codebase has 45 — silently omitting
  interfaces, enums, internal DTOs, and nested event arg classes.
- **Don't just verify existence — verify accuracy**: An issue can exist but the
  report can be wrong about its details. That's ⚠️, not ✅.
- **Don't call it a false positive when it's just stale**: If `dotnet format` no
  longer shows the error, the issue was probably fixed between report and verification.
  Note it as "cannot reproduce, likely fixed" — that's ⚠️, not ❌.
- **Don't invent new issues**: Your job is to verify what the report says, not to
  find additional problems. If you discover new issues, note them briefly but don't
  add them to the verdict — that's scope creep.
- **Don't skip validation because the report "feels right"**: Always read the code.
  Even a 95% accurate report has subtle inaccuracies that matter for priority decisions.
- **Watch the header claim vs the detail table**: A report may say "48 个源文件"
  in the header but list 47 in the appendix table. The header and body can contradict.
  Always use the most detailed breakdown as your starting point and flag the header
  as a separate potential inconsistency.
- **Don't assume subdirectory line numbers in the report add up**: A report claiming
  5,510 total lines may have subdirectory breakdowns summing to 5,566. Always add up
  the report's own sub-totals first before comparing to source.
- **Beware of the "class counting methodology" gap**: A report counts 30 "源类" while
  your grep finds 45+ public/internal classes. The report may be excluding enums,
  interfaces, nested DTOs, event args, and generic type specializations. Understand
  the report's inclusion criteria — if it's not documented, flag the methodology gap
  in your verdict rather than calling the count flat wrong.
- **When spot-checking individual files, prefer files the report gives exact line
  numbers for** (e.g. Appendix A per-file listings). If the report only provides
  subdirectory totals, note that spot-checking can only validate at the subdirectory
  level, not per-file.
- **Verify the previous report's own numbers** when the current report cites it.
  Don't trust the current report's characterization of the previous report's line
  count — read the previous report's appendix yourself.
- **For phase pass/fail reviews, don't stop at green tests**: green tests are only
  evidence after you have read the SRS/design acceptance criteria and confirmed the
  tests assert the required semantics. A phase with passing tests but missing direct
  assertions for a required branch should be reported as a test gap or `passed:false`
  depending on severity.
- **Keep requested JSON-like verdicts compact**: when the user asks for fields such
  as `passed`, `security_concerns`, `logic_errors`, `test_gaps`, `evidence`, and
  `recommended_fixes`, return that shape directly with evidence-dense bullets rather
  than a long narrative.