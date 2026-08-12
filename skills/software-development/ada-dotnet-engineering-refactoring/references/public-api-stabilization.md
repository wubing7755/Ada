# .NET public API stabilization pattern

Use this during late-phase .NET library refactoring, especially before NuGet/package boundaries harden.

## Trigger

- A refactoring plan says "public surface", "API stabilization", "发布前收窄 public surface", or "historical rule cleanup".
- Architecture/deviation docs identify helper/interoperability types that are `public` but not intended package API.
- SRS removed or revised an old rule, but stale guards/error codes remain in source.

## Workflow

1. **Read the source-of-truth requirement first.** Confirm the current SRS text and ACs before deleting or preserving behavior. If Description and AC disagree, patch the requirement text so they align.
2. **Classify each public type by protocol ownership:**
   - Keep public when consumers must name the type in layout declarations, DI/service protocols, event args, or callback signatures.
   - Make internal when it is a query/helper/style adapter, component-private interop wrapper, or implementation detail behind a public facade.
   - If a public interface exposes a callback DTO, keep that DTO public until the interface protocol changes.
3. **Write RED tests for the API boundary, not only behavior.** Reflection tests are appropriate here:
   - absent stale method names on owning types,
   - absent stale enum members,
   - helper/interop types are not public,
   - intentionally public protocol DTOs remain public.
4. **Delete stale rule remnants in all API layers.** Remove both the unused guard and any public error code that represented the deleted requirement; otherwise the package still advertises the old behavior.
5. **Update traceability and deviation docs in the same phase.** Mark which DEV item was cleaned, which REQ changed, and why any remaining public type is intentionally public.
6. **Verify with both full and focused evidence:**
   - `dotnet build -v q`
   - focused API-boundary tests
   - full `dotnet test --no-build -v q` when claiming suite-green
   - `dotnet format --verify-no-changes`
   - `git diff --check`
   - source search under `src` for stale guard/error names
   - added-line secret scan

## Lib Phase 20 example

- Deleted `LayoutRepair` historical last-panel-visible guard because current `REQ-F-104` AC3 allows collapsing the last expanded panel and assigning space to Editor Area.
- Removed stale `DockErrorCode.LastPanelCannotCollapse` so the public API no longer advertises deleted `REQ-F-130`.
- Changed `LayoutQuery`, `LayoutStyleAdapter`, `DragInterop`, and `DragType` to `internal`.
- Kept `DragCallback` public because `IDragService.Callback` / `CallbackReference` still expose it.
- Added `PublicSurfaceStabilizationTests` as focused reflection guardrails.

## Pitfalls

- Do not make a callback/DTO internal if a public interface still returns or accepts it; this breaks consumers and the demo/test compile.
- Do not claim stale names are gone based on docs/tests only; search under `src` so test guard strings do not count as false positives.
- Do not mark a phase fully complete while independent review is still running; report “local complete, awaiting independent review”.
