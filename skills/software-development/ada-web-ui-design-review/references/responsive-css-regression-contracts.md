# Responsive CSS Regression Contracts

Use this pattern when a responsive defect needs a cheap static guard in addition to real-browser verification. Static CSS contracts catch accidental declaration removal; they do not prove rendered geometry.

## Make the CSS test relocatable

Do not locate repository files by walking upward from `AppContext.BaseDirectory`. That fails when the test output is copied, packaged, or executed outside the checkout.

Embed the real stylesheet in the test assembly:

```xml
<ItemGroup>
  <EmbeddedResource Include="..\..\src\App\wwwroot\css\app.css"
                    LogicalName="App.Tests.TestAssets.app.css" />
</ItemGroup>
```

Read it by the exact logical name:

```csharp
private const string CssResourceName = "App.Tests.TestAssets.app.css";

using var stream = typeof(ResponsiveCssTests).Assembly
    .GetManifestResourceStream(CssResourceName);
Assert.NotNull(stream);
using var reader = new StreamReader(stream!);
var css = reader.ReadToEnd();
```

Verification must include copying the complete test output directory outside the repository and executing the focused test from there. This proves there is no hidden checkout-path dependency.

## Parse declarations without ordering assumptions

CSS allows one selector to appear in multiple rules. A contract helper should:

1. collect every exact selector match;
2. concatenate the rule bodies;
3. assert `property: value` independently of declaration order;
4. scope breakpoint assertions to the intended media query.

Do not use one regex that assumes `right`, `left`, and `max-width` appear in a fixed order. Do not read only the first matching selector block.

## Useful static contracts

- narrow header: actual padding owner, `white-space`, fixed control widths, menu anchoring;
- media: `height:auto`, `aspect-ratio`, `align-self`, breakpoint overrides;
- min-content overflow: `min-width:0` on the relevant flex chain and `overflow-wrap:anywhere` on long user content;
- fragment targets: `scroll-margin-top` on every real target selector.

## Required real-browser proof

Run the published artifact at `320 / 375 / 430 / 768 / 1024 / 1440` and assert:

- `documentElement.scrollWidth <= innerWidth` in both closed and opened UI states;
- image displayed ratio matches natural ratio (record rendered width and height, not only CSS text);
- narrow text is one line by measured height, not merely because a `nowrap` declaration exists;
- direct-load and SPA fragment navigation both satisfy `target.top >= stickyHeader.bottom`;
- language-specific long content does not overflow;
- console, page, HTTP, and request errors are empty.

For `<img width height>` inside a flex row, a validated minimal correction is usually:

```css
.media {
    width: 240px;
    height: auto;
    aspect-ratio: 16 / 9;
    align-self: flex-start;
    object-fit: cover;
}
```

At a vertical-card breakpoint, remove any fixed crop height and restate `height:auto` plus the intended aspect ratio. `height:auto` alone may still be defeated by flex cross-axis stretching, hence the explicit `align-self` and rendered-ratio assertion.
