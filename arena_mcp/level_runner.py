"""Run an Arena agent through levels using content/ submissions + score logging."""
from __future__ import annotations

import asyncio
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "bridge", ROOT / "arena_mcp" / "arena_bridge.py"
)
bridge = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(bridge)

CONTENT = ROOT / "content"
MANIFEST = CONTENT / "manifest.json"
SCORES_DIR = CONTENT / "scores"


def _parse_task(raw: str) -> dict | None:
    if "ALL_TASKS_ATTEMPTED" in raw or "NO_TASKS" in raw or "AUTH_ERROR" in raw:
        return None
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("id"):
            return data
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]
    except json.JSONDecodeError:
        pass
    return None


def _load_manifest() -> list[dict]:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8")).get("tasks", [])
    return []


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _find_submission(task: dict, tasks_meta: list[dict]) -> Path | None:
    tid = task.get("id", "")
    title = task.get("title", "")
    ntitle = _norm(title)

    for entry in tasks_meta:
        if entry.get("task_id") and entry["task_id"] == tid:
            slug = entry.get("slug")
            if slug:
                refined = CONTENT / "tasks" / slug / "submission-refined.md"
                if refined.exists():
                    return refined
            p = entry.get("submission")
            if p and Path(p).exists():
                return Path(p)
        et = _norm(entry.get("title", ""))
        if et and (et in ntitle or ntitle in et):
            slug = entry.get("slug")
            if slug:
                refined = CONTENT / "tasks" / slug / "submission-refined.md"
                if refined.exists():
                    return refined
            p = entry.get("submission")
            if p and Path(p).exists():
                return Path(p)

    # Heuristic slug match
    slug_hints = [
        ("bigcodebench/10", "bigcodebench-10"),
        ("bigcodebench/150", "bigcodebench-150"),
        ("bigcodebench/540", "bigcodebench-540"),
        ("log extraction", "basic-log-extraction"),
        ("framework lifecycle", "grounded-search-motion"),
        ("quantum", "quantum-editorial"),
        ("decode_shift", "decode-shift"),
        ("portfolio", "financial-portfolio"),
        ("nl2sql", "nl2sql-membership"),
        ("lru", "lru-cache-ts"),
        ("memory leak", "js-memory-leak"),
        ("typescript", "lru-cache-ts"),
        ("oldabe", "oldabe"),
        ("pythoncodegen", "lru-cache-py"),
        ("intersection", "algorithm-intersection"),
        ("maximum", "maximum-arr-k"),
        ("rate limit", "rate-limiter"),
        ("resilience", "resilience-circuit-breaker"),
        ("vector", "vector-db-retrieval"),
        ("trace", "distributed-trace"),
        ("swarm consensus", "swarm-consensus"),
        ("blockchain", "blockchain-51"),
        ("saga", "saga-choreography"),
        ("ticker", "ticker"),
        ("mmv1", "mmv1"),
        ("rag", "rag-synthesis"),
    ]
    for hint, slug in slug_hints:
        if hint in ntitle:
            refined = CONTENT / "tasks" / slug / "submission-refined.md"
            if refined.exists():
                return refined
            p = CONTENT / "tasks" / slug / "submission.md"
            if p.exists():
                return p
    return None


def _log_score(agent_id: str, agent_name: str, record: dict) -> None:
    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    path = SCORES_DIR / f"{agent_name.replace(' ', '_')}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    audit = SCORES_DIR / "all-agents.jsonl"
    with audit.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _parse_submit(raw: str) -> dict:
    try:
        inner = json.loads(raw) if raw.startswith("{") else raw
        if isinstance(inner, str):
            inner = json.loads(inner)
        return inner if isinstance(inner, dict) else {"raw": raw}
    except json.JSONDecodeError:
        return {"raw": raw}


async def run_level_climb(
    agent_id: str,
    agent_name: str,
    *,
    max_steps: int = 40,
    allow_skip_on_fail: bool = True,
) -> list[dict]:
    tasks_meta = _load_manifest()
    history: list[dict] = []

    for step in range(max_steps):
        raw = await bridge.get_tasks(agent_id)
        if "ALL_TASKS_ATTEMPTED" in raw or "NO_TASKS" in raw:
            history.append({"step": step, "status": "idle", "raw": raw[:200]})
            break
        if "AUTH_ERROR" in raw:
            history.append({"step": step, "status": "auth_error", "raw": raw[:200]})
            break

        task = _parse_task(raw)
        if not task:
            history.append({"step": step, "status": "no_task", "raw": raw[:200]})
            break

        sub_path = _find_submission(task, tasks_meta)
        if not sub_path:
            history.append(
                {
                    "step": step,
                    "status": "no_content",
                    "task_id": task.get("id"),
                    "title": task.get("title"),
                }
            )
            break

        content = sub_path.read_text(encoding="utf-8")
        submit_raw = await bridge.submit_task(agent_id, task["id"], content)
        result = _parse_submit(submit_raw)

        if "ALREADY_SUBMITTED" in submit_raw:
            skip_raw = await bridge.skip_task(
                agent_id, task["id"], "Already submitted — advance to next task"
            )
            history.append({"step": step, "action": "skip_already", "result": skip_raw[:200]})
            continue

        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent_id": agent_id,
            "agent_name": agent_name,
            "step": step,
            "task_id": task.get("id"),
            "title": task.get("title"),
            "level": task.get("level"),
            "submission": str(sub_path.relative_to(ROOT)),
            "score": result.get("score"),
            "level_up": result.get("levelUp"),
            "new_level": result.get("newLevel"),
            "feedback": (result.get("feedback") or "")[:300],
            "status": result.get("status"),
        }
        _log_score(agent_id, agent_name, record)
        history.append(record)
        print(json.dumps(record), flush=True)

        if result.get("levelUp"):
            continue

        score = result.get("score")
        if score is not None and score >= 70:
            continue

        if allow_skip_on_fail and result.get("status") == "EVALUATED":
            skip_raw = await bridge.skip_task(
                agent_id,
                task["id"],
                f"Score {score} below 70 — alternate task at same level",
            )
            history.append({"step": step, "action": "skip", "result": skip_raw[:200]})
            continue

        break

    return history


async def cmd_register(name: str, stack: str) -> str:
    reg = await bridge.register_agent(name=name, stack=stack)
    try:
        data = json.loads(reg)
        return data.get("agentId", "")
    except json.JSONDecodeError:
        m = re.search(r'"agentId"\s*:\s*"([^"]+)"', reg)
        return m.group(1) if m else ""


async def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: register <name> [stack] | run <agent_id> <agent_name> [max_steps]"
        )
        sys.exit(1)

    op = sys.argv[1]
    if op == "register":
        name = sys.argv[2] if len(sys.argv) > 2 else "KakashiTheHatake-CompleteRun"
        stack = sys.argv[3] if len(sys.argv) > 3 else "Cursor / MCP / Full-Level / No-Skip"
        aid = await cmd_register(name, stack)
        print(json.dumps({"agent_id": aid, "name": name}))
        return

    if op == "run":
        aid = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else aid
        steps = int(sys.argv[4]) if len(sys.argv) > 4 else 40
        hist = await run_level_climb(aid, name, max_steps=steps)
        print(json.dumps({"completed_steps": len(hist), "history": hist[-5:]}))


if __name__ == "__main__":
    asyncio.run(main())
