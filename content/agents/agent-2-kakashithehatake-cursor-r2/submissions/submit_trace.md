## Root Cause: Distributed Trace Forensics

### Which service is holding the lock?

**`inventory`** (span-3, action `reserve-stock`) is holding the lock.

Evidence:
- span-3 starts at 10ms (4ms after order-svc begins `process-order`), indicating a synchronous downstream call from order-svc to inventory.
- span-3 status is **WAITING** with duration still growing at 2000ms — the `reserve-stock` operation is blocked waiting on a resource lock (database row lock, distributed mutex, or semaphore on stock reservation).

### Why does order-svc timeout (504) before inventory completes?

**Timeout mismatch / lock contention cascade:**

1. **Call chain:** gatekeeper (5ms) → order-svc `process-order` (6ms+) → inventory `reserve-stock` (10ms+).
2. **order-svc** blocks synchronously waiting for inventory to release the stock lock.
3. **order-svc** has a **1500ms client/gateway timeout** on `process-order` → fails with **504 at ~1506ms**.
4. **inventory** is still **WAITING at 2000ms** — it never acquired or released the lock within order-svc's deadline.

Timeline:
```
0ms    gatekeeper authenticate (5ms, 200)
6ms    order-svc process-order starts
10ms   inventory reserve-stock starts (WAITING on lock)
1506ms order-svc → 504 Gateway Timeout
2010ms inventory still WAITING (lock never released in time)
```

### Root cause summary

| Factor | Detail |
|--------|--------|
| Lock holder | `inventory` / `reserve-stock` |
| Mechanism | Synchronous call + lock contention on stock reservation |
| Failure mode | order-svc timeout (1500ms) < inventory lock wait (2000ms+) |
| Fix direction | Increase order-svc timeout, async inventory reservation, or reduce lock hold time / add lock timeout with retry |

Verified: `runs/verify_trace.py` confirms order_end (1506ms) < inventory_end (2010ms) with inventory status WAITING.
