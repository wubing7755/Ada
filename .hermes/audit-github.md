# GitHub Skills Audit Report

**Audit Date:** 2026-07-23  
**Path:** `temp-skills/github/`  
**Skills Audited:** 8  
**Auditor:** Hermes Agent (subagent)  
**Methodology:** Each SKILL.md evaluated across 6 dimensions, scored 1–5 (5 = perfect), for a max total of 30.

---

## Scoring Dimensions

| # | Dimension | Description |
|---|-----------|-------------|
| 1 | **Frontmatter Completeness** | `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags,related_skills}` present; `name` ≤64 chars; `description` ≤1024 chars; file starts with `---` |
| 2 | **Structure & Readability** | Has Overview, "When to Use", main body, Pitfalls, and Verification Checklist sections |
| 3 | **Description Quality** | Starts with "Use when…"; focuses on trigger conditions; not generic |
| 4 | **Content Quality** | Steps have verifiable completion conditions; no no-op prose; no duplicate content; references scripts/templates/references |
| 5 | **Size** | File size in characters; 8k–15k is ideal range |

---

## Per-Skill Scorecards

---

### 1. codebase-inspection

| Dimension | Score | Notes |
|-----------|:-----:|-------|
| Frontmatter | **5** | All fields present. Extra: `platforms`, `prerequisites`. |
| Structure | **3** | Has Overview, When to Use, Pitfalls. Missing: Verification Checklist. |
| Description | **2** | "Inspect codebases w/ pygount: LOC, languages, ratios." Does NOT start with "Use when…"; describes what, not when. |
| Content | **3** | Commands are actionable. No supporting files (references/templates/scripts). Section 2 overlaps with Pitfalls #1. |
| Size | **2** | 3,744 chars — well below 8k ideal minimum. |
| **TOTAL** | **15/25** | |

**Defects:**
1. No Verification Checklist — no way for the agent to confirm it did the right thing
2. No supporting files (references/, templates/, scripts/) — bare SKILL.md only
3. Description doesn't follow "Use when…" convention
4. Severely underweight at 3,744 chars — content is sparse; missing sections on JSON output parsing, CI integration, or common failure modes
5. Section numbering skips (1 → 2 → 3 → 4 → 5 → 6), but sections 3/4/5 are single-command one-liners that don't justify separate top-level headings
6. Prerequisites `pip install` command uses `--break-system-packages` which may not be available on all pip versions; no venv/uv alternative given
7. "When to Use" lists trigger conditions but they're generic — more usage tips than true triggers

---

### 2. git-cross-platform-pitfalls

| Dimension | Score | Notes |
|-----------|:-----:|-------|
| Frontmatter | **4** | Missing `platforms` field. `description` is 206 chars (valid but long). All other fields present. |
| Structure | **3** | No explicit "When to Use" section. No Verification Checklist. Body is well-organized as diagnostic reference. |
| Description | **3** | Long-form descriptive summary — lists specific pitfall types. Doesn't start with "Use when…" but is specific and useful. |
| Content | **3** | Each pitfall has detection commands + fix. Pitfall 5 partially duplicates Pitfall 2. No supporting files. |
| Size | **3** | 7,162 chars — slightly below 8k ideal. |
| **TOTAL** | **16/25** | |

**Defects:**
1. No "When to Use" section — when should an agent reach for this skill?
2. No Verification Checklist
3. Missing `platforms` field in frontmatter (ironic for a cross-platform skill)
4. No supporting files (references/, templates/, scripts/)
5. Pitfall 5 (General Stale Branch) conceptually overlaps with Pitfall 2 (Dependabot Stale Base) — could be merged or one could reference the other
6. Description is informational but doesn't follow "Use when…" trigger convention
7. Quick Diagnostic Commands section at the end feels tacked on — should be moved earlier or integrated into detection sections

---

### 3. github-auth

