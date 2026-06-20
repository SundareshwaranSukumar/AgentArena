"""Continuous Arena monitor — polls all agents in agents.json every 30s until runs/FINISH."""
from __future__ import annotations

import asyncio
import importlib.util
import json
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

AGENTS = json.loads((ROOT / "arena_mcp" / "agents.json").read_text(encoding="utf-8"))
POLL_SEC = 30
LOG = ROOT / "runs" / "cursor_poll.log"
STATE = ROOT / "runs" / "pending_task.json"
STATUS = ROOT / "runs" / "agents_status.json"
FINISH = ROOT / "runs" / "FINISH"


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def parse_task(raw: str) -> dict | None:
    if "ALL_TASKS_ATTEMPTED" in raw or "AUTH_ERROR" in raw:
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


async def poll_agent(agent: dict) -> dict:
    import config

    config.refresh_runtime_secrets()
    raw = await bridge.get_tasks(agent["id"])
    task = parse_task(raw)
    entry = {
        "agent_id": agent["id"],
        "agent_name": agent["name"],
        "label": agent["label"],
        "raw": raw[:300],
        "task": task,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    if task:
        payload = {
            "agent_id": agent["id"],
            "agent_name": agent["name"],
            "label": agent["label"],
            "raw": raw,
            "task": task,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }
        STATE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        log(
            f"NEW TASK [{agent['label']}] {agent['name']}: "
            f"{task.get('title')} id={task.get('id')} L{task.get('level')}"
        )
    elif "AUTH_ERROR" in raw or ("Invalid" in raw and "token" in raw.lower()):
        log(f"AUTH ERROR [{agent['label']}] — refresh EPHEMERAL_JWT: {raw[:120]}")
    else:
        log(f"idle [{agent['label']}] {agent['name']}: {raw[:90]}")
    return entry


async def poll_all() -> list[dict]:
    results = []
    for agent in AGENTS:
        results.append(await poll_agent(agent))
    STATUS.write_text(
        json.dumps(
            {"agents": results, "updated_at": datetime.now(timezone.utc).isoformat()},
            indent=2,
        ),
        encoding="utf-8",
    )
    return results


async def main() -> None:
    log(f"CONTINUOUS — {len(AGENTS)}-agent poller active until FINISH (runs/FINISH or say FINISH)")
    if FINISH.exists():
        FINISH.unlink()
    while True:
        if FINISH.exists():
            log("FINISH detected — stopping continuous monitor")
            break
        await poll_all()
        await asyncio.sleep(POLL_SEC)


if __name__ == "__main__":
    asyncio.run(main())
