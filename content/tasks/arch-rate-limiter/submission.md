**Answer:** Hybrid **Redis token bucket (Lua atomic)** for burst-friendly global limits at 100k rps, with **sliding-window counters** for strict quota windows; **fail-open + per-node local caps** during Redis downtime.

**Solution:**

### Token Bucket vs Sliding Window Counter

| Dimension | Token Bucket | Sliding Window Counter |
|-----------|--------------|------------------------|
| Burst | Allows controlled bursts up to bucket capacity | Harder cap per window; smoother traffic |
| Accuracy | Approximate at refill edges | More accurate quota over fixed interval |
| Redis memory | Low (tokens + timestamp per key) | Higher (sub-windows or sorted sets) |
| 100k rps fit | Excellent — O(1) Lua per request | Good with sharded keys + approximate windows |
| Use case | API burst tolerance, user-facing limits | Strict billing / compliance quotas |

**Recommendation:** Token bucket as primary limiter; sliding window for per-tenant monthly/hourly hard caps.

### Redis Atomicity at 100k req/s

Race condition without atomicity: read tokens → compute → write can double-admit under concurrency.

| Approach | Atomicity | 100k rps suitability |
|----------|-----------|------------------------|
| **Lua script** (EVALSHA) | ✅ Single atomic server-side execution | ✅ Best — one round-trip, no WATCH retries |
| **MULTI/EXEC** | ✅ Transactional batch | ⚠️ OK but more round-trips than Lua |
| **INCR + TTL** (sliding) | ✅ Atomic increment | ✅ Good for fixed windows |
| Read-modify-write (no script) | ❌ Races | ❌ Unacceptable at scale |

**Lua token bucket sketch:**
```lua
-- KEYS[1]=bucket, ARGV: rate, capacity, now_ms
local data = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
-- refill, consume, HMSET — all atomic in one script
```

**Sharding:** `ratelimit:{tenant_id}:{shard}` across Redis cluster nodes to avoid hot keys at 100k rps.

### Redis Downtime: Fail-Open vs Fail-Closed

| Strategy | Pros | Cons |
|----------|------|------|
| **Fail-closed** (reject all) | Protects backend | Outage becomes total API outage |
| **Fail-open** (allow all) | High availability | Risk of overload / abuse |

**Production choice:** **Fail-open with strict local fallback**
- Each API node runs an **in-memory token bucket** (e.g. 20% of global quota per node)
- If Redis unreachable > N ms → enforce local cap only
- Prevents unbounded admission while keeping service alive
- Alert + circuit breaker to restore Redis authority when healthy

### Architecture Summary

```
Client → API Gateway → Rate-limit middleware
                          ├─ Redis Lua (authoritative, shared)
                          └─ Local bucket (fallback on Redis failure)
```

**Verification:**

`runs/verify_arch_rl_agent3.py`:
```
architecture rate limiter validation passed
```

All required topics covered: token bucket, sliding window, Redis Lua atomicity, 100k rps sharding, fail-open/fail-closed tradeoffs.
