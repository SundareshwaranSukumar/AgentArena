"""
Agent Arena autonomous competitor — Google ADK + FastMCP.

Tutorial:  https://tutorial.agent-arena.dev/
Reference: https://github.com/xprilion/agent-arena-bot

Usage:
  python agent.py
"""

from __future__ import annotations

import ast
import asyncio
import contextlib
import time
import io
import json
import operator
import re
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastmcp.client import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from traceloop.sdk import set_association_properties
from traceloop.sdk.decorators import workflow
from traceloop.sdk.tracing import set_conversation_id

import config
from evaluation import RunState
from prompts import build_system_prompt, build_task_prompt, detect_task_type
from tracing import agent_logger, init_tracing, task_logger

try:
    from google.adk.models.lite_llm import LiteLlm
    from google.genai.errors import ClientError, ServerError

    _LITELLM_AVAILABLE = True
except ImportError:
    _LITELLM_AVAILABLE = False
    ClientError = ServerError = Exception  # type: ignore[misc, assignment]

# Mutable model selection for fallback on 503/429
_model_in_use: list[str] = [config.MODEL]
_provider_in_use: list[str] = ["gemini"]  # "gemini" | "kimi"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _log(tag: str, msg: str) -> None:
    emoji = {
        "REGISTER": "📝", "FETCH": "📥", "SUBMIT": "📤", "SCORE": "🏆",
        "LEVEL": "🚀", "SKIP": "⏭️", "ERROR": "❌", "WARN": "⚠️",
        "DONE": "✅", "TASK": "📋", "LOOP": "🔄", "AGENT": "🤖",
        "IDLE": "💤", "REPORT": "📊", "WAIT": "⏳",
    }.get(tag, "•")
    print(f"[{_ts()}] {emoji} [{tag}] {msg}")


def _using_kimi() -> bool:
    return _provider_in_use[0] == "kimi"


def _kimi_extra_body() -> dict | None:
    if "moonshot" in config.KIMI_API_BASE:
        return {"thinking": {"type": "disabled"}}
    return None


def _build_kimi_llm() -> LiteLlm:
    kwargs: dict = {
        "model": f"openai/{config.KIMI_MODEL}",
        "api_base": config.KIMI_API_BASE,
        "api_key": config.KIMI_API_KEY,
    }
    extra = _kimi_extra_body()
    if extra:
        kwargs["extra_body"] = extra
    return LiteLlm(**kwargs)


def _init_llm_primary() -> None:
    """Start on Kimi (primary) or Gemini (secondary) per config."""
    if config.kimi_primary():
        _provider_in_use[0] = "kimi"
    else:
        _provider_in_use[0] = "gemini"
        _model_in_use[0] = config.MODEL


async def _verify_kimi_or_fallback(runner: Runner) -> None:
    """Ping Kimi at startup; fall back to Gemini if credits/auth fail."""
    if not config.kimi_primary() or not _LITELLM_AVAILABLE:
        return
    try:
        import litellm

        kwargs: dict = {
            "model": f"openai/{config.KIMI_MODEL}",
            "messages": [{"role": "user", "content": "ping"}],
            "api_base": config.KIMI_API_BASE,
            "api_key": config.KIMI_API_KEY,
            "max_tokens": 4,
        }
        extra = _kimi_extra_body()
        if extra:
            kwargs["extra_body"] = extra
        litellm.completion(**kwargs)
        _log("AGENT", f"Kimi primary ready — {config.KIMI_MODEL}")
    except Exception as exc:
        msg = str(exc).lower()
        if config.gemini_available() and any(
            k in msg for k in ("402", "credit", "exhaust", "401", "auth", "429", "quota")
        ):
            _log("WARN", f"Kimi unavailable ({str(exc)[:80]}) — starting on Gemini backup")
            _switch_to_gemini(runner)
        else:
            raise


def _apply_active_model(runner: Runner) -> None:
    runner.agent.model = active_model()


def active_model():
    if _using_kimi() and config.kimi_available() and _LITELLM_AVAILABLE:
        return _build_kimi_llm()
    return _model_in_use[0]


def active_model_name() -> str:
    if _using_kimi():
        return f"kimi/{config.KIMI_MODEL}"
    return _model_in_use[0]


def _set_runner_model(runner: Runner, model_name: str) -> None:
    _model_in_use[0] = model_name
    _provider_in_use[0] = "gemini"
    runner.agent.model = model_name


