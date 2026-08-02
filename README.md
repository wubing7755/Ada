English | [简体中文](README.zh-CN.md)

> **Status:** Canonical

# Ada — Hermes Profile Distribution

Ada is a distributable Hermes Profile: a software-engineering-focused agent that prioritizes correctness and verifiability. The name comes from Ada Lovelace — the first person to see that a machine could express ideas as well as compute numbers.

Ada helps developers understand, design, build, debug, and evolve software systems. Its value is not in knowing many terms, but in seeing the problem clearly, making sound judgments, and driving work to runnable, verifiable results. It is not a chat persona that only serves up terminology; it is a technical partner with engineering judgment.

Persona and engineering principles are defined once in [SOUL.md](SOUL.md); the 50 distributed skills live under [skills/](skills/).

Current version: `0.3.0`, requires Hermes `>=0.19.0`.

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

Ada's 50 skills follow Agent Skills progressive disclosure: discovery loads only skill names and `description`; once a task matches, the corresponding `SKILL.md` is loaded for the execution protocol; `references/`, `scripts/`, `assets/`, and `evals/` are read only when needed.

In practice, you usually describe the goal and let the agent load the matching skill — there is no need to memorize or invoke the 50 skill names by hand.

## Skill Catalog (50 skills)

All Ada-owned skills use the `ada-` prefix. Categories and order follow `distribution.yaml`.

### Agent and Workflow

| Skill | Purpose |
|---|---|
| `ada-agent-assisted-development` | Structured agent orchestration: subagent review, phased implementation, quality audits |
| `ada-continuous-phased-delivery` | Continuous execution of approved multi-phase plans within authorization boundaries |
| `ada-hermes-agent-skill-authoring` | SKILL.md authoring and validation: frontmatter, lifecycle, publishing |
| `ada-hermes-configuration` | Hermes configuration and persona design: SOUL.md, memory, profiles |
| `ada-hermes-doc-sync` | Syncs project documentation with a live Hermes installation (skill catalogs, command references) |
| `ada-hermes-operations` | Hermes operating discipline: evidence standards, context management, approval boundaries |
| `ada-requesting-code-review` | Pre-commit review: security scan, quality gates, structured review requests |
| `ada-skill-optimization` | Audits and optimizes Hermes-generated skills: frontmatter, dedup, curator |
| `ada-systematic-debugging` | Four-phase root-cause debugging: understand the bug before fixing it |
| `ada-test-driven-development` | Test-driven development enforcing RED-GREEN-REFACTOR |

### SRS Lifecycle

| Skill | Purpose |
|---|---|
| `ada-requirements-authoring` | Lightweight single-requirement authoring and acceptance-criteria review |
| `ada-srs-lifecycle` | Unified entry point for the SRS lifecycle: derivation, authoring, review, revision |
| `ada-srs-review` | SRS quality review: dead requirements, cross-references, terminology drift |
| `ada-srs-revision` | Large-scale SRS revision: terminology replacement, renumbering, reference repair |
| `ada-srs-writing` | SRS authoring: structural patterns, quality rules, requirement entry format |
| `ada-tp-to-srs-derivation` | Derives an SRS from a technical proposal (TP) |
| `ada-doc-comparison-analysis` | Compares document versions and merges SRS drafts |
| `ada-docs-revision` | Large-scale revision of general technical documents: terminology, structure |

### Audit and Traceability

| Skill | Purpose |
|---|---|
| `ada-code-dedup-audit` | Pre-commit audit of duplication between new and existing code |
| `ada-code-efficiency-review` | Performance review: N+1 queries, redundant work, hot paths |
| `ada-library-public-api-review` | Reviews a library's public API and compatibility boundary from an external consumer's perspective |
| `ada-doc-implementation-audit` | Verifies documentation against source, tests, and git diffs |
| `ada-doc-traceability-audit` | Documentation-internal traceability audit: SRS entries, matrices, appendices |
| `ada-pre-implementation-audit` | Pre-implementation audit: verifies the current-state claims a plan depends on |
| `ada-project-audit` | Whole/legacy project audit: implementation status, code health, traceability drift |
| `ada-stateful-service-audit` | Audits stateful services: transactions, invariants, persistence, concurrency, history semantics |
| `ada-traceability-audit` | Requirements traceability matrix to source consistency checks |
| `ada-ui-interaction-protocol-contracts` | Designs and validates interaction protocol contracts across UI/host boundaries |

### Code Quality

| Skill | Purpose |
|---|---|
| `ada-code-quality-analysis` | Multi-dimensional code quality audit: complexity, duplication, dead code, security |
| `ada-code-quality-pipeline` | End-to-end code quality reporting: analysis, verification, QA gates |
| `ada-code-quality-report-verification` | Independently verifies every claim in a quality report |
| `ada-quality-report-qa` | Three-agent QA pipeline: statistical errors, coverage false negatives, security omissions |
| `ada-simplify-code` | Parallel three-agent cleanup of recent changes: review, simplify, verify |

### .NET and Blazor

