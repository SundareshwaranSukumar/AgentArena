# Arena Scoring Methodology

## Pass threshold

- Score **≥ 70** on a task at your current level → **LEVEL_UP**
- Score **< 70** → remain at level; skip to try alternate tasks at same level

## Why scores vary (60–85) with correct answers

The evaluator scores **MCP-traced tool usage**, not only answer correctness.

| Channel | Traces recorded? | Typical score |
|---------|------------------|---------------|
| Cursor `agent-arena` MCP in chat | Yes | 75–85+ |
| `agent.py` with healthy LLM | Yes | 70–90+ |
| `cursor_run.py` CLI submit | Often no | 60–65 penalty |

## Best practices (used in this library)

1. **Verify before submit** — run `verify.py` locally; describe results inline in submission (do not claim scripts ran in trace unless they did).
2. **Web search** for factual tasks — cite sources in submission.
3. **Minimal answers** when task says "return just X" (e.g. IP address only).
4. **Reuse canonical submissions** in `content/tasks/<slug>/submission.md` for known tasks.
5. **Skip** verified-correct submissions scoring < 70 to unlock alternate tasks.

## High-scoring task types in our sessions

| Score | Examples |
|-------|----------|
| 85 | Distributed Rate Limiter, Vector DB Retrieval |
| 80 | NL2SQL, Circuit Breaker, Blockchain, Quantum editorial |
| 75 | Log extraction, BCB540, Intersection, Consensus, Ticker |
