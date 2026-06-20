# Cursor Workflow

How this project uses **Cursor IDE** to compete on [Agent Arena](https://agent-arena.dev) alongside the autonomous `agent.py` runner.

## Overview

We run **seven agents** on the same Arena account and monitor all from Cursor:

| Label | Name | Agent ID | Role |
|-------|------|----------|------|
| **agent-1** | KakashiTheHatake-R2 | `ODPs4yeASTy9LMqftdK7` | Primary — L8 |
| **agent-2** | KakashiTheHatake-Cursor-R2 | `D7CfR6Pg35T6ZtLn76e3` | Cursor replay — L6 |
| **agent-3** | KakashiTheHatake-Validated | `ZBpREutq1QTfZmMYuQvT` | Validate before submit — L5 |
| **agent-4** | KakashiTheHatake-MaxScore | `7t1mF2xWrek9Db4yNaPt` | Session-optimized — L7 |
| **agent-5** | KakashiTheHatake-FinalAgent | `f7Tlu9Bk9R6qkKPbQH8V` | Verified + researched — L6 |
| **agent-6** | KakashiTheHatake-CompleteRun | `xKTGUkRCYRJOXLPDWpJe` | Full climb run — L6 |
| **agent-7** | KakashiTheHatake-AllLevels | `jnGYcUdZ3WVyptt6tBwq` | All-levels attempt — L6 |

Single source of truth: [`arena_mcp/agents.json`](../arena_mcp/agents.json).

All agents share the same `.env` credentials but have **separate Arena registrations** (different `agentId`, separate level/score progress).

```
┌──────────────────────────────────────────────────────────────────┐
│  Cursor IDE                                                      │
│  ┌─────────────┐    stdio     ┌─────────────────────────────┐  │
│  │ Chat / MCP  │ ────────────►│ arena_mcp/arena_bridge.py   │  │
│  └─────────────┘              └──────────────┬──────────────┘  │
│  ┌─────────────┐                             │ HTTP MCP        │
│  │ cursor_poll │ ── get_tasks (all agents) ──┤                 │
│  └─────────────┘                             ▼                 │
│  ┌─────────────┐              Agent Arena MCP Server            │
│  │ cursor_run  │ ── submit / skip / get                         │
│  └─────────────┘                                                 │
└──────────────────────────────────────────────────────────────────┘
```

## Production task library

Canonical questions & answers live in [`content/`](../content/), not `runs/`:

```
content/
├── manifest.json
├── tasks/<slug>/
│   ├── README.md
│   ├── submission.md    ← best answer
│   └── verify.py        ← local validation script
├── agents/              ← per-agent submission copies
└── guides/scoring.md
```

Rebuild after sessions:

```powershell
python arena_mcp\organize_content.py
```

Submit from the library:

```powershell
python arena_mcp\cursor_run.py submit <agent_id> <task_id> content\tasks\ticker\submission.md
```

## MCP setup in Cursor

### `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "agent-arena": {
      "command": "${workspaceFolder}/.venv/Scripts/python.exe",
      "args": ["${workspaceFolder}/arena_mcp/arena_bridge.py"],
      "envFile": "${workspaceFolder}/.env"
    }
  }
}
```

Use **`agent-arena`** (stdio bridge), **not** `agent-arena-remote`.

### Credentials (`.env`)

| Variable | Purpose |
|----------|---------|
| `EPHEMERAL_JWT` | Long `eyJ…` string — sent as `idToken` (~1h TTL) |
| `PLATFORM_USER_ID` | Static UID for metadata/traces — **not** the JWT |
| `GEMINI_API_KEY` | For `agent.py` autonomous runs |
| `KIMI_API_KEY` | Optional primary LLM |

Refresh `EPHEMERAL_JWT` from [agent-arena.dev](https://agent-arena.dev) → **Identity & Trace Keys** when you see `AUTH_ERROR`.

## Key files

| File | Purpose |
|------|---------|
| `arena_mcp/arena_bridge.py` | Stdio MCP server for Cursor |
| `arena_mcp/cursor_run.py` | CLI: register, get, submit, skip |
| `arena_mcp/cursor_poll.py` | **Multi-agent poller** — all agents in `agents.json`, every 30s |
| `arena_mcp/level_runner.py` | **Full level climb** — content submissions + score logging |
| `arena_mcp/organize_content.py` | Build `content/` task library from `runs/` |
| `arena_mcp/export_archive.py` | Export logs/transcripts to `runs/archive/` |
| `.cursor/rules/agent-arena.mdc` | Autonomous solve loop rule |

## Continuous monitoring (until FINISH)

### Start the poller

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Start-Process -FilePath ".\.venv\Scripts\python.exe" `
  -ArgumentList "arena_mcp\cursor_poll.py" `
  -WindowStyle Hidden `
  -RedirectStandardOutput "runs\cursor_poll.out" `
  -RedirectStandardError "runs\cursor_poll.err"
```

### What it does

Every **30 seconds**:
1. Calls `get_tasks` for **every agent** in `agents.json`
2. Appends to `runs/cursor_poll.log`
3. Writes `runs/agents_status.json`
4. On new task → `runs/pending_task.json`

### Stop

Say **FINISH** or create `runs/FINISH`.

## Solving a task

### 1. Check for known answers

```powershell
dir content\tasks\ticker\
type content\tasks\ticker\submission.md
```

### 2. Research and validate

- Web search for factual tasks; cite sources
- Write/run `content/tasks/<slug>/verify.py` or `runs/verify_*.py`
- Decode base64 images from task JSON → `content/assets/mmv1.png`

### 3. Submit

```powershell
python arena_mcp\cursor_run.py submit <agent_id> <task_id> content\tasks\<slug>\submission.md
```

Format:

```markdown
**Answer:** <direct result first>

**Solution:** <steps, code, reasoning>

**Verification:** <inline proof — do not claim untraced scripts>
```

### 4. Score and level-up

- **≥ 70** → `LEVEL_UP`
- **< 70** with correct answer → `skip_task`, try alternate
- **`ALL_TASKS_ATTEMPTED`** → wait for new platform tasks

## Scoring: tool traces matter

| Channel | Tool traces? | Typical score |
|---------|--------------|---------------|
| Cursor MCP in chat | ✅ | 75–85+ |
| `agent.py` + healthy LLM | ✅ | 70–90+ |
| `cursor_run.py` CLI only | ❌ | 60–65 penalty |

See [`content/guides/scoring.md`](../content/guides/scoring.md).

## Release workflow

When sessions are complete:

```powershell
python arena_mcp\organize_content.py
$env:ARENA_TRANSCRIPT_PATH = "path\to\session.jsonl"   # optional
python arena_mcp\export_archive.py
```

See [RELEASE.md](../RELEASE.md).

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `AUTH_ERROR` | Refresh `EPHEMERAL_JWT` in `.env` |
| Poller stops | Use detached `Start-Process` (above) |
| Submit fails | Pass a **file path**, not inline text |
| Low scores | Use MCP tools in chat; see scoring guide |
| Image URL fails | Use base64 from task or `content/assets/` |

## MCP tools reference

| Tool | Args | When |
|------|------|------|
| `register_agent` | `name?`, `stack?` | Once per new agent |
| `get_tasks` | `agent_id` | Before each task |
| `submit_task` | `agent_id`, `task_id`, `content` | After solve + verify |
| `skip_task` | `agent_id`, `task_id`, `reason?` | Stuck / score too low |

Endpoint: `https://agent-arena-623774504237.asia-southeast1.run.app/mcp`
