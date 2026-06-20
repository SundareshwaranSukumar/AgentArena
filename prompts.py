"""
Dynamic prompt engine — optimized for precise, fast Arena submissions.
"""

from __future__ import annotations

TASK_PATTERNS = {
    "code": [
        "code", "function", "implement", "write a", "program", "script",
        "class", "algorithm", "api", "method", "library", "module", "package",
        "build", "create a", "develop", "application", "service", "endpoint",
    ],
    "debug": [
        "debug", "fix", "error", "bug", "issue", "broken", "fails",
        "exception", "traceback", "crash", "wrong", "incorrect", "not working",
    ],
    "explain": [
        "explain", "describe", "what is", "how does", "why", "difference between",
        "concept", "theory", "overview", "introduction", "compare", "contrast",
    ],
    "optimize": [
        "optimize", "performance", "efficient", "slow", "bottleneck", "memory",
        "speed", "complexity", "scale", "improve", "faster", "latency",
    ],
    "design": [
        "design", "architecture", "system", "database schema", "pattern",
        "structure", "model", "diagram", "microservice",
    ],
    "test": [
        "test", "unit test", "pytest", "assert", "coverage", "mock", "testing",
    ],
    "data": [
        "data", "csv", "json", "sql", "query", "database", "etl", "pipeline",
        "pandas", "dataframe",
    ],
    "math": [
        "calculate", "compute", "sum", "equation", "formula", "probability",
        "percentage", "integer", "prime", "factorial", "modulo",
    ],
    "security": [
        "security", "auth", "jwt", "oauth", "encrypt", "hash", "vulnerability",
        "xss", "csrf", "sql injection",
    ],
}


def detect_task_type(title: str = "", description: str = "") -> str:
    text = f"{title} {description}".lower()
    scores = {
        task_type: sum(1 for kw in keywords if kw in text)
        for task_type, keywords in TASK_PATTERNS.items()
    }
    if not scores or max(scores.values(), default=0) == 0:
        return "general"
    return max(scores, key=scores.get)


def build_task_prompt(task: dict, agent_id: str, task_id: str) -> str:
    """Single-turn prompt: tool-verify → precise answer → submit."""
    task_type = detect_task_type(task.get("title", ""), task.get("description", ""))
    title = task.get("title", "Task")
    desc = task.get("description", "")

    tool_hint = {
        "math": "Use calculate() for every number — never estimate.",
        "code": "Use run_python() to verify output before submit.",
        "debug": "Use run_python() to confirm the fix runs.",
        "data": "Use run_python() or calculate() to validate results.",
    }.get(task_type, "Use calculate/web_search/run_python when they improve accuracy.")

    return f"""Solve this Arena task in ONE turn. Be fast and precise.

TYPE: {task_type.upper()}
TITLE: {title}
DESCRIPTION:
{desc}

SPEED RULES:
1. {tool_hint}
2. Structure submit_task content as:
   **Answer:** <direct final result first, one line if possible>
   **Solution:** <minimal steps — no fluff, no task restatement>
   **Verification:** <tool output or proof, if used>
3. Temperature is 0 — give exact values, code, and facts only.
4. Call submit_task NOW with agent_id="{agent_id}", task_id="{task_id}".
5. Do not ask questions. Do not skip unless truly impossible.

Target score: 90+. Submit in this turn."""


def build_system_prompt(agent_name: str, agent_stack: str) -> str:
    return f"""You are {agent_name}, a precision Arena solver ({agent_stack}).

GOAL: Maximum score (90+) with minimum latency. Score >= 70 levels up.

TOOLS:
- submit_task / get_tasks / skip_task / register_agent — Arena MCP
- calculate — exact math (always for numbers)
- run_python — verify code/logic before submit
- web_search — only when facts are not in the task text

BEHAVIOR:
- Lead every answer with the direct result, then brief justification.
- Never guess numbers or code output — use tools first.
- No preamble, no "Certainly!", no repeating the question.
- One task_id per submit. Autonomous — never ask the user anything.

Identity: {agent_name} | {agent_stack}"""
