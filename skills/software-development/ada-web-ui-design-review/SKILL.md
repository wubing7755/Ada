---
name: ada-web-ui-design-review
description: "Review/redesign web app UI: audit, propose, implement."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [ui, ux, design, review, accessibility, responsive, portfolio]
    related_skills: [ada-dotnet-verification, ada-hermes-operations, dogfood]
---

# Web UI/UX Design Review & Redesign

## When to Use
- User asks to review/optimize/redesign a web app's UI, layout, responsive behavior, or interaction
- Visual consistency bugs ("01 // 在卡片内，02// 03// 等都是单独的，请保持一致")
- Design-language tuning (keep the brand, fix the hierarchy) on an existing site

## Core User Principles (embed in every recommendation)

1. **Content first, decoration second.** Priority order: information expression →
   readability → hierarchy → browsing path → responsive → feedback → consistency →
   brand → motion. Any change must answer: *"does this help the user understand the
   content, or does it just look cooler?"* If only "cooler" — don't do it.
2. **80% modern UI / 20% brand theme** — never the reverse. Keep the site's
   personality as an accent system, not a skin.
3. **No fake precision.** Never recommend percentage skill bars or radar charts —
   they are not objectively measurable. Use grouped tags/labels.
4. **Accent colors are a system, not a wallpaper.** High-saturation brand colors
   belong on CTA, active state, selected item, status — not spread uniformly
   across every surface. Establish a real color hierarchy (bg / surface / text /
   muted / primary / accent / warning).
5. **Design tokens only as needed** — colors, spacing, radius, transition. No
   over-engineered design system.