| Dimension | Score | Notes |
|-----------|:-----:|-------|
| Frontmatter | **5** | All fields present. Includes `platforms`. |
| Structure | **3** | Has "Detection Flow" (poor man's When to Use). No Pitfalls section (Troubleshooting table is close). No Verification Checklist. |
| Description | **2** | "GitHub auth setup: HTTPS tokens, SSH keys, gh CLI login." Does NOT start with "Use when…". |
| Content | **4** | Each method has verify steps. Has `scripts/gh-env.sh`. Git identity config duplicated across HTTPS and SSH options. |
| Size | **3** | 7,843 chars — slightly below 8k. |
| **TOTAL** | **17/25** | |

**Defects:**
1. No "When to Use" section — the Detection Flow is close but structured as a detection script, not trigger conditions
2. No Pitfalls section — Troubleshooting table partially covers this but isn't the same
3. No Verification Checklist
4. Description doesn't follow "Use when…" convention
5. Git identity configuration (`user.name`/`user.email`) repeated verbatim in both HTTPS and SSH options — should be extracted once
6. Slightly underweight at 7,843 chars
7. Token extraction helper at the end is useful but should be in a shared script, not buried in a section

---

### 4. github-ci-debug

| Dimension | Score | Notes |
|-----------|:-----:|-------|
| Frontmatter | **5** | All fields present. Includes `platforms`. |
| Structure | **3** | Has Pitfalls section. No "When to Use." No Verification Checklist. |
| Description | **2** | "Diagnose and fix GitHub Actions CI failures — …" Does NOT start with "Use when…". |
| Content | **4** | Rules are actionable with detection + fix. Has references/ (2 files) and scripts/ (1 file). Token extraction duplicated from github-auth. |
| Size | **4** | 8,243 chars — at low end of ideal range. |
| **TOTAL** | **18/25** | |

**Defects:**
1. No "When to Use" section
2. No Verification Checklist — how does the agent know the fix worked?
3. Description doesn't follow "Use when…" convention
4. Token extraction section (lines 196–203) is copy-pasted from github-auth — should reference it instead
5. `***` placeholder for tokens in curl examples is inconsistent; some sections use `***`, others show real env var usage
6. References to `git-cross-platform-pitfalls` at the end of Pitfalls section is good cross-referencing but arrives too late — should be called out earlier in the staleness rules
7. Rule numbering (Rule 1 through Rule 8) is flat — no grouping by category (staleness vs. runner issues vs. template compliance)

---

### 5. github-code-review

| Dimension | Score | Notes |
|-----------|:-----:|-------|
| Frontmatter | **5** | All fields present. Includes `platforms`. |
| Structure | **3** | Has Verification Checklist (Section 3, strong). No "When to Use." No Pitfalls section. |
| Description | **2** | "Review PRs: diffs, inline comments via gh or REST." Does NOT start with "Use when…". Very short. |
| Content | **4** | Clear workflows. Has `references/review-output-template.md`. Auth detection block copy-pasted. PR checkout duplicated between sections 2 and 5. |
| Size | **5** | 14,096 chars — ideal. |
| **TOTAL** | **19/25** | |

**Defects:**
1. No "When to Use" section
2. No Pitfalls section — things like "token scopes needed for API comments" or "line numbers shift after force-push" aren't covered
3. Description doesn't follow "Use when…" convention; too minimal
4. Auth detection block (lines 25–43) is copy-pasted from other skills — should be a shared include or reference `github-auth`
5. PR checkout pattern appears in both Section 2 ("Check Out PR Locally") and Section 5 Step 3 — duplicated
6. The `***` token placeholder in curl examples is used inconsistently
7. Section 5 "PR Review Workflow (End-to-End)" is excellent but should be the main body; Sections 1–4 feel like reference appendices that belong after the workflow

---

### 6. github-issues

| Dimension | Score | Notes |
|-----------|:-----:|-------|
| Frontmatter | **5** | All fields present. Includes `platforms`. |
| Structure | **2** | No "When to Use." No Pitfalls. No Verification Checklist. |
| Description | **2** | "Create, triage, label, assign GitHub issues via gh or REST." Does NOT start with "Use when…". |
| Content | **4** | Has `templates/bug-report.md` and `templates/feature-request.md`. Auth detection block copy-pasted. Bug report template exists both inline and as a template file (redundancy). |
| Size | **4** | 9,685 chars — good. |
| **TOTAL** | **17/25** | |

**Defects:**
1. No "When to Use" section
2. No Pitfalls section — common issues like "GitHub API returns PRs in /issues endpoint", label name restrictions, rate limiting
3. No Verification Checklist
4. Description doesn't follow "Use when…" convention
5. Auth detection block (lines 26–43) copy-pasted
6. Bug report template exists both inline (lines 144–162) and at `templates/bug-report.md` — pick one
7. No guidance on issue templates (`.github/ISSUE_TEMPLATE/`) or issue forms — an important GitHub feature
8. Bulk operations section uses `xargs` with `gh` but doesn't handle empty issue lists (will error)

---

### 7. github-pr-workflow

| Dimension | Score | Notes |
|-----------|:-----:|-------|
| Frontmatter | **5** | All fields present. Includes `platforms`. |
| Structure | **2** | No "When to Use." No Pitfalls. No Verification Checklist. |
| Description | **2** | "GitHub PR lifecycle: branch, commit, open, CI, merge." Does NOT start with "Use when…". |
| Content | **4** | Well-organized lifecycle. Has references/ (2 files) and templates/ (2 files). Auth detection block copy-pasted. CI monitoring overlaps with github-ci-debug. |
| Size | **4** | 10,402 chars — good. |
| **TOTAL** | **17/25** | |

**Defects:**
1. No "When to Use" section
2. No Pitfalls section — despite being one of the most pitfall-prone workflows (merge conflicts, protected branches, required reviews, stale CI)
3. No Verification Checklist
4. Description doesn't follow "Use when…" convention
5. Auth detection block copy-pasted
6. CI monitoring section (Section 4) and auto-fix section (Section 5) overlap with `github-ci-debug` skill — should cross-reference instead of duplicating
7. `gh pr checks --watch` is shown but no mention that it can hang indefinitely on queued runners
8. Auto-merge GraphQL mutation (lines 319–328) has complex escaping that's likely to break when copied — should use `-d @-` with heredoc
9. Quick Reference Table (end) is useful but duplicates content from the body

---

### 8. github-repo-management

| Dimension | Score | Notes |
|-----------|:-----:|-------|
| Frontmatter | **5** | All fields present. Includes `platforms`. |
| Structure | **2** | No "When to Use." No Pitfalls. No Verification Checklist. |
| Description | **2** | "Clone/create/fork repos; manage remotes, releases." Does NOT start with "Use when…". |
| Content | **4** | Comprehensive coverage (10 sections). Has `references/github-api-cheatsheet.md`. Auth detection block copy-pasted. Secrets encryption section overly complex. Gist section tangential. |
| Size | **5** | 14,249 chars — ideal. |
| **TOTAL** | **18/25** | |

**Defects:**
1. No "When to Use" section
2. No Pitfalls section — many gotchas: fork syncing, branch protection, org permission requirements
3. No Verification Checklist
4. Description doesn't follow "Use when…" convention
5. Auth detection block (lines 25–53) copy-pasted
6. Secrets encryption section (lines 315–356) with PyNaCl is overly implementation-heavy for a skill reference — should point to `gh secret set` as primary and note curl as last resort
7. Gist section (Section 10, lines 469–502) is tangential to repository management — belongs in a separate skill or appendix
8. Section 9 "GitHub Actions Workflows" overlaps with `github-ci-debug` and `github-pr-workflow`

---

## Summary Ranking Table

| Rank | Skill | Front. | Struct. | Desc. | Content | Size | **TOTAL** |
|:----:|-------|:------:|:-------:|:-----:|:-------:|:----:|:---------:|
| 1 | **github-code-review** | 5 | 3 | 2 | 4 | 5 | **19** |
| 2 | **github-ci-debug** | 5 | 3 | 2 | 4 | 4 | **18** |
| 2 | **github-repo-management** | 5 | 2 | 2 | 4 | 5 | **18** |
| 4 | **github-auth** | 5 | 3 | 2 | 4 | 3 | **17** |
| 4 | **github-issues** | 5 | 2 | 2 | 4 | 4 | **17** |
| 4 | **github-pr-workflow** | 5 | 2 | 2 | 4 | 4 | **17** |
| 7 | **git-cross-platform-pitfalls** | 4 | 3 | 3 | 3 | 3 | **16** |
| 8 | **codebase-inspection** | 5 | 3 | 2 | 3 | 2 | **15** |

**Average score:** 17.1 / 25 (68.5%)

---

## Cross-Cutting Findings

### Systemic Issues (Affect 6+ Skills)

1. **No skill uses "Use when…" in description** — All 8 skills violate the Hermes skill convention. Descriptions describe *what* the skill does, not *when* to load it. Every description should be rewritten to start with "Use when…" followed by trigger conditions.

2. **Auth detection block duplicated in 6 skills** — `github-code-review`, `github-issues`, `github-pr-workflow`, `github-repo-management`, `github-ci-debug`, and `github-auth` all contain near-identical 15-line auth detection scripts. This is a maintenance hazard. Create a shared `scripts/auth-detect.sh` in `github-auth/` and have all other skills source it.

3. **No Verification Checklists** — Only `github-code-review` has one (Section 3, strong quality). The other 7 skills lack any structured way for an agent to confirm it completed the task correctly.

4. **Missing "When to Use" sections** — Only `codebase-inspection` has one. The other 7 skills need explicit trigger-condition sections.

5. **Missing Pitfalls sections** — Only `codebase-inspection`, `github-ci-debug`, and `git-cross-platform-pitfalls` have explicit Pitfalls sections. The other 5 lack them entirely.

6. **`***` token placeholder inconsistency** — Some curl examples use `***`, others hardcode real-looking env vars. Should standardize on `$GITHUB_TOKEN` with env var export patterns.

### Strengths

- **Excellent frontmatter discipline** — 7 of 8 skills have perfect frontmatter; only `git-cross-platform-pitfalls` is missing `platforms`
- **Rich supporting files** — 5 of 8 skills have references/, templates/, or scripts/ directories
- **Dual-path design** — Every API-facing skill provides both `gh` and `curl` paths, which is excellent for portability
- **Actionable content** — Nearly all commands are directly executable; minimal theoretical prose
- **Good cross-referencing** — `github-ci-debug` and `git-cross-platform-pitfalls` reference each other appropriately

### Weaknesses

- **Description convention not followed** — 8/8 skills fail the "Use when…" trigger standard
- **Structural gaps** — "When to Use" missing in 7/8, Pitfalls missing in 5/8, Verification Checklist missing in 7/8
- **Duplication debt** — Auth detection block duplicated 6 times; CI monitoring duplicated between `github-pr-workflow` and `github-ci-debug`
- **Size inconsistency** — Range from 3,744 to 14,249 chars; 2 skills are underweight, 1 is borderline

---

## Remediation Priorities

| Priority | Action | Skills Affected | Effort |
|----------|--------|:---------------:|:------:|
| 🔴 P0 | Rewrite all descriptions to "Use when…" convention | All 8 | Low |
| 🔴 P0 | Add "When to Use" sections to 7 skills | All except codebase-inspection | Medium |
| 🟡 P1 | Extract shared auth detection to `github-auth/scripts/auth-detect.sh` | 6 skills | Medium |
| 🟡 P1 | Add Verification Checklists to 7 skills | All except github-code-review | Medium |
| 🟡 P1 | Add Pitfalls sections to 5 skills | github-auth, github-code-review, github-issues, github-pr-workflow, github-repo-management | Medium |
| 🟢 P2 | Bulk up `codebase-inspection` (3,744 → 8,000+ chars) | codebase-inspection | Medium |
| 🟢 P2 | Deduplicate bug report template (inline vs. templates/) | github-issues | Low |
| 🟢 P2 | Add `platforms` field to git-cross-platform-pitfalls | git-cross-platform-pitfalls | Low |
| 🟢 P2 | Standardize `***` → `$GITHUB_TOKEN` in curl examples | All | Low |

---

*Report generated by Hermes Agent subagent. All file sizes confirmed via `ls -la`. Skill content read in full via `read_file`.*
