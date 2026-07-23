# Autonomous AI Agents Skills — Quality Audit Report

**Path:** `temp-skills/autonomous-ai-agents/`  
**Date:** 2026-07-23  
**Auditor:** Hermes Agent  
**5 Skills Audited:** claude-code, codex, coding-agent-readiness, hermes-agent, opencode

---

## Scoring Methodology

Each skill is scored across 6 dimensions on a 1–5 scale (5 = perfect):

| # | Dimension | What We Check |
|---|-----------|---------------|
| 1 | **Frontmatter Completeness** | name, description, version, author, license, `metadata.hermes.{tags,related_skills}`; name ≤64 chars; desc ≤1024 chars; file starts with `---` |
| 2 | **Structure & Readability** | Overview / When to Use / main body / Pitfalls / Verification Checklist sections present and well-organized |
| 3 | **Description Quality** | Description prefixed with "Use when…" or trigger-condition phrasing; focuses on *when* not *what* |
| 4 | **Content Quality** | Steps have verifiable completion conditions; no no-op prose ("be careful", "be thorough"); no duplicated content; references/templates/scripts linked where applicable |
| 5 | **Size** | Char count in 8–15K ideal range; over 20K needs splitting; under 5K may lack depth |
| 6 | **Defects / Issues** | Concrete list of problems — missing sections, broken links, oversized, weak descriptions, missing cross-references |

---

## Individual Skill Scorecards

---

### 1. claude-code

| Dimension | Score | Notes |
|-----------|-------|-------|
| Frontmatter | **5/5** | All required fields present. `platforms`, `version: 2.2.0`. `related_skills` covers all siblings. |
| Structure | **5/5** | Deeply organized: Overview → Prerequisites → Two Modes → Print Deep Dive → CLI Flags → Settings → Slash Commands → Hooks → MCP → Pitfalls → Rules. Excellent flow. |
| Description | **2/5** | `"Delegate coding to Claude Code CLI (features, PRs)."` — describes *what*, not *when*. Should start with `"Use when..."` trigger phrasing. |
| Content | **4/5** | Nearly every section has verifiable commands with expected outputs. Minor: "Be thorough." (line 473) is no-op prose. No duplicated content despite length. No `references/` directory despite complexity — the TMUX dialog patterns and MCP config examples would benefit from being pulled out. |
| Size | **1/5** | **34,902 chars / 745 lines.** Massively over 20K threshold. Needs splitting: `claude-code-print`, `claude-code-interactive`, `claude-code-config`, `claude-code-hooks-mcp` are natural seams. |
| **TOTAL** | **22/30** | |

**Defects:**

1. **CRITICAL — Oversized (34,902 chars).** Exceeds the 20K split threshold by ~75%. LLMs pay per-token for skill context — most of this is reference-material bloat the agent rarely needs for a given task. Split recommendations:
   - `claude-code-print` (~8K): Print mode deep dive, JSON output, streaming, piped input, bare mode
   - `claude-code-interactive` (~10K): TMUX orchestration, dialog handling, slash commands, keyboard shortcuts, monitoring
   - `claude-code-config` (~8K): Settings hierarchy, CLAUDE.md, rules, hooks, MCP, subagents
   - `claude-code-pr-review` (~5K): PR review patterns, worktrees, parallel instances
2. **Description not trigger-oriented.** `"Delegate coding to Claude Code CLI (features, PRs)."` → should be `"Use when the user asks to delegate a coding task to Claude Code or needs Claude Code CLI orchestration guidance."`
3. **No-op prose:** `"Be thorough."` (line 473 in PR review prompt).
4. **No `references/` directory.** TMUX dialog-handling patterns (lines 83–115) and MCP config examples (lines 637–671) are large, self-contained blocks that could live in `references/tmux-orchestration.md` and `references/mcp-integration.md` to reduce the main SKILL.md footprint.
5. **No Verification Checklist section.** Despite having "Pitfalls & Gotchas" and "Rules for Hermes Agents", there's no explicit verification/smoke-test section.
6. **Table-heavy content strain.** The CLI flags reference (lines 246–333), slash commands (lines 362–402), keyboard shortcuts (430–465), and hook types (608–618) are dense reference tables. Consider moving to `references/cli-flags.md`.