def _switch_to_gemini(runner: Runner) -> bool:
    if not config.gemini_available():
        return False
    if not _using_kimi():
        chain = config.model_chain()
        try:
            idx = chain.index(_model_in_use[0])
        except ValueError:
            idx = -1
        if idx + 1 < len(chain):
            nxt = chain[idx + 1]
            _set_runner_model(runner, nxt)
            _log("WARN", f"Switched Gemini model → {nxt}")
            return True
        return False
    _provider_in_use[0] = "gemini"
    _model_in_use[0] = config.model_chain()[0]
    runner.agent.model = _model_in_use[0]
    _log("WARN", f"Switched to Gemini backup → {_model_in_use[0]}")
    return True


def _switch_to_kimi(runner: Runner) -> bool:
    if not config.kimi_available() or not _LITELLM_AVAILABLE:
        return False
    if _using_kimi():
        return False
    _provider_in_use[0] = "kimi"
    runner.agent.model = _build_kimi_llm()
    _log("WARN", f"Switched to Kimi primary → {config.KIMI_MODEL}")
    return True


def _rotate_model(runner: Runner) -> bool:
    if config.kimi_primary():
        if _using_kimi():
            return _switch_to_gemini(runner)
        if _switch_to_gemini(runner):
            return True
        return _switch_to_kimi(runner)
    if not _using_kimi():
        chain = config.model_chain()
        try:
            idx = chain.index(_model_in_use[0])
        except ValueError:
            idx = -1
        if idx + 1 < len(chain):
            nxt = chain[idx + 1]
            _set_runner_model(runner, nxt)
            _log("WARN", f"Switched model → {nxt}")
            return True
    return _switch_to_kimi(runner)


_last_llm_call: float = 0.0


def _parse_retry_delay_sec(exc: BaseException) -> float | None:
    """Extract RetryInfo delay from Gemini 429/503 error text."""
    msg = str(exc)
    match = re.search(r"retry in ([\d.]+)s", msg, re.I)
    if match:
        return float(match.group(1))
    match = re.search(r"'retryDelay':\s*'(\d+)s'", msg)
    if match:
        return float(match.group(1))
    return None


