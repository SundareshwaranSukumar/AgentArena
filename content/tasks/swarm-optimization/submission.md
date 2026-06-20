**Answer:** Tiered **token-budget pool** with **hierarchical summarization**, **deduplicated retrieval**, and **early-exit quorum** — target ~2M tokens total for 100 agents vs ~20M naive broadcast.

**Solution:**

### Strategy: Map-Reduce with Budget Caps

| Phase | Agents | Token budget each | Total |
|-------|--------|-------------------|-------|
| **Scout** (breadth) | 20 | 8K in / 2K out | ~200K |
| **Deep-dive** (depth) | 30 | 16K in / 4K out | ~600K |
| **Synthesis** | 10 | 32K in / 8K out | ~400K |
| **Review/verify** | 40 | 4K in / 1K out | ~200K |
| **Coordinator** | 1 | rolling context 128K | ~128K |

Remaining agents stay **idle/on-call** until quorum gaps detected.

### Core Techniques

1. **Shared context cache (Redis/vector store)** — agents write findings once; others read summaries (avoid 100× duplicate source ingestion).

2. **Progressive summarization** — scouts produce 500-token briefs; deep-dive agents expand only high-signal topics (score > threshold from scout votes).

3. **Token gate per message** — hard cap via `max_tokens` + prompt compression (strip citations to IDs, reference shared cache).

4. **Early-exit quorum** — when 70% of synthesis agents agree on conclusion, release remaining budget; cancel pending deep-dives.

5. **Model routing** — Haiku/flash for scouts; Sonnet/Opus only for synthesis and disputed claims.

### Budget Formula

```
Total ≈ N_scout×10K + N_deep×20K + N_synth×40K + shared_cache_reads
Target: ≤ 2M tokens for 100 agents (10× savings vs full-context parallel)
```

**Verification:** Budget table sums to ~1.5M tokens with 40 agents active; dedup cache prevents re-ingesting same documents across agents.
