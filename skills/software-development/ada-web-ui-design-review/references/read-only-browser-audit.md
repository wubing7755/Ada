# Read-only real-browser UI audit playbook

Use this when the user asks for an independent audit of the **current worktree** and forbids repository edits.

## Isolation contract

1. Record the original repository baseline (`HEAD`, branch, `git status --short`, changed-file list) **and a content digest for the authored files under review**. A hash of `git status --porcelain` is insufficient because it hashes path/status records, not file contents; a concurrent editor can change an already-modified file without changing that hash.
2. Mirror the current worktree to a unique temp directory outside the repository. Include tracked modifications and untracked assets; exclude `.git`, `.vs`, `bin`, `obj`, and test outputs.
3. Confirm key reviewed files byte-match the mirror before running evidence. If the implementation may still be changing, recompute the authored-file digest before reporting; on drift, create a fresh mirror and rerun every affected static/test/browser probe.
4. Run content generation, restore, build, dev server, npm installs, browser harnesses, screenshots, and reports only in that temp area.
5. Serve the temp mirror, not stale output from the original checkout.
6. At the end, compare both repository status and reviewed-file contents to the baseline and state explicitly whether repository files changed during the audit and whether those changes came from the auditor.

This is stronger than saying “read-only”: it makes generated `wwwroot/data`, `bin/obj`, screenshots, and ad-hoc scripts physically unable to dirty the reviewed worktree.

## Test matrix: dimension × route × language × state

A closed-page viewport matrix is insufficient. Cover:

- Widths: 320, 375, 430, 768, 1024, 1440.
- Every relevant route and data state.
- Both languages. Run the complete narrow-width matrix in English too: long translated copy can overflow where Chinese does not.
- Stateful variants: mobile menu closed/open, sorted/filtered lists, populated search results, fragment landings, loading/error states.
- Keyboard variants: disclosure opened by Enter, Tab into contents, Escape from a child, route-change focus, and focus after leaving the disclosure.

For every state collect both a screenshot and DOM/computed-geometry evidence. A defect that exists only when a menu is open will be invisible to closed-state overflow checks.

## Deterministic browser probes

### Horizontal overflow

Record all three:

```js
({
  innerWidth,
  clientWidth: document.documentElement.clientWidth,
  scrollWidth: document.documentElement.scrollWidth,
})
```

Then enumerate visible elements whose bounding rectangle crosses the viewport. For overlays, record the trigger and popup rectangles before judging the screenshot. Subpixel values around the edge should be interpreted with a small tolerance (for example 0.5 px).

### Responsive header and disclosure

Measure each direct topbar child, unique flex lines, sticky-header height, popup rectangle, and `aria-expanded`. Verify:

- no second flex line unless intentionally designed;
- the popup remains inside the viewport at every collapsed-nav width;
- Escape closes and returns focus while focus is in the disclosure;
- behavior after focus moves outside or an outside pointer click;
- collapsed menu links still meet the touch-target requirement at *all* widths where the nav is collapsed, not only the smallest media query.

### Image/card geometry

For each rendered image record `naturalWidth/naturalHeight` and displayed `width/height`, plus the containing card height. Compare aspect ratios rather than trusting `object-fit`.

Important pitfall: HTML `width`/`height` attributes are presentational sizing hints. If CSS changes only width inside a flex row, the attribute-provided height can remain 540 px; flex stretch plus `object-fit: cover` then produces a 240×540 crop and forces the whole card tall. Mobile rules that set a fixed `height: 200px` can create the opposite extreme at wide tablet widths. Always verify the actual box at both sides of the breakpoint.

### Sticky-header fragment landing

After clicking the real link and waiting for async content, compare:

```js
const target = document.getElementById(location.hash.slice(1)).getBoundingClientRect();
const header = document.querySelector('header').getBoundingClientRect();
({ targetTop: target.top, headerBottom: header.bottom,
   obscured: target.top < header.bottom && target.bottom > 0 })
```

`scrollIntoView({block:'start'})` is not sufficient with a sticky header. Test both same-page links and cross-route search-result anchors. Look for `scroll-margin-top` or an equivalent offset.

### Accessibility beyond Axe

Axe is a floor, not the audit:

- Capture heading order; a page can pass Axe while rendering H2 before its H1.
- Measure standalone touch targets. Ignore programmatically focused headings with `tabindex=-1`; they are not pointer targets.
- Distinguish WCAG AA 24 px exceptions from a product-specific 44 px acceptance rule. Report both accurately.
- Probe focus outline width/color/offset after keyboard input.
- For every internal `overflow:auto|scroll` region, record `tabIndex`, accessible role/name, and a keyboard scroll attempt. A text-only preview with `tabIndex=-1` can be mouse-scrollable yet unreachable to a sighted keyboard user.
- Compare active/inactive toggle styles and enabled/disabled action styles using computed color, border, opacity, cursor, and geometry. Move the automation pointer away before measuring: a lingering `:hover` state can falsely look like the selected modifier works.
- Test `prefers-reduced-motion` against runtime UI and the pre-WASM loader.
- To inspect the static loader, abort `_framework` requests so the loader remains mounted; then verify visible text, accessible name, document `lang`, and computed animation state.

### Bilingual leakage

After switching to English, inspect rendered content—not only UI resource keys. Search visible text for CJK runs while excluding intentional language-switch labels, visually hidden “new window” text if localized, and hidden error UI. Common leaks are taxonomy tags or skill names modeled as a single string while group names are localized.

## Reporting contract

- Lead with PASS/FAIL and merge recommendation.
- Sort findings by severity.
- For each finding include: route/state/viewport/language, exact measured evidence, user impact, and source `file:line` chain.
- Separate failures from verified passes (console, search, sorting, focus, contrast, reduced motion, image load).
- State untestable states caused by genuinely empty current data.
- Keep screenshots as corroboration; measurements and reproduction steps are the primary evidence.
