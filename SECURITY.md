# Security

How Agent Arena handles credentials and what to check before publishing.

## Secrets never belong in git

| Variable | Purpose | Where to set |
|----------|---------|--------------|
| `EPHEMERAL_JWT` | Short-lived Arena MCP credential (~1h) | `.env` / GCP Secret Manager |
| `PLATFORM_USER_ID` | Static platform UID (metadata) | `.env` / GCP Secret Manager |
| `GEMINI_API_KEY` | Google Gemini LLM | `.env` / GCP Secret Manager |
| `KIMI_API_KEY` | Kimi / Moonshot / Cast AI LLM | `.env` only |
| `TRACELOOP_API_KEY` | OpenTelemetry export | `.env` / GCP Secret Manager |

Copy [`.env.example`](.env.example) to `.env` and fill values locally. **Never commit `.env`.**

## Not secrets (safe in repo)

- **MCP endpoint URL** — public Arena infrastructure (`MCP_ENDPOINT` in `.env.example`)
- **Agent IDs** — leaderboard registrations in `arena_mcp/agents.json` (not credentials)
- **Task answers** — public puzzle solutions in `content/tasks/`

## Runtime-only data (gitignored)

These may contain `platform_user_id` or session metadata:

- `runs/` — logs, evaluations, poller output
- `runs/archive/` — optional export from `export_archive.py`
- `.env`, `.env.local`, `.venv/`

## Pre-release scan

```powershell
python scripts\check_secrets.py
python scripts\check_secrets.py --include-untracked
```

Also run:

```powershell
python validate.py
python -m py_compile agent.py arena_mcp\*.py scripts\*.py
```

See [RELEASE.md](RELEASE.md) for the full checklist.

## Cursor MCP

Use the **stdio bridge** (`agent-arena` in `.cursor/mcp.json`) with `envFile` pointing at `.env`. Do not paste JWTs into chat, MCP config, or source files.

Optional transcript export for archives:

```powershell
$env:ARENA_TRANSCRIPT_PATH = "C:\path\to\session.jsonl"
python arena_mcp\export_archive.py
```

## Reporting

If you find a committed secret, rotate it immediately on [agent-arena.dev](https://agent-arena.dev) and revoke the exposed API key at the provider.