| Skill | Purpose |
|---|---|
| `ada-blazor-component-library` | Blazor component library construction and maintenance patterns |
| `ada-blazor-interaction-pitfalls` | Blazor lifecycle and rendering behavior pitfalls |
| `ada-blazor-interop-pitfalls` | Blazor JS interop and DOM event pitfalls |
| `ada-blazor-ui-audit` | End-to-end component library audit: rendering, state, CSS, interop, assets |
| `ada-dotnet-blazor-library` | .NET Blazor component library engineering: RCL, demo, public API, publishing |
| `ada-dotnet-engineering-refactoring` | .NET engineering-level refactoring: domain primitives, value type migration, public API |
| `ada-dotnet-verification` | .NET build/test/format/package verification |

### Refactoring

| Skill | Purpose |
|---|---|
| `ada-bugfix-architecture-root-cause` | Shared root-cause analysis across multiple bugs: trace architectural issues first |
| `ada-engineering-refactoring` | Architecture-level refactoring: type constraints, interface contracts, implementation separation |
| `ada-refactoring-lifecycle` | Engineering refactoring lifecycle: planning, phased execution, verification |

### Cross-platform Engineering and Tooling

| Skill | Purpose |
|---|---|
| `ada-cmake-cpack-packaging` | CMake/CPack cross-platform packaging and installers |
| `ada-node-inspect-debugger` | Node.js `--inspect` + CDP debugging |
| `ada-powershell-from-bash` | Running PowerShell correctly from git-bash |
| `ada-python-debugpy` | Python debugpy/DAP interactive debugging |

### Documents and Deliverables

| Skill | Purpose |
|---|---|
| `ada-business-document-authoring` | Evidence-to-decision business documents (DOCX/PDF) |
| `ada-document-artifacts` | DOCX/PDF/XLSX/SVG document and diagram processing |

### Research and Planning

| Skill | Purpose |
|---|---|
| `ada-research-planning` | Stress-testing plans, domain modeling, large task decomposition, strategic reading |

## Common Workflows

| Scenario | Recommended skill chain | Expected outcome |
|---|---|---|
| Deriving an SRS from a technical proposal | `ada-tp-to-srs-derivation` → `ada-srs-review` → `ada-srs-revision` | Reviewable, traceable requirements document |
| Fixing a complex failure | `ada-systematic-debugging` → the relevant technical skill → `ada-requesting-code-review` | Root-cause evidence, minimal fix, regression verification |
| Engineering-grade refactoring | `ada-refactoring-lifecycle` → `ada-dotnet-engineering-refactoring` / `ada-engineering-refactoring` → `ada-dotnet-verification` | Phased changes with independent quality gates |
| Multi-phase implementation | `ada-agent-assisted-development` + `ada-continuous-phased-delivery` | Continuous execution with per-phase review and verification |
| Documentation consistency audit | `ada-doc-implementation-audit` / `ada-doc-traceability-audit` / `ada-traceability-audit` | Evidence-backed gap list |
| Code quality report | `ada-code-quality-analysis` → `ada-code-quality-report-verification` → `ada-quality-report-qa` | Independently verified quality report |
| Blazor component library delivery | `ada-dotnet-blazor-library` → `ada-blazor-component-library` → `ada-blazor-ui-audit` | Publishable, verifiable component library |

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
├── .github/workflows/          # GitHub Actions quality gates
└── skills/software-development/  # 50 ada-* skills
```

## Quality Validation

The repository gates every pull request targeting `main` through the `Ada Profile Quality / validate-profile` GitHub Actions check, and re-runs it after pushes to `main`. The checks include:

- validator unit tests; consistency between `distribution.yaml`, the actual skill directory, and the README skill catalog/count; README vs. manifest version consistency;
- YAML/frontmatter, resource links, inter-skill references, and eval structure checks; private runtime state leak checks (memories, sessions, credentials, `local/`, etc.);
- Python `compileall` and changed-file `git diff --check`;
- an isolated install/update smoke test with a temporary `HERMES_HOME`, confirming all 50 skills and user state survive an update.

The same gates can be run locally:

```bash
python -m unittest scripts/tests/test_validate_skill_quality.py -v
python scripts/validate_skill_quality.py
python -m compileall -q scripts
python scripts/smoke_profile_distribution.py
git diff --check
```

> The automated gates are necessary but not sufficient: they cannot prove a skill is useful in real tasks, free of stale assumptions, or legally distributable. The validator currently passes while keeping 24 pre-existing advisory eval warnings (for example, insufficient trigger/reject case coverage); this is known quality debt, not a claim that every quality dimension is warning-free.

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
| `0.3.0` (current, untagged) | Adds GitHub Actions quality gates; consolidates local Ada engineering skills into a unified 50-skill catalog |
| `v0.2.0` (tagged) | Manifest 0.2.2: skill-trigger refinements, self-contained skills, three new skills absorbed from hermes-use |
| `v0.1.0` (tagged) | Initial profile distribution |

## License

MIT — declared in the `license` field of `distribution.yaml`.