def _is_transient_llm_error(exc: BaseException) -> bool:
    msg = str(exc).upper()
    transient = ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "HIGH DEMAND")
    if any(k in msg for k in transient):
        return True
    if isinstance(exc, ServerError):
        return True
    if isinstance(exc, ClientError):
        return any(k in msg for k in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"))
    return False


async def _throttle_llm() -> None:
    """Respect free-tier RPM limits between Gemini LLM turns."""
    if _using_kimi():
        return
    global _last_llm_call
    wait = config.LLM_MIN_INTERVAL_SEC - (time.monotonic() - _last_llm_call)
    if wait > 0:
        _log("WAIT", f"Rate limit spacing {wait:.0f}s")
        await asyncio.sleep(wait)
    _last_llm_call = time.monotonic()


def _parse_agent_id(result: str) -> str:
    """Extract agent ID from MCP register_agent response (text or JSON)."""
    match = re.search(r"AGENT_ID:\s*(\S+?)\.?(\s|$)", result)
    if match:
        return match.group(1)
    try:
        data = json.loads(result)
        if isinstance(data, dict) and data.get("agentId"):
            return str(data["agentId"])
    except json.JSONDecodeError:
        pass
    match = re.search(r'"agentId"\s*:\s*"([^"]+)"', result)
    return match.group(1) if match else ""


def _parse_level(result: str, default: int = 1) -> int:
    match = re.search(r"Level[:\s]+(\d+)", result, re.I)
    if match:
        return int(match.group(1))
    try:
        data = json.loads(result)
        if isinstance(data, dict) and data.get("level") is not None:
            return int(data["level"])
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return default


def parse_submission_result(result: str) -> tuple[int, bool, int]:
    try:
        data = json.loads(result)
        if isinstance(data, dict):
            score = int(data.get("score", data.get("points", -1)))
            levelled_up = bool(
                data.get("levelledUp")
                or data.get("levelled_up")
                or data.get("levelUp")
                or "LEVEL_UP" in str(data.get("message", "")).upper()
            )
            level = int(data.get("level", 0) or 0)
            if score >= 0:
                return score, levelled_up, level
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    score_match = re.search(r"(?:Score|score)[:\s=]+(\d+)(?:/100)?", result, re.I)
    score = int(score_match.group(1)) if score_match else -1
    levelled_up = bool(re.search(r"LEVEL[_\s-]?UP", result, re.I))
    level_match = re.search(r"level[=:\s]+(\d+)", result, re.I)
    level = int(level_match.group(1)) if level_match else 0
    return score, levelled_up, level


# ── Helper tools (tutorial section 10 — boost scores to 85+) ───────────────

_SAFE_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_SAFE_UNOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def eval_math(expression: str) -> str:
    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_UNOPS:
            return _SAFE_UNOPS[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_BINOPS:
            return _SAFE_BINOPS[type(node.op)](_eval(node.left), _eval(node.right))
        raise ValueError(f"Unsupported expression: {expression}")

    tree = ast.parse(expression.strip(), mode="eval")
    value = _eval(tree)
    return str(int(value)) if value == int(value) else str(value)


async def web_search(query: str) -> str:
    """Search the internet for current facts."""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        return f"Search failed: {exc}"

    parts: list[str] = []
    if data.get("AbstractText"):
        parts.append(data["AbstractText"])
    for topic in data.get("RelatedTopics", [])[:5]:
        if isinstance(topic, dict) and topic.get("Text"):
            parts.append(f"- {topic['Text']}")
    return "\n".join(parts) if parts else f"No results for: {query}"


async def calculate(expression: str) -> str:
    """Evaluate a math expression safely."""
    try:
        return f"Result: {eval_math(expression)}"
    except Exception as exc:
        return f"Error: {exc}"


async def run_python(code: str) -> str:
    """Execute Python code in a restricted sandbox."""
    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
        "enumerate": enumerate, "float": float, "int": int, "len": len,
        "list": list, "max": max, "min": min, "print": print, "range": range,
        "round": round, "set": set, "sorted": sorted, "str": str, "sum": sum,
        "tuple": tuple, "zip": zip,
    }
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout):
            exec(code, {"__builtins__": safe_builtins}, {})  # noqa: S102
    except Exception as exc:
        return f"Execution error: {exc}\n{stdout.getvalue()}"
    out = stdout.getvalue().strip()
    return out or "Code ran successfully (no printed output)."


# ── MCP + Arena tools ────────────────────────────────────────────────────────

async def mcp_call(tool_name: str, arguments: dict, state: RunState) -> str:
    transport = StreamableHttpTransport(url=config.MCP_ENDPOINT)
    try:
        async with Client(transport=transport, name=config.APP_NAME) as client:
            set_association_properties({
                "execution.id": state.execution_id,
                "run.id": state.run_id,
                "agent.id": state.agent_id,
                "task.id": state.task_id,
                "agent.name": config.AGENT_NAME,
                "platform.user_id": config.PLATFORM_USER_ID,
            })
            if state.conversation_id:
                set_conversation_id(state.conversation_id)
            result = await client.call_tool(tool_name, arguments)
            if result is None:
                return f"ERROR: {tool_name} returned no response"
            return "\n".join(
                getattr(b, "text", "") for b in result.content if getattr(b, "text", None)
            )
    except ToolError as exc:
        _log("ERROR", f"{tool_name}: {exc}")
        return f"ERROR: {exc}"
    except Exception as exc:
        _log("ERROR", f"{tool_name}: {exc}")
        return f"ERROR: {exc}"


def _apply_task_from_result(state: RunState, result: str) -> bool:
    """Parse get_tasks response into state. Returns True if a task was loaded."""
    try:
        data = json.loads(result)
        task_obj: Optional[dict] = None
        if isinstance(data, dict) and "id" in data:
            task_obj = data
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            task_obj = data[0]
        if task_obj:
            state.task_id = task_obj["id"]
            state.current_task = task_obj
            state.conversation_id = f"{state.agent_id}-{state.task_id}"
            set_association_properties({"task.id": state.task_id})
            set_conversation_id(state.conversation_id)
            _log("FETCH", f"'{task_obj.get('title')}' L{task_obj.get('level')}")
            return True
    except json.JSONDecodeError:
        pass
    return False


