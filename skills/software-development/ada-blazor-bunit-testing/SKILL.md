---
name: ada-blazor-bunit-testing
description: "Use when writing bUnit tests for Blazor components."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [blazor, bunit, testing, wasm]
    related_skills: [ada-blazor-interaction-pitfalls, ada-dotnet-verification, ada-test-driven-development]
    trigger_keywords: ['bUnit', 'RenderComponent', 'WaitForAssertion', 'UploadFiles', 'cut.Render', 'EditorRequired', 'FindAll']
---

# bUnit 测试 Blazor 组件

## Overview

Verified bUnit 1.x (1.40.0) authoring facts for Blazor component projects
(verified in a real component-library project with 30+ bUnit tests).
These are behaviors observed in real tests, not documentation guesses.

## Verified bUnit 1.x Facts

### EditorRequired is NOT enforced on RenderComponent

bUnit 1.40 renders a component with a missing `[Parameter, EditorRequired]`
property **without throwing** — the parameter stays null. Consequences:

- Single-panel tests still run with a null required parameter. If the panel
  dereferences it inside `_ = InvokeAsync(...)`, the NRE is swallowed by the
  fire-and-forget (test passes anyway). Guard with `is not null` in the
  component, or accept the hidden NRE.
- Do not rely on bUnit to catch a forgotten required parameter in tests.

Razor usage is the opposite: omitting an `[EditorRequired]` parameter from a
component used in a `.razor` route emits RZ2012, which becomes an ERROR under
`TreatWarningsAsErrors` (component-library repos commonly set it). So when a route stops
passing a parameter (e.g. `Model` is now resolved from Context), REMOVE
`EditorRequired` from that parameter — keeping a `= null!` non-nullable
declaration and assigning it in `OnInitialized` compiles clean and matches
how `Content` was already handled.

### `WaitForAssertion` + `Assert.Single` is a selector-count trap

When the assertion inside `WaitForAssertion` uses
`Assert.Single(FindAll("..."))` but the selector matches more than one
element, the failure is reported at that assertion — with a confusing
"Collection contained 2 items" message that looks like a product bug. It may
also be the wrong assertion in the flow. Diagnose by asserting the **exact
expected count** first:

```csharp
cut.WaitForAssertion(
    () => Assert.Equal(2, cut.FindAll("[data-testid='editor'] .dbc-action").Count));
cut.FindAll("[data-testid='editor'] .dbc-action")[0].Click(); // Text button
```

Classic instance: an editor toolbar has TWO `.dbc-action` buttons (Text,
Table); `Assert.Single` fails even though the flow is correct.

### `cut.Render()` forces a host re-render

`IRenderedFragment.Render()` (bUnit 1.x) re-renders the root component,
re-executing Route/ContentRoutes fragments and calling `OnParametersSet` on
children. This is the reliable repro for host-rerender-clobber bugs:
render workspace → type unsaved text → `cut.Render()` → assert textarea keeps
the value. Prefer a real workspace operation (Undo/Redo) when the flow has
one; `cut.Render()` is the deterministic fallback.

### `Click()` is fire-and-forget: stale handler ids fail LATE

bUnit's `Click()`/`TriggerEvent` extensions are `_ = TriggerEventAsync(...)`
— the dispatch task is discarded. If a pending render replaces the DOM
between the `FindAll` query and the dispatch, the clicked element's
`blazor:onclick` id is no longer registered and the failure surfaces as
`UnknownEventHandlerIdException` inside the NEXT `WaitForAssertion` (via
`AssertNoUnhandledExceptions`), NOT at the `Click()` call. Stack signature:
`Renderer.GetRequiredEventCallback` → `TestRenderer.DispatchEventAsync`.

Typical trigger: a fire-and-forget `_ = InvokeAsync(StateHasChanged)` (e.g.
from a `StateChanged` subscription in `OnModelChanged`) lands after the query
and before the click. The bUnit error text explicitly recommends re-issuing
`FindAll` after each render. Robust pattern:

```csharp
cut.Find("...").Change("unsaved-A");            // fires fire-and-forget re-render
cut.WaitForAssertion(() => Assert.Equal("unsaved-A", ...)); // may return EARLY (DOM value already set)
cut.Render();                                   // flush pending render
var tabs = cut.FindAll("[role='tab']");         // re-query AFTER flush
tabs[0].Click();
```

Always re-query `FindAll` immediately before each click, and add
`cut.Render()` (or a real workspace operation) when a fire-and-forget
re-render is in play.

### KeepAliveWithinGroup only mounts previously-selected outlets

A `KeepAliveWithinGroup` content-lifetime mode does NOT mount every item on
first render. The cache accumulates items that were SELECTED over time; on
first render only the selected item's outlet exists. To assert two mounted
content components (e.g. two same-Kind documents with independent state),
select the other item first, then assert:

```csharp
await workspace.ExecuteAsync(new SelectItemOperation(itemId));
cut.WaitForAssertion(() => Assert.Equal(2, cut.FindComponents<StatefulContent>().Count));
```

This mirrors the existing `ContentLifetimeTests` pattern — keep-alive is
verified after a selection switch, not on initial render.

