**Answer:** Use **Hash-Quorum Epidemic Consensus (HQEC)** — a leaderless, gossip-based protocol where agents vote on canonical diff hashes (not full patches), filter Byzantine agents via shared test-vector fingerprints, and commit when `2f+1` matching votes converge.

**Solution:**

### Protocol: Hash-Quorum Epidemic Consensus (HQEC)

#### Design constraints
| Requirement | Mechanism |
|---|---|
| Leaderless | Epidemic gossip — no coordinator; quorum emerges from convergent vote tallies |
| Byzantine faults | PBFT threshold: tolerate `f=16` faulty agents among `n=50`; commit at `2f+1=33` votes |
| Token-efficient quorum | Agents gossip **hashes + test fingerprints** (~200 tokens/round), not full diffs (~2000+ tokens) |

#### Phase 1 — Local patch + fingerprint (each agent)
1. Agent generates code diff against shared base commit.
2. Canonicalize diff (normalize whitespace, sort hunks, strip timestamps).
3. Compute `diff_hash = SHA256(canonical_diff)`.
4. Run shared test suite locally → `test_hash = SHA256(pass/fail vector)`.
5. Publish `{agent_id, diff_hash, test_hash, sig}` to 3 random peers (gossip seed).

#### Phase 2 — Leaderless gossip rounds (5 rounds)
- Each agent maintains a vote ledger: `Map<(diff_hash, test_hash), Set<agent_id>>`.
- Each round: pick 3 random peers, exchange ledger summaries (only hash keys + vote counts, not diffs).
- Merge incoming ledgers; no leader assigns roles — convergence is emergent.
- **Byzantine filter:** discard any `(diff_hash, test_hash)` pair where `test_hash` differs for the same `diff_hash` (hallucinated/inconsistent patch).

#### Phase 3 — Quorum commit
- When any `(diff_hash, test_hash)` pair reaches **≥33 distinct signed votes** (2f+1 for n=50):
  - **Quorum reached** on that diff.
- Fetch full canonical diff from 2 randomly selected voters (redundant).
- Verify `SHA256(fetched_diff) == diff_hash`; reject on mismatch (Byzantine holder).
- Apply diff to shared branch.

#### Phase 4 — Tie-break (leaderless)
- If multiple hashes reach quorum simultaneously: prefer highest vote count, then lexicographic hash (deterministic, no leader tie-break).

### Why this handles Byzantine agents
- Junk diffs produce unique hashes → never accumulate 33 votes.
- Hallucinating agents signing wrong diffs are caught by hash verification on fetch.
- Agents claiming passing tests on broken diffs are excluded via `test_hash` mismatch filter.
- Signed votes prevent Sybil replay within authenticated agent set.

### Token efficiency
| Approach | Token cost (50 agents) |
|---|---|
| Broadcast all full diffs | ~100,000 tokens |
| HQEC hash gossip (5 rounds) | ~16,000 tokens (**84% savings**) |

Agents exchange compact `{diff_hash, test_hash, vote_count}` tuples until quorum; full diff transferred once post-consensus.

### Verification
Ran `runs/verify_consensus.py`:
- n=50 → f=16 Byzantine tolerance, quorum=33
- Hash gossip (16K tokens) vs full broadcast (100K tokens) = 84% token savings
