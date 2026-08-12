# Admin Long-Form Editor Boundaries

Use this reference when redesigning an admin CMS/editor that mixes metadata fields with long-form Markdown or rich-text content.

## Core recommendation

Separate the workflow into two workspaces when the body is long enough to need sustained editing:

1. **Metadata workspace** — type, publication status, slug, titles, summaries, tags, cover, external link, publication date.
2. **Content workspace** — body editor, live preview, save state, and writing-specific navigation protection.

A card on the metadata page should be an explicit entry point into the content workspace, not a decorative wrapper around another embedded editor. Give it a clear button such as “Edit content” or “Save as draft and edit content.”

## Why the persistence boundary matters

A separate page is not enough. If the content page loads a full article DTO and later sends the full DTO back, it can overwrite metadata changed elsewhere with stale values.

Prefer a narrow update contract such as:

```http
PUT /api/admin/posts/{id}/content
Content-Type: application/json

{
  "bodyMarkdown": "..."
}
```

The handler should update only body-owned fields and the modification timestamp. Tests must record all metadata before the request and assert every unrelated field remains unchanged afterward.

The **inverse boundary is equally important**: after splitting the workspaces, the metadata page must not keep sending a stale full-record DTO containing `BodyMarkdown` or `BodyHtml`. Otherwise a metadata save from an older tab can silently undo a newer content save. Prefer a details-only endpoint/request that excludes all body fields. Add a three-step concurrency regression: load the old representation, save a distinct body through the content endpoint, then save metadata using the old representation and assert the distinct body is unchanged. A planned test is not evidence until its route exists and the focused/full test actually passes.

## New-item flow

A content route normally needs a persistent ID. For a new item:

- Require the minimum identifying field, usually the primary title.
- Use an explicit “Save as draft and edit content” action.
- Force draft status during this transition so an empty-body item cannot be published accidentally.
- Return the created representation or ID and navigate directly to its content route.
- Do not silently create blank drafts.

## Legacy body-source compatibility

Systems may contain records with rendered HTML but no Markdown source. Define transition semantics before splitting the editor:

- Opening the content editor should preview sanitized legacy HTML when Markdown is absent.
- Saving empty Markdown should preserve existing legacy HTML unless the product has an explicit destructive-clear action.
- Saving non-empty Markdown may promote Markdown to the primary body source and clear stale rendered HTML if rendering happens at display time.
- Never expose storage details such as `BodyHtml`, fallback, or API behavior as user-facing copy.

## Interaction contract

For a dedicated content workspace:

- Desktop: editor and preview side by side, each independently scrollable, using most of the available viewport height.
- Narrow screens: switch between Edit and Preview; do not stack two tall panes.
- Show explicit saved/unsaved/saving/error states.
- Support Ctrl/Cmd+S and block the browser’s default save-page action.
- Warn before internal navigation, refresh, or close when content is dirty.
- Preserve text and dirty state after a failed save. Treat non-2xx responses, network/CORS failures, timeouts, and malformed success payloads as recoverable save failures rather than letting them escape the component event handler.
- Snapshot the exact body submitted before awaiting the request. If the user keeps typing while save is in flight, update the saved baseline from the response but keep the newer editor text and recompute dirty state; never overwrite the editor or set dirty=false unconditionally.
- Make every independently scrollable read-only preview keyboard-focusable (`tabindex="0"`) and expose it as a named region so keyboard users can scroll text-only content.
- Give active Edit/Preview controls and disabled Save controls a real computed visual state. A modifier class or `aria-pressed` value alone is not visual evidence; verify styles after moving the automation pointer away so `:hover` cannot masquerade as the active state.
- Dispose global keyboard and scroll listeners when leaving the page. If the page derives from an `IDisposable` base but adds `IAsyncDisposable`, invoke the inherited cleanup from the async path as well so base event subscriptions are not leaked.
- Protect async live preview from out-of-order completion so an older render cannot replace newer input.

## Verification checklist

- Existing-item card reaches the correct content route.
- New-item transition creates a draft only after minimum validation.
- Content save changes no metadata fields, and a later metadata save made from a stale representation does not change the newly saved body.
- Unauthorized and non-admin calls are rejected consistently.
- Legacy HTML-only content remains visible in both the editor preview and the metadata entry-card summary, and is not erased by an empty Markdown save.
- Desktop panes are truly side by side and use available height.
- Mobile shows one pane at a time and has no horizontal overflow.
- Text-only preview content can receive keyboard focus and scroll; active pane and disabled save states remain visibly distinct after hover is removed.
- Ctrl/Cmd+S fires one request; listeners and inherited subscriptions do not survive page disposal.
- Dirty navigation prompts before save and does not prompt after successful save.
- Preview uses the same sanitization/rendering pipeline as the public view.
