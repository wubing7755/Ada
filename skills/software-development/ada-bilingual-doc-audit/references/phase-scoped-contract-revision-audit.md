# Phase-Scoped Bilingual Contract Revision Audit

Use this reference when one approved phase revises an existing bilingual SRS/HLD/ADR set. The goal is to prove both **global invariants** and **no newly introduced drift** without turning pre-existing inconsistencies into false blockers.

## 1. Freeze the baseline before adding an ID

Before proposing a new `REQ-*`, `DES-*`, ADR, or gate:

1. Read any baseline ADR and repository tests that freeze exact counts or sets.
2. Count formal requirement blocks and the marker-bounded index rows.
3. Inspect requirement-audit/traceability tables that require one row per formal ID.
4. Ask whether an existing requirement already owns the new observable behavior.

Prefer extending an existing requirement when the behavior is semantically part of that contract. Add a new ID only when it represents a genuinely independent obligation and update every count/set/audit dependency deliberately.

A green baseline test after the revision is necessary but not sufficient: it proves counts and sets, not semantic placement.

## 2. Separate global invariants from changed-scope parity

Run two batteries:

### Global invariants

- formal requirement count and ID uniqueness;
- EN/ZH formal ID set equality;
- body IDs equal marker-bounded index IDs;
- HLD DES ID set equality;
- code-fence balance;
- relative-link resolvability;
- repository baseline tests.

### Changed-scope parity

For only the IDs/design blocks touched by the phase, compare:

- requirement tuple: ID, priority marker, Actor;
- Source IDs;
- AC label sequence and count;
- must/should/may and failure semantics;
- body title vs local appendix/index title;
- DES tuple: ID, title, Source footer;
- ADR tuple: status, date, decision maker, related IDs, supersession relationship;
- traceability/gate state claims.

Do not make a phase fail because an unrelated requirement had a pre-existing title-capitalization or wording mismatch. Prove whether a mismatch is newly introduced with `git diff` or by comparing the same invariant against `HEAD`. Report pre-existing drift separately if it matters.

## 3. Robust SRS block parsing

Requirements commonly live inside fenced blocks. Parse each complete fence rather than assuming one field order for the whole repository.

AC labels may use ASCII or full-width colons:

```python
ac_labels = re.findall(r'^\s*(AC\d+)\s*[:：]', block, re.M)
```

This also avoids matching prose references such as `REQ-F-140 AC2:`. Do not use `^AC\d+:` for a bilingual pair: it counts English ACs and silently returns zero for Chinese `AC1：`.

Bound index extraction with the repository markers before scanning rows:

```python
start = text.index('<!-- 项目:requirements-index:start -->')
end = text.index('<!-- 项目:requirements-index:end -->')
index_region = text[start:end]
```

## 4. Contract migration residuals

When a new ADR supersedes an old API or resolution rule, zero-count scans must distinguish:

- **normative stale statements** — defects;
- **historical OI/context/supersession statements** naming the old contract — intentional;
- **implementation work-package text** — preferably describe the old API generically if the symbol name is not required.

Use a location allowlist, not a blanket assertion that the old symbol appears zero times.

## 5. Gate semantics

Keep decision readiness separate from implementation evidence:

- a decision gate may become `Closed` when the maintainer accepts the ADR and freezes the contract;
- the implementation traceability row remains `In Progress` until code, package, and runtime evidence exist.

Do not leave the same gate marked `Closed` in HLD and `In Progress` in traceability. If the repository uses one gate row for both decision and delivery, split the concepts explicitly.

## 6. Minimum evidence report

Report actual outputs, not planned checks:

- formal counts per language;
- DES counts per language;
- changed-ID tuple/AC parity result;
- body/index set result;
- links/fences result;
- focused baseline tests;
- repository build/test/format when the phase gate requires them;
- independent review findings and verified fixes;
- Git state and whether commit authority exists.