async def bootstrap_arena(state: RunState) -> None:
    """Register + fetch first task via MCP directly (no LLM round-trip)."""
    stack = config.AGENT_STACK or f"Python / ADK / {active_model_name()}"
    reg = await mcp_call(
        "register_agent",
        _register_payload(config.AGENT_NAME, stack),
        state,
    )
    agent_id = _parse_agent_id(reg)
    if agent_id:
        state.agent_id = agent_id
        state.conversation_id = agent_id
        set_association_properties({"agent.id": agent_id})
        set_conversation_id(agent_id)
    state.current_level = _parse_level(reg, state.current_level)
    _log("REGISTER", f"agent_id={state.agent_id} level={state.current_level}")

    if not state.agent_id:
        raise RuntimeError(
            "Registration failed — refresh EPHEMERAL_JWT in .env (Identity & Trace Keys)"
        )

    tasks = await mcp_call(
        "get_tasks",
        {"idToken": config.ID_TOKEN, "agentId": state.agent_id},
        state,
    )
    _apply_task_from_result(state, tasks)


async def fetch_next_task(state: RunState) -> bool:
    """Fetch next task via MCP. Returns False if no task available."""
    state.current_task = None
    state.task_id = ""
    if not state.agent_id:
        return False
    result = await mcp_call(
        "get_tasks",
        {"idToken": config.ID_TOKEN, "agentId": state.agent_id},
        state,
    )
    return _apply_task_from_result(state, result)


def _register_payload(name: str, stack: str) -> dict:
    payload: dict = {"idToken": config.ID_TOKEN, "name": name, "stack": stack}
    if config.LINKEDIN_URL:
        payload["linkedinUrl"] = config.LINKEDIN_URL
    if config.GITHUB_URL:
        payload["githubUrl"] = config.GITHUB_URL
    return payload


def make_tools(state: RunState) -> list:
    async def register_agent(name: str, stack: str) -> str:
        """Register this agent in Agent Arena. Call once at start."""
        result = await mcp_call("register_agent", _register_payload(name, stack), state)
        agent_id = _parse_agent_id(result)
        if agent_id:
            state.agent_id = agent_id
            state.conversation_id = state.agent_id
            set_association_properties({"agent.id": state.agent_id})
            set_conversation_id(state.agent_id)
        state.current_level = _parse_level(result, state.current_level)
        agent_logger.info("Registered", extra={"agent_id": state.agent_id})
        _log("REGISTER", f"agent_id={state.agent_id} level={state.current_level}")
        if "AUTH_ERROR" in result or (
            "Invalid" in result and "token" in result.lower()
        ):
            _log("ERROR", result[:200])
        return result

    async def get_tasks(agent_id: str) -> str:
        """Fetch the currently assigned task for this agent's level."""
        result = await mcp_call(
            "get_tasks", {"idToken": config.ID_TOKEN, "agentId": agent_id}, state
        )
        _apply_task_from_result(state, result)
        return result

    async def skip_task(agent_id: str, task_id: str, reason: str = "") -> str:
        """Abandon the current task and fetch a new one via get_tasks."""
        _log("SKIP", f"{task_id[:8]} reason={reason[:50]}")
        args: dict = {"idToken": config.ID_TOKEN, "agentId": agent_id, "taskId": task_id}
        if reason:
            args["reason"] = reason
        return await mcp_call("skip_task", args, state)

    async def submit_task(agent_id: str, task_id: str, content: str) -> str:
        """Submit your answer. Scored 0-100. Score >= 70 means LEVEL_UP."""
        state.execution_id = str(uuid.uuid4())
        set_association_properties({"execution.id": state.execution_id, "task.id": task_id})
        task_logger.info("Submitting", extra={"task_id": task_id})

        result = await mcp_call("submit_task", {
            "idToken": config.ID_TOKEN,
            "agentId": agent_id,
            "taskId": task_id,
            "executionId": state.execution_id,
            "content": content,
            "metadata": {
                "agent_name": config.AGENT_NAME,
                "agent_stack": config.AGENT_STACK,
                "platform_user_id": config.PLATFORM_USER_ID,
                "run_id": state.run_id,
                "model": active_model_name(),
            },
        }, state)

        score, levelled_up, level = parse_submission_result(result)
        title = (
            state.current_task.get("title", task_id)
            if state.current_task else task_id
        )
        state.record(
            level or state.current_level, title, score, levelled_up,
            task_id=task_id, raw_response=result,
        )
        _log("SCORE", f"{score}/100 {'🚀 LEVEL_UP!' if levelled_up else ''}")
        print(state.scoreboard(active_model_name()))
        return result

    async def report_status() -> str:
        """Report current agent progress and score history."""
        return json.dumps(state.summary(active_model_name()), indent=2)

    return [
        register_agent, get_tasks, skip_task, submit_task, report_status,
        web_search, calculate, run_python,
    ]


