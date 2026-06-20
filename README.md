# KakashiTheHatake — Agent Arena

Autonomous **Google ADK + FastMCP** agent and **Cursor MCP** workflow for [Agent Arena](https://agent-arena.dev).

## Production layout

```
AgentArena/
├── agent.py              # Autonomous ADK runner
├── config.py             # All secrets from environment (.env)
├── arena_mcp/            # MCP bridge, poller, CLI, content organizer
├── content/              # ★ Ship this — canonical Q&A task library (30 tasks)
├── docs/                 # Full documentation
├── deploy/               # GCP Cloud Run Job
├── scripts/              # Release utilities (secret scan)
├── SECURITY.md           # Credential handling
├── RELEASE.md            # Release checklist
└── runs/                 # Runtime only (gitignored except README)
```

## Active agents (7)

| Label | Name | Agent ID | Level |
|-------|------|----------|-------|
| agent-1 | KakashiTheHatake-R2 | `ODPs4yeASTy9LMqftdK7` | 8 |
| agent-2 | KakashiTheHatake-Cursor-R2 | `D7CfR6Pg35T6ZtLn76e3` | 6 |
| agent-3 | KakashiTheHatake-Validated | `ZBpREutq1QTfZmMYuQvT` | 5 |
| agent-4 | KakashiTheHatake-MaxScore | `7t1mF2xWrek9Db4yNaPt` | 7 |
| agent-5 | KakashiTheHatake-FinalAgent | `f7Tlu9Bk9R6qkKPbQH8V` | 6 |
| agent-6 | KakashiTheHatake-CompleteRun | `xKTGUkRCYRJOXLPDWpJe` | 6 |
| agent-7 | KakashiTheHatake-AllLevels | `jnGYcUdZ3WVyptt6tBwq` | 6 |

Config: [`arena_mcp/agents.json`](arena_mcp/agents.json) — copy [`agents.json.example`](arena_mcp/agents.json.example) for new setups.

## Quick start

```powershell
copy .env.example .env          # EPHEMERAL_JWT, GEMINI_API_KEY, … (never commit .env)
pip install -r requirements.txt
python validate.py

# Monitor all agents (until FINISH)
python arena_mcp\cursor_poll.py

# One-shot Arena CLI
python arena_mcp\cursor_run.py get <agent_id>
python arena_mcp\cursor_run.py submit <agent_id> <task_id> content\tasks\<slug>\submission.md
```

## Task library (release artifact)

**30 tasks** with verified submissions:

```powershell
python arena_mcp\organize_content.py   # rebuild content/ from runs/
```

Browse [`content/tasks/`](content/tasks/) or [`content/manifest.json`](content/manifest.json).

## Security & release

```powershell
python scripts\check_secrets.py     # scan for leaked keys before git push
```

See [SECURITY.md](SECURITY.md) and [RELEASE.md](RELEASE.md).

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/README.md](docs/README.md) | Index |
| [docs/CURSOR.md](docs/CURSOR.md) | Cursor MCP workflow, 7-agent polling |
| [docs/GUIDE.md](docs/GUIDE.md) | `agent.py`, scoring, troubleshooting |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | GCP deploy |

Say **FINISH** to stop background monitoring.
