# CSS contract scope and mutation verification

Use this when a .NET test embeds the production stylesheet and asserts responsive CSS declarations.

## Failure mode

A helper that regex-matches a selector across the entire stylesheet and concatenates every body crosses cascade boundaries. If the base `.project-image` rule regresses to `height:540px`, but the `@media` version still has `height:auto`, an assertion for `height:auto` can incorrectly pass.

## Scope discipline

1. Parse the root stylesheet and remove complete `@media` blocks with balanced-brace scanning.
2. Assert base/desktop declarations only against that root scope.
3. Extract the intended media block and assert responsive declarations only inside it.
4. Aggregate duplicate selector bodies only inside one already-isolated scope.
5. Keep a synthetic test such as:

```css
.project-image { height: 540px; aspect-ratio: 4 / 3; }
@media (max-width: 768px) {
  .project-image { height: auto; aspect-ratio: 16 / 9; }
}
```

The root extractor must retain `540px / 4:3` and exclude `auto / 16:9`.

## Mutation proof

A contract test is not proven strong merely because it passes the desired CSS. Run a disposable-copy mutation:

1. Run the exact focused test and require PASS.
2. Locate the intended root selector, not the first repeated declaration text in the file.
3. Mutate only that selector and assert exactly one replacement.
4. Rebuild the embedded resource and run the same focused test.
5. Require a non-zero exit and confirm the failure names the intended test/assertion.
6. Delete the disposable copy; never mutate the working tree for this probe.

A broad replacement that hits another selector is a verifier bug, not evidence that the contract is weak.

## Browser follow-up

CSS contracts do not prove rendered geometry. On the freshly published artifact:

- test every DOM variant that carries the same route/fragment contract (for example full and compact cards);
- verify direct deep links and SPA navigation from a real source such as search results;
- measure `target.top >= stickyHeader.bottom` and record the remaining gap;
- inspect the actual markup before writing selectors;
- disable HTTP cache when injecting resource failures or doing repeated full navigations;
- record console, runtime, request, and HTTP errors.

If the harness times out because its selector is wrong, or a mutation targets the wrong occurrence, the run is FAIL. Correct it and rerun rather than salvaging earlier partial output as a final PASS.
