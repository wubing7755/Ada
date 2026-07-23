# Blazor Service Wiring: LayoutContext + ContentRegistry

Pattern from the Atlas project (Phase 1) for resolving content components
by key from a Razor Class Library's `ContentRegistry`.

## Problem

`TabContent.razor` creates `new ContentRegistry()` every render. That registry
is empty — no content keys are ever registered. `Resolve("atlas-demo")` always
fails with "Content key 'atlas-demo' is not registered."

## Solution

Make `LayoutContext` own the `ContentRegistry`. Pre-register demo/fallback
components in the constructor. Have `TabContent` use `Context?.ContentRegistry`.

### LayoutContext.cs

```csharp
public sealed class LayoutContext
{
    public ContentRegistry ContentRegistry { get; }

    public LayoutContext(LayoutState state, EventDispatcher eventDispatcher, ContentRegistry contentRegistry)
    {
        State = state;
        Events = eventDispatcher;
        ContentRegistry = contentRegistry;

        // Phase 1: pre-register built-in demo component
        if (!ContentRegistry.IsRegistered("atlas-demo"))
        {
            ContentRegistry.Register<DemoContent>("atlas-demo");
        }
    }
}
```

### TabContent.razor

```csharp
// BEFORE (broken — empty registry every render):
var registry = new ContentRegistry();

// AFTER (correct — uses Context's registry):
var registry = Context?.ContentRegistry ?? new ContentRegistry();
```

## Key Insight

Services that hold state (like `ContentRegistry`) must be owned by a
longer-lived container (`LayoutContext`), not instantiated per-component-per-render.
The `?? new ContentRegistry()` fallback is safe only when a registered one exists
— if Context is null, the fallback will still fail to resolve keys, but at least
won't throw NRE.
