# Agent Arena Documentation

Complete reference for the **KakashiTheHatake** Agent Arena project — autonomous ADK agent, Cursor MCP workflow, production task library, and GCP deployment.

## Reading order

| Doc | Contents |
|-----|----------|
| [PROBLEM.md](./PROBLEM.md) | What Agent Arena is, constraints, success criteria |
| [GUIDE.md](./GUIDE.md) | Architecture, `agent.py` run loop, scoring, troubleshooting |
| [CURSOR.md](./CURSOR.md) | **Cursor workflow** — MCP bridge, 5-agent polling, submissions |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | GCP Cloud Run Job deployment |
| [../RELEASE.md](../RELEASE.md) | Production release checklist |
| [../SECURITY.md](../SECURITY.md) | **Secrets** — what never goes in git |
| [../content/README.md](../content/README.md) | **Task library** — canonical Q&A (ship in releases) |
| [../content/guides/scoring.md](../content/guides/scoring.md) | Scoring methodology and best practices |

## Project layout

```
agent.py, config.py, prompts.py   ← Autonomous runner
arena_mcp/                        ← MCP bridge, poller, CLI, organizer
content/                          ← Production Q&A (tracked in git)
docs/                             ← This folder
scripts/                          ← check_secrets.py (pre-release)
SECURITY.md                       ← Credential policy
runs/                             ← Runtime logs (gitignored)
deploy/                           ← GCP manifests
```

## Two ways to compete

```
┌─────────────────────────────────────────────────────────────────┐
│  Mode A — agent.py (autonomous)                                 │
│  python agent.py  →  ADK + Gemini/Kimi  →  MCP tools in trace   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Mode B — Cursor + MCP (interactive)                            │
│  Cursor chat  →  agent-arena MCP  →  research + verify + submit │
│  arena_mcp/cursor_poll.py monitors all agents in background     │
└─────────────────────────────────────────────────────────────────┘
```

## Quick start

```powershell
copy .env.example .env          # fill EPHEMERAL_JWT, GEMINI_API_KEY, etc.
pip install -r requirements.txt
python validate.py
python scripts\check_secrets.py # before any git commit

# Autonomous run
python agent.py

# Cursor-driven (see CURSOR.md)
python arena_mcp\cursor_poll.py
python arena_mcp\cursor_run.py get <agent_id>

# Rebuild production task library after sessions
python arena_mcp\organize_content.py
```

## Active agents (7)

| Label | Name | Agent ID | Peak level |
|-------|------|----------|------------|
| agent-1 | KakashiTheHatake-R2 | `ODPs4yeASTy9LMqftdK7` | 8 |
| agent-2 | KakashiTheHatake-Cursor-R2 | `D7CfR6Pg35T6ZtLn76e3` | 6 |
| agent-3 | KakashiTheHatake-Validated | `ZBpREutq1QTfZmMYuQvT` | 5 |
| agent-4 | KakashiTheHatake-MaxScore | `7t1mF2xWrek9Db4yNaPt` | 7 |
| agent-5 | KakashiTheHatake-FinalAgent | `f7Tlu9Bk9R6qkKPbQH8V` | 6 |
| agent-6 | KakashiTheHatake-CompleteRun | `xKTGUkRCYRJOXLPDWpJe` | 6 |
| agent-7 | KakashiTheHatake-AllLevels | `jnGYcUdZ3WVyptt6tBwq` | 6 |

All seven are listed in `arena_mcp/agents.json` and monitored by `cursor_poll.py` until **FINISH**.

## External links

- [Agent Arena Platform](https://agent-arena.dev)
- [Official Tutorial](https://tutorial.agent-arena.dev/)
- [Reference Bot](https://github.com/xprilion/agent-arena-bot)
