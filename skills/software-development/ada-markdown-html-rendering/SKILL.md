---
name: ada-markdown-html-rendering
description: "Markdown renders wrong: images stripped, numbering lost."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [markdown, markdig, htmlsanitizer, ganss-xss, rendering, sanitization]
    related_skills: [ada-dotnet-verification, ada-blazor-wasm-api-integration, ada-data-migration-delivery-audit]
---

# Markdown → HTML Rendering Pitfalls

## When to Use

- Rendering imported/blog-exported Markdown (blog exports, WordPress, pasted HTML) to safe HTML
- Debugging "images missing from rendered post" or "ordered list shows 1. 1. 1." in a browser
- Building or repairing a Markdig + HtmlSanitizer (Ganss.XSS) whitelist render pipeline
- Re-rendering stored content after a renderer change, or writing sanitizer/renderer regression tests

Rendering imported or user-written Markdown to safe HTML with a Markdig-style
renderer plus a whitelist sanitizer (Ganss.XSS `HtmlSanitizer`) is NOT
lossless. Three silent data-loss/format bugs recur and are only caught in a
real browser, because unit tests use clean Markdown syntax while real content
(blog exports, pasted HTML) uses raw HTML blocks and unusual list structure.

Core discipline: **render-then-sanitize is a two-stage pipeline; verify what
the sanitizer does to HTML the renderer emits, not what the renderer emits in
isolation.** Reproduce with the REAL source document (or a faithful snippet),
not a hand-written clean example — clean examples pass while real content
breaks.

## Frontend pipeline (markdown-it + DOMPurify) — display rendering since 2026-08

Display rendering no longer runs through Markdig + HtmlSanitizer: the site moved
it client-side to `markdown-it` + `DOMPurify` + `markdown-it-anchor` +
`highlight.js` (esbuild IIFE bundle exposing `window.MarkdownRenderer.render/renderHtml`,
invoked from Blazor via `MarkdownRenderService`). Backend Markdig is retained
ONLY for build/import-time helpers: fetched-HTML sanitize (`Sanitize`), excerpts
(`PlainTextExcerpt.ExtractFromMarkdown`), search index text. Verified facts:

- **List numbering**: markdown-it natively emits `<ol start="N">` for lists split
  by code blocks — the backend ordered-list hacks are deleted, not ported.
- **div-wrapped img**: `html:true` preserves `<div align="left"><img>`;
  DOMPurify default allows div/img — no whitelist surgery needed.
- **Chinese anchors**: markdown-it-anchor URL-encodes slug ids (`%E6%A8%A1...`),
  which do NOT match blog-export author-written `#中文锚点` hrefs — safe because
  backup markdown posts contain zero `](#` links (DB scan verified). If a
  future post adds `](#)` links to markdown, slugify needs a compatibility
  config; posts whose body is raw HTML (legacy dual-track) keep blog-export ids +
  `anchor-navigation.js` `decodeURIComponent` (href URL-encoded, id raw Chinese
  → match works).
- **Node smoke**: DOMPurify needs a DOM — smoke script runs the bundle under jsdom.
- **Snapshot export**: when posts have in-site detail pages (e.g. `/blog/{id}`),
  export local body for EVERY post with one — never exclude by ExternalUrl.
  Excluding blog entries breaks static-mode parity (api mode always carried the
  markdown; the snapshot then renders nothing in static mode).

Full executed architecture and the dual-track data contract are covered in the four pitfalls below; the project-specific pipeline references are intentionally not distributed.

## Pitfall 1: Disallowed wrapper tag removes its whole subtree

**Symptom**: images missing from rendered post; DB BodyHtml has no `<img>` at
all even though the source Markdown has 40 of them.

**Root cause**: blog-export Markdown wraps images in raw-HTML containers such
as `<div align="left">`. `HtmlSanitizer` drops tags not on `AllowedTags` —
and in this configuration drops the **entire subtree**, including the
whitelisted `<img>` inside. A standalone `<img>` survives; the same `<img>`
inside a disallowed `<div>` vanishes. Div isn't a security risk; it's just
not in the whitelist.

