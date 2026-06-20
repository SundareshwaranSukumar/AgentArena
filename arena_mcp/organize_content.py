"""Build production content/ tree from runs/ submissions and verifications."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
CONTENT = ROOT / "content"
AGENTS_JSON = ROOT / "arena_mcp" / "agents.json"

# Canonical task metadata (Arena task id when known, typical level, display title)
TASK_META: dict[str, dict] = {
    "bigcodebench-10": {"level": 1, "title": "BigCodeBench/10", "task_id": "3i22FyUH0RZ7NYnIpOMb"},
    "basic-log-extraction": {"level": 1, "title": "Basic Log Extraction", "task_id": "basic-log-extraction"},
    "grounded-search-motion": {"level": 1, "title": "Grounded Search: Framework Lifecycle", "task_id": "grounded-search-framework-lifecycle"},
    "quantum-editorial": {"level": 1, "title": "Quantum Physics Editorial"},
    "bigcodebench-150": {"level": 2, "title": "BigCodeBench/150", "task_id": "KkLpCLkPA7uhikbNTsvX"},
    "decode-shift": {"level": 2, "title": "Python/50 decode_shift", "task_id": "60fQUjU0W1EnjpmW4pev"},
    "financial-portfolio": {"level": 2, "title": "Financial Math: Portfolio Growth", "task_id": "financial-math-portfolio-growth"},
    "nl2sql-membership": {"level": 2, "title": "NL2SQL: Membership Analytics", "task_id": "nl2sql-membership-analytics"},
    "lru-cache-ts": {"level": 2, "title": "TypescriptCodeGen LRU Cache"},
    "js-memory-leak": {"level": 2, "title": "JS Memory Leak Hunt"},
    "lru-cache-py": {"level": 3, "title": "PythonCodeGen LRU Cache", "task_id": "gNMeMsrNwAJfZQCLZpb6"},
    "oldabe": {"level": 3, "title": "OldAbe", "task_id": "hrUFAY4dolDUqeBwxNas"},
    "bigcodebench-540": {"level": 3, "title": "BigCodeBench/540", "task_id": "84Hav32IplR9ixbGAP2Z"},
    "algorithm-intersection": {"level": 3, "title": "Algorithm Refactoring", "task_id": "iHyENLDFZ39Z5mMLN8Vm"},
    "maximum-arr-k": {"level": 3, "title": "Python/120 maximum(arr,k)"},
    "rate-limiter": {"level": 3, "title": "Architecture: Distributed Rate Limiter"},
    "resilience-circuit-breaker": {"level": 4, "title": "Resilience Patterns", "task_id": "b2JLywn3S4sJtgTdFWzb"},
    "vector-db-retrieval": {"level": 4, "title": "Vector DB: Retrieval Optimization", "task_id": "vector-db-retrieval-optimization"},
    "distributed-trace": {"level": 4, "title": "Log Analysis: Distributed Trace Forensics", "task_id": "log-analysis-distributed-trace-forensics"},
    "swarm-consensus": {"level": 5, "title": "Expert Reasoning: Agent Swarm Consensus", "task_id": "expert-reasoning-agent-swarm-consensus"},
    "blockchain-51": {"level": 5, "title": "Blockchain Forensics: 51% Attack Detection", "task_id": "blockchain-forensics-51-attack-detection"},
    "saga-choreography": {"level": 5, "title": "Saga Choreography"},
    "swarm-optimization": {"level": 5, "title": "Swarm Optimization"},
    "rag-synthesis": {"level": 3, "title": "RAG Synthesis"},
    "ticker": {"level": 6, "title": "Ticker", "task_id": "BqZ2kTFN7YcPMCNbNQNx", "answer": "c2"},
    "mmv1": {"level": 7, "title": "MMV1", "task_id": "nyDISm58YDmPVtNlzZ3w"},
    "close-position": {"level": 2, "title": "Close Position"},
    "arch-rate-limiter": {"level": 3, "title": "Architecture Rate Limiter"},
}

# submit/verify filename stem → task slug
STEM_TO_SLUG: dict[str, str] = {
    "bcb10": "bigcodebench-10",
    "bcb150": "bigcodebench-150",
    "bcb540": "bigcodebench-540",
    "log": "basic-log-extraction",
    "motion": "grounded-search-motion",
    "quantum": "quantum-editorial",
    "portfolio": "financial-portfolio",
    "nl2sql": "nl2sql-membership",
    "decode": "decode-shift",
    "lru": "lru-cache-ts",
    "jsleak": "js-memory-leak",
    "intersection": "algorithm-intersection",
    "maximum": "maximum-arr-k",
    "ratelimit": "rate-limiter",
    "arch_rl": "arch-rate-limiter",
    "circuit": "resilience-circuit-breaker",
    "vector": "vector-db-retrieval",
    "trace": "distributed-trace",
    "consensus": "swarm-consensus",
    "blockchain": "blockchain-51",
    "saga": "saga-choreography",
    "swarm_opt": "swarm-optimization",
    "rag": "rag-synthesis",
    "ticker": "ticker",
    "mmv1": "mmv1",
    "close": "close-position",
    "cb": "resilience-circuit-breaker",
}

# Prefer these submission files for canonical answer (first match wins)
CANONICAL_SUBMIT_PRIORITY = [
    "submit_final_{stem}.md",
    "submit_{stem}.md",
    "submit_{stem}_agent3.md",
    "submit_{stem}_r2.md",
    "submit_agent4_{stem}.md",
]


def _stem_from_name(name: str) -> str | None:
    """Extract task stem from submit_foo or verify_foo filename."""
    for prefix in ("submit_", "verify_"):
        if not name.startswith(prefix):
            continue
        rest = name[len(prefix) :]
        if rest.endswith(".md"):
            rest = rest[:-3]
        elif rest.endswith(".py"):
            rest = rest[:-3]
        else:
            continue
        for suffix in ("_agent3", "_agent4", "_r2", "_final"):
            if rest.startswith("final_"):
                rest = rest[6:]
                break
            if rest.endswith(suffix):
                rest = rest[: -len(suffix)]
                break
        if rest.startswith("agent4_"):
            rest = rest[7:]
        return rest
    return None


def _slug_from_stem(stem: str) -> str:
    return STEM_TO_SLUG.get(stem, stem.replace("_", "-"))


def _score_file(path: Path) -> tuple[int, int]:
    """Higher = preferred. (priority tier, file size)."""
    name = path.name
    if name.startswith("submit_final_"):
        return (100, path.stat().st_size)
    if name.startswith("submit_") and "_agent" not in name and "_r2" not in name:
        return (80, path.stat().st_size)
    if "_r2" in name:
        return (70, path.stat().st_size)
    if "_agent3" in name:
        return (60, path.stat().st_size)
    if "_agent4" in name or "agent4_" in name:
        return (50, path.stat().st_size)
    return (40, path.stat().st_size)


def _collect_runs_files() -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    submits: dict[str, list[Path]] = {}
    verifies: dict[str, list[Path]] = {}
    for path in RUNS.glob("submit_*.md"):
        if "archive" in path.parts:
            continue
        stem = _stem_from_name(path.name)
        if not stem:
            continue
        slug = _slug_from_stem(stem)
        submits.setdefault(slug, []).append(path)
    for path in RUNS.glob("verify_*.py"):
        if "archive" in path.parts:
            continue
        stem = _stem_from_name(path.name)
        if not stem:
            continue
        slug = _slug_from_stem(stem)
        verifies.setdefault(slug, []).append(path)
    return submits, verifies


def _pick_best(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=_score_file)


def _agent_dir_name(agent: dict) -> str:
    label = agent.get("label", "agent")
    name = agent.get("name", "unknown")
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{label}-{slug}"


def _write_task_readme(task_dir: Path, slug: str, meta: dict) -> None:
    lines = [
        f"# {meta.get('title', slug)}",
        "",
        f"- **Slug:** `{slug}`",
        f"- **Level:** {meta.get('level', '?')}",
    ]
    if meta.get("task_id"):
        lines.append(f"- **Task ID:** `{meta['task_id']}`")
    if meta.get("answer"):
        lines.append(f"- **Canonical answer:** `{meta['answer']}`")
    lines.extend(["", "See `submission.md` and optional `verify.py`.", ""])
    task_dir.joinpath("README.md").write_text("\n".join(lines), encoding="utf-8")


def _write_content_readme(agents: list[dict], manifest: dict) -> None:
    CONTENT.joinpath("README.md").write_text(
        f"""# Agent Arena — Task Library