### Optional `[Inject]` is impossible in .NET 6 — resolve via IServiceProvider

.NET 6's `ComponentFactory.CreateInitializer` throws for ANY unregistered
`[Inject]` property — including nullable reference types — at component
instantiation (`"Cannot provide a value for property 'X' on type 'Y'. There
is no registered service of type 'Z'"`). Verified against aspnetcore
v6.0.0 source and reproduced in bUnit 1.40. A component declaring
`[Inject] MyService? Optional` CRASHES in real apps too, not just tests, so
"optional injection with null fallback" cannot use the attribute. The
working pattern:

```csharp
[Inject] private IServiceProvider ServiceProvider { get; set; } = null!;

// in OnParametersSet:
effectiveScope ??= ServiceProvider.GetService(typeof(ISomeService)) as ISomeService
    ?? new DefaultImplementation();
```

`IServiceProvider` itself always resolves (MS.DI built-in service; bUnit's
TestServiceProvider returns the provider), so the ComponentFactory null check
never fires for it.

### Async event handlers that throw must be contained

A component event handler that can throw a domain exception (e.g. a file-store
duplicate-name rule in `InputFile OnChange`) escapes to the WASM top level as
`Error: System.InvalidOperationException...` and bUnit converts it into a
failing test at the dispatch. Contain it: try/catch in the handler, surface a
visible message element (`role="status"`, `data-testid`), and
`await InvokeAsync(StateHasChanged)`; test asserts the message appears AND the
store is unchanged. Re-query `FindComponent<InputFile>()` before each
`UploadFiles` — the component re-renders after the first upload.

```csharp
input.UploadFiles(InputFileContent.CreateFromText(ValidDbc, "engine.dbc"));
input = cut.FindComponent<InputFile>();
input.UploadFiles(InputFileContent.CreateFromText(ValidDbc, "engine.dbc")); // duplicate
cut.WaitForAssertion(() =>
{
    Assert.Single(store.FilesIn("DBC"));
    Assert.Contains("already exists", cut.Find("[data-testid='dbc-tree-message']").TextContent);
});
```

### Temp diagnostic test pattern

When a bUnit test fails at an unexpected point, write a throwaway test that
dumps reality, run it, delete it:

```csharp
private readonly ITestOutputHelper _output; // ctor-inject

[Fact]
public void Dump_state()
{
    var cut = RenderComponent<...>();
    _output.WriteLine("count: " + cut.FindAll("[data-testid='x']").Count);
    foreach (var el in cut.FindAll("[data-testid='x']"))
        _output.WriteLine("EL: " + el.OuterHtml);
}
```

Run with `dotnet test ... --logger "console;verbosity=detailed"` and grep the
standard-output section. This resolves "which element, how many, what markup"
questions in one cycle instead of guessing. `System.Console.WriteLine` with a
`[DEBUG]` prefix also prints under the same logger flag and avoids constructor
injection; grep for the prefix. Delete the file after.

### InputFile upload through a full workspace

```csharp
cut.FindComponent<InputFile>()
    .UploadFiles(InputFileContent.CreateFromText(ValidDbc, "engine.dbc"));
```

bUnit awaits async `OnChange` handlers, so the store mutation is visible
immediately; render propagation may need `WaitForAssertion` for the new DOM
elements. `FindComponent<InputFile>()` throws if more than one exists.

### Razor naming collision: EventCallback parameter vs handler method

Renaming a parameter to the Blazor-conventional `OnXxx` collides with a
private handler method of the same name (`OnMessageSelected`) → CS0102 "type
already contains a definition". Name private handlers `HandleXxx`:

```razor
[Parameter] public EventCallback<DbcMessage> OnMessageSelected { get; set; }
@onclick="() => HandleMessageSelected(message)"
private Task HandleMessageSelected(DbcMessage m)
    => OnMessageSelected.InvokeAsync(m);
```

### Misc verified facts

- CSS attribute selectors with single quotes work: `[data-testid='dbc-file']`.
- `Find`/`FindAll` return per-call wrappers; compare node identity with
  `Unwrap()` (raw element), not wrapper reference equality.
- `@bind="Model.EditedContent"` (model property) vs `@bind="editedContent"`
  (local field): binding to the model is what survives host re-renders.
- `@onclick="Model.Save"` binds a parameterless void method directly.
- **Blazor event attributes render as `blazor:onclick` (not `onclick`) in
  bUnit's markup**, so `element.HasAttribute("onclick")` is false. To assert
  that an element's attribute frame survived a reorder/render (the "naked
  element" symptom), assert on `data-*` and `aria-label` instead — or match
  `blazor:onclick` if the event binding itself is the question.

## Workflow: fail-first repro for render bugs

1. Write the failing test reproducing the user-visible symptom through the
   real component flow (not a unit-level shortcut).
2. Run → confirm FAIL at the intended assertion (the red test IS the bug
   evidence).
3. Implement the minimal fix.
4. Run full suite → PASS, no regression.
5. When a behavior change is intentional (e.g., tab title now follows the
   file name), UPDATE the existing test's assertions to the new behavior —
   never bypass or delete it.
