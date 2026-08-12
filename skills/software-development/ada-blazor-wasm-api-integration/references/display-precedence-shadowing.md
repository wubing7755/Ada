# Display-Precedence Shadowing — "edit saved but page still shows old text"（真实项目，2026-08）

Symptom sequence that led here (after the session-cache fix, Pitfall 7):

1. User edited post body in Admin → public detail page showed the new body. ✓
2. User edited post SUMMARY/intro in Admin → list cards still showed the OLD
   intro. ✗ No cache involved — backend DTO, DB, and frontend model all
   carried the new value.

## Root cause

Two fields target the same display slot on list cards:

| field | source | always non-empty? |
|---|---|---|
| `Intro` (`Post.Intros` ← `SummaryZh`) | hand-written by author | no |
| `Excerpt` (`Post.Excerpts` ← `BodyExcerpt`) | derived by backend from markdown | **yes** (any post with a body) |

The original razor logic was:

```razor
@if (!string.IsNullOrEmpty(Excerpt)) { <p class="post-intro">@Excerpt</p> }
else if (!string.IsNullOrEmpty(Intro)) { <p class="post-intro">@Intro</p> }
```

Because `Excerpt` is non-empty for every post with a body, the first branch
always wins and the hand-written intro is dead code. Editing `SummaryZh`
looks like a no-op to the user.

## Why it was mistaken for a cache bug

Same observable symptom ("I saved it but the page didn't change"), and it
happened immediately after the cache fix, so the natural hypothesis was
"cache not fully removed". The debug ladder that resolved it:

1. Verify the backend is NOT stale (curl the API / check DB) — it wasn't.
2. Trace which frontend field the UI actually renders — `PostListItem.razor`
   showed `Excerpt` first.
3. Conclude: display precedence, not data staleness.

## Fix

Invert precedence; extract the decision as a pure function so it is
unit-testable without bUnit (this repo has no bUnit by decision):

```razor
@if (!string.IsNullOrEmpty(DisplayIntro)) { <p class="post-intro">@DisplayIntro</p> }
...
private string DisplayIntro => SelectIntro(Intro, Excerpt);

public static string SelectIntro(string? intro, string? excerpt)
    => !string.IsNullOrWhiteSpace(intro) ? intro.Trim() : (excerpt ?? "");
```

Tests (`PostListItemSummaryTests`, 4 cases): intro wins when both present;
fallback to excerpt when intro empty; empty when both missing; whitespace-only
intro treated as missing.

## Rules for this class of bug

- Hand-authored intent (intro/summary/description) should WIN over any
  derived/auto-extracted field for the same slot; derived is the fallback.
- Do not silently drop the hand-written field when a derived field is added
  later — that is exactly how this bug was born (BodyExcerpt was added for
  API mode, and the `if` was written excerpt-first "because API mode has it").
- Distinguish the list-card semantic (intro-first) from the detail-page
  semantic (intro only when no local body) — they are NOT the same rule.
- When a user reports "edited X, page still shows old X" AFTER a cache fix,
  check display precedence before assuming another caching layer.
