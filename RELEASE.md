# Production Release Checklist

Use this when tagging a release after Arena sessions complete.

## 1. Stop active monitoring

Say **FINISH** in Cursor or create `runs/FINISH`. Confirm poller exited.

## 2. Build the task library

```powershell
python arena_mcp\organize_content.py
```

Output: [`content/`](content/) — **30 tasks** with `submission.md`, `verify.py`, and `manifest.json`.

Optional local archive (gitignored):

```powershell
$env:ARENA_TRANSCRIPT_PATH = "path\to\session.jsonl"   # optional
python arena_mcp\export_archive.py
```

## 3. Verify release contents

| Include | Path |
|---------|------|
| Task Q&A | `content/tasks/**` |
| Agent registry | `arena_mcp/agents.json` |
| MCP bridge | `arena_mcp/arena_bridge.py` |
| Docs | `docs/`, `SECURITY.md` |
| Autonomous runner | `agent.py`, `config.py`, `prompts.py` |
| Deploy | `deploy/`, `Dockerfile`, `cloudbuild.yaml` |
| Secret scan | `scripts/check_secrets.py` |

| Exclude | Reason |
|---------|--------|
| `.env`, `.env.local` | Secrets |
| `runs/*` (except README) | Ephemeral runtime (may contain platform_user_id) |
| `.venv/` | Local environment |

## 4. Sanity checks

```powershell
python scripts\check_secrets.py
python scripts\check_secrets.py --include-untracked
python validate.py
python -m py_compile agent.py arena_mcp\*.py scripts\*.py
```

Spot-check high-value tasks: `content/tasks/ticker/`, `content/tasks/swarm-consensus/`, `content/tasks/nl2sql-membership/`.

## 5. Tag and publish

```powershell
git add content/ docs/ scripts/ SECURITY.md README.md RELEASE.md arena_mcp/ runs/README.md .gitignore .env.example
git status
git tag v1.0.0
git push origin main --tags
```

Adjust version as needed.

## Scoring notes for maintainers

See [`content/guides/scoring.md`](content/guides/scoring.md). For maximum Arena scores, submit via **Cursor MCP tools in chat** or **`agent.py`** so tool calls appear in traces — not CLI-only `cursor_run.py`.
