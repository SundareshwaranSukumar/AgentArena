# Runtime workspace

This directory is **gitignored** — ephemeral Arena session state only.

| File / pattern | Purpose |
|----------------|---------|
| `cursor_poll.log` | Background poller output |
| `agents_status.json` | Latest snapshot of all agents |
| `pending_task.json` | Most recently detected task |
| `submit_*.md`, `verify_*.py` | Working copies during active sessions |
| `FINISH` | Create to stop the poller |
| `archive/` | Optional export snapshots (logs, transcripts) |

## Production release

Canonical **questions & answers** live in [`../content/`](../content/) — regenerate after sessions:

```powershell
python arena_mcp\organize_content.py
```

Do not ship `runs/` in releases; ship `content/` instead.
