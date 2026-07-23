# SKILL.md Quality Audit — temp-skills/software-development/

**Audit date:** 2026-07-23  
**Scope:** 32 SKILL.md files under `temp-skills/software-development/`  
**Auditor:** Hermes Agent (automated + manual review)  

---

## Scoring Methodology

| Dimension | Description | Weight |
|-----------|-------------|--------|
| **D1. Frontmatter** | `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags,related_skills}` completeness; name ≤64 chars; description ≤1024 chars; file starts with `---` | 1–5 |
| **D2. Structure** | Overview / When to Use / body / Pitfalls / Verification Checklist sections; ≥3 `##`-level sections | 1–5 |
| **D3. Description** | Starts with "Use when..." trigger; focused on trigger conditions, not generic fluff | 1–5 |
| **D4. Content** | Verifiable completion conditions per step; no no-op prose; no duplicate content; references to supporting files | 1–5 |
| **D5. Size** | Ideal: 8–15k chars. Stub <1.5k, Thin <4k, Below 4–8k, Over 15–20k, Overweight 20–25k, Very large >25k → split | 1–5 |
| **Total** | Sum of D1–D5 (max 25) | — |
| **Avg** | Total / 5 | — |

---

## Individual Score Cards

### 1. agent-assisted-development
- **Size:** 14,409 chars | **D1:** 4.4 | **D2:** 5.0 | **D3:** 3.5 | **D4:** 4.7 | **D5:** 5.0 | **Total:** 22.6 | **Avg:** 4.5
- **D1 Issues:** None — all fields present (name, description, version, author, license, metadata.hermes.tags, metadata.hermes.related_skills)
- **D2 Issues:** None — has Overview, When to Use, Pitfalls, Verification sections, 7+ ## sections
- **D3 Issues:** Description is a bit generic ("Structured workflows for software development with Hermes Agent...") rather than a crisp trigger like "Use when..."
- **D4 Issues:** None significant. Has references (`references/scenario-guides.md`). Steps have verifiable conditions. Strong Rule of Three, sub-agent isolation rules.
- **D5:** Ideal range (8–15k)
- **Verdict:** 🟢 **Top tier.** Gold standard for workflow skills. Description could be more trigger-focused.

---

### 2. blazor-component-library
- **Size:** 19,767 chars | **D1:** 3.4 | **D2:** 3.0 | **D3:** 3.5 | **D4:** 5.0 | **D5:** 4.0 | **Total:** 18.9 | **Avg:** 3.8
- **D1 Issues:** Uses non-standard `metadata.hermes.trigger_keywords` and `usage_prompt` instead of `tags` and `related_skills`. Missing `related_skills`.
- **D2 Issues:** No "When to Use" section. No "Verification Checklist" section. No "Pitfalls" section (pitfalls are embedded inline).
- **D3 Issues:** Description is a catalog of patterns, not a trigger condition. Does not start with "Use when...".
- **D4 Issues:** None — content is excellent: namespace collision fixes, TS build pipeline, xUnit integration, commit conventions, specific code examples.
- **D5:** Slightly over ideal (15–20k)
- **Verdict:** 🟡 **Good content, weak metadata.** Fix frontmatter and add structural sections.

---

### 3. bugfix-architecture-root-cause
- **Size:** 14,110 chars | **D1:** 4.4 | **D2:** 4.2 | **D3:** 3.5 | **D4:** 4.7 | **D5:** 5.0 | **Total:** 21.8 | **Avg:** 4.4
- **D1 Issues:** Description uses YAML block scalar `>-` (non-standard, should be quoted string). All required fields present.
- **D2 Issues:** Has "When to Use" and "Pitfalls". Missing explicit "Overview" and "Verification Checklist" sections.
- **D3 Issues:** Description reads: "When fixing multiple UI/behavior bugs, trace them to a shared architecture-level root cause..." — good trigger focus, but uses `>-` block scalar.
- **D4 Issues:** None significant. Strong decision trees, concrete analysis templates.
- **D5:** Ideal range
- **Verdict:** 🟢 **Excellent.** Fix YAML block scalar and add missing sections.

---

### 4. cmake-cpack-packaging
- **Size:** 37,951 chars | **D1:** 4.4 | **D2:** 3.4 | **D3:** 3.5 | **D4:** 4.7 | **D5:** 2.0 | **Total:** 18.0 | **Avg:** 3.6
- **D1 Issues:** All fields present. Well-formed.
- **D2 Issues:** No explicit "When to Use" or "Verification Checklist" sections. Content is encyclopedia-style (choice tables, code blocks).
- **D3 Issues:** Description is informational, not trigger-focused.
- **D4 Issues:** Excellent depth, but too encyclopedic. No references/ directory referenced.
- **D5:** **Very large (38k chars) — strongly recommend splitting** into: (1) CMake/CPack fundamentals, (2) WiX/MSI installer, (3) NSIS installer.
- **Verdict:** 🔴 **Split required.** Great reference material but unmanageable as a single skill.

