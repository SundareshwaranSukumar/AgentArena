"""Central configuration — override via environment variables or .env file."""

from __future__ import annotations

import os
import re
import sys

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _env_int(name: str, default: int) -> int:
    return int(os.environ.get(name, str(default)))


def _env_float(name: str, default: float) -> float:
    return float(os.environ.get(name, str(default)))


# ── Identity & trace keys (Agent Arena platform) ─────────────────────────────
# Platform User ID — static UID for your agency cluster (metadata / tracing)
PLATFORM_USER_ID = _env("PLATFORM_USER_ID")

# Ephemeral JWT — short-lived credential sent as idToken on every MCP tool call
EPHEMERAL_JWT = (
    _env("EPHEMERAL_JWT")
    or _env("ARENA_ID_TOKEN")  # legacy
    or _env("ID_TOKEN")  # legacy
)

# Traceloop API Key — OpenTelemetry trace export
TRACELOOP_API_KEY = _env("TRACELOOP_API_KEY")

# MCP idToken payload field (same value as EPHEMERAL_JWT)
ID_TOKEN = EPHEMERAL_JWT

# ── Agent identity (leaderboard) ─────────────────────────────────────────────
AGENT_NAME = _env("AGENT_NAME", "KakashiTheHatake")
AGENT_STACK = _env("AGENT_STACK", "Python / ADK / Gemini Flash / MCP")
LINKEDIN_URL = _env("LINKEDIN_URL", "")
GITHUB_URL = _env("GITHUB_URL", "")

# ── Model ───────────────────────────────────────────────────────────────────
MODEL = _env("MODEL", "gemini-2.5-flash")
MODEL_FALLBACKS = [
    m.strip()
    for m in _env(
        "MODEL_FALLBACKS",
        "gemini-3.5-flash,gemini-2.0-flash-lite,gemini-1.5-flash",
    ).split(",")
    if m.strip()
]
GEMINI_API_KEY = _env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY")
TEMPERATURE = _env_float("TEMPERATURE", 0.0)
MAX_OUTPUT_TOKENS = _env_int("MAX_OUTPUT_TOKENS", 4096)
LLM_MAX_RETRIES = _env_int("LLM_MAX_RETRIES", 8)
LLM_RETRY_BASE_SEC = _env_float("LLM_RETRY_BASE_SEC", 50.0)
# Free tier: 5 req/min per model — stay under with ~13s between LLM calls
LLM_MIN_INTERVAL_SEC = _env_float("LLM_MIN_INTERVAL_SEC", 13.0)

# ADK reads GOOGLE_API_KEY only — avoid duplicate-env warning
if GEMINI_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    os.environ.pop("GEMINI_API_KEY", None)

# Kimi API (Moonshot / Cast AI) — primary LLM when LLM_PRIMARY=kimi
KIMI_API_KEY = _env("KIMI_API_KEY") or _env("MOONSHOT_API_KEY")
KIMI_MODEL = _env("KIMI_MODEL", "kimi-k2.6")
_kimi_base_override = _env("KIMI_API_BASE")
if (KIMI_API_KEY or "").startswith("castai_"):
    KIMI_API_BASE = (
        _kimi_base_override
        if _kimi_base_override and "cast.ai" in _kimi_base_override
        else "https://llm.cast.ai/openai/v1"
    )
else:
    KIMI_API_BASE = _kimi_base_override or "https://api.moonshot.ai/v1"

# LLM_PRIMARY: kimi (default when key present) | gemini
LLM_PRIMARY = _env(
    "LLM_PRIMARY",
    "kimi" if KIMI_API_KEY else "gemini",
).lower()

# Continuous operation — poll Arena when idle, recover from errors
RUN_CONTINUOUS = _env("RUN_CONTINUOUS", "true").lower() in ("1", "true", "yes")
IDLE_POLL_SEC = _env_int("IDLE_POLL_SEC", 30)
ERROR_COOLDOWN_SEC = _env_int("ERROR_COOLDOWN_SEC", 45)
REPORT_EVERY_N_TASKS = _env_int("REPORT_EVERY_N_TASKS", 10)


def kimi_available() -> bool:
    return bool(KIMI_API_KEY)


def kimi_primary() -> bool:
    return LLM_PRIMARY == "kimi" and kimi_available()


def gemini_available() -> bool:
    return bool(GEMINI_API_KEY)