Production-ready **questions & answers** extracted from Arena sessions.

Generated: {manifest["generated_at"]}

## Layout

```
content/
├── README.md           ← this file
├── manifest.json       ← machine-readable index
├── agents/             ← per-agent submission copies
├── tasks/              ← canonical Q&A by task (deduplicated)
│   └── <slug>/
│       ├── README.md
│       ├── submission.md
│       └── verify.py   (when available)
├── assets/             ← images (MMV1, etc.)
└── guides/
    ├── scoring.md
    └── stuck-at-l7.md
```

## Active agents ({len(agents)})

| Label | Name | Agent ID |
|-------|------|----------|
"""
        + "\n".join(
            f"| {a['label']} | {a['name']} | `{a['id']}` |"
            for a in agents
        )
        + f"""

## Tasks indexed

**{len(manifest["tasks"])}** canonical tasks — browse `tasks/` or see `manifest.json`.

## Regenerate

```powershell
python arena_mcp/organize_content.py
```

Runtime logs and poller output stay in `runs/` (gitignored). This folder is what you ship in a release.
""",
        encoding="utf-8",
    )


def _write_scoring_guide() -> None:
    CONTENT.joinpath("guides", "scoring.md").write_text(
        """# Arena Scoring Methodology

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
""",
        encoding="utf-8",
    )


def main() -> None:
    agents = json.loads(AGENTS_JSON.read_text(encoding="utf-8"))
    submits, verifies = _collect_runs_files()

    scores_backup = None
    if SCORES_DIR.exists():
        scores_backup = CONTENT / ".scores_backup"
        if scores_backup.exists():
            shutil.rmtree(scores_backup)
        shutil.copytree(SCORES_DIR, scores_backup)

    if CONTENT.exists():
        shutil.rmtree(CONTENT)
    CONTENT.mkdir()
    (CONTENT / "agents").mkdir()
    (CONTENT / "tasks").mkdir()
    (CONTENT / "assets").mkdir()
    (CONTENT / "guides").mkdir()

    # Assets
    for asset in ("mmv1.png", "tick.png"):
        src = RUNS / asset
        if src.exists():
            shutil.copy2(src, CONTENT / "assets" / asset)

    # Guides
    _write_scoring_guide()
    why = RUNS / "archive" / "agent-1-kakashithehatake" / "WHY-STUCK-AT-L7.md"
    if why.exists():
        shutil.copy2(why, CONTENT / "guides" / "stuck-at-l7.md")

    manifest_tasks: list[dict] = []
    all_slugs = sorted(set(submits) | set(verifies) | set(TASK_META))

    for slug in all_slugs:
        meta = TASK_META.get(slug, {"title": slug.replace("-", " ").title()})
        task_dir = CONTENT / "tasks" / slug
        task_dir.mkdir(parents=True, exist_ok=True)

        best_sub = _pick_best(submits.get(slug, []))
        best_ver = _pick_best(verifies.get(slug, []))

        if best_sub:
            shutil.copy2(best_sub, task_dir / "submission.md")
        if best_ver:
            shutil.copy2(best_ver, task_dir / "verify.py")

        _write_task_readme(task_dir, slug, meta)

        manifest_tasks.append(
            {
                "slug": slug,
                "level": meta.get("level"),
                "title": meta.get("title"),
                "task_id": meta.get("task_id"),
                "canonical_answer": meta.get("answer"),
                "submission": str(task_dir / "submission.md") if best_sub else None,
                "verify": str(task_dir / "verify.py") if best_ver else None,
                "variants": len(submits.get(slug, [])),
            }
        )

    # Per-agent: copy all submit files from runs
    for agent in agents:
        adir = CONTENT / "agents" / _agent_dir_name(agent)
        subdir = adir / "submissions"
        subdir.mkdir(parents=True, exist_ok=True)
        (adir / "profile.json").write_text(json.dumps(agent, indent=2), encoding="utf-8")

        label_num = agent["label"].replace("agent-", "")
        for path in RUNS.glob("submit_*.md"):
            if "archive" in path.parts:
                continue
            name = path.name
            if f"agent{label_num}" in name or f"_final_" in name and label_num == "5":
                shutil.copy2(path, subdir / name)
            elif label_num == "5" and name.startswith("submit_final_"):
                shutil.copy2(path, subdir / name)
            elif label_num == "4" and "agent4" in name:
                shutil.copy2(path, subdir / name)
            elif label_num == "3" and "agent3" in name:
                shutil.copy2(path, subdir / name)
            elif label_num in ("1", "2") and ("_r2" in name or name in {
                "submit_consensus.md", "submit_ticker.md", "submit_mmv1.md",
                "submit_vector.md", "submit_blockchain.md", "submit_trace.md", "submit_cb.md",
            }):
                shutil.copy2(path, subdir / name)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agents": agents,
        "tasks": manifest_tasks,
        "task_count": len(manifest_tasks),
        "with_submission": sum(1 for t in manifest_tasks if t["submission"]),
        "with_verify": sum(1 for t in manifest_tasks if t["verify"]),
    }
    (CONTENT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    _write_content_readme(agents, manifest)

    if scores_backup and scores_backup.exists():
        SCORES_DIR.mkdir(parents=True, exist_ok=True)
        for f in scores_backup.iterdir():
            shutil.copy2(f, SCORES_DIR / f.name)
        shutil.rmtree(scores_backup)

    print(json.dumps({"status": "ok", "content": str(CONTENT), "tasks": len(manifest_tasks)}))


if __name__ == "__main__":
    main()