---

### 5. code-dedup-audit
- **Size:** 7,599 chars | **D1:** 4.4 | **D2:** 4.2 | **D3:** 3.5 | **D4:** 3.7 | **D5:** 3.0 | **Total:** 18.8 | **Avg:** 3.8
- **D1 Issues:** All fields present. Good.
- **D2 Issues:** Has "When to Use". Missing explicit "Overview" and "Verification Checklist".
- **D3 Issues:** Description quotes what user says, which is good. Doesn't start with "Use when...".
- **D4 Issues:** Methodology is clear but lacks file:line verification examples. No references/.
- **D5:** Below ideal range (4–8k chars)
- **Verdict:** 🟡 **Solid, needs expansion.** Add references and flesh out to 10k+.

---

### 6. code-efficiency-review
- **Size:** 9,200 chars | **D1:** 3.4 | **D2:** 3.4 | **D3:** 3.0 | **D4:** 3.7 | **D5:** 5.0 | **Total:** 17.5 | **Avg:** 3.5
- **D1 Issues:** Missing `license`. Missing `metadata.hermes.related_skills`.
- **D2 Issues:** No explicit "When to Use" section. No "Verification Checklist".
- **D3 Issues:** Description is generic.
- **D4 Issues:** Adequate content. No references/.
- **D5:** Ideal range
- **Verdict:** 🟡 **Adequate but incomplete.** Add missing frontmatter and structural sections.

---

### 7. code-quality-analysis
- **Size:** 13,676 chars | **D1:** 4.4 | **D2:** 4.2 | **D3:** 3.5 | **D4:** 4.7 | **D5:** 5.0 | **Total:** 21.8 | **Avg:** 4.4
- **D1 Issues:** All fields present.
- **D2 Issues:** Has core structure but missing explicit "Pitfalls" and "Verification Checklist" sections.
- **D3 Issues:** Description is informational, not trigger-focused.
- **D4 Issues:** Good methodology. Has concrete analysis dimensions. No references/.
- **D5:** Ideal range
- **Verdict:** 🟢 **Strong.** Add missing structural sections.

---

### 8. code-quality-pipeline
- **Size:** 2,033 chars | **D1:** 3.4 | **D2:** 2.6 | **D3:** 2.5 | **D4:** 2.7 | **D5:** 2.0 | **Total:** 13.2 | **Avg:** 2.6
- **D1 Issues:** Missing `license`. Missing `related_skills`.
- **D2 Issues:** Only 2 ## sections. No Pitfalls, no Verification Checklist.
- **D3 Issues:** Description is Chinese, generic.
- **D4 Issues:** Thin content. Acts as an umbrella/router to 3 sub-skills. No verifiable steps.
- **D5:** Very thin (<4k chars)
- **Verdict:** 🟡 **Valid umbrella, borderline stub.** Expand with routing rules, pitfalls for pipeline execution.

---

### 9. code-quality-report-verification
- **Size:** 15,530 chars | **D1:** 3.4 | **D2:** 4.2 | **D3:** 3.5 | **D4:** 4.2 | **D5:** 4.0 | **Total:** 19.3 | **Avg:** 3.9
- **D1 Issues:** Missing `license`. Missing `related_skills`.
- **D2 Issues:** Good structure. Missing explicit "Pitfalls" section.
- **D3 Issues:** Description is generic.
- **D4 Issues:** Good verification methodology. Has multi-agent review pattern.
- **D5:** Slightly over ideal (15–20k)
- **Verdict:** 🟢 **Good.** Fix frontmatter and trim.

---

### 10. doc-comparison-analysis
- **Size:** 8,551 chars | **D1:** 2.2 | **D2:** 3.4 | **D3:** 2.5 | **D4:** 3.2 | **D5:** 3.0 | **Total:** 14.3 | **Avg:** 2.9
- **D1 Issues:** Missing `version`, `author`, `license`. Missing `metadata.hermes` entirely.
- **D2 Issues:** Has "Triggers" and "Workflow". No "Pitfalls" or "Verification Checklist".
- **D3 Issues:** Description is generic and doesn't start with trigger.
- **D4 Issues:** Adequate workflow. No references/.
- **D5:** Below ideal range (4–8k)
- **Verdict:** 🔴 **Needs significant work.** Missing core frontmatter fields.

---

