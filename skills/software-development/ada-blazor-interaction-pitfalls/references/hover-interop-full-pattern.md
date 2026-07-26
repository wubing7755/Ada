# Hover Interop — Full Pattern

Complete JS-interop-based replacement for `@onmouseenter`/`@onmouseleave` in Blazor WASM (.NET 6).

## TypeScript (index.ts)

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

  const enter = (_e: MouseEvent) => {
    dotNetHelper.invokeMethodAsync('OnMouseEnter', panelId);
  };
  const leave = (_e: MouseEvent) => {
    dotNetHelper.invokeMethodAsync('OnMouseLeave', panelId);
  };

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

## C# Interop Stubs (DragInterop.cs)

```csharp
public static async ValueTask RegisterHoverEvents(
    IJSRuntime js,
    ElementReference element,
    DotNetObjectReference<HoverCallback> callback,
    string panelId)
{
    var module = await GetModuleAsync(js);
    await module.InvokeVoidAsync("registerHoverEvents", element, callback, panelId);
}

public static async ValueTask UnregisterHoverEvents(
    IJSRuntime js,
    ElementReference element)
{
    var module = await GetModuleAsync(js);
    await module.InvokeVoidAsync("unregisterHoverEvents", element);
}
```

## C# Callback Class

```csharp
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

    [JSInvokable] public Task OnMouseEnter(string panelId) => _onEnter(panelId);
    [JSInvokable] public Task OnMouseLeave(string panelId) => _onLeave(panelId);

    public async ValueTask DisposeAsync() => _ref.Dispose();
}
```

## Component Usage

```csharp
// ToolBarEntry.razor or similar — key patterns:

// 1. REF REGISTRATION — sync OnAfterRender (parent-first order)
protected override void OnAfterRender(bool firstRender)
{
    RegisterElementRef?.Invoke(_elRef);
}

// 2. HOVER REGISTRATION — async, guarded
private string? _lastRegisteredPanelId;
private HoverCallback? _hoverCallback;

protected override async Task OnAfterRenderAsync(bool firstRender)
{
    var currentPanelId = Panel.Id.Value;

    // GUARD: skip if Panel unchanged (no re-registration churn)
    if (!firstRender && string.Equals(_lastRegisteredPanelId, currentPanelId, StringComparison.Ordinal))
        return;

    // UNREGISTER old
    if (_hoverCallback is not null)
    {
        try { await DragInterop.UnregisterHoverEvents(JS, _wrapperRef); }
        catch (JSException) { /* DOM removed */ }
        await _hoverCallback.DisposeAsync();
    }

    // REGISTER new
    _hoverCallback = new HoverCallback(
        async panelId => await OnMouseEnter.InvokeAsync(new PanelId(panelId)),
        async panelId => await OnMouseLeave.InvokeAsync(new PanelId(panelId)));

    try
    {
        await DragInterop.RegisterHoverEvents(JS, _wrapperRef, _hoverCallback.Reference, currentPanelId);
        _lastRegisteredPanelId = currentPanelId;
    }
    catch (JSException)
    {
        System.Diagnostics.Debug.WriteLine($"[Atlas] hover register failed for '{currentPanelId}' — DOM missing.");
    }
}

// 3. DISPOSE — unregister + dispose
public async ValueTask DisposeAsync()
{
    if (_hoverCallback is not null)
    {
        try { await DragInterop.UnregisterHoverEvents(JS, _wrapperRef); }
        catch (JSException) { /* already removed */ }
        await _hoverCallback.DisposeAsync();
    }
}
```

## Why This Pattern

| Concern | Solution |
|---------|----------|
| `@onmouseenter` silent failure | Native `addEventListener` via JS interop |
| Re-registration churn on every render | `_lastRegisteredPanelId` string guard |
| Stale DOTNET refs after dispose | `unregisterHoverEvents` BEFORE `DisposeAsync` |
| DOM removal between renders | try/catch `JSException` |
| Parent reads refs before child populates | `RegisterElementRef` in sync `OnAfterRender` |
| Per-render index reset for `StateHasChanged` | `ShouldRender()` instead of `OnParametersSet` |

## Verification

```bash
dotnet build -v q && dotnet test --no-build -v q
# Hover callbacks exercised via ToolBarEntry + DragInteropLifecycle tests
# Must pass: 208/208
```