---

### 2. codex

| Dimension | Score | Notes |
|-----------|-------|-------|
| Frontmatter | **4/5** | All required fields present. `platforms` included. `version: 1.0.0`. `related_skills` omits `opencode` (present in all other skills in this family). |
| Structure | **3/5** | Has When to Use, Prerequisites, One-Shot, Background, Key Flags, PR Reviews, Parallel Patterns, Rules. Missing: dedicated **Pitfalls** section and **Verification Checklist**. The "Hermes Gateway Caveat" is effectively a pitfall but isn't labeled as such. |
| Description | **2/5** | `"Delegate coding to OpenAI Codex CLI (features, PRs)."` — same issue as claude-code. Action-oriented, not trigger-oriented. |
| Content | **3/5** | Commands are concrete and copy-pasteable. Rule #6 "Don't interfere — be patient" is mild no-op prose. The "Hermes Gateway Caveat" section (lines 79–95) is excellent — specific error messages, root cause, and fix. No `references/` directory. |
| Size | **3/5** | **5,517 chars / 149 lines.** Under the 8K ideal minimum. Slightly thin — could benefit from troubleshooting section, model selection guidance, and a verification smoke-test. |
| **TOTAL** | **19/30** | |

**Defects:**

1. **Missing `opencode` in `related_skills`.** Frontmatter lists `[claude-code, hermes-agent]` but opencode is a sibling in the same family and references codex.
2. **No dedicated Pitfalls section.** The Gateway Caveat (bubblewrap errors, sandbox failures) is effectively a pitfall but buried mid-document. Other pitfalls worth calling out: `pty=true` is required (currently only in Rules #1), Codex requires a git repo, `--sandbox danger-full-access` safety implications.
3. **No Verification Checklist.** Unlike opencode (which has a smoke test: `OPENCODE_SMOKE_OK`), there's no way to verify codex is working correctly.
4. **Description not trigger-oriented.** See claude-code. Should be `"Use when the user asks to delegate..."`.
5. **PR review pattern is terse.** Lines 97–103 show a review command but don't explain what `codex review` actually does or how to interpret output. Compare to claude-code's detailed PR review section.
6. **Missing troubleshooting.** What if `codex exec` hangs? What if auth fails? What if the sandbox breaks? A minimal troubleshooting section would improve the 5.5K footprint.
7. **No `references/` directory.** The Gateway Caveat could live as `references/gateway-sandbox-caveat.md`.

---

### 3. coding-agent-readiness

| Dimension | Score | Notes |
|-----------|-------|-------|
| Frontmatter | **4/5** | All required fields present. `related_skills` covers all three coding agents. Missing: `platforms` field (present in all others in this family). |
| Structure | **3/5** | Has intro, 3 numbered steps, decision table, pitfall, Docker notes, reference files list. Missing: explicit **When to Use** header and **Verification Checklist**. Compact but clear. |
| Description | **3/5** | `"Pre-flight checks before delegating to Claude Code, Codex, or OpenCode in the Docker sandbox."` — trigger-oriented ("before delegating"). Slightly long and context-specific (Docker sandbox). |
| Content | **5/5** | Every step has a specific command. The decision table (lines 35–41) is clear: "delegate vs write directly" with cell-by-cell guidance. Has 2 reference files properly linked. No no-op prose. No duplicated content. Pristine. |
| Size | **3/5** | **2,691 chars / 61 lines.** Very small — half the 5K minimum. But the skill is intentionally narrow (pre-flight checks only), so brevity is a feature, not a bug. |
| **TOTAL** | **22/30** | |

**Defects:**

1. **Missing `platforms` in frontmatter.** All four siblings have `platforms: [linux, macos, windows]`. This one doesn't.
2. **No explicit "When to Use" header.** The intro paragraph (lines 15–16) serves this role but isn't a labeled section. Adding `## When to Use` with bullet points would improve scannability.
3. **No Verification Checklist.** What confirms the readiness check is complete? A small checklist would help: "□ Binary found, □ Auth confirmed, □ Decision made (delegate/write)."
4. **Docker-specific framing may be too narrow.** The title says "coding agent readiness" but the description and intro mention "Docker sandbox" — the decision table is Docker-agnostic. Consider broadening the scope or renaming.
5. **Missing "what to do if checks fail" guidance.** Step 1 says "if not installed: `npm install -g`" but Step 2 (auth) has no fallback path beyond the decision table. What if auth times out?
6. **Very small.** At 2.7K chars, it could be absorbed into a broader "coding-agent-orchestration" umbrella skill. But standalone is defensible given its focused purpose.

---

### 4. hermes-agent

| Dimension | Score | Notes |
|-----------|-------|-------|
| Frontmatter | **5/5** | All required fields. `platforms` included. `homepage` bonus field. `version: 2.3.0`. `related_skills` covers all siblings. |
| Structure | **4/5** | Encyclopedic: Overview → Quick Start → CLI Reference → Slash Commands → Config → Providers → Toolsets → Context Files → Security → Voice → Spawning → Background Systems → Surfaces → Windows Quirks → Troubleshooting → Where to Find → Contributor Guide. Missing: explicit **Pitfalls** section and **Verification Checklist**. The Troubleshooting section partially fills the pitfalls gap. |
| Description | **2/5** | `"Configure, extend, or contribute to Hermes Agent."` — describes what the skill covers, not when to use it. Should be trigger-oriented like `"Use when setting up, configuring, troubleshooting, extending, or contributing to Hermes Agent."` |
| Content | **4/5** | Commands are actionable with concrete flags. "Scope & Verification" (lines 35–43) is meta-good — tells the reader what to verify against. References `native-mcp.md` and `webhooks.md` properly linked. Some sections read like reference-manual pages rather than skill guidance (Contributor Quick Reference could be split). No no-op prose. No duplicated content despite 1,111 lines — impressive editorial discipline. |
| Size | **1/5** | **52,417 chars / 1,111 lines.** This is the largest skill in the audit — over 2.6× the split threshold. Splitting is urgent. |
| **TOTAL** | **20/30** | |

**Defects:**

1. **CRITICAL — Oversized (52,417 chars).** Far exceeds the 20K threshold. This one skill is larger than all four others combined. Natural split points:
   - `hermes-agent-core` (~12K): Overview, Quick Start, CLI Reference, Slash Commands, Key Paths & Config
   - `hermes-agent-config` (~8K): Config Sections, Providers, Toolsets, Project Context Files, Security & Privacy Toggles
   - `hermes-agent-advanced` (~10K): Voice, Spawning Instances, Background Systems (Delegation, Cron, Curator, Kanban), Surfaces, Windows Quirks
   - `hermes-agent-troubleshooting` (~6K): Troubleshooting, Where to Find Things
   - `hermes-agent-contrib` (~8K): Contributor Quick Reference, project layout, adding tools/commands, agent loop, testing, commit conventions
2. **Description not trigger-oriented.** See above.
3. **No Pitfalls section.** Troubleshooting (lines 894–943) covers failure modes but isn't a concise "gotchas to watch out for" list. A compact Pitfalls section at the top would complement the diagnostic Troubleshooting section at the bottom.
4. **No Verification Checklist.** After reading 1,111 lines, the agent has no quick way to confirm Hermes is correctly set up. A 5-item checklist (`hermes doctor`, `hermes --version`, `hermes status`, etc.) would close this gap.
5. **Reference-manual tone.** Sections like "Slash Commands" (lines 263–363, 100 lines of command tables) and "CLI Reference" (lines 73–260, 187 lines) are reference material — useful but heavy in context. Moving CLI/Slash command tables to `references/cli-reference.md` and `references/slash-commands.md` would trim ~8K from the main file.
6. **Some content duplicates official docs.** The provider table (lines 407–430) and toolsets table (437–470) are duplicative of hermes-agent.nousresearch.com docs. They serve as a quick reference but bloat the skill. Consider a one-liner "See docs at URL" with only the most-used entries.

---

### 5. opencode

| Dimension | Score | Notes |
|-----------|-------|-------|
| Frontmatter | **5/5** | All required fields present. `platforms` included. `version: 1.2.0`. `related_skills` covers siblings. |
| Structure | **5/5** | Gold standard: Intro → When to Use → Prerequisites → Binary Resolution → One-Shot → Interactive → Flags → Procedure → PR Review → Parallel → Session/Cost → **Pitfalls** → **Verification** → Rules. Has every recommended section. |
| Description | **2/5** | `"Delegate coding to OpenCode CLI (features, PR review)."` — same trigger issue as siblings. But the body has an excellent "When to Use" section. |
| Content | **4/5** | Numbered procedure (lines 140–148) with clear steps. Verification section has actual smoke test: `opencode run 'Respond with exactly: OPENCODE_SMOKE_OK'`. Pitfalls are specific and actionable (e.g., `/exit` is not valid — opens agent selector). No reference files. Slight thinness in parallel work pattern. |
| Size | **4/5** | **7,470 chars / 219 lines.** Just under the 8K ideal minimum. Appropriately sized for a coding-agent orchestration guide — enough depth without bloat. |
| **TOTAL** | **24/30** | |

**Defects:**

1. **Description not trigger-oriented.** `"Delegate coding to OpenCode CLI (features, PR review)."` → `"Use when the user asks to delegate coding, refactoring, or PR review tasks to OpenCode CLI."`
2. **No `references/` directory.** The Binary Resolution troubleshooting (lines 34–46, `which -a opencode`, pinning explicit path) and TUI keybindings table (lines 100–111) could live in `references/binary-resolution.md` and `references/tui-keybindings.md`.
3. **Parallel Work Pattern section is thin.** Lines 164–171 show two `opencode run` commands in background but don't cover collision risks, worktree isolation vs temp dirs, or how to merge results. Compare to claude-code's parallel section which uses tmux with monitoring.
4. **Missing model selection guidance.** `--model` is mentioned in the flags table but there's no guidance on which models work well with OpenCode or how provider/model syntax works (e.g., `openrouter/anthropic/claude-sonnet-4` vs just `claude-sonnet-4`).
5. **PR review with `-f` flag is fragile.** Line 161: `-f $(git diff origin/main --name-only | head -20 | tr '\n' ' ')` — this space-separates filenames but `-f` may not handle that well. The example could use multiple `-f` flags instead.
6. **Minor:** TUI keybindings table (lines 100–111) says `Ctrl+X L/M/N/E` but these are Emacs/TUI conventions that may not work in all terminals (especially on Windows). No Windows caveat mentioned.

---

## Summary Rankings

| Rank | Skill | Frontmatter | Structure | Description | Content | Size | **TOTAL** |
|------|-------|:-----------:|:---------:|:-----------:|:-------:|:----:|:---------:|
| 🥇 1 | **opencode** | 5 | 5 | 2 | 4 | 4 | **24/30** |
| 🥈 2 | **claude-code** | 5 | 5 | 2 | 4 | 1 | **22/30** |
| 🥈 2 | **coding-agent-readiness** | 4 | 3 | 3 | 5 | 3 | **22/30** |
| 🥉 4 | **hermes-agent** | 5 | 4 | 2 | 4 | 1 | **20/30** |
| 5 | **codex** | 4 | 3 | 2 | 3 | 3 | **19/30** |

---

## Aggregate Findings

### Common Issues Across All 5 Skills

| Issue | Affected Skills | Severity |
|-------|----------------|----------|
| **Description doesn't start with "Use when..."** | ALL 5 | Medium — consistent pattern; suggests a convention gap, not individual negligence |
| **Missing Verification Checklist** | claude-code, codex, coding-agent-readiness, hermes-agent (4/5) | High — only opencode has an explicit smoke test |
| **Missing explicit Pitfalls section** | codex, hermes-agent (2/5) | Medium |
| **No `references/` directory** | claude-code, codex, opencode (3/5) | Medium — self-contained content that could be split out |

### Size Crisis

| Skill | Chars | Lines | Status |
|-------|-------|-------|--------|
| hermes-agent | 52,417 | 1,111 | 🔴 **URGENT** — 2.6× over 20K split threshold |
| claude-code | 34,902 | 745 | 🔴 **URGENT** — 1.7× over 20K split threshold |
| opencode | 7,470 | 219 | 🟢 Near ideal minimum |
| codex | 5,517 | 149 | 🟡 Slightly under ideal range |
| coding-agent-readiness | 2,691 | 61 | 🟡 Very small but defensibly narrow scope |

**The two largest skills (hermes-agent + claude-code) together account for 87,319 chars — 84% of the total skill content across all 5 files.** Both urgently need splitting.

### Strengths

- **Frontmatter quality is excellent across the board.** All skills have complete metadata. The `related_skills` cross-linking creates a navigable graph.
- **opencode is the gold standard for structure.** It has every recommended section (When to Use, Pitfalls, Verification, Rules) at the right size.
- **coding-agent-readiness is a model of focused content quality.** Zero no-op prose, every line earns its keep, properly references supporting files.
- **claude-code's depth is impressive.** Despite size issues, the content itself is well-organized, accurate, and actionable.
- **hermes-agent's editorial discipline at scale is notable.** 1,111 lines with no duplication — whoever maintains this has good process.

### Recommended Actions (Priority Order)

1. **🔴 Split hermes-agent SKILL.md** — proposed 5 sub-skills (see defects above)
2. **🔴 Split claude-code SKILL.md** — proposed 4 sub-skills (see defects above)
3. **🟡 Add Verification Checklists** to codex, coding-agent-readiness, and hermes-agent
4. **🟡 Fix descriptions** across all 5 skills to use "Use when..." trigger phrasing
5. **🟡 Add missing `related_skills` entry** — codex should reference opencode
6. **🟡 Add `platforms` field** to coding-agent-readiness frontmatter
7. **🟢 Add `references/` directories** to claude-code, codex, and opencode — pull out large self-contained blocks
8. **🟢 Add Pitfalls sections** to codex and hermes-agent
9. **🟢 Bulk up thin skills** — codex could benefit from troubleshooting and verification content; coding-agent-readiness could add fallback guidance for failed auth checks

---

## File-Size Distribution

```
hermes-agent          ████████████████████████████████████████████████████  52,417 (50.4%)
claude-code           ██████████████████████████████████                    34,902 (33.6%)
opencode              ███████                                               7,470  (7.2%)
codex                 █████                                                 5,517  (5.3%)
coding-agent-readiness ██                                                    2,691  (2.6%)
                      ─────────────────────────────────────────────────────
                      TOTAL: 103,597 chars
```

---

## Verification

This report was generated by:
- Reading all 5 SKILL.md files in full
- Measuring exact byte and character counts via `wc`
- Validating frontmatter YAML structure and field presence
- Auditing section headers, prose quality, and cross-references
- Checking for `references/`, `templates/`, and `scripts/` directory presence

*Report saved to: `.hermes/audit-autonomous.md`*