### 11. docs-revision
- **Size:** 4,206 chars | **D1:** 3.4 | **D2:** 3.4 | **D3:** 3.5 | **D4:** 2.7 | **D5:** 2.0 | **Total:** 15.0 | **Avg:** 3.0
- **D1 Issues:** Missing `related_skills`. 
- **D2 Issues:** Has "Workflow" phases. No "Overview", "Pitfalls", or "Verification Checklist".
- **D3 Issues:** Description starts with "Use when..." — good trigger focus.
- **D4 Issues:** Thin content. Few verifiable steps.
- **D5:** Very thin (<4k chars)
- **Verdict:** 🟡 **Thin but focused.** Expand with pitfalls and verification.

---

### 12. dotnet-blazor-library
- **Size:** 10,156 chars | **D1:** 3.4 | **D2:** 3.4 | **D3:** 4.0 | **D4:** 3.7 | **D5:** 5.0 | **Total:** 19.5 | **Avg:** 3.9
- **D1 Issues:** Missing `related_skills`. All other fields present.
- **D2 Issues:** Has "Trigger" section. No "Pitfalls" or "Verification Checklist".
- **D3 Issues:** Description starts with "Use when..." — good. Trigger-focused.
- **D4 Issues:** Good project structure and naming conventions. No references/.
- **D5:** Ideal range
- **Verdict:** 🟢 **Good.** Add missing sections and related_skills.

---

### 13. dotnet-engineering-refactoring
- **Size:** 16,418 chars | **D1:** 2.8 | **D2:** 4.2 | **D3:** 4.0 | **D4:** 4.2 | **D5:** 4.0 | **Total:** 19.2 | **Avg:** 3.8
- **D1 Issues:** Missing `license`. Missing `platforms`.
- **D2 Issues:** Has "Trigger", "Pitfalls". Missing "Verification Checklist".
- **D3 Issues:** Description starts with "Use when..." — good trigger language.
- **D4 Issues:** Strong content: domain primitives, orchestrator extraction, command base classes. No references/.
- **D5:** Slightly over ideal (15–20k)
- **Verdict:** 🟢 **Good engineering content.** Fix frontmatter.

---

### 14. dotnet-verification
- **Size:** 3,289 chars | **D1:** 4.4 | **D2:** 2.6 | **D3:** 3.5 | **D4:** 3.2 | **D5:** 2.0 | **Total:** 15.7 | **Avg:** 3.1
- **D1 Issues:** All fields present. Has `related_skills`.
- **D2 Issues:** Only 1 ## section (Verification ladder). No "When to Use", "Pitfalls", "Verification Checklist".
- **D3 Issues:** Description is procedural, not trigger-focused.
- **D4 Issues:** Content is focused and practical but thin. No references/.
- **D5:** Very thin (<4k chars)
- **Verdict:** 🟡 **Thin but useful.** Expand with structure and pitfalls.

---

### 15. engineering-refactoring
- **Size:** 22,734 chars | **D1:** 4.4 | **D2:** 4.2 | **D3:** 3.5 | **D4:** 4.7 | **D5:** 3.0 | **Total:** 19.8 | **Avg:** 4.0
- **D1 Issues:** All fields present. Good.
- **D2 Issues:** Has "When to Use", "Pitfalls". Missing "Verification Checklist".
- **D3 Issues:** Description is strong: "Use when the user rejects mechanical dedup..." — but doesn't start with "Use when".
- **D4 Issues:** Excellent depth. Strong engineering philosophy. No references/.
- **D5:** Overweight (20–25k chars) — consider splitting
- **Verdict:** 🟡 **Overweight but excellent.** Consider splitting into core philosophy + .NET patterns.

---

### 16. hermes-agent-skill-authoring
- **Size:** 10,847 chars | **D1:** 4.4 | **D2:** 4.2 | **D3:** 3.5 | **D4:** 4.2 | **D5:** 5.0 | **Total:** 21.3 | **Avg:** 4.3
- **D1 Issues:** All fields present.
- **D2 Issues:** Has "When to Use", structure sections. Missing explicit "Pitfalls".
- **D3 Issues:** Description is informational, not trigger-focused.
- **D4 Issues:** Good validator and authoring guidance. Has references/ mentions.
- **D5:** Ideal range
- **Verdict:** 🟢 **Strong.** Add pitfalls section.

---

### 17. hermes-configuration
- **Size:** 3,624 chars | **D1:** 3.4 | **D2:** 2.6 | **D3:** 2.5 | **D4:** 3.2 | **D5:** 2.0 | **Total:** 13.7 | **Avg:** 2.7
- **D1 Issues:** Missing `license`. Missing `related_skills`.
- **D2 Issues:** Only 1 ## section (SOUL.md). No "When to Use", "Pitfalls", "Verification Checklist".
- **D3 Issues:** Description is generic.
- **D4 Issues:** Content is practical (SOUL.md design table). Thin.
- **D5:** Very thin (<4k chars)
- **Verdict:** 🟡 **Useful but a stub.** Expand significantly.