def refresh_runtime_secrets() -> None:
    """Reload .env so a refreshed EPHEMERAL_JWT is picked up without restart."""
    global EPHEMERAL_JWT, ID_TOKEN, GEMINI_API_KEY, KIMI_API_KEY  # noqa: PLW0603
    load_dotenv(override=True)
    EPHEMERAL_JWT = (
        _env("EPHEMERAL_JWT")
        or _env("ARENA_ID_TOKEN")
        or _env("ID_TOKEN")
    )
    ID_TOKEN = EPHEMERAL_JWT
    GEMINI_API_KEY = _env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY")
    KIMI_API_KEY = _env("KIMI_API_KEY") or _env("MOONSHOT_API_KEY")
    if GEMINI_API_KEY:
        os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
        os.environ.pop("GEMINI_API_KEY", None)

# ── Arena MCP ───────────────────────────────────────────────────────────────
MCP_ENDPOINT = _env(
    "MCP_ENDPOINT",
    "https://agent-arena-623774504237.asia-southeast1.run.app/mcp",
)

# ── Run limits ──────────────────────────────────────────────────────────────
MAX_TASKS = _env_int("MAX_TASKS", _env_int("MAX_TURNS", 100))
APP_NAME = _env("APP_NAME", "kakashi-hatake")
USER_ID = _env("USER_ID", "arena-user")

# ── Tracing ─────────────────────────────────────────────────────────────────
TRACELOOP_APP_NAME = _env("TRACELOOP_APP_NAME", APP_NAME)
OTEL_SERVICE_NAME = _env("OTEL_SERVICE_NAME", APP_NAME)

# ── Evaluation output ───────────────────────────────────────────────────────
EVAL_OUTPUT_DIR = _env("EVAL_OUTPUT_DIR", "runs")
EVAL_OUTPUT_FILE = _env("EVAL_OUTPUT_FILE", "")


def model_chain() -> list[str]:
    """Primary model first, then fallbacks (deduplicated)."""
    chain: list[str] = []
    seen: set[str] = set()
    for name in [MODEL, *MODEL_FALLBACKS]:
        if name and name not in seen:
            chain.append(name)
            seen.add(name)
    return chain


def is_valid_jwt(token: str) -> bool:
    """JWTs have three base64url segments and are typically 800+ characters."""
    if not token or len(token) < 100:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    return bool(re.match(r"^[A-Za-z0-9_-]+$", parts[0]))


def validate_config(*, check_gemini: bool = False) -> list[str]:
    errors: list[str] = []

    if not GEMINI_API_KEY and not kimi_available():
        errors.append(
            "Missing GEMINI_API_KEY or KIMI_API_KEY. "
            "Gemini: https://aistudio.google.com — Kimi: https://platform.kimi.ai"
        )

    if not EPHEMERAL_JWT:
        errors.append(
            "Missing EPHEMERAL_JWT — the short-lived JWT from Agent Arena "
            "(Identity & Trace Keys). Do not use PLATFORM_USER_ID here."
        )
    elif not is_valid_jwt(EPHEMERAL_JWT):
        if EPHEMERAL_JWT == PLATFORM_USER_ID:
            errors.append(
                "EPHEMERAL_JWT is set to your PLATFORM_USER_ID. "
                "Use the Ephemeral JWT (starts with eyJ…), not the Platform User ID."
            )
        else:
            errors.append(
                f"EPHEMERAL_JWT looks invalid (length={len(EPHEMERAL_JWT)}). "
                "Copy the Ephemeral JWT from agent-arena.dev — it expires in ~1 hour."
            )

    if not PLATFORM_USER_ID:
        errors.append(
            "Missing PLATFORM_USER_ID — static Platform User ID from Identity & Trace Keys."
        )

    if check_gemini and gemini_available() and not kimi_primary():
        try:
            from google import genai

            client = genai.Client(api_key=GEMINI_API_KEY)
            client.models.generate_content(model=MODEL, contents="ping")
        except Exception as exc:
            msg = str(exc)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                errors.append(
                    f"Gemini quota exceeded for model '{MODEL}'. "
                    "Fallbacks will be tried at runtime via MODEL_FALLBACKS."
                )
            elif "503" in msg or "UNAVAILABLE" in msg:
                pass  # transient — runtime retry handles this
            elif "401" in msg or "API key" in msg.lower():
                errors.append(f"Invalid GEMINI_API_KEY: {exc}")
            else:
                errors.append(f"Gemini API check failed: {exc}")

    return errors


def exit_if_invalid(*, check_gemini: bool = False) -> None:
    errors = validate_config(check_gemini=check_gemini)
    if errors:
        print("Configuration errors:", file=sys.stderr)
        for err in errors:
            print(f"  • {err}", file=sys.stderr)
        sys.exit(1)
