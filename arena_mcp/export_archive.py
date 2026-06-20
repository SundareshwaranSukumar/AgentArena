"""Export Agent Arena logs and session artifacts into runs/archive/ for local review."""
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "runs" / "archive"
RUNS = ROOT / "runs"
CONTENT = ROOT / "content"
AGENTS_JSON = ROOT / "arena_mcp" / "agents.json"


def _slug(label: str, name: str) -> str:
    base = f"{label}-{name}".lower()
    return re.sub(r"[^a-z0-9-]+", "-", base).strip("-")


def _load_agents() -> list[dict]:
    if not AGENTS_JSON.exists():
        return []
    return json.loads(AGENTS_JSON.read_text(encoding="utf-8"))


def _transcript_path() -> Path | None:
    raw = os.environ.get("ARENA_TRANSCRIPT_PATH", "").strip()
    if raw:
        return Path(raw)
    return None


def _copy(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_glob(pattern: str, dest_dir: Path) -> list[str]:
    copied: list[str] = []
    for path in sorted(RUNS.glob(pattern)):
        if "archive" in path.parts:
            continue
        rel = path.name
        _copy(path, dest_dir / rel)
        copied.append(rel)
    return copied


async def _fetch_arena_status(agent_id: str, name: str) -> dict:
    spec = importlib.util.spec_from_file_location(
        "bridge", ROOT / "arena_mcp" / "arena_bridge.py"
    )
    bridge = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(bridge)
    reg = await bridge.register_agent(name)
    tasks = await bridge.get_tasks(agent_id)
    return {
        "register": reg,
        "get_tasks": tasks,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def _write_readme(path: Path, agents: list[dict]) -> None:
    rows = "\n".join(
        f"| {a.get('label', '?')} | {a.get('name', '?')} | `{a.get('id', '?')}` |"
        for a in agents
    )
    path.write_text(
        f"""# Agent Arena Archive

Local export of logs, submissions, and optional session transcript.
**Not for git** — see `.gitignore` (`runs/archive/`).

## Folder layout

```
archive/
├── README.md
├── manifest.json
├── agent-<label>-<name>/
│   ├── profile.json
│   ├── arena-status.json   (when MCP reachable)
│   ├── submissions/        (from content/agents/ or runs/)
│   └── ...
└── transcript/
    └── cursor-session.jsonl  (when ARENA_TRANSCRIPT_PATH set)
```

## Re-export

```powershell
$env:ARENA_TRANSCRIPT_PATH = "path\\to\\session.jsonl"   # optional
python arena_mcp\\export_archive.py
```

## Agents in this export

| Label | Name | ID |
|-------|------|-----|
{rows}
""",
        encoding="utf-8",
    )


async def main() -> None:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    agents = _load_agents()
    transcript = _transcript_path()
    tx_dir = ARCHIVE / "transcript"
    tx_dir.mkdir(parents=True, exist_ok=True)

    agent_dirs: dict[str, Path] = {}
    for agent in agents:
        slug = _slug(agent.get("label", "agent"), agent.get("name", "unknown"))
        agent_dir = ARCHIVE / slug
        agent_dir.mkdir(parents=True, exist_ok=True)
        agent_dirs[agent["id"]] = agent_dir

        profile_src = CONTENT / "agents" / slug / "profile.json"
        if profile_src.exists():
            _copy(profile_src, agent_dir / "profile.json")
        else:
            (agent_dir / "profile.json").write_text(
                json.dumps(agent, indent=2), encoding="utf-8"
            )

        subs_src = CONTENT / "agents" / slug / "submissions"
        if subs_src.is_dir():
            for f in subs_src.glob("*.md"):
                _copy(f, agent_dir / "submissions" / f.name)

    # Shared runtime artifacts (first agent folder + global logs/)
    logs_dir = ARCHIVE / "logs"
    for name in (
        "agent.log",
        "agent.err.log",
        "cursor_poll.log",
        "cursor_poll.out",
        "cursor_poll.err",
        "agents_status.json",
    ):
        _copy(RUNS / name, logs_dir / name)

    for path in RUNS.glob("*.json"):
        if path.name in ("manifest.json", "pending_task.json", "agents_status.json"):
            continue
        _copy(path, ARCHIVE / "evaluations" / path.name)

    for name in ("mmv1.png", "tick.png"):
        _copy(RUNS / name, ARCHIVE / "assets" / name)
        _copy(CONTENT / "assets" / name, ARCHIVE / "assets" / name)

    if transcript and transcript.exists():
        _copy(transcript, tx_dir / "cursor-session.jsonl")

    # Live Arena status per agent
    for agent in agents:
        agent_dir = agent_dirs.get(agent["id"])
        if not agent_dir:
            continue
        try:
            status = await _fetch_arena_status(agent["id"], agent["name"])
            (agent_dir / "arena-status.json").write_text(
                json.dumps(status, indent=2), encoding="utf-8"
            )
        except Exception as exc:
            (agent_dir / "arena-status.json").write_text(
                json.dumps({"error": str(exc)}, indent=2), encoding="utf-8"
            )

    _write_readme(ARCHIVE / "README.md", agents)

    manifest = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "archive_path": str(ARCHIVE),
        "agents": agents,
        "transcript": (
            "transcript/cursor-session.jsonl"
            if transcript and transcript.exists()
            else None
        ),
    }

    try:
        spec_oc = importlib.util.spec_from_file_location(
            "organize_content", ROOT / "arena_mcp" / "organize_content.py"
        )
        oc = importlib.util.module_from_spec(spec_oc)
        assert spec_oc.loader
        spec_oc.loader.exec_module(oc)
        oc.main()
        manifest["content_library"] = str(CONTENT)
    except Exception as exc:
        manifest["content_library_error"] = str(exc)

    (ARCHIVE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "archive": str(ARCHIVE),
                "agents": len(agents),
                "transcript": bool(transcript and transcript.exists()),
            }
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