---

### 18. hermes-doc-sync
- **Size:** 8,213 chars | **D1:** 3.4 | **D2:** 3.4 | **D3:** 2.5 | **D4:** 2.7 | **D5:** 3.0 | **Total:** 15.0 | **Avg:** 3.0
- **D1 Issues:** Missing `license`. Missing `related_skills`.
- **D2 Issues:** Has workflow phases. No "Pitfalls" or "Verification Checklist".
- **D3 Issues:** Description is generic.
- **D4 Issues:** Procedural content, few verifiable conditions. No references/.
- **D5:** Below ideal range (4–8k)
- **Verdict:** 🟡 **Thin.** Expand with pitfalls and verification.

---

### 19. node-inspect-debugger
- **Size:** 11,248 chars | **D1:** 3.4 | **D2:** 3.4 | **D3:** 2.5 | **D4:** 4.2 | **D5:** 5.0 | **Total:** 18.5 | **Avg:** 3.7
- **D1 Issues:** Missing `license`. Missing `related_skills`.
- **D2 Issues:** Has workflow. No explicit "Pitfalls" or "Verification Checklist".
- **D3 Issues:** Description is generic.
- **D4 Issues:** Good CDP (Chrome DevTools Protocol) CLI content. Practical.
- **D5:** Ideal range
- **Verdict:** 🟢 **Good technical content.** Fix frontmatter.

---

### 20. powershell-from-bash
- **Size:** 3,012 chars | **D1:** 3.4 | **D2:** 2.6 | **D3:** 3.5 | **D4:** 3.7 | **D5:** 2.0 | **Total:** 15.2 | **Avg:** 3.0
- **D1 Issues:** Missing `related_skills`. All other fields present.
- **D2 Issues:** No ## sections at all — just headings. No "When to Use", "Pitfalls", "Verification Checklist".
- **D3 Issues:** Description is focused: "Run PowerShell commands and scripts from git-bash/MSYS on Windows without path/variable mangling."
- **D4 Issues:** Very practical: 2 problems + fixes + invocation pattern. Concise. No references/.
- **D5:** Very thin (<4k chars)
- **Verdict:** 🟡 **Dense and useful but too thin.** Add structure and references.

---

### 21. python-debugpy
- **Size:** 13,547 chars | **D1:** 3.4 | **D2:** 4.2 | **D3:** 2.5 | **D4:** 4.2 | **D5:** 5.0 | **Total:** 19.3 | **Avg:** 3.9
- **D1 Issues:** Missing `license`. Missing `related_skills`.
- **D2 Issues:** Has workflow sections. Missing explicit "Pitfalls" and "Verification Checklist".
- **D3 Issues:** Description is generic.
- **D4 Issues:** Good debugpy configuration patterns.
- **D5:** Ideal range
- **Verdict:** 🟢 **Good.** Fix frontmatter and add sections.

---

### 22. quality-report-qa
- **Size:** 3,797 chars | **D1:** 3.4 | **D2:** 2.6 | **D3:** 2.5 | **D4:** 3.2 | **D5:** 2.0 | **Total:** 13.7 | **Avg:** 2.7
- **D1 Issues:** Missing `license`. Missing `related_skills`.
- **D2 Issues:** Only 1 ## section (4 gates). No "When to Use", "Pitfalls", "Verification Checklist".
- **D3 Issues:** Description is generic.
- **D4 Issues:** 4 concrete QA gates with shell commands. Practical but thin.
- **D5:** Very thin (<4k chars)
- **Verdict:** 🟡 **Practical but thin.** Expand with structure.

---

### 23. refactoring-lifecycle
- **Size:** 2,090 chars | **D1:** 3.4 | **D2:** 2.6 | **D3:** 2.5 | **D4:** 2.7 | **D5:** 2.0 | **Total:** 13.2 | **Avg:** 2.6
- **D1 Issues:** Missing `license`. Missing `related_skills`. Has non-standard `sub_skills`.
- **D2 Issues:** Only 2 ## sections. No "Pitfalls", "Verification Checklist".
- **D3 Issues:** Description is Chinese, generic.
- **D4 Issues:** Acts as umbrella/router to 2 sub-skills. Thin.
- **D5:** Very thin (<4k chars)
- **Verdict:** 🟡 **Valid umbrella, borderline stub.** Expand with routing logic and pitfalls.

---

