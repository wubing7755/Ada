# SPA state and fault isolation patterns

Use these patterns when a Blazor WASM route loads multiple static JSON sources, derives state from query parameters, or performs post-render fragment scrolling.

## 1. Latest-request commit gate

A request version must guard both successful results and stale exceptions:

```csharp
public sealed class LatestRequestCoordinator
{
    private int _version;

    public async Task<bool> RunLatestAsync<T>(Func<Task<T>> request, Action<T> commit)
    {
        var requestVersion = Interlocked.Increment(ref _version);
        T result;
        try
        {
            result = await request();
        }
        catch (Exception) when (requestVersion != Volatile.Read(ref _version))
        {
            return false; // stale failure cannot break the current page
        }

        if (requestVersion != Volatile.Read(ref _version))
            return false;

        commit(result);
        return true;
    }

    public void Invalidate() => Interlocked.Increment(ref _version);
}
```

Required tests:

1. Start request A, then B; complete B and then A; only B commits.
2. Start A, invalidate, complete A; A does not commit.
3. Start A, then B; complete B; fail A; stale A returns `false` without surfacing its exception.
4. A current request exception still propagates.

## 2. Query lifecycle ownership

Use `[SupplyParameterFromQuery]` plus `OnParametersSetAsync`. The input handler updates the URL only; parameter processing launches the search. This prevents duplicate requests from two lifecycle paths.

When the query becomes blank:

- invalidate the current request generation;
- clear result state;
- do not let an in-flight result repopulate the page.

Browser verification should start a deliberately delayed query, immediately enter a second query, then wait beyond the first delay and assert that URL, input, and result DOM still represent the second query.

## 3. Section-level content boundaries

For independent page sections, load every source even when an earlier one fails. If the content service has a plain `Dictionary` cache, keep calls sequential unless the cache is made concurrency-safe.

Catch only expected content-boundary failures:

```csharp
catch (Exception exception) when (
    exception is HttpRequestException
        or JsonException
        or NotSupportedException
        or InvalidOperationException
        or TaskCanceledException)
{
    return null;
}
```

Do not expose raw exception messages to visitors. Render the existing empty-state copy for the failed section while preserving all successful sections.

## 4. Fragment completion semantics

A fragment helper should return:

- `true`: no hash, unsupported/ignored target, or successful scroll;
- `false`: recoverable JS interop failure, so a later render/navigation can retry.

Assign `_fragmentHandled` from the helper result. Reset it from `NavigationManager.LocationChanged` for same-route hash changes. A retry loop must be bounded; an unconditional `StateHasChanged` on every failure can spin forever.

## 5. Browser failure injection

When repeatedly reloading one origin and injecting failures into static JSON requests:

- disable the browser HTTP cache (`Network.setCacheDisabled`) or use fresh isolated browser contexts;
- verify the intended request actually received the injected status;
- allow that expected 500 in network evidence, but require zero unhandled runtime exceptions and zero unrelated console/network failures;
- assert that only the targeted section becomes empty and every other section remains populated;
- do not hard-code current content counts when availability (`> 0`) is the real contract.

This distinguishes a true section fault boundary from a false pass caused by cached JSON.
