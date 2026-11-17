English | [简体中文](README.zh-CN.md)

> **Status:** Canonical

# Ada — Hermes Profile Distribution

Ada is a distributable Hermes Profile: a software-engineering-focused agent that prioritizes correctness and verifiability. The name comes from Ada Lovelace — the first person to see that a machine could express ideas as well as compute numbers.

Ada helps developers understand, design, build, debug, and evolve software systems. Its value is not in knowing many terms, but in seeing the problem clearly, making sound judgments, and driving work to runnable, verifiable results. It is not a chat persona that only serves up terminology; it is a technical partner with engineering judgment.

Persona and engineering principles are defined once in [SOUL.md](SOUL.md); the 12 distributed skills live under [skills/](skills/).

Current version: `0.6.0`, requires Hermes `>=0.19.0`.

## Who Ada Is For

Ada is for developers and teams that need requirements analysis, engineering design, implementation and debugging, audits and verification, and engineering-grade refactoring — and for teams that value evidence, minimal changes, compatibility with existing systems, and long-term maintenance cost.

Ada is not a general-purpose life assistant. Life, emotional, and non-technical daily matters are not its main focus; such questions are a better fit for Thea.

## How Ada Works

Ada works in a "facts → hypotheses → verification → change → re-verification" loop:

1. Separate facts, assumptions, and unknowns first; trust observable evidence — actual code, errors and stack traces, build and test results, configuration, and official documentation;
2. When something breaks, narrow the problem space before choosing the verification method with the highest information gain; keep changes minimal and treat runnable, reproducible results as the bar;
3. Never fake certainty: when you do not know, say so and give the most direct verification path.

Engineering principles: correctness over convenience, clarity over cleverness, verifiability over what merely sounds plausible, maintainability over short-term tricks. The full specification lives in [SOUL.md](SOUL.md).

## Quick Start

### 1. Install Hermes Agent

Ada requires Hermes `>=0.19.0`. Install per platform:

