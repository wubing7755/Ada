# Lib Phase 1 Plan — Reference Template

This reference captures the conventions and task breakdown used in the Lib Phase 1 implementation. It serves as a template for future Blazor component library phases or similar projects.

## Architecture Decision: State-driven Component Architecture (not MVVM)

Lib rejected traditional MVVM because:

| Lib concern | MVVM suitability |
|---|---|
| Multi-region dock hierarchy tree | Poor — no natural ViewModel nesting |
| Editor View / Tab state machine | Poor — ViewModel doesn't own lifecycle |
| Drag with high-frequency pointer events | Poor — binding overhead |
| Layout export/import | Better as pure model/serializer |
| Multi-instance isolation | Better as scoped context |
| Fast sequential operation serialization | Better as command queue |

Instead, Lib uses:

```text
Razor Components
    ↓ events
LibLayoutContext (per-instance)
    ↓ commands
Command/Reducer (pure state transitions)
    ↓
LayoutState / Domain Model
```

## Key Design Constraints

| Constraint | Decision | Reason |
|---|---|---|
| .NET version | `net6.0` | Legacy customer compatibility |
| Future packaging | Razor Class Library | Code organized with extraction in mind |
| JS interop source | TypeScript | Maintainability, type safety |
| JS build tool | esbuild via npx | No global install required |
| JS artifacts in Git | Excluded | Generated during MSBuild |
| Test framework | xUnit | Standard Blazor ecosystem choice |
| UI style | Neutral, JetBrains-like structure | Not brand-specific |
| Commit format | Conventional Commits | Per-module scopes, one feature per commit |
| Error handling | `DockResult` / `DockResult<T>` | No exceptions for expected failures |

## Phase 1 Task Sequence

Each task produces one commit. Order matters — models before services, services before components.

1. **Scaffolding**: xUnit project + TypeScript build pipeline + `.gitignore`
2. **Enums & Results**: `DockErrorCode`, `DockResult`, `DockResult<T>`, `LayoutEnums`
3. **Domain Models**: `LayoutState`, `RegionModel`, `DockPanelModel`, `EditorViewModel`, `TabModel`, `RegionNames`
4. **Validator**: `LibLayoutValidator` — region name checks, fixed-vs-dock, duplicates
5. **Content Registry**: `LibContentRegistry` — register/resolve/is-registered
6. **Layout Context**: `LibLayoutContext` — OpenTab, ActivateTab, GetTab, event dispatch, multi-instance isolation
7. **Static Components**: All `.razor` files — layout, regions, panels, toolbars, editor area, tabs, splitters
8. **Styling**: Neutral CSS with `xd-` prefix, JetBrains-like structure, `prefers-reduced-motion`
9. **DynamicContent**: `DynamicComponent` rendering via ContentRegistry, error isolation per tab
10. **Demo Page**: Replace prototype `Dock.razor` with formal Lib components
11. **Traceability**: Update `docs/requirements-traceability.md`

## Verification at Each Task

Every task ends with:
```bash
dotnet test Lib.slnx --no-restore
```

Expected: all tests pass, build succeeds, no new CS errors.

Only `NETSDK1138` (EOL target framework) warning is acceptable for `net6.0` builds.

## Pitfalls Discovered

1. **Namespace collision** (see SKILL.md main body): `Components/Lib/` conflicts with root `Lib` namespace. Fix: rename to `Components/Docking/` or use `global::` prefix.

2. **Patch tool with Razor files**: Removing `@using` lines via `patch` can consume adjacent markup. Always verify post-patch with `read_file`.

3. **MSBuild npm dependency**: `npx --yes` downloads esbuild on first use. Ensure `node` and `npm` are available in the build environment.
