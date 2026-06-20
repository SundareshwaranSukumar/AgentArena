"""One-shot MCP helpers for Cursor-driven Arena runs."""
from __future__ import annotations

import asyncio
import importlib.util
import json
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "bridge", ROOT / "arena_mcp" / "arena_bridge.py"
)
bridge = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(bridge)


def parse_agent_id(text: str) -> str:
    try:
        data = json.loads(text)
        if isinstance(data, dict) and data.get("agentId"):
            return str(data["agentId"])
    except json.JSONDecodeError:
        pass
    m = re.search(r'"agentId"\s*:\s*"([^"]+)"', text)
    if m:
        return m.group(1)
    m = re.search(r"AGENT_ID:\s*(\S+)", text)
    return m.group(1).rstrip(".") if m else ""


def parse_task(text: str) -> dict | None:
    try:
        data = json.loads(text)
        if isinstance(data, dict) and data.get("id"):
            return data
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]
    except json.JSONDecodeError:
        pass
    return None


async def cmd_register(name: str | None = None, stack: str | None = None) -> None:
    reg = await bridge.register_agent(name=name, stack=stack)
    aid = parse_agent_id(reg)
    print(json.dumps({"register": reg, "agent_id": aid}))


async def cmd_get(agent_id: str) -> None:
    raw = await bridge.get_tasks(agent_id)
    task = parse_task(raw)
    print(json.dumps({"raw": raw, "task": task}))


async def cmd_submit(agent_id: str, task_id: str, content: str) -> None:
    result = await bridge.submit_task(agent_id, task_id, content)
    print(json.dumps({"submit": result}))


async def cmd_skip(agent_id: str, task_id: str, reason: str = "") -> None:
    result = await bridge.skip_task(agent_id, task_id, reason)
    print(json.dumps({"skip": result}))


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: register [name] [stack] | get <agent_id> | submit <agent_id> <task_id> <content_file> | skip <agent_id> <task_id> [reason]")
        sys.exit(1)
    op = sys.argv[1]
    if op == "register":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        stack = sys.argv[3] if len(sys.argv) > 3 else None
        await cmd_register(name, stack)
    elif op == "get" and len(sys.argv) >= 3:
        await cmd_get(sys.argv[2])
    elif op == "submit" and len(sys.argv) >= 5:
        content = Path(sys.argv[4]).read_text(encoding="utf-8")
        await cmd_submit(sys.argv[2], sys.argv[3], content)
    elif op == "skip" and len(sys.argv) >= 4:
        reason = sys.argv[4] if len(sys.argv) > 4 else ""
        await cmd_skip(sys.argv[2], sys.argv[3], reason)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