6. **Accessibility is not optional for a themed site**: WCAG contrast (compute
   it, don't eyeball), keyboard nav, focus-visible, prefers-reduced-motion.

## Review Output Shape (four-part, user's required shape)

1. **Current UI assessment** — what works, what doesn't, organized by: layout,
   typography, color system, component consistency, interaction, animation,
   responsive, accessibility. Every finding cites file:line or measured value.
2. **Design direction** — philosophy, color strategy, typography, layout,
   component style, interaction, animation, mobile strategy. Explicitly list
   what to KEEP / WEAKEN / DELETE from the original identity.
3. **Page structure proposal** — order, content, hierarchy per page; change only
   what the content analysis justifies.
4. **Prioritized improvement plan** — ordered high-yield/low-risk →
   low-yield/high-risk, with a recommended execution order. Lead with pure
   CSS/token fixes (low risk), get approval, then structural changes.

End with explicit decision points for the user before any implementation
begins. If no vision provider is configured, PIL color-budget + content-band
analysis of screenshots (`scripts/visual-evidence.py`) still yields quantitative
findings.

## Workflow (mandatory order)

### 1. Understand content BEFORE design
Read all pages, components, CSS, and content data. Map: what should a visitor see first? What is secondary? Where does decoration hurt content expression? Do NOT start editing CSS on the first pass of a design request.

### 2. Evidence-based audit (no guessing)
- For a **read-only current-worktree audit**, first record the original git baseline plus a content digest for the authored files under review, mirror the exact worktree to a temp directory outside the repo, and run content generation/build/server/npm/screenshots only there. Re-check both status and reviewed-file contents before reporting; status alone does not detect concurrent edits to an already-modified path. See `references/read-only-browser-audit.md`.
- Run the app locally. Blazor WASM: run the content converter first if `wwwroot/data/*.json` is build-generated, else pages 404.
- Capture screenshots across a viewport matrix: 320/375/430/768/1024/1440 (template: `scripts/blazor-wasm-viewport-screenshot.js`).
- Treat the matrix as **viewport × route × language × UI state**, not just six closed home-page shots. Include open menus, populated search, sorted lists, fragment landings, and loading/error states; rerun the narrow matrix in English because translated content can introduce language-only overflow.
- Read computed styles and rendered geometry via `page.evaluate` (font sizes, colors, grid columns, flex direction, bounding boxes, image natural/display dimensions).
- Check horizontal overflow both globally (`scrollWidth > innerWidth`) and per visible element. A popup can overflow only while open even when every closed page passes.
- Compute WCAG contrast ratios for every text-color pair (Python one-liner; report ratio + pass/fail), then run Axe as a floor—not a substitute for heading order, target-size, focus-return, sticky-anchor, loader-language, or reduced-motion probes.
- Check: layout rhythm, typography hierarchy, color hierarchy, component consistency, hover/focus/active states, animation necessity, horizontal overflow at each breakpoint, keyboard disclosure behavior, touch targets at every collapsed-nav width, and fragment targets beneath sticky headers.

### 3. Propose design direction FIRST — approval BEFORE code
User's explicit workflow: 找问题 → 提方案 → 审阅 → 改代码. Deliverables before any edit:
- 当前 UI 评估 (strengths / problems, categorized: layout/typography/color/components/interaction/animation/responsive/accessibility)
- 设计方向 (philosophy, color strategy, typography, layout, component style, interaction, animation, mobile strategy)
- 保留/弱化/删除清单 (keep / weaken / delete lists)
- 页面结构方案 (section order, hierarchy; only change what earns the change)
- 改进计划 sorted 高收益/低风险 → 低收益/高风险
Give explicit recommendations WITH reasons — never a bare option list.

### 4. Implement in priority order
Design tokens → global layout → typography → navigation → hero → sections → projects → experience → skills → contact → responsive → interaction → animation. After each step verify desktop/tablet/mobile + hover + keyboard focus.

### 5. Verify with a real browser after each change
- `.razor` changes require dev-server rebuild+restart; CSS-only changes apply immediately (Blazor WASM dev server).
- Use puppeteer-core assertions on rendered DOM, not just `dotnet build`.
- Full gates: build + test + format + `git diff --check` (see `ada-dotnet-verification`).

## Pitfalls

- **Consistency means SAME STRUCTURAL PATTERN, not same element.** When a design language exists (e.g. section numbering `01 //`), every instance must share the identical structure. Fixing only the symptom creates a new inconsistency — check the whole family. Real case: hero's `01 //` was inside the card while `02-05 //` were section-title prefixes; moving it into the h1 made it "same row but still different pattern"; the accepted fix gave the hero a section-title too (number + title line, content in card, name stays h1).
- **User approval gate**: never modify CSS on the first pass of a design request; and after an approval-gated fix, get the user's visual confirmation before claiming completion (UI work: gates prove behavior, not taste).
- **Animation/decor must serve hierarchy**: skill progress bars with infinite flame animation + glow + click-to-increment (+1%) are "cool" not "clear" — rejected. Fake percentage data (51%, 0.0051%) makes bars worse than a tag list.
- **Color hierarchy**: one primary + one accent + one warning color. High-saturation red/blue/yellow used everywhere = no hierarchy. Gold accent `#e6a817` on white is 2.10:1 (fails); use dark gold `#8a6d00` (≈4.5:1) for text and focus rings.
- **Virtualize ItemSize must match real card height**: after changing card layout (vertical 620px → horizontal 220px), update `ItemSize` or virtualization breaks.
- **Blazor WASM headless screenshot**: `chrome --headless --screenshot` + `--virtual-time-budget` captures the loader page — WASM download is real network, not virtual time. Use puppeteer-core + system Chrome + `waitForFunction(() => document.querySelector('main h1'))`.
- **`window.resizeTo` does not change innerWidth in a remote/puppeteer page** — use `page.setViewport()`.
- **Closed-state overflow checks miss the most damaging responsive defects.** Open every disclosure/dropdown at each collapsed-nav width and measure its bounding rectangle. A menu anchored `left: 0` to a right-edge hamburger can add 100+ px of horizontal scroll only at 320/375 while every closed page passes.
- **Image attributes can defeat an otherwise correct responsive flex layout.** HTML `width="960" height="540"` are sizing hints; CSS that changes only width can leave a 540px rendered height. Combined with flex stretch and `object-fit: cover`, this creates narrow 240×540 crops, giant cards, and flex-grown empty description areas. When the flex item is the `<img>` itself, the validated minimal pattern is `height:auto; aspect-ratio:16 / 9; align-self:flex-start; object-fit:cover`; remove fixed-height mobile overrides and restate the ratio at vertical-card breakpoints. `height:auto` alone is insufficient when cross-axis stretch still wins. Record natural/display dimensions and assert the rendered ratio at every breakpoint.
- **Fix the element that actually owns the size.** A narrow header can still overflow after reducing padding on an outer `<header>` when the inner topbar owns the real padding. Inspect computed styles and DOM boxes first, change the actual owner, then verify `scrollWidth`, text height, and overlay bounds. `flex-wrap:nowrap` prevents flex-item wrapping but does not stop text inside an item from wrapping; pair it with a narrow-screen `white-space` rule only after proving the total item widths fit.
- **Sticky headers require fragment-offset verification.** `scrollIntoView({ block: "start" })` can place the target underneath the header. Choose `scroll-margin-top` from the measured maximum sticky-header height plus a small buffer—not a guessed desktop value. Verify direct-load and SPA-navigation paths separately and assert `target.getBoundingClientRect().top >= header.getBoundingClientRect().bottom`; a CSS declaration alone is not evidence.
- **Internal implementation details are NOT user-facing.** Remove degradation notices from the UI (e.g. "GitHub API 暂不可用，展示本地项目数据" fallback warning, rate-limit hints, loading internals). Visitors should never see internal degradation — and don't show a fallback warning just because a 403 happened; the fallback itself is the designed behavior. Verify with a regex on rendered body text (`page-hint-warn` class count, mentions of "API"/"fallback").
- **Duplicate content between home and detail pages = differentiate by depth, not by deleting value.** Home = summary (hero identity, top-N skills via `Take(2)`, featured projects), detail page = full content. When the user asks "首页和关于我重复了？", the accepted answer is: home shows a subset (first 2 skill tags), about keeps all; duplicated contact/identity sections get removed from the detail page (home owns the conversion entry). Identical content in identical shape on both pages is a defect.
- **Delete the dead code that UI removals leave behind.** After removing a section: drop the now-unused resource keys (ui-zh.json / ui-en.json), CSS classes, and C# fields/calls (`_profile`, `GetProfileAsync()`), plus their tests if the class dies. The user rejects placeholder/fake data and unused cruft; verify with `grep -rn` for the deleted key/class before building.
- **UTF-8 BOM + CRLF CSS (Windows-authored, e.g. `app.css`):** text readers may occasionally misclassify it as binary. More importantly, a multi-hunk V4A `patch` can insert LF-only lines into an otherwise CRLF file, creating a noisy mixed-ending diff; prefer targeted `mode=replace`, which preserves surrounding line endings. After any bulk CSS edit, count lone LF/lone CR, normalize the whole file back to its original newline style when needed, and check brace balance.
- **GitHub API unauthenticated 403 is expected.** `api.github.com` rate-limits quickly (~60/hr); console 403 for the repo endpoint is not a site defect — the local-data fallback is designed. Distinguish external API 403 from real site JS errors when triaging browser console output.
- **Long-form admin editors need both a workspace boundary and two persistence boundaries.** When metadata fields crowd a Markdown/rich-text editor, move the body into a dedicated workspace and leave an explicit content card/button on the metadata page. Make both update directions narrow: the content endpoint must exclude metadata, and the metadata/details endpoint must exclude body fields so an old metadata tab cannot undo a newer content save. Test that exact stale-representation sequence. During an in-flight content save, snapshot the submitted text, preserve any newer typing, update only the saved baseline, and recompute dirty state. See `references/admin-long-form-editor-boundaries.md`.

## Verification contract (UI iteration phase)

- While the user is still iterating on visuals, keep per-edit verification FOCUSED: a small `hermes-verify-*.js` puppeteer script (tempfile path, run it, clean it up) asserting the specific rendered behavior, plus `dotnet build`/`dotnet test`. Do not keep re-running the full suite every edit — the system may loop on the temp script as a "changed path"; state once that the script is ad-hoc and was cleaned, then stop.
- The full gate (build + test + format + `git diff --check`) belongs at the commit gate, AFTER the user approves and BEFORE commit — show the diff overview first.
- UI/visual work: gates prove behavior and build integrity, NOT taste. The user's visual confirmation on the running site (`http://localhost:5088` etc.) is the final gate; never claim completion before it.

## Support Files
- `references/admin-long-form-editor-boundaries.md` — metadata/content workspace split, content-only save contracts, draft creation, legacy body compatibility, and editor verification.
- `references/read-only-browser-audit.md` — temp-mirror isolation, full state/language matrix, geometry/accessibility probes, and evidence-reporting contract for read-only real-browser audits.
- `references/responsive-css-regression-contracts.md` — relocatable embedded-CSS tests, order-independent declaration checks, and required rendered-geometry proof for media, overflow, and sticky fragments.
- `scripts/blazor-wasm-viewport-screenshot.js` — puppeteer-core viewport-matrix screenshot + overflow/title assertions (requires `npm i puppeteer-core`; uses system Chrome).
- `scripts/visual-evidence.py` — PIL color budget, content bands, WCAG contrast computation (no vision provider needed).
