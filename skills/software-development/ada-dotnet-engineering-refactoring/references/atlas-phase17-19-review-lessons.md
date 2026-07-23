# Atlas Phase 17–19 review lessons (2026-07-23)

Use this as a compact checklist when doing engineering-grade Blazor/.NET refactoring with independent review.

## ErrorBoundary security

Do not render exception type names or `exception.Message` in client-visible Blazor `ErrorBoundary` UI for arbitrary content components. Keep the UI generic and log details through an internal/debug path if needed. Reviewers should fail closed on client-visible implementation details because component exceptions can contain file paths, data values, or secrets.

## Lifecycle tests must be behavioral

Static source-text/reflection tests are not enough for lifecycle contracts such as JS listener attach/detach or drop-target unregister. Prefer behavioral evidence:

- Node/JS runtime smoke with a fake DOM element that records `addEventListener` / `removeEventListener` and attributes.
- Fake `IJSRuntime` that records invocation order.
- Component lifecycle tests that exercise rerender and `DisposeAsync` when practical.

If a test claims `detach` works, it should prove a registered listener was removed, not merely assert that source contains `removeEventListener`.

## Render identity hashes

When a Blazor component skips re-registration based on a hash, include every input that affects rendered element identity/order. For Toolbar entries, panel ID alone is insufficient: include `RegionName` and display/render state so moves between same-side groups or auto-hide state changes force detach/attach against the new `ElementReference`.

## DI boundary without public internal types

When a public-facing service interface would need to expose an internal command type, split the protocol:

- Keep the public/injected interface narrow (for example `IUndoStack`: execute, undo/redo, clear, state).
- Add an internal side interface (for example `ICommandRecorder`) implemented by the default concrete service.
- The orchestrator can detect the internal recorder for command history without concrete-casting injected services.

This preserves substitutability and avoids leaking internal command abstractions into public APIs.

## Windows ad-hoc verification evidence

For Git-Bash/MSYS repos on Windows, create the temp verifier under `C:\Users\usr\AppData\Local\Temp`, convert with `cygpath -u`, print both Windows and MSYS paths, execute, remove the script, and report cleanup. Label filtered commands as focused/ad-hoc verification, not full-suite verification.