```bash
# Windows (PowerShell)
iex (irm https://hermes-agent.nousresearch.com/install.ps1)

# Linux / macOS
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

### 2. Install the Ada Profile

Install from GitHub and create an `ada` wrapper:

```bash
hermes profile install github.com/wubing7755/Ada --alias
```

For local development, install from the repository root instead:

```bash
hermes profile install . --name ada --alias
```

`--alias` creates a shell wrapper (`ada` → `hermes -p ada`), after which you can use the `ada` command directly.

### 3. Configure a Model and Credentials

```bash
ada setup        # interactive wizard (model, terminal, gateway, etc.)
ada model        # choose the default model and provider
```

### 4. Start Ada

```bash
ada                                     # start an interactive session
ada chat -q "Review this repository and identify the highest-risk issue."
```

### 5. Verify the Installation

```bash
hermes profile info ada    # distribution manifest: version, Hermes requirement, source
hermes profile show ada    # details of the installed profile
```

## How Skills Are Loaded

Ada's 12 skills follow Agent Skills progressive disclosure: discovery loads only skill names and `description`; once a task matches, the corresponding `SKILL.md` is loaded for the execution protocol; `references/`, `scripts/`, `assets/`, and `evals/` are read only when needed.

In practice, you usually describe the goal and let the agent load the matching skill — there is no need to memorize or invoke the 12 skill names by hand.

## Skill Catalog (12 skills)

All Ada-owned skills use the `ada-` prefix. Categories and order follow `distribution.yaml`.

### Core Engineering Workflow

| Skill | Purpose |
|---|---|
| `ada-agent-assisted-development` | Structured agent orchestration: subagent review, phased implementation, quality audits |
| `ada-research-planning` | Stress-testing plans, domain modeling, large task decomposition, strategic reading |
| `ada-systematic-debugging` | Four-phase root-cause debugging: understand the bug before fixing it |
| `ada-test-driven-development` | Test-driven development enforcing RED-GREEN-REFACTOR |

### Code Quality and Refactoring

| Skill | Purpose |
|---|---|
| `ada-requesting-code-review` | Pre-commit review: security scan, quality gates, structured review requests |
| `ada-code-quality-analysis` | Multi-dimensional code quality audit: complexity, duplication, dead code, security |
| `ada-simplify-code` | Parallel three-agent cleanup of recent changes: review, simplify, verify |
| `ada-engineering-refactoring` | Architecture-level refactoring: type constraints, interface contracts, implementation separation |

### Git Delivery

| Skill | Purpose |
|---|---|
| `ada-git-pr-delivery` | Turns a dirty worktree into a clean PR: pointer fix, commit conventions, PR template |
| `ada-git-destructive-operations` | Safe handling of resets and local-commit deletion with clarify-based intent |

### Windows Environment Tooling

| Skill | Purpose |
|---|---|
| `ada-windows-file-editing` | Windows/MSYS file editing: CRLF, MSYS paths, case-insensitive dir conflicts, piped exit codes |
| `ada-powershell-from-bash` | Running PowerShell correctly from git-bash |

## Common Workflows

| Scenario | Recommended skill chain | Expected outcome |
|---|---|---|
| Fixing a complex failure | `ada-systematic-debugging` → `ada-test-driven-development` → `ada-requesting-code-review` | Root-cause evidence, minimal fix, regression verification |
| Implementing a new feature | `ada-research-planning` → `ada-agent-assisted-development` → `ada-test-driven-development` | Decomposed plan, phased implementation with per-phase review |
| Engineering-grade refactoring | `ada-code-quality-analysis` → `ada-engineering-refactoring` → `ada-requesting-code-review` | Phased changes with independent quality gates |
| Cleaning up recent changes | `ada-simplify-code` → `ada-requesting-code-review` | Simplified, verified diff ready for commit |
| Code quality report | `ada-code-quality-analysis` | Evidence-backed audit with file:line findings |
| Shipping work as a PR | `ada-requesting-code-review` → `ada-git-pr-delivery` | Clean branch, conventional commits, reviewable PR |

## Built-in Hermes Dependencies

Ada relies on Hermes `>=0.19.0` for the following built-in skills (shipped with Hermes, not part of this distribution):

| Category | Skills |
|---|---|
| Autonomous AI agents | `claude-code`, `codex`, `opencode`, `hermes-agent` |
| GitHub workflows | `github-pr-workflow`, `github-code-review`, `github-issues`, `github-auth`, `github-repo-management`, `codebase-inspection` |
| General workflows | `plan`, `spike` |

## Repository Structure

```text
Ada/
├── distribution.yaml           # Profile distribution manifest (name, version, skill catalog)
├── SOUL.md                     # Ada's persona and engineering principles
├── README.md                   # English entry (Canonical)
├── README.zh-CN.md             # Simplified Chinese version (Synchronized)
├── docs/                       # Quality standard (skill-quality-standard.md)
├── scripts/                    # Validator, isolated smoke test, and unit tests
├── templates/                  # Portable AGENTS.md template distilled from SOUL.md
├── .github/workflows/          # GitHub Actions quality gates
└── skills/software-development/  # 12 ada-* skills
```

## Quality Validation

The repository gates every pull request targeting `main` through the `Ada Profile Quality / validate-profile` GitHub Actions check, and re-runs it after pushes to `main`. The checks include:

- validator unit tests; consistency between `distribution.yaml`, the actual skill directory, and the README skill catalog/count; README vs. manifest version consistency;
- YAML/frontmatter, resource links, inter-skill references, and eval structure checks; private runtime state leak checks (memories, sessions, credentials, `local/`, etc.);
- Python `compileall` and changed-file `git diff --check`;
- an isolated install/update smoke test with a temporary `HERMES_HOME`, confirming all 12 skills and user state survive an update.

The same gates can be run locally:

```bash
python -m unittest scripts/tests/test_validate_skill_quality.py -v
python scripts/validate_skill_quality.py
python -m compileall -q scripts
python scripts/smoke_profile_distribution.py
git diff --check
```

> The automated gates are necessary but not sufficient: they cannot prove a skill is useful in real tasks, free of stale assumptions, or legally distributable. The validator currently passes while keeping 8 pre-existing advisory eval warnings (for example, insufficient trigger/reject case coverage); this is known quality debt, not a claim that every quality dimension is warning-free.

## Updating Ada

```bash
hermes profile info ada      # current installed version, source, and Hermes requirement
hermes profile update ada    # re-pull from the recorded source and apply updates
```

`profile update` overwrites distribution-owned content (`SOUL.md`, `skills/`, `cron/`, `mcp.json`, etc.) but never touches user data such as memories, sessions, auth, or `.env`; `config.yaml` keeps local overrides by default unless `--force-config` is passed explicitly.

## Distribution Boundary and Privacy

- This distribution does not carry the installer's memories, sessions, API keys, or local logs.
- Installers use their own model configuration and credentials.
- The validator rejects private runtime paths (such as `memories/`, `sessions/`, credential files, `local/`) from the distribution.
- Skill quality standards live in `docs/skill-quality-standard.md`.

## Versions

| Version | Notes |
|---|---|
| `0.6.0` (current, untagged) | Backports persona-level improvements from the Copilot Ada variant into SOUL.md: falsification-first evidence seeking, revise conclusions on conflicting evidence, autonomous execution within authorization, risk disclosure regardless of user preference, workspace protection, authorization granularity, untrusted-content injection defense, delivery standards; synced to templates/AGENTS.md |
| `v0.5.0` (tagged) | Lean core: trims the 77-skill catalog to 12 general-purpose engineering skills; removes SRS lifecycle, audit/report pipelines, .NET/Blazor/CMake stack-specific, document-delivery, and Hermes self-maintenance clusters; SOUL.md adds security and availability engineering principles (tiered stance + 7 hard bottom lines); adds a portable AGENTS.md template for other agent tools |
| `0.4.0` | Absorbs 27 accumulated self-learned skills from local/desktop Ada profiles into a unified 77-skill catalog; adds SRS-to-design, NuGet, security, Git/PR delivery, bilingual docs, UI review clusters |
| `v0.2.0` (tagged) | Manifest 0.2.2: skill-trigger refinements, self-contained skills, three new skills absorbed from hermes-use |
| `v0.1.0` (tagged) | Initial profile distribution |

## License

MIT — declared in the `license` field of `distribution.yaml`.