### 24. requirements-authoring
- **Size:** 6,784 chars | **D1:** 4.4 | **D2:** 3.4 | **D3:** 4.0 | **D4:** 3.7 | **D5:** 3.0 | **Total:** 18.5 | **Avg:** 3.7
- **D1 Issues:** All fields present. Good.
- **D2 Issues:** Has "When to Load". No "Pitfalls" or "Verification Checklist".
- **D3 Issues:** Description starts with "Use when..." and is trigger-focused.
- **D4 Issues:** Good SRS vs Design boundary content. Self-check questions are practical. No references/.
- **D5:** Below ideal range (4–8k)
- **Verdict:** 🟢 **Good content, needs expansion.** Add pitfalls and references.

---

### 25. simplify-code
- **Size:** 11,138 chars | **D1:** 3.4 | **D2:** 4.2 | **D3:** 2.5 | **D4:** 4.7 | **D5:** 5.0 | **Total:** 19.8 | **Avg:** 4.0
- **D1 Issues:** Missing `license`. Missing `related_skills`.
- **D2 Issues:** Has workflow structure. Missing explicit "Pitfalls" and "Verification Checklist".
- **D3 Issues:** Description is generic.
- **D4 Issues:** Good 3-agent parallel review pattern. Strong methodology.
- **D5:** Ideal range
- **Verdict:** 🟢 **Strong content.** Fix frontmatter.

---

### 26. skill-optimization
- **Size:** 7,818 chars | **D1:** 4.4 | **D2:** 4.2 | **D3:** 3.5 | **D4:** 3.7 | **D5:** 3.0 | **Total:** 18.8 | **Avg:** 3.8
- **D1 Issues:** All fields present. Good.
- **D2 Issues:** Has "When to Use", "Workflow". Missing "Pitfalls" and "Verification Checklist".
- **D3 Issues:** Description starts with "Use when..." — good trigger. Slightly wordy.
- **D4 Issues:** Good skill audit methodology. Has `hermes skills list` commands. No references/.
- **D5:** Below ideal range (4–8k)
- **Verdict:** 🟢 **Good.** Expand to 10k+ with references.

---

### 27. srs-documentation
- **Size:** 6,672 chars | **D1:** 4.4 | **D2:** 3.4 | **D3:** 2.5 | **D4:** 3.2 | **D5:** 3.0 | **Total:** 16.5 | **Avg:** 3.3
- **D1 Issues:** All fields present. Good.
- **D2 Issues:** Has "When to Use", "Document Structure". No "Pitfalls" or "Verification Checklist".
- **D3 Issues:** Description is generic.
- **D4 Issues:** Document structure guidance is good. Thin on verifiable steps. No references/.
- **D5:** Below ideal range (4–8k)
- **Verdict:** 🟡 **Adequate.** Expand with pitfalls.

---

### 28. srs-lifecycle
- **Size:** 2,116 chars | **D1:** 3.4 | **D2:** 2.6 | **D3:** 2.5 | **D4:** 2.7 | **D5:** 2.0 | **Total:** 13.2 | **Avg:** 2.6
- **D1 Issues:** Missing `license`. Missing `related_skills`. Has non-standard `sub_skills`.
- **D2 Issues:** Only 2 ## sections. No "Pitfalls", "Verification Checklist".
- **D3 Issues:** Description is Chinese, generic.
- **D4 Issues:** Acts as umbrella/router to 4 sub-skills. Thin content.
- **D5:** Very thin (<4k chars)
- **Verdict:** 🟡 **Valid umbrella, borderline stub.** Expand.

---

### 29. srs-review
- **Size:** 28,001 chars | **D1:** 3.4 | **D2:** 4.2 | **D3:** 2.5 | **D4:** 4.7 | **D5:** 2.0 | **Total:** 16.8 | **Avg:** 3.4
- **D1 Issues:** Missing `license`. Missing `tags` (only has `related_skills`).
- **D2 Issues:** Has "Triggers", "Workflow". Missing explicit "Pitfalls" and "Verification Checklist".
- **D3 Issues:** Description is generic.
- **D4 Issues:** Deep review methodology. Has cross-checking patterns. No references/.
- **D5:** **Very large (28k chars) — strongly recommend splitting** into: (1) SRS review methodology, (2) SRS review checklist/templates.
- **Verdict:** 🔴 **Overweight.** Good content but unmanageable size.

---

### 30. srs-revision
- **Size:** 9,410 chars | **D1:** 4.4 | **D2:** 5.0 | **D3:** 3.5 | **D4:** 5.0 | **D5:** 5.0 | **Total:** 22.9 | **Avg:** 4.6
- **D1 Issues:** All fields present.
- **D2 Issues:** **None** — has Overview, When to Use, Pitfalls, Verification Checklist, References. Full structure.
- **D3 Issues:** Description could be more trigger-focused.
- **D4 Issues:** **None** — excellent. Has references/ (`references/atlas-stacking-to-tabgroup.md`, `references/atlas-terminology.md`, `references/survey-commands.md`), scripts/ (`scripts/verify-terminology.py`). Every step has verifiable conditions. Concrete grep commands for verification.
- **D5:** Ideal range
- **Verdict:** 🟢 **Gold standard.** The best-structured skill in the audit.