def build_agent(state: RunState) -> LlmAgent:
    stack = config.AGENT_STACK or f"Python / ADK / {active_model_name()} / Traceloop"
    return LlmAgent(
        name="arena_agent",
        model=active_model(),
        instruction=build_system_prompt(config.AGENT_NAME, stack),
        tools=make_tools(state),
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=config.TEMPERATURE,
            max_output_tokens=config.MAX_OUTPUT_TOKENS,
        ),
    )


async def run_turn(
    runner: Runner,
    session_id: str,
    message: str,
) -> str:
    """Send one message; collect tool activity and final text from the ADK stream."""
    content = genai_types.Content(
        role="user", parts=[genai_types.Part(text=message)]
    )
    final_text = ""
    async for event in runner.run_async(
        user_id=config.USER_ID,
        session_id=session_id,
        new_message=content,
    ):
        if not event.content or not event.content.parts:
            continue
        for part in event.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                _log("AGENT", f"→ {fc.name}")
            elif hasattr(part, "function_response") and part.function_response:
                fr = part.function_response
                preview = str(fr.response)[:120].replace("\n", " ")
                _log("AGENT", f"← {fr.name} {preview}")
            elif hasattr(part, "text") and part.text:
                final_text = part.text
    return final_text


async def run_turn_with_retry(
    runner: Runner,
    session_id: str,
    message: str,
) -> str:
    """Retry LLM turns on 503/429 with backoff and model fallback."""
    delay = config.LLM_RETRY_BASE_SEC
    last_exc: BaseException | None = None

    for attempt in range(1, config.LLM_MAX_RETRIES + 1):
        try:
            await _throttle_llm()
            return await run_turn(runner, session_id, message)
        except BaseException as exc:
            last_exc = exc
            if not _is_transient_llm_error(exc):
                raise
            retry_after = _parse_retry_delay_sec(exc)
            wait = max(delay, retry_after or 0) + 2
            _log(
                "WARN",
                f"LLM busy/error ({attempt}/{config.LLM_MAX_RETRIES}) "
                f"[{active_model_name()}]: retry in {wait:.0f}s — {str(exc)[:80]}",
            )
            if attempt >= 2:
                _rotate_model(runner)
            await asyncio.sleep(min(wait, 120))
            delay = min(max(delay * 1.5, wait), 120)

    assert last_exc is not None
    raise last_exc


async def ensure_arena_ready(state: RunState) -> bool:
    """Bootstrap or refresh Arena connection; retry until a task is available."""
    config.refresh_runtime_secrets()
    try:
        await bootstrap_arena(state)
        if state.current_task and state.task_id:
            return True
    except Exception as exc:
        _log("WARN", f"Arena bootstrap failed: {exc}")
    return False


async def wait_for_task(state: RunState) -> bool:
    """Poll Arena until a task is available (continuous mode)."""
    while True:
        config.refresh_runtime_secrets()
        if state.agent_id and await fetch_next_task(state):
            return True
        if not state.agent_id and await ensure_arena_ready(state):
            return True
        _log(
            "IDLE",
            f"No task available — polling again in {config.IDLE_POLL_SEC}s "
            "(refresh EPHEMERAL_JWT in .env if auth errors persist)",
        )
        await asyncio.sleep(config.IDLE_POLL_SEC)


async def solve_current_task(
    runner: Runner,
    state: RunState,
    task_num: int,
) -> None:
    """Run one task turn (+ recovery submit if needed)."""
    task = state.current_task
    if not task or not state.task_id:
        return

    task_type = detect_task_type(task.get("title", ""), task.get("description", ""))
    print(f"\n{'━' * 60}")
    _log("TASK", f"#{task_num} | {task.get('title')} | {task_type.upper()}")
    print(f"{'━' * 60}")

    prev_attempted = state.tasks_attempted
    prompt = build_task_prompt(task, state.agent_id, state.task_id)
    try:
        await run_turn_with_retry(runner, state.run_id, prompt)
    except BaseException as exc:
        _log("ERROR", f"Task solve failed: {exc}")
        await asyncio.sleep(config.ERROR_COOLDOWN_SEC)
        return

    if state.tasks_attempted <= prev_attempted:
        _log("WARN", "Not submitted — recovery turn...")
        try:
            await run_turn_with_retry(
                runner,
                state.run_id,
                f"Submit NOW: submit_task(agent_id='{state.agent_id}', "
                f"task_id='{state.task_id}', content=<precise answer with "
                f"**Answer:** first). Use calculate/run_python if needed.",
            )
        except BaseException as exc:
            _log("ERROR", f"Recovery failed: {exc}")
            await asyncio.sleep(config.ERROR_COOLDOWN_SEC)


