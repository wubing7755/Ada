# Blazor mouseenter/mouseleave Fix Pattern (Atlas, 2026-07-24)

## Problem

`@onmouseenter` and `@onmouseleave` are silently ignored in Blazor .NET 6.
These DOM events do not bubble — Blazor's event delegation at document level
never receives them. Razor generates no compiler warning for unrecognized
event attributes.

## Fix: Three-Layer Pattern

### Layer 1 — TypeScript (`index.ts`)

Add to the existing interop module. Uses `WeakMap` (same pattern as `dragHandlers`)
for leak-safe listener tracking.

```typescript
const hoverHandlers = new WeakMap<HTMLElement, {
  enter: (e: MouseEvent) => void;
  leave: (e: MouseEvent) => void;
}>();

export function registerHoverEvents(
  element: HTMLElement | null,
  dotNetHelper: DotNetDragCallback,
  panelId: string
): void {
  if (!element) return;
  unregisterHoverEvents(element);

  const enter = (_e: MouseEvent) => dotNetHelper.invokeMethodAsync('OnMouseEnter', panelId);
  const leave = (_e: MouseEvent) => dotNetHelper.invokeMethodAsync('OnMouseLeave', panelId);

  hoverHandlers.set(element, { enter, leave });
  element.addEventListener('mouseenter', enter);
  element.addEventListener('mouseleave', leave);
}

export function unregisterHoverEvents(element: HTMLElement | null): void {
  if (!element) return;
  const handlers = hoverHandlers.get(element);
  if (handlers) {
    element.removeEventListener('mouseenter', handlers.enter);
    element.removeEventListener('mouseleave', handlers.leave);
    hoverHandlers.delete(element);
  }
}
```

### Layer 2 — C# Interop (`DragInterop.cs`)

```csharp
// HoverCallback — lightweight IAsyncDisposable wrapper
// Use internal visibility — not part of the NuGet public API surface.
// DragCallback remains public because IDragService.CallbackReference exposes it.
internal sealed class HoverCallback : IAsyncDisposable
{
    private readonly DotNetObjectReference<HoverCallback> _ref;
    private readonly Func<string, Task> _onEnter;
    private readonly Func<string, Task> _onLeave;

    public HoverCallback(Func<string, Task> onEnter, Func<string, Task> onLeave)
    {
        _ref = DotNetObjectReference.Create(this);
        _onEnter = onEnter;
        _onLeave = onLeave;
    }

    public DotNetObjectReference<HoverCallback> Reference => _ref;

    [JSInvokable] public Task OnMouseEnter(string id) => _onEnter(id);
    [JSInvokable] public Task OnMouseLeave(string id) => _onLeave(id);

    public async ValueTask DisposeAsync() { _ref.Dispose(); }
}

// Static methods in DragInterop (internal static class):
public static async ValueTask RegisterHoverEvents(
    IJSRuntime js, ElementReference element,
    DotNetObjectReference<HoverCallback> callback, string panelId)
{
    var module = await GetModuleAsync(js);
    await module.InvokeVoidAsync("registerHoverEvents", element, callback, panelId);
}

public static async ValueTask UnregisterHoverEvents(
    IJSRuntime js, ElementReference element)
{
    var module = await GetModuleAsync(js);
    await module.InvokeVoidAsync("unregisterHoverEvents", element);
}
```

### Layer 3 — Razor Component

```razor
@inject IJSRuntime JS
@implements IAsyncDisposable

<div @ref="_wrapperRef">
    <button @onclick="..." ... />
</div>

@code {
    private ElementReference _wrapperRef;
    private ElementReference _elRef;
    private HoverCallback? _hoverCallback;
    private string? _lastRegisteredPanelId;

    /// <summary>
    /// Synchronous ref registration stays in OnAfterRender so the parent
    /// component reads populated _entryRefs before its own OnAfterRenderAsync runs.
    /// Blazor lifecycle is parent-first depth-first: sync before async.
    /// </summary>
    protected override void OnAfterRender(bool firstRender)
    {
        RegisterElementRef?.Invoke(_elRef);
    }

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        var currentId = Panel.Id.Value;

        // GUARD: only re-register when panel identity changes
        if (!firstRender && string.Equals(_lastRegisteredPanelId, currentId,
                StringComparison.Ordinal))
            return;

        if (_hoverCallback is not null)
        {
            try { await DragInterop.UnregisterHoverEvents(JS, _wrapperRef); }
            catch (JSException) { /* DOM element removed */ }
            await _hoverCallback.DisposeAsync();
        }

        _hoverCallback = new HoverCallback(
            async panelId => await OnMouseEnter.InvokeAsync(new PanelId(panelId)),
            async panelId => await OnMouseLeave.InvokeAsync(new PanelId(panelId)));

        try
        {
            await DragInterop.RegisterHoverEvents(
                JS, _wrapperRef, _hoverCallback.Reference, currentId);
            _lastRegisteredPanelId = currentId;
        }
        catch (JSException)
        {
            Debug.WriteLine($"[Atlas] hover register failed for '{currentId}'");
        }
    }

    public async ValueTask DisposeAsync()
    {
        if (_hoverCallback is not null)
        {
            try { await DragInterop.UnregisterHoverEvents(JS, _wrapperRef); }
            catch (JSException) { }
            await _hoverCallback.DisposeAsync();
        }
    }
}
```

## Design Decisions

| Decision | Rationale |
|----------|----------|
| Register on wrapper `<div>`, not inner `<button>` | mouseenter/mouseleave fire at element boundary — wrapper covers full entry area |
| `WeakMap` in TS | Same pattern as `dragHandlers` — avoids leaks if C# component is collected |
| `IAsyncDisposable` on HoverCallback | Releases `DotNetObjectReference` to prevent interop leaks |
| Inline lambdas in HoverCallback constructor | Keeps callback wiring at call site, no extra class needed |
| `internal sealed` on HoverCallback | Not part of NuGet public API; only `DragCallback` (used by `IDragService`) is public |
| Render guard (`_lastRegisteredPanelId`) | Prevents HoverCallback recreate + JS re-register on every Blazor render cycle |
| Separate `OnAfterRender` / `OnAfterRenderAsync` | Parent-first sync → async lifecycle: ref registration must complete before parent reads `_entryRefs` |

## Pitfalls Avoided

### 1. Recreating HoverCallback on Every Render

Without the `_lastRegisteredPanelId` guard, each Blazor render destroys and recreates
the `HoverCallback` + JS listeners. 2N JS interop calls per render (N = entries). Fix:
string-identity guard matching `DockPanel.razor`'s `_lastHeaderPanelId` pattern.

### 2. Silent Exception Propagation

`RegisterHoverEvents` without try/catch lets `JSException` propagate to Blazor's render
pipeline as `renderFragmentException`. Wrap in try/catch — same pattern as drag handler
registration in `ToolBar.razor` and `TabBar.razor`.

### 3. Parent-First Lifecycle Order

Merging `OnAfterRender(bool)` (sync ref registration) into `OnAfterRenderAsync(bool)`
breaks parent-child communication: parent's `OnAfterRenderAsync` runs before child's,
reading unpopulated `_entryRefs`. Keep sync registration in `OnAfterRender`.
