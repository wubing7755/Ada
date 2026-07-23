# @ref Inside RenderFragment Pitfall (Blazor)

## Discovery Context

Session: REQ-F-149 ToolBar 空间分区布局实现 (Atlas project, refactor/base-class-optimization)
Date: 2026-07-22
Files: `src/Atlas/Components/ToolBar.razor`

## The Problem

When refactoring repeated entry-rendering code in ToolBar.razor (3 nearly identical
blocks for Up Dock, Lower Dock, and Bottom Dock entries), we extracted the markup
into a helper method returning `RenderFragment`:

```csharp
// ❌ BROKEN — compiles but ElementReference capture fails at runtime
private RenderFragment RenderEntry(DockPanelModel panel) => __builder =>
{
    var currentIndex = _renderIndex;
    <button @ref="_entryRefs[currentIndex]" @onclick="...">
        @panel.Title
    </button>
    _entryPanelIds[currentIndex] = panel.Id;
    _renderIndex = currentIndex + 1;
};
```

Called in the template:
```razor
@foreach (var panel in upDockGroup!)
{
    @RenderEntry(panel)  @* ❌ @ref silently broken *@
}
```

## Symptoms

- `dotnet build`: ✅ 0 errors (the compiler generates valid C#)
- `dotnet test`: ✅ all 130 unit tests pass (no bUnit component tests exist)
- **Runtime crash** in browser:

```
JSException: Cannot read properties of null (reading 'removeAttribute')
TypeError: Cannot read properties of null (reading 'removeAttribute')
    at Module.detachDragHandlers (atlas.js:11:11)
```

- Stack trace points to `DragInterop.DetachDragHandlers` called from
  `ToolBar.OnAfterRenderAsync`
- The `ElementReference` passes the `Equals(default(ElementReference))` check
  (it's NOT default), but the underlying DOM element ID doesn't exist in the
  browser's DOM

## Root Cause

Blazor's `@ref` directive relies on the Razor compiler generating specific
`RenderTreeBuilder.AddElementReferenceCapture()` calls. When `@ref` appears
inside a `RenderFragment` lambda returned from a C# method, the generated
code captures a reference that the Blazor renderer cannot properly map to
the actual DOM element after diffing.

The `__builder` pattern generates a `RenderFragment` delegate, but the
Blazor rendering pipeline processes these differently from inline template
markup — the `AddElementReferenceCapture` sequence number and the internal
ID assignment don't align with the DOM elements Blazor creates.

## Verified Fix

1. **Keep all `@ref` assignments inline** in the main template. Accept template
   duplication as the necessary cost of correct ElementReference capture.

2. **Extract only display-only content** into helpers. The icon/text conditional
   (no @ref, no event handlers) is safe to extract:

```csharp
// ✅ SAFE — display-only, no @ref, no event handlers
private static RenderFragment EntryIcon(DockPanelModel panel) => __builder =>
{
    if (panel.Icon is not null)
        <span class="xd-toolbar-entry-icon">@panel.Icon</span>
    else
        <span>@GetInitial(panel.Title)</span>
};
```

3. **Wrap DetachDragHandlers in try-catch** as defense-in-depth against stale
   ElementReferences from Blazor's DOM diffing:

```csharp
try
{
    await DragInterop.DetachDragHandlers(JS, elRef);
}
catch (JSException)
{
    // DOM element no longer exists — nothing to detach.
}
```

4. **Trim stale entries** from `_entryRefs` and `_entryPanelIds` in
   `OnParametersSet` to prevent unbounded growth when panels move between sides.

## Key Takeaway

`@ref` + `RenderFragment` from C# methods = silent Blazor runtime failure.
Only inline `@ref` in the main `.razor` template. When duplication is
unavoidable, prefer it over broken ElementReference capture.
