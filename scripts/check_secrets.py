"""Scan the repository for accidental secret leakage before release.

Exit 0 when clean; exit 1 when potential secrets are found in tracked paths.

Usage:
    python scripts/check_secrets.py
    python scripts/check_secrets.py --include-untracked
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Directories never scanned (local/runtime only)
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "runs",
}

# Files allowed to mention env var names / placeholder patterns
ALLOWLIST_FILES = {
    ".env.example",
    "SECURITY.md",
    "scripts/check_secrets.py",
    "deploy/setup-gcp.sh",
    "deploy/cloud-run-job.yaml",
    "cloudbuild.yaml",
    "docs/DEPLOYMENT.md",
    "docs/GUIDE.md",
    "docs/CURSOR.md",
    "config.py",
    "validate.py",
    "tracing.py",
    "agent.py",
    "arena_mcp/arena_bridge.py",
    "arena_mcp/cursor_poll.py",
    "arena_mcp/export_archive.py",
    "content/guides/stuck-at-l7.md",
}

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("JWT (eyJ…)", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
    ("OpenAI-style key (sk-…)", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("Google API key (AIza…)", re.compile(r"AIza[A-Za-z0-9_-]{30,}")),
    ("Cast AI key", re.compile(r"castai_v1_[A-Za-z0-9_-]{10,}")),
    ("Hardcoded assignment", re.compile(
        r"(?i)(api[_-]?key|secret|password|token|jwt)\s*=\s*['\"][^'\"\\s]{12,}['\"]"
    )),
    ("Firebase-style UID in JSON", re.compile(r'"platform_user_id"\s*:\s*"[A-Za-z0-9]{20,}"')),
    ("Windows user home path", re.compile(r"[A-Za-z]:\\Users\\[^\\]+\\")),
]


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _git_tracked_files() -> set[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in out.stdout.splitlines() if line.strip()}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()


def _iter_files(*, include_untracked: bool, scan_env: bool) -> list[Path]:
    tracked = _git_tracked_files()
    files: list[Path] = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = _rel(path)
        if rel == ".env":
            if scan_env:
                files.append(path)
            continue
        if include_untracked or not tracked:
            files.append(path)
        elif rel in tracked:
            files.append(path)
    return files


def _is_allowlisted(rel: str) -> bool:
    if rel in ALLOWLIST_FILES:
        return True
    if rel.endswith(".example") or rel.endswith(".md"):
        # Docs may describe env vars; still catch real JWTs via eyJ pattern
        return rel.endswith(".md") and "eyJ" not in rel
    return False


def scan(*, include_untracked: bool = False, scan_env: bool = False) -> list[tuple[str, str, str, int]]:
    """Return list of (rel_path, pattern_name, matched_text, line_no)."""
    findings: list[tuple[str, str, str, int]] = []

    for path in _iter_files(include_untracked=include_untracked, scan_env=scan_env):
        rel = _rel(path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            for name, pattern in PATTERNS:
                m = pattern.search(line)
                if not m:
                    continue
                matched = m.group(0)
                # Docs: allow env var *names* but not real values
                if rel.endswith(".md") and name != "JWT (eyJ…)" and "eyJ" not in matched:
                    if matched.startswith('"platform_user_id"'):
                        continue
                    if "Hardcoded assignment" in name:
                        continue
                if _is_allowlisted(rel) and name in (
                    "Hardcoded assignment",
                    "Firebase-style UID in JSON",
                    "Windows user home path",
                ):
                    continue
                findings.append((rel, name, matched[:80], line_no))
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan repo for leaked secrets")
    parser.add_argument(
        "--include-untracked",
        action="store_true",
        help="Also scan untracked files (default: git-tracked only)",
    )
    parser.add_argument(
        "--scan-env",
        action="store_true",
        help="Also scan .env (local only — file must stay gitignored)",
    )
    args = parser.parse_args()

    print("Secret scan — Agent Arena\n")
    tracked = _git_tracked_files()
    if tracked:
        print(f"Scanning {len(tracked)} git-tracked file(s)" + (
            " + untracked" if args.include_untracked else ""
        ) + (" + .env" if args.scan_env else "") + "\n")
    else:
        print("No git index — scanning project tree (excluding runs/, .venv/)\n")

    findings = scan(
        include_untracked=args.include_untracked,
        scan_env=args.scan_env,
    )

    if not findings:
        print("OK — no secret patterns detected in scanned paths.")
        sys.exit(0)

    print(f"FAIL — {len(findings)} potential secret(s):\n")
    for rel, name, matched, line_no in findings:
        print(f"  {rel}:{line_no}  [{name}]  {matched!r}")
    print("\nRemove or redact before committing. See SECURITY.md.")
    sys.exit(1)


if __name__ == "__main__":
    main()