---

### 31. srs-writing
- **Size:** 12,396 chars | **D1:** 4.4 | **D2:** 4.2 | **D3:** 2.5 | **D4:** 4.7 | **D5:** 5.0 | **Total:** 20.8 | **Avg:** 4.2
- **D1 Issues:** All fields present.
- **D2 Issues:** Has "Pitfalls" (extensive). Missing explicit "Overview" and "Verification Checklist".
- **D3 Issues:** Description is Chinese, generic.
- **D4 Issues:** Excellent pitfalls section (one of the best). Has references/ (`references/srs-renumbering.md`, `references/spatial-diagram-templates.md`). Deep domain knowledge.
- **D5:** Ideal range
- **Verdict:** 🟢 **Excellent.** Add verification checklist.

---

### 32. tp-to-srs-derivation
- **Size:** 30,210 chars | **D1:** 4.4 | **D2:** 5.0 | **D3:** 3.5 | **D4:** 5.0 | **D5:** 2.0 | **Total:** 19.9 | **Avg:** 4.0
- **D1 Issues:** All fields present. Well-formed.
- **D2 Issues:** None — has When to Use, Pitfalls (17 pitfalls!), Verification, References, full 10-phase workflow.
- **D3 Issues:** Description could be more trigger-focused.
- **D4 Issues:** **None** — gold standard for content. 17 pitfalls, 10 phases, 5 derivation paths, bilingual conventions. Has references/ (`references/requirement-format-example.md`, `references/srs-self-evolution.md`), scripts/ (`scripts/verify-srs-fences.py`).
- **D5:** **Very large (30k chars) — strongly recommend splitting** into: (1) TP-to-SRS derivation core workflow, (2) SRS format & conventions reference, (3) Self-evolution & QA methodology.
- **Verdict:** 🔴 **Split required.** Best content in the audit but unmanageable as a single skill.

---

## Summary Ranking

