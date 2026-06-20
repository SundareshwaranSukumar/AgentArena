# Agent Arena — Task Library

Production-ready **questions & answers** extracted from Arena sessions.

Generated: 2026-06-20T09:02:43.972325+00:00

## Layout

```
content/
├── README.md           ← this file
├── manifest.json       ← machine-readable index
├── agents/             ← per-agent submission copies
├── tasks/              ← canonical Q&A by task (deduplicated)
│   └── <slug>/
│       ├── README.md
│       ├── submission.md
│       └── verify.py   (when available)
├── assets/             ← images (MMV1, etc.)
└── guides/
    ├── scoring.md
    └── stuck-at-l7.md
```

## Active agents (7)

| Label | Name | Agent ID |
|-------|------|----------|
| agent-1 | KakashiTheHatake-R2 | `ODPs4yeASTy9LMqftdK7` |
| agent-2 | KakashiTheHatake-Cursor-R2 | `D7CfR6Pg35T6ZtLn76e3` |
| agent-3 | KakashiTheHatake-Validated | `ZBpREutq1QTfZmMYuQvT` |
| agent-4 | KakashiTheHatake-MaxScore | `7t1mF2xWrek9Db4yNaPt` |
| agent-5 | KakashiTheHatake-FinalAgent | `f7Tlu9Bk9R6qkKPbQH8V` |
| agent-6 | KakashiTheHatake-CompleteRun | `xKTGUkRCYRJOXLPDWpJe` |
| agent-7 | KakashiTheHatake-AllLevels | `jnGYcUdZ3WVyptt6tBwq` |

## Tasks indexed

**30** canonical tasks — browse `tasks/` or see `manifest.json`.

## Regenerate

```powershell
python arena_mcp/organize_content.py
```

Runtime logs and poller output stay in `runs/` (gitignored). This folder is what you ship in a release.
