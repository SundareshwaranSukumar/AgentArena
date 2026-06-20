"""
Stdio MCP bridge for Cursor — Agent Arena tools with credentials from .env.

Cursor connects via .cursor/mcp.json; this process forwards tool calls to the
remote Arena MCP and injects EPHEMERAL_JWT as idToken automatically.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402 — loads .env from project root
from fastmcp import FastMCP  # noqa: E402
from fastmcp.client import Client  # noqa: E402
from fastmcp.client.transports import StreamableHttpTransport  # noqa: E402
from fastmcp.exceptions import ToolError  # noqa: E402

arena = FastMCP(
    "agent-arena",
    instructions=(
        "Agent Arena benchmark MCP. Workflow: register_agent() once, then repeat "
        "get_tasks(agent_id) → solve → submit_task(agent_id, task_id, content). "
        "Score >= 70 levels up. Structure answers with **Answer:** first, then "
        "**Solution:** and **Verification:**. Use Cursor tools for math/code checks. "
        "If AUTH_ERROR, refresh EPHEMERAL_JWT in .env (~1h TTL) and retry."
    ),
)


async def _arena_call(tool_name: str, arguments: dict) -> str:
    config.refresh_runtime_secrets()
    if not config.ID_TOKEN:
        return (
            "ERROR: Missing EPHEMERAL_JWT in .env — copy the Ephemeral JWT "
            "(eyJ…) from agent-arena.dev Identity & Trace Keys panel."
        )
    transport = StreamableHttpTransport(url=config.MCP_ENDPOINT)
    try:
        async with Client(transport, name="cursor-arena-bridge") as client:
            result = await client.call_tool(tool_name, arguments)
            if result is None:
                return f"ERROR: {tool_name} returned no response"
            return "\n".join(
                getattr(b, "text", "")
                for b in result.content
                if getattr(b, "text", None)
            )
    except ToolError as exc:
        return f"ERROR: {exc}"
    except Exception as exc:
        return f"ERROR: {exc}"


@arena.tool
async def register_agent(
    name: str | None = None,
    stack: str | None = None,
) -> str:
    """Register this agent in Agent Arena. Returns agentId — call once per session."""
    config.refresh_runtime_secrets()
    agent_name = name or config.AGENT_NAME
    agent_stack = stack or config.AGENT_STACK or "Cursor / MCP"
    payload: dict = {
        "idToken": config.ID_TOKEN,
        "name": agent_name,
        "stack": agent_stack,
    }
    if config.LINKEDIN_URL:
        payload["linkedinUrl"] = config.LINKEDIN_URL
    if config.GITHUB_URL:
        payload["githubUrl"] = config.GITHUB_URL
    return await _arena_call("register_agent", payload)


@arena.tool
async def get_tasks(agent_id: str) -> str:
    """Fetch the current task (JSON: id, title, description, level, points)."""
    return await _arena_call(
        "get_tasks",
        {"idToken": config.ID_TOKEN, "agentId": agent_id},
    )


@arena.tool
async def submit_task(agent_id: str, task_id: str, content: str) -> str:
    """Submit an answer for AI scoring (0–100). Score >= 70 triggers LEVEL_UP."""
    return await _arena_call(
        "submit_task",
        {
            "idToken": config.ID_TOKEN,
            "agentId": agent_id,
            "taskId": task_id,
            "executionId": str(uuid.uuid4()),
            "content": content,
            "metadata": {
                "agent_name": config.AGENT_NAME,
                "agent_stack": config.AGENT_STACK or "Cursor / MCP",
                "platform_user_id": config.PLATFORM_USER_ID,
                "client": "cursor-mcp",
            },
        },
    )


@arena.tool
async def skip_task(agent_id: str, task_id: str, reason: str = "") -> str:
    """Skip the current task when it is impossible or stuck."""
    args: dict = {
        "idToken": config.ID_TOKEN,
        "agentId": agent_id,
        "taskId": task_id,
    }
    if reason:
        args["reason"] = reason
    return await _arena_call("skip_task", args)


if __name__ == "__main__":
    arena.run()
