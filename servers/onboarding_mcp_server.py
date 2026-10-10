"""Mock HR, documents, access, and policy systems, exposed as one MCP server."""

import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(os.environ.get("ONBOARDING_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT))

from case_engine import (  # noqa: E402
    complete_requirement,
    get_case,
    list_cases,
    log_reminder,
    portfolio,
    readiness,
    reset_store,
    search_policy,
    submit_update,
)

mcp = FastMCP("Onboarding Case Server")


@mcp.tool()
def get_employee_case(employee_id: str) -> dict:
    """Return the raw onboarding case: requirements, documents, meetings, reminders."""
    try:
        return get_case(employee_id)
    except KeyError as exc:
        return {"ok": False, "error": str(exc)}


@mcp.tool()
def get_readiness(employee_id: str, viewer_role: str = "employee") -> dict:
    """Return what is settled, blocked, owned by whom, and the single next action."""
    if employee_id in {"all", "portfolio"}:
        return portfolio(viewer_role or "hr")
    try:
        return readiness(employee_id, viewer_role or "employee")
    except KeyError as exc:
        return {"ok": False, "error": str(exc)}


@mcp.tool()
def list_onboarding_cases() -> list:
    """Summaries for every employee the onboarding owner is tracking."""
    return list_cases()


@mcp.tool()
def search_onboarding_policy(query: str) -> dict:
    """Find the policy passage that matters for this moment."""
    hits = search_policy(query, limit=2)
    return {"query": query, "hits": hits}


@mcp.tool()
def submit_requirement_update(employee_id: str, requirement_id: str, note: str, actor_role: str = "employee") -> dict:
    """Record a document or form as submitted and waiting for review."""
    return submit_update(employee_id, requirement_id, note, actor_role)


@mcp.tool()
def complete_onboarding_requirement(employee_id: str, requirement_id: str, actor_role: str, note: str = "") -> dict:
    """Mark a requirement done when the caller is allowed to close it."""
    return complete_requirement(employee_id, requirement_id, actor_role, note)


@mcp.tool()
def log_onboarding_reminder(employee_id: str, requirement_id: str, message: str, audience: str) -> dict:
    """Store a reminder that was approved by a person. Does not auto-send email."""
    return log_reminder(employee_id, requirement_id, message, audience)


@mcp.tool()
def reset_demo_data() -> dict:
    """Restore Maya and Rohan to the seeded onboarding stories."""
    reset_store()
    return {"ok": True}


if __name__ == "__main__":
    mcp.run()
