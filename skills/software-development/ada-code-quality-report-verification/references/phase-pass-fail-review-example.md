# Phase Pass/Fail Review Example: Lib MovePanel Display-State / Undo Semantics

Use this as a compact pattern for independent fail-closed reviews of an implementation phase, especially when the user asks for a JSON-like verdict rather than a narrative report.

## Review target

- Phase: `Lib Phase C: MovePanel display-state and undo semantics`
- Requirements/design anchors:
  - `docs/SRS.md` — `REQ-F-069 AC7`
  - `docs/refactoring/bottom-dock-auto-collapse-design-2026-07-23.md` — Phase C verification criteria
  - `docs/requirements-traceability.md` — implementation/test mapping
- Source/tests inspected:
  - `src/Lib/Services/Commands/MovePanelCommand.cs`
  - `tests/Lib.Tests/Services/Commands/MovePanelCommandTests.cs`
  - `src/Lib/Services/DragService.cs`
  - `tests/Lib.Tests/Services/DragServiceTests.cs`

## Verification shape

1. Read the requirement/design acceptance criteria first, not just the implementation diff.
2. Inspect the changed command source and adjacent call paths.
3. Inspect focused tests and verify they assert the actual semantics, not just event firing or non-null state.
4. Run the focused test slice, then the broader local quality gate.
5. Fail closed: return `passed:false` if there is any blocking semantics mismatch, missing focused coverage for a required branch, or failed verification command. Otherwise return `passed:true` with concrete evidence.

## Concrete checks used

- `Execute()` captured both source and target region snapshots before mutation.
- Target region active expanded panel(s) were collapsed and deactivated.
- Moved panel was reassigned to target, expanded, and activated.
- `Undo()` restored captured panels' original region, display state, and active state.
- Focused tests covered collapsed moved panel, auto-hidden moved panel, target active collapse, and undo restoration.

## Commands used

```bash
dotnet test tests/Lib.Tests/Lib.Tests.csproj --filter 'FullyQualifiedName~MovePanelCommandTests|FullyQualifiedName~LibDragServiceTests' -v q

dotnet build -v q && dotnet test --no-build -v q && dotnet format --verify-no-changes && git diff --check
```

## Output shape requested by user

```js
{
  passed: true | false,
  security_concerns: [],
  logic_errors: [],
  test_gaps: [],
  evidence: [],
  recommended_fixes: []
}
```

Keep it evidence-dense and avoid long prose when this shape is requested.