async def run_session(runner: Runner, state: RunState) -> None:
    """Main loop — runs continuously until RUN_CONTINUOUS=false or Ctrl+C."""
    _log("REGISTER", "Bootstrapping (direct MCP)...")
    if not await ensure_arena_ready(state):
        if not config.RUN_CONTINUOUS:
            raise RuntimeError("No task available from Arena.")
        await wait_for_task(state)

    task_num = 0
    while True:
        if config.MAX_TASKS > 0 and task_num >= config.MAX_TASKS and not config.RUN_CONTINUOUS:
            break

        if not state.current_task or not state.task_id:
            if not config.RUN_CONTINUOUS:
                _log("DONE", "No active task — stopping.")
                break
            await wait_for_task(state)
            continue

        task_num += 1
        await solve_current_task(runner, state, task_num)

        if (
            config.REPORT_EVERY_N_TASKS > 0
            and task_num % config.REPORT_EVERY_N_TASKS == 0
        ):
            print(state.scoreboard(active_model_name()))
            path = state.export_report(active_model_name())
            _log("REPORT", f"Checkpoint → {path}")

        _log("LOOP", "Fetching next task...")
        if await fetch_next_task(state):
            continue

        if not config.RUN_CONTINUOUS:
            _log("DONE", "No more tasks.")
            break

        state.current_task = None
        state.task_id = ""
        await wait_for_task(state)

    print(state.scoreboard(active_model_name()))
    report_path = state.export_report(active_model_name())
    _log("DONE", f"Evaluation report → {report_path}")
    agent_logger.info("Run complete", extra=state.summary(active_model_name()))


@workflow(name="arena_adk_run")
async def run() -> None:
    if config.kimi_primary():
        config.exit_if_invalid(check_gemini=False)
    else:
        config.exit_if_invalid(check_gemini=True)

    state = RunState()
    _init_llm_primary()
    model_name = active_model_name()
    backup = (
        f"  |  Gemini backup: {config.MODEL}"
        if config.kimi_primary() and config.gemini_available()
        else (
            f"  |  Kimi backup: {config.KIMI_MODEL}"
            if config.gemini_available() and config.kimi_available()
            else ""
        )
    )
    mode = "continuous" if config.RUN_CONTINUOUS else f"max {config.MAX_TASKS} tasks"

    print(f"\n{'═' * 60}")
    print(f"  AGENT ARENA — {config.AGENT_NAME}")
    print(f"  Primary: {model_name}  |  Mode: {mode}{backup}")
    print(f"{'═' * 60}\n")

    set_association_properties({
        "run.id": state.run_id,
        "agent.name": config.AGENT_NAME,
    })

    sessions = InMemorySessionService()
    await sessions.create_session(
        app_name=config.APP_NAME,
        user_id=config.USER_ID,
        session_id=state.run_id,
    )
    runner = Runner(
        agent=build_agent(state),
        app_name=config.APP_NAME,
        session_service=sessions,
    )
    _apply_active_model(runner)
    await _verify_kimi_or_fallback(runner)

    await run_session(runner, state)


if __name__ == "__main__":
    import os
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    init_tracing()
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    while True:
        try:
            asyncio.run(run())
            if not config.RUN_CONTINUOUS:
                break
            _log("LOOP", f"Session ended — restarting in {config.ERROR_COOLDOWN_SEC}s...")
            time.sleep(config.ERROR_COOLDOWN_SEC)
        except KeyboardInterrupt:
            _log("DONE", "Stopped by user.")
            break
        except Exception as exc:
            _log("ERROR", f"Fatal error: {exc} — restarting in {config.ERROR_COOLDOWN_SEC}s...")
            time.sleep(config.ERROR_COOLDOWN_SEC)
            if not config.RUN_CONTINUOUS:
                raise
