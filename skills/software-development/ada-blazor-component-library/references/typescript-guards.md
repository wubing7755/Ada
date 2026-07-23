# TypeScript: Window Resize + Visibility Change Guards

Per SRS REQ-F-129 and REQ-F-137, drag operations must cancel when:
- The browser window is resized mid-drag
- The page becomes hidden (tab switch)

## Implementation

Add to `startDrag()`:
```typescript
window.addEventListener('resize', onWindowResize);
document.addEventListener('visibilitychange', onVisibilityChange);
```

Both handlers call `cleanupDrag()` + remove all listeners (pointer, key, resize, visibility). The same cleanup must be added to `onDragEnd()` and `onKeyDown()` (Escape).

## Pitfall

Forgetting to remove these listeners in normal drag-end paths causes stale handlers that fire on the next session. Every exit path from a drag operation must call `cleanupDrag()` which removes ALL listeners: pointer events, keyboard events, resize, and visibilitychange.
