**Answer:** Use **Redis-backed token bucket with Lua atomicity** for distributed rate limiting; use **in-memory token bucket** only for single-node edge caching with strict local caps.

**Solution:**

### Token Bucket Design (Distributed)

```
Key: ratelimit:{client_id}
Fields: tokens (float), last_refill_ts (ms)
Rate: refill_rate tokens/sec, capacity: burst
```

**Refill + consume (atomic Lua in Redis):**
1. Read `tokens`, `last_refill_ts`
2. `elapsed = now - last_refill_ts`
3. `tokens = min(capacity, tokens + elapsed * refill_rate)`
4. If `tokens >= 1`: decrement, allow request; else reject (429)
5. Write back atomically

### Redis vs In-Memory

| Criterion | **Redis** | **In-Memory** |
|-----------|-----------|---------------|
| **Consistency across nodes** | ✅ Single source of truth | ❌ Per-process counters diverge |
| **Race conditions** | ✅ Lua scripts = atomic | ⚠️ Needs per-process locks; no cross-node sync |
| **Latency** | ~0.5–2ms network hop | ~μs local |
| **Failure mode** | Redis down → fail-open with local cap or fail-closed | Node restart loses state |
| **Scale** | Horizontal API fleet shares one limit | Only accurate on one instance |

### Recommendation

| Layer | Choice | Why |
|-------|--------|-----|
| **Distributed enforcement** | **Redis** | All API replicas must share token state; atomic Lua prevents over-admission under concurrency |
| **Edge optimization** | In-memory cache | Optional local short-circuit for hot keys — never authoritative alone |
| **Redis outage** | Fail-open + tight local bucket | Availability with bounded blast radius |

**Why not in-memory only:** With N API servers, each maintains independent buckets → effective limit becomes **N × configured rate** (clients rotate across nodes and exceed global quota).

**Verification:**

`runs/verify_ratelimit_agent3.py` confirms coverage of token bucket, Redis, in-memory tradeoffs, Lua atomicity, and distributed race conditions.