| Rank | Skill | D1 | D2 | D3 | D4 | D5 | Total | Avg | Verdict |
|:----:|-------|:--:|:--:|:--:|:--:|:--:|:-----:|:---:|:-------:|
| 🥇 1 | **srs-revision** | 4.4 | 5.0 | 3.5 | 5.0 | 5.0 | **22.9** | 4.6 | Gold standard |
| 🥈 2 | **agent-assisted-development** | 4.4 | 5.0 | 3.5 | 4.7 | 5.0 | **22.6** | 4.5 | Top tier |
| 🥉 3 | **bugfix-architecture-root-cause** | 4.4 | 4.2 | 3.5 | 4.7 | 5.0 | **21.8** | 4.4 | Excellent |
| 3 | **code-quality-analysis** | 4.4 | 4.2 | 3.5 | 4.7 | 5.0 | **21.8** | 4.4 | Excellent |
| 5 | **hermes-agent-skill-authoring** | 4.4 | 4.2 | 3.5 | 4.2 | 5.0 | **21.3** | 4.3 | Strong |
| 6 | **srs-writing** | 4.4 | 4.2 | 2.5 | 4.7 | 5.0 | **20.8** | 4.2 | Excellent |
| 7 | **tp-to-srs-derivation** | 4.4 | 5.0 | 3.5 | 5.0 | 2.0 | **19.9** | 4.0 | Split needed |
| 7 | **engineering-refactoring** | 4.4 | 4.2 | 3.5 | 4.7 | 3.0 | **19.8** | 4.0 | Overweight |
| 7 | **simplify-code** | 3.4 | 4.2 | 2.5 | 4.7 | 5.0 | **19.8** | 4.0 | Strong |
| 10 | **dotnet-blazor-library** | 3.4 | 3.4 | 4.0 | 3.7 | 5.0 | **19.5** | 3.9 | Good |
| 11 | **python-debugpy** | 3.4 | 4.2 | 2.5 | 4.2 | 5.0 | **19.3** | 3.9 | Good |
| 11 | **code-quality-report-verification** | 3.4 | 4.2 | 3.5 | 4.2 | 4.0 | **19.3** | 3.9 | Good |
| 13 | **dotnet-engineering-refactoring** | 2.8 | 4.2 | 4.0 | 4.2 | 4.0 | **19.2** | 3.8 | Good |
| 14 | **blazor-component-library** | 3.4 | 3.0 | 3.5 | 5.0 | 4.0 | **18.9** | 3.8 | Good content, weak meta |
| 14 | **code-dedup-audit** | 4.4 | 4.2 | 3.5 | 3.7 | 3.0 | **18.8** | 3.8 | Solid, thin |
| 14 | **skill-optimization** | 4.4 | 4.2 | 3.5 | 3.7 | 3.0 | **18.8** | 3.8 | Good |
| 17 | **node-inspect-debugger** | 3.4 | 3.4 | 2.5 | 4.2 | 5.0 | **18.5** | 3.7 | Good tech |
| 17 | **requirements-authoring** | 4.4 | 3.4 | 4.0 | 3.7 | 3.0 | **18.5** | 3.7 | Good |
| 19 | **cmake-cpack-packaging** | 4.4 | 3.4 | 3.5 | 4.7 | 2.0 | **18.0** | 3.6 | Split needed |
| 20 | **code-efficiency-review** | 3.4 | 3.4 | 3.0 | 3.7 | 5.0 | **17.5** | 3.5 | Adequate |
| 21 | **srs-review** | 3.4 | 4.2 | 2.5 | 4.7 | 2.0 | **16.8** | 3.4 | Split needed |
| 22 | **srs-documentation** | 4.4 | 3.4 | 2.5 | 3.2 | 3.0 | **16.5** | 3.3 | Adequate |
| 23 | **dotnet-verification** | 4.4 | 2.6 | 3.5 | 3.2 | 2.0 | **15.7** | 3.1 | Thin |
| 24 | **powershell-from-bash** | 3.4 | 2.6 | 3.5 | 3.7 | 2.0 | **15.2** | 3.0 | Dense, thin |
| 24 | **hermes-doc-sync** | 3.4 | 3.4 | 2.5 | 2.7 | 3.0 | **15.0** | 3.0 | Thin |
| 24 | **docs-revision** | 3.4 | 3.4 | 3.5 | 2.7 | 2.0 | **15.0** | 3.0 | Thin |
| 27 | **doc-comparison-analysis** | 2.2 | 3.4 | 2.5 | 3.2 | 3.0 | **14.3** | 2.9 | Needs work |
| 28 | **hermes-configuration** | 3.4 | 2.6 | 2.5 | 3.2 | 2.0 | **13.7** | 2.7 | Stub |
| 28 | **quality-report-qa** | 3.4 | 2.6 | 2.5 | 3.2 | 2.0 | **13.7** | 2.7 | Stub |
| 30 | **code-quality-pipeline** | 3.4 | 2.6 | 2.5 | 2.7 | 2.0 | **13.2** | 2.6 | Umbrella stub |
| 30 | **refactoring-lifecycle** | 3.4 | 2.6 | 2.5 | 2.7 | 2.0 | **13.2** | 2.6 | Umbrella stub |
| 30 | **srs-lifecycle** | 3.4 | 2.6 | 2.5 | 2.7 | 2.0 | **13.2** | 2.6 | Umbrella stub |

---

## Aggregate Statistics

### Size Distribution

| Category | Count | Skills |
|----------|:-----:|--------|
| 🔴 **Stub** (<1.5k) | 0 | — |
| 🟠 **Very Thin** (1.5–4k) | 8 | code-quality-pipeline, refactoring-lifecycle, srs-lifecycle, powershell-from-bash, dotnet-verification, hermes-configuration, quality-report-qa, docs-revision |
| 🟡 **Below Ideal** (4–8k) | 7 | code-dedup-audit, doc-comparison-analysis, hermes-doc-sync, requirements-authoring, skill-optimization, srs-documentation, code-efficiency-review |
| 🟢 **Ideal** (8–15k) | 11 | agent-assisted-development, bugfix-architecture-root-cause, code-quality-analysis, dotnet-blazor-library, hermes-agent-skill-authoring, node-inspect-debugger, powershell-from-bash, python-debugpy, simplify-code, srs-revision, srs-writing |
| 🟡 **Slightly Over** (15–20k) | 3 | blazor-component-library, code-quality-report-verification, dotnet-engineering-refactoring |
| 🟠 **Overweight** (20–25k) | 1 | engineering-refactoring |
| 🔴 **Very Large** (>25k) | 3 | cmake-cpack-packaging, srs-review, tp-to-srs-derivation |

### Frontmatter Issues