**Fix**: add the wrapper container tags used by your content (`div`,
`figure`, `figcaption`, …) to `AllowedTags`. The sanitizer then strips only
disallowed attributes (`align`, `style`, …) and keeps children. Verify with a
test that uses the REAL structure: `<div align="left">\n<img src="..."\nwidth="550px"\nalt="..." />\n</div>`.

## Pitfall 2: Blocks split ordered lists → browser shows 1. 1. 1.

**Symptom**: rendered ordered list shows every item as `1.`; the source
numbered them 1, 2, 3.

**Root cause**: CommonMark renders `1. a` + (blank line) + code/div block +
(blank line) + `2. b` as **two separate `<ol>` elements**, each restarting at
1. Blog exports frequently place a fenced code block or an image `<div>`
between list items.

**Fix (two-part, both verified)**:
1. **Pre-process**: when a fenced code block sits between two ordered-list
   item lines, indent the whole block by 4 spaces — Markdig then treats it as
   content of the previous item and keeps the list continuous. (Indenting a
   `<div>` the same way does NOT work — it silently drops the div content.)
2. **Post-process**: restore source numbers on whatever lists still got
   split/merged (see Pitfall 3) with `<ol start="N">` / `<li value="N">`,
   applied **after** sanitization so the attributes aren't stripped.

## Pitfall 3: Markdig merges adjacent items and drops source numbers

**Symptom**: source uses segmented numbering (`1. a`, `2. b`, then `1. c`,
`2. d` — a common segmented-numbering style) but rendered output shows `1. 2. 3. 4.`.

**Root cause**: Markdown list numbers are formatting, not content. Markdig
merges adjacent items with no block between them into one `<ol>` and
renumbers from 1 — the source's `2. 1. 2.` intent is lost.

**Fix**: collect source numbers while scanning the Markdown
(`^\s*(\d+)[\.)]\s+`), then post-process the sanitized HTML: first `<li>` of
an `<ol>` gets `<ol start="N">` when N != 1; later `<li>` gets
`<li value="N">` when N != previous+1. Regex over `<ol>…</ol>` with a
`<li>…</li>` inner pass is sufficient when content has no nested lists
(typical for blog bodies).

## Pitfall 4: In-page anchor links jump to the site homepage (Blazor WASM)

**Symptom**: clicking a content link like `[模块 3](#模块-3...)` navigates to the
homepage (`/`) or does nothing, instead of scrolling to the heading.

**Root cause** (three layers, all must be handled):
1. Sanitizer whitelist strips `id` from headings → anchor targets vanish. Add
   `id` (plus `class`, `lang`) to `AllowedAttributes` and keep it there.
2. Blazor WASM intercepts every `<a href="#...">` click as an internal route;
   `#锚点` parses to an empty path → navigates to `/`. Registering a click
   handler after `blazor.webassembly.js` loads is too late — Blazor's own
   listener wins.
3. `history.replaceState(null, '', '#xxx')` resolves the relative URL against
   `<base href="/">` → URL becomes `/#xxx`, losing the current path.

**Fix (verified)**: a dedicated `anchor-navigation.js` that
- listens at **window capture phase** (`window.addEventListener('click', handler, true)`),
- finds `a[href^="#"]`, `decodeURIComponent` the fragment, `getElementById`,
- on hit: `preventDefault()` + `stopPropagation()` +
  `scrollIntoView({behavior:'smooth', block:'start'})` +
  `history.replaceState(null, '', window.location.pathname + window.location.search + '#' + id)`.
- Load it in `index.html` **BEFORE `blazor.webassembly.js`** — the capture
  listener must exist before Blazor's click interception is registered.

## Verification pattern

- Unit tests must include the REAL structural forms: raw-HTML `<img>` with
  multiline attributes inside a `<div>`; list items split by code blocks;
  segmented numbering (`1. 2. 1. 2.`).
- After fixing the renderer, RE-RENDER stored content (rebuild/import step),
  then query the stored HTML: `<ol start="2">` present, `<img>` count equals
  source, no external-image `src` remains after localization.
- Remember `dotnet run --no-build` after editing the renderer library runs
  the STALE binary — rebuild first, or your "fix didn't work" twice in a row.

## References

本技能无独立 references：四个渲染陷阱（包装标签丢子树、列表分段、分段编号、页内锚点）与验证模式均在正文。
