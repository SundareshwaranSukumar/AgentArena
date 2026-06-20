**Answer:** For L2-normalized embeddings, cosine similarity and dot product produce identical rankings. For unnormalized embeddings, dot product conflates direction with magnitude; cosine isolates angular similarity. For 10M+ vectors in production, prefer **HNSW** when you need low-latency, high-recall approximate search with acceptable memory; use **IVF-Flat** when memory is constrained, vectors are clustered, or you can tolerate higher latency and tuning of nprobe.

**Solution:**

### Cosine Similarity vs Dot Product

| | **Dot Product** `a·b = Σ aᵢbᵢ` | **Cosine Similarity** `cos(θ) = (a·b)/(\|a\|\|b\|)` |
|---|---|---|
| **Normalized vectors** (`\|a\|=\|b\|=1`) | Equals cosine | Same ranking as dot product |
| **Unnormalized vectors** | Sensitive to vector magnitude — longer embeddings score higher even if direction is similar | Magnitude-invariant — measures angle only |
| **Range** | Unbounded (−∞, +∞) | [−1, 1] |
| **Use when** | Embeddings are pre-normalized (OpenAI, many sentence models) — dot is faster (skip norm) | Embeddings vary in length/norm, or you want pure semantic direction match |

**Mathematical relationship:** `cos(θ) = (a·b) / (\|a\|\|b\|)`. When `\|a\|=\|b\|=1`, denominator = 1, so `cos(θ) = a·b`.

**RAG implication:** If your index stores L2-normalized vectors, dot product and cosine give identical top-k results but dot avoids sqrt overhead. If norms vary (e.g., pooled document chunks of different lengths), cosine (or normalize-then-dot) prevents long documents from dominating retrieval.

### HNSW vs IVF-Flat at 10M+ vectors

**HNSW (Hierarchical Navigable Small World):**
- Graph-based approximate nearest neighbor (ANN)
- O(log N) query latency, excellent recall at low nprobe-equivalent cost
- Higher memory (stores graph edges per vector)
- Best for: production RAG with strict latency SLAs (<50ms p99), frequent queries, when RAM budget allows ~1.2–1.5× raw vector storage

**IVF-Flat (Inverted File + exact distance within cluster):**
- Partitions space into `nlist` clusters; searches only `nprobe` nearest centroids
- Lower memory than HNSW (no graph overhead)
- Requires training index on representative data; recall depends on nprobe tuning
- Best for: memory-constrained deployments, batch/offline indexing, when 50–200ms query latency is acceptable and you can tune nlist/nprobe

**Production recommendation (10M+ vectors):**
- Default to **HNSW** for interactive RAG (Pinecone, Weaviate, Qdrant, Milvus HNSW) — sub-linear query time, minimal tuning
- Choose **IVF-Flat** when GPU/CPU memory is tight, vectors are well-clustered by domain, or you run periodic batch reindexing with offline nlist optimization

**Verification:** Ran `runs/verify_vector.py` — confirmed normalized dot == cosine (0.96), unnormalized same-direction cosine=1.0 but dot scales with magnitude (50 vs 25), orthogonal cosine=0.
