# Blazor-Specific Refactoring Patterns

When refactoring `.razor` files to engineering-grade quality, these patterns address the unique constraints of Blazor's component model.

## Template Duplication → Child Component

When a `.razor` template repeats a markup block ≥2× with different data, extract it into a child component:

```razor
@* Extract: ToolBarEntry.razor *@
<div class="xd-toolbar-entry-wrapper @(IsAutoHidden ? "xd-autohidden" : null)"
     @onmouseenter="() => OnMouseEnter.InvokeAsync(Panel.Id)">
    <button class="xd-toolbar-entry @ActiveClass" @ref="_elRef"
            @onclick="() => OnClick.InvokeAsync(Panel.Id)">
        @if (Panel.Icon is not null) { <span>@Panel.Icon</span> }
        else { <span>@GetInitial(Panel.Title)</span> }
    </button>
</div>
@code {
    [Parameter, EditorRequired] public DockPanelModel Panel { get; set; } = null!;
    [Parameter] public EventCallback<string> OnClick { get; set; }
    private ElementReference _elRef;
    public ElementReference ElementRef => _elRef;
}
```

**Known Blazor constraint**: `@ref` on a RenderFragment cannot capture ElementReference from the parent. Expose via a public property on the child component instead.

## Inline Declarations → Computed Properties

Move logic out of inline `@{}` blocks into `@code` computed properties:

```razor
@* ✗ Inline *@
@{ var upperGroups = UpperSectionPanels.GroupBy(...).ToList(); }

@* ✓ Property *@
@code { private IReadOnlyList<...> UpperGroups => UpperSectionPanels.GroupBy(...).ToList(); }
```

This makes the template cleaner and the logic testable/refactorable independently of the markup.

## Lifecycle Sequence → Named Methods

When `OnInitialized` (or other lifecycle methods) does 3+ things, extract into named helper methods:

```csharp
protected override void OnInitialized()
{
    _context = Context ?? new LayoutContext(State);
    _style = new LayoutStyleAdapter(State);
    SubscribeToEvents();
}
private void SubscribeToEvents() { ... }
```

Each named method should do exactly one thing. The lifecycle method becomes a readable sequence of intent-revealing calls.

## Common Blazor Pitfalls in Refactoring

- **`@key` on re-registering components** — Without `@key`, Blazor reuses component instances across parameter changes, keeping stale `_registered` boolean flags that prevent re-registration.
- **`@ref` parameter naming** — `@ref="ref => ..."` fails because `ref` is a C# keyword. Use a different parameter name: `@ref="elRef => ..."`.
- **Delegate calls with value types** — `@onclick="@(() => OnHeaderClick(activePanel.Id))"` fails CS1503 when `Id` is a strong type. Use `.Value` to get the primitive.
- **Ternary type inference with value types** — `var current = hasPanels ? somePanel.Id : null;` fails CS0173. Use `.Value` on the strong-typed side.
