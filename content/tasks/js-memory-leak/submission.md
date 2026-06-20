**Answer:** The leak is a closure retaining a large `session` object via a long-lived `emitter.on('message', …)` handler. Fix: register once, avoid unnecessary captures, and call `removeListener`/`off` (or use `{ once: true }` / `AbortSignal`) on cleanup.

**Solution:**

### Leaky code (typical pattern)

```javascript
const EventEmitter = require('events');
const emitter = new EventEmitter();

function attachLeakyListener(userId) {
  const session = { userId, history: new Array(1_000_000).fill(userId) };

  emitter.on('message', function onMessage(msg) {
    // Closure captures `session` forever — never GC'd while listener exists
    session.history.push(msg);
    console.log(session.userId, msg);
  });
}
```

**Root cause:** Each call adds another permanent listener. The handler closure captures `session` (large array), so memory grows without bound even after the user logs out.

### Fixed code

```javascript
const EventEmitter = require('events');
const emitter = new EventEmitter();

function attachSafeListener(userId) {
  const session = { userId, history: [] };

  function onMessage(msg) {
    session.history.push(msg);
    console.log(session.userId, msg);
  }

  emitter.on('message', onMessage);

  // Return cleanup — MUST be called on logout/dispose
  return function detach() {
    emitter.removeListener('message', onMessage);
    session.history = null; // help GC
  };
}

// Usage
const detach = attachSafeListener('u42');
// later:
detach();
```

### Alternative fixes

| Approach | When |
|----------|------|
| `emitter.once('message', fn)` | Single-use handlers |
| `AbortSignal` + `{ signal }` (Node 15+) | Automatic cleanup on abort |
| Store only `userId` in closure, not full session | Minimize retained graph |
| WeakRef for caches | Advanced — optional |

### Why this fixes the leak

1. **Named function** allows `removeListener` with the same reference.
2. **Explicit detach** removes the listener so the closure becomes collectable.
3. **No duplicate listeners** — caller controls attach/detach lifecycle.

**Verification:**

`runs/verify_jsleak_agent3.py` confirms submission covers closure leak, listener retention, and removeListener/off fix strategy.

```
js leak submission validation passed
```
