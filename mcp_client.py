import asyncio
import json
import os
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

ROOT = Path(__file__).resolve().parent
SERVER = ROOT / "servers" / "onboarding_mcp_server.py"

_client = None
_tools_cache = None


def get_client() -> MultiServerMCPClient:
    global _client
    if _client is None:
        env = os.environ.copy()
        env["ONBOARDING_ROOT"] = str(ROOT)
        if os.environ.get("ONBOARDING_STORE_PATH"):
            env["ONBOARDING_STORE_PATH"] = os.environ["ONBOARDING_STORE_PATH"]
        _client = MultiServerMCPClient(
            {
                "onboarding": {
                    "transport": "stdio",
                    "command": sys.executable,
                    "args": [str(SERVER)],
                    "env": env,
                }
            }
        )
    return _client


async def get_tools():
    global _tools_cache
    if _tools_cache is None:
        _tools_cache = await get_client().get_tools()
    return _tools_cache


def _unwrap(result):
    if isinstance(result, str):
        text = result.strip()
        if text[:1] in "[{":
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return result
        return result
    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, dict) and "text" in first:
            return _unwrap(first["text"])
        if hasattr(first, "text"):
            return _unwrap(first.text)
    return result


async def call_tool(tool_name: str, args: dict | None = None):
    tools = await get_tools()
    tool = next((item for item in tools if item.name == tool_name), None)
    if tool is None:
        names = ", ".join(item.name for item in tools)
        raise ValueError(f"Tool '{tool_name}' not found. Available: {names}")
    result = await tool.ainvoke(args or {})
    return _unwrap(result)


def call_tool_sync(tool_name: str, args: dict | None = None):
    return asyncio.run(call_tool(tool_name, args))