| Issue | Count | Affected Skills |
|-------|:-----:|-----------------|
| Missing `license` | 13 | code-efficiency-review, code-quality-pipeline, code-quality-report-verification, doc-comparison-analysis, dotnet-engineering-refactoring, hermes-configuration, hermes-doc-sync, node-inspect-debugger, python-debugpy, quality-report-qa, refactoring-lifecycle, srs-lifecycle, srs-review |
| Missing `related_skills` | 11 | blazor-component-library, code-efficiency-review, code-quality-pipeline, code-quality-report-verification, docs-revision, dotnet-blazor-library, hermes-configuration, hermes-doc-sync, node-inspect-debugger, powershell-from-bash, python-debugpy, quality-report-qa, refactoring-lifecycle, srs-lifecycle |
| Missing `version` | 1 | doc-comparison-analysis |
| Missing `author` | 1 | doc-comparison-analysis |
| Missing `metadata.hermes` entirely | 1 | doc-comparison-analysis |
| Non-standard YAML (`>-` block scalar) | 1 | bugfix-architecture-root-cause |
| Non-standard metadata keys | 3 | blazor-component-library (trigger_keywords, usage_prompt), refactoring-lifecycle (sub_skills), srs-lifecycle (sub_skills) |

### Structural Issues

| Issue | Count |
|-------|:-----:|
| Missing "Pitfalls" section | 19 |
| Missing "Verification Checklist" section | 25 |
| Missing "When to Use" section | 8 |
| Missing "Overview" section | 14 |
| Fewer than 3 `##` sections | 6 |

---

## Critical Actions (Priority-Ordered)

### 🔴 P0 — Split Immediately (3 skills)
1. **cmake-cpack-packaging** (37,951 chars) → Split into: CMake/CPack fundamentals, WiX/MSI installer, NSIS installer
2. **tp-to-srs-derivation** (30,210 chars) → Split into: Derivation workflow, Format/conventions reference, Self-evolution methodology
3. **srs-review** (28,001 chars) → Split into: Review methodology, Review checklist/templates

### 🔴 P1 — Fix Broken Frontmatter (1 skill)
4. **doc-comparison-analysis** — Missing `version`, `author`, `license`, `metadata.hermes` entirely

### 🟡 P2 — Add Missing `license` (13 skills)
5. code-efficiency-review, code-quality-pipeline, code-quality-report-verification, doc-comparison-analysis, dotnet-engineering-refactoring, hermes-configuration, hermes-doc-sync, node-inspect-debugger, python-debugpy, quality-report-qa, refactoring-lifecycle, srs-lifecycle, srs-review

### 🟡 P3 — Add Missing `related_skills` (14 skills)
6. All skills listed in frontmatter issues table above

### 🟢 P4 — Expand Thin Skills (8 skills <4k chars)
7. code-quality-pipeline, refactoring-lifecycle, srs-lifecycle, powershell-from-bash, dotnet-verification, hermes-configuration, quality-report-qa, docs-revision

### 🟢 P5 — Add Missing Structural Sections (bulk)
8. Add "Pitfalls" to 19 skills, "Verification Checklist" to 25 skills

---

## Best Practices Observed

| Practice | Exemplar Skills |
|----------|----------------|
| Full `references/` directory with supporting files | srs-revision, tp-to-srs-derivation, srs-writing, agent-assisted-development |
| `scripts/` directory with validation scripts | srs-revision, tp-to-srs-derivation |
| Concrete grep/shell verification commands | srs-revision, quality-report-qa, docs-revision |
| "When to Use" with clear triggers AND "Do NOT use for" exclusions | bugfix-architecture-root-cause, code-dedup-audit |
| Multi-agent review patterns | simplify-code, agent-assisted-development, code-quality-report-verification |
| Decision trees / routing tables | refactoring-lifecycle, srs-lifecycle, code-quality-pipeline |
| Commitment to "Review-Then-Execute" | srs-revision, tp-to-srs-derivation |

---

## Key Recommendations

1. **Establish a canonical YAML frontmatter template** and validate all skills against it. 13/32 (40%) are missing `license`, 14/32 (44%) are missing `related_skills`.

2. **Define a minimum structural template**: Every skill must have Overview, When to Use (with explicit exclusions), Pitfalls, and Verification Checklist sections. Currently 25/32 (78%) are missing a Verification Checklist.

3. **Enforce size guidelines**: 
   - Umbrella/router skills (code-quality-pipeline, refactoring-lifecycle, srs-lifecycle) can be thin (~3-4k) but must have clear routing tables, not just a list of sub-skills.
   - Full skills should target 8-15k chars. Over 20k must be split.

4. **Standardize `description` format**: All descriptions should start with "Use when..." and focus on trigger conditions. Currently ~15/32 descriptions are generic or informational.

5. **Add `references/` directories**: Only 4/32 skills reference supporting files. srs-revision and tp-to-srs-derivation set the standard.

---

*Report generated by Hermes Agent audit. All scores are relative to ideal skill standards defined in `hermes-agent-skill-authoring`.*
