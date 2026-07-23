# Refactoring closeout: docs, verification, and backlog separation

Use this at the end of a multi-phase .NET refactoring plan, especially when the user asks whether all document-required repair issues are done.

## Closeout audit

1. Separate these scopes before answering:
   - **Refactoring/deviation plan complete**: the DEV/Phase repair set was implemented, verified, and independently reviewed.
   - **Whole SRS complete**: every traceability row is implemented/tested. This is usually a broader product backlog and must not be implied by plan completion.

2. Search the relevant docs for stale status markers before finalizing:
   - `待最终验收`
   - `待浏览器验收`
   - `等待最终验收 / 独立审查`
   - stale top-level status such as `执行中（Phase 16–18 已完成）`
   - unchecked phase checklist items (`- [ ]`) for phases that have real passing evidence.

3. Only convert statuses to “已验证” or “completed” when evidence exists:
   - build/test/format/diff-check output,
   - focused/ad-hoc verification for changed behavior,
   - independent review passed with no security or logic blockers.

4. Keep caveats precise:
   - Browser smoke is not full manual drag UX acceptance.
   - Focused/ad-hoc scripts are not full-suite green unless they actually ran an unfiltered full suite.
   - A completed architecture remediation plan does not close remaining SRS rows marked `Not Implemented`, `Partial`, or missing browser/performance/accessibility evidence.

5. Historical analysis docs should be marked as baseline snapshots rather than rewritten wholesale. Add a note that old missing-file observations or old test counts refer to the pre-refactoring baseline.

6. Normalize trailing whitespace in new Markdown docs when `git diff --check` or reviewer feedback flags hard-break spaces. Prefer normal line breaks unless Markdown hard breaks are intentionally required.

## Recommended final answer

Use a two-layer conclusion:

- “The document-required DEV/Phase repair set is complete and verified.”
- “The full SRS product backlog is not complete if traceability still contains `Not Implemented`, `Partial`, or unverified browser/performance/a11y items.”

Then list the completed DEV rows and a few representative remaining SRS backlog items separately.