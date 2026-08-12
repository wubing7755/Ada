# HTTP Fake-Handler Design Traps (Blazor WASM service tests)

Lessons from a real dual-mode Blazor WASM project (`ApiContentSource` / `AuthService` / `AppConfigService`)
tests. These are generic to any `HttpClient`-fake based unit test, surfaced here in the
Blazor WASM service-testing context.

## Trap 1: an `object`-typed helper overload silently serializes raw responses

A fake with `OnJson(method, path, object body)` plus `OnJson(method, path, string json,
HttpStatusCode status)` — calling `OnJson("GET", "api/posts/X", new HttpResponseMessage(NotFound))`
binds to the `object` overload and `JsonSerializer.Serialize(HttpResponseMessage)` returns
**200 with garbage JSON**. The detail lookup then deserializes an empty DTO (`Id == ""`)
instead of 404ing, and the "404 fallback" path in product code never runs — the test fails
with a confusing `Assert.Equal("post-1", "")`.

**Fix**: give raw-response registration its own clearly-named method
(`On(method, path, Func<HttpRequestMessage, HttpResponseMessage>)`); never let a
`HttpResponseMessage` flow into a JSON-body overload. When a test failure shows an
unexpected empty object, check whether the fake returned a serialized response object.

## Trap 2: route fakes by `PathAndQuery`, not `AbsolutePath`

`request.RequestUri.AbsolutePath` strips the query string — every paged/filtered call
(`api/posts?postType=article&page=1&pageSize=100`) collapses to the same route key and the
fake returns the first registered response for all of them. Use
`request.RequestUri.PathAndQuery.TrimStart('/')` so query params are part of the route
identity, and register fixtures with the exact query string the code emits.

## Trap 3: pagination fixtures must make pageSize match item counts

Product loop stops when `items.Count < dto.PageSize`. A fixture that claims
`"pageSize":100` but returns 2 items terminates after page 1 — the "merge N pages" test
silently never exercises page 2. Simulate real paging: return `"pageSize":2` with 2 items
on page 1, then 1 item on page 2.

## Trap 4: list fixtures need type-discriminating fields

Mapping code branches on DTO fields (e.g. `postType` → frontend `Type`). A fixture that
only sets `{"slug":"a1"}` maps to the DEFAULT type (`blog`) and an `Assert.Contains(p =>
p.Type == "thought")` fails with "Filter not matched". Include the discriminator field in
every fixture item.

## Trap 5: assert cache behavior as "no new requests", not an absolute count

A service that loads a config file (1 request) then fetches two paged lists (2 requests)
makes a first call total of 3 — asserting `RequestCount == 2` fails even though caching is
correct. Capture `afterFirst = handler.RequestCount`, run the cached call, then assert the
count is unchanged.

## Verification workflow

- A fake-handler bug and a product bug look identical from the assertion output. When a
  new test fails, print/inspect the fake's captured request path and response body BEFORE
  changing product code.
- Contract-test the cross-cutting fix (e.g. "all API calls go through ResolveApiUrl") by
  asserting the source string of the component, since unit tests with `BaseAddress =
  localhost` cannot catch origin-resolution mistakes.
