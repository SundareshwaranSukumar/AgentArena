# Solution Guide

Autonomous **Google ADK + FastMCP** agent following the [official tutorial](https://tutorial.agent-arena.dev/) and [presentation reference bot](https://github.com/xprilion/agent-arena-bot).

> **Also using Cursor?** See [CURSOR.md](./CURSOR.md) for the dual-agent MCP workflow, polling, and submission strategy.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  agent.py — main loop                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ prompts.py  │  │ evaluation.py│  │  tracing.py   │  │
│  │ task-type   │  │ RunState     │  │  Traceloop    │  │
│  │ detection   │  │ scoreboard   │  │  OTel logs    │  │
│  │ dynamic     │  │ JSON export  │  │               │  │
│  │ prompts     │  │              │  │               │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│                          │                              │
│  Google ADK LlmAgent ────┼── Arena tools (MCP)          │
│  (+ Kimi via LiteLLM)    └── Helper tools (local)      │
└──────────────────────────┬──────────────────────────────┘
                           │ FastMCP HTTP
                           ▼
              Agent Arena MCP Server (/mcp)
```

## Dual-mode operation

| Mode | Entry | Best for |
|------|-------|----------|
| **Autonomous** | `python agent.py` | Hands-off runs, traced tool calls via ADK |
| **Cursor MCP** | Chat + `arena_mcp/*` | Hard tasks, image OCR, manual verification |

Both modes use the same MCP endpoint and `.env` credentials. See [CURSOR.md](./CURSOR.md).

## Production task library

After Arena sessions, canonical Q&A is organized under [`content/`](../content/):

```powershell
python arena_mcp\organize_content.py
```

Each task has `content/tasks/<slug>/submission.md` and optional `verify.py`. Ship `content/` in releases; keep ephemeral logs in `runs/` (gitignored). See [RELEASE.md](../RELEASE.md).

## Credentials

| Credential | Env variable | Purpose |
|------------|--------------|---------|
| Platform User ID | `PLATFORM_USER_ID` | Static UID — metadata & traces |
| Ephemeral JWT | `EPHEMERAL_JWT` | MCP `idToken` (expires ~1h) |
| Traceloop API Key | `TRACELOOP_API_KEY` | Trace export |
| Gemini API Key | `GEMINI_API_KEY` | LLM ([AI Studio](https://aistudio.google.com)) |
| Kimi API Key | `KIMI_API_KEY` | Optional primary LLM (`LLM_PRIMARY=kimi`) |

Copy platform keys from **Identity & Trace Keys** on [agent-arena.dev](https://agent-arena.dev).

**Do not** put `PLATFORM_USER_ID` in `EPHEMERAL_JWT` — the JWT is the long `eyJ…` string.

```bash
cp .env.example .env
# Edit .env
```

### Key settings (`config.py`)

| Variable | Purpose |
|----------|---------|
| `AGENT_NAME` | Leaderboard name (default: KakashiTheHatake) |
| `LLM_PRIMARY` | `kimi` or `gemini` — Kimi first, Gemini fallback |
| `MODEL` | Gemini model (`gemini-2.5-flash`, `gemini-3.5-flash`) |
| `RUN_CONTINUOUS` | `true` — poll Arena when idle instead of exiting |
| `MAX_TASKS` | Tasks per run (0 = unlimited in continuous mode) |
| `TEMPERATURE` | `0.1` recommended for precision |
| `EVAL_OUTPUT_DIR` | JSON evaluation reports (`runs/`) |

Cast AI keys (`castai_v1_…`) auto-route to `https://llm.cast.ai/openai/v1`.

## Run locally

```bash
pip install -r requirements.txt
python validate.py
python agent.py
```

### Continuous mode

With `RUN_CONTINUOUS=true`, the agent:
- Polls every 30s when no tasks are available
- Reloads `.env` while polling (refresh JWT without restart)
- Falls back Gemini → Kimi on API errors
- Writes checkpoint JSON to `runs/` every 10 tasks

### Cursor continuous monitor

```powershell
python arena_mcp\cursor_poll.py   # both agents, 30s interval
```

Logs: `runs/cursor_poll.log` | Pending task: `runs/pending_task.json`

## Run lifecycle (`agent.py`)

```
1. Bootstrap
   register_agent → get_tasks (fetch first task, do NOT submit)

2. For each task:
   a. Detect task type (code, debug, explain, …)
   b. Build dynamic prompt (analyze + solve + submit)
   c. ADK turn with helper tools (web_search, calculate, run_python)
   d. Recovery turn if submit was missed
   e. get_tasks for next challenge

3. Finalize
   report_status() → scoreboard → export JSON report
```

## Tools available to the LLM

### Arena MCP tools (required)

| Tool | When |
|------|------|
| `register_agent` | Once at start |
| `get_tasks` | Before each task |
| `submit_task` | After solving |
| `skip_task` | Impossible or stuck tasks |
| `report_status` | End of run summary |

### Helper tools (boost scores)

| Tool | When |
|------|------|
| `web_search` | Factual / current-info tasks |
| `calculate` | Exact math |
| `run_python` | Verify code/algorithms before submit |

## Scoring strategy

| Tip | Impact |
|-----|--------|
| Use helper tools before submit | Avoids 60–65 methodology penalties |
| Search first | 65 → 85 on factual tasks |
| Exact math via `calculate` | Avoids LLM arithmetic errors |
| Verify with `run_python` | Catches logic bugs |
| `temperature=0.1` | More precise technical answers |
| Task-type prompts | Tailored structure per category |

Level-up threshold: **score ≥ 70**.

## Project files

| File | Role |
|------|------|
| `agent.py` | Main entry — ADK agent, tools, run loop |
| `prompts.py` | Task-type detection + dynamic prompts |
| `config.py` | Environment-based configuration |
| `evaluation.py` | RunState, scoreboard, JSON export |
| `tracing.py` | Traceloop / OpenTelemetry setup |
| `validate.py` | Pre-flight credential check |
| `arena_mcp/arena_bridge.py` | Cursor stdio MCP bridge |
| `arena_mcp/cursor_poll.py` | Dual-agent background poller |
| `arena_mcp/cursor_run.py` | CLI get/submit/skip |
| `arena_mcp/export_archive.py` | Archive logs and task history |
| `runs/archive/` | Exported session data |

## Evaluation reports

After each run, JSON is written to `runs/<run_id>.json`:

```json
{
  "run_id": "...",
  "agent_id": "xvSwNAIPH6ZcazzPMLbv",
  "final_level": 7,
  "total_score": 1856,
  "tasks_attempted": 6,
  "level_history": [...]
}
```

Full session archive: `python arena_mcp/export_archive.py`

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Token expired | Refresh `EPHEMERAL_JWT` (~1h TTL) |
| Kimi 402 credits | Falls back to Gemini; add credits or set `LLM_PRIMARY=gemini` |
| Gemini 429/503 | Rate-limit backoff + model rotation in `agent.py` |
| Task not submitted | Recovery turn runs automatically; check Traceloop traces |
| Low scores via Cursor CLI | Use MCP tools in chat or `agent.py` for traced helpers |
| Stuck at Level 7 | See `runs/archive/agent-1-kakashithehatake/WHY-STUCK-AT-L7.md` |
| MCP timeout | Fresh connection per call is by design |

## Deploy to GCP

See [DEPLOYMENT.md](./DEPLOYMENT.md).

## External links

- [Agent Arena Platform](https://agent-arena.dev)
- [Complete Tutorial](https://tutorial.agent-arena.dev/)
- [Presentation Reference Bot](https://github.com/xprilion/agent-arena-bot)
- [Google ADK Docs](https://google.github.io/adk-docs/)
