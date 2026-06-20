"""Preflight checks before a full agent run."""

from __future__ import annotations

import asyncio
import sys

import config


async def check_mcp_auth() -> str | None:
    """Return error message if Arena MCP auth fails."""
    from fastmcp.client import Client
    from fastmcp.client.transports import StreamableHttpTransport
    from fastmcp.exceptions import ToolError

    transport = StreamableHttpTransport(url=config.MCP_ENDPOINT)
    try:
        async with Client(transport, name="preflight") as client:
            result = await client.call_tool(
                "register_agent",
                {
                    "idToken": config.ID_TOKEN,
                    "name": config.AGENT_NAME,
                    "stack": config.AGENT_STACK,
                },
            )
        text = "\n".join(
            getattr(b, "text", "") for b in result.content if getattr(b, "text", None)
        )
        if "AUTH_ERROR" in text or ("Invalid" in text and "token" in text.lower()):
            return text
        # Text format: "AGENT_ID: xxx" — or JSON: {"agentId":"..."}
        if "AGENT_ID" in text or "agentId" in text:
            print(f"  Arena MCP OK — registration successful")
            return None
        try:
            data = __import__("json").loads(text)
            if data.get("agentId") or data.get("status") == "REGISTERED":
                print(f"  Arena MCP OK — agentId={data.get('agentId', '?')}")
                return None
        except Exception:
            pass
        return f"Unexpected register_agent response: {text[:200]}"
    except ToolError as exc:
        return str(exc)
    except Exception as exc:
        return f"MCP connection failed: {exc}"


async def check_kimi() -> str | None:
    """Return error message if Kimi API is misconfigured."""
    if not config.kimi_available():
        return None
    if not _LITELLM_AVAILABLE:
        return "KIMI_API_KEY set but litellm is not installed (pip install litellm)"
    try:
        import litellm

        kwargs: dict = {
            "model": f"openai/{config.KIMI_MODEL}",
            "messages": [{"role": "user", "content": "ping"}],
            "api_base": config.KIMI_API_BASE,
            "api_key": config.KIMI_API_KEY,
            "max_tokens": 8,
        }
        if "moonshot" in config.KIMI_API_BASE:
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
        litellm.completion(**kwargs)
        print(f"  Kimi API OK — {config.KIMI_MODEL} @ {config.KIMI_API_BASE}")
        return None
    except Exception as exc:
        return f"Kimi API check failed: {exc}"


def _litellm_available() -> bool:
    try:
        import litellm  # noqa: F401
        return True
    except ImportError:
        return False


_LITELLM_AVAILABLE = _litellm_available()


def main() -> None:
    print("Agent Arena preflight checks\n")
    if config.kimi_primary():
        config.exit_if_invalid(check_gemini=False)
    else:
        config.exit_if_invalid(check_gemini=True)

    if config.kimi_primary():
        kimi_err = asyncio.run(check_kimi())
        if kimi_err:
            credits_exhausted = any(
                s in kimi_err.lower() for s in ("402", "credits", "exhausted", "quota")
            )
            if credits_exhausted and config.gemini_available():
                print(
                    f"  WARN: Kimi unavailable ({kimi_err[:80]}...) — Gemini backup will be used"
                )
            else:
                print(f"\n{kimi_err}", file=sys.stderr)
                sys.exit(1)
        if config.gemini_available():
            print(f"  Gemini backup OK ({config.MODEL})")
    else:
        if config.GEMINI_API_KEY:
            print("  Gemini API OK")
        kimi_err = asyncio.run(check_kimi()) if config.kimi_available() else None
        if kimi_err:
            print(f"\n{kimi_err}", file=sys.stderr)
            sys.exit(1)

    err = asyncio.run(check_mcp_auth())
    if err:
        print(f"\nArena MCP error: {err}", file=sys.stderr)
        sys.exit(1)

    print("\nAll checks passed. Run: python agent.py")


if __name__ == "__main__":
    main()
