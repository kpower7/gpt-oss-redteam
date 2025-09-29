import os
from typing import Dict

from gpt_oss_redteam.mcp_tools import get_mcp_tools_from_env, get_mcp_tools_from_http


def _is_openai_function_tool(tool: Dict) -> bool:
    return isinstance(tool, dict) and tool.get("type") == "function" and isinstance(tool.get("function"), dict)


def test_env_hook_fallback_on_invalid_url(monkeypatch):
    # Point to a non-routable port to force failure and fallback to builtin
    monkeypatch.setenv("MCP_REGISTRY_URL", "http://127.0.0.1:1/registry.json")
    tools = get_mcp_tools_from_env()
    assert isinstance(tools, list) and len(tools) > 0
    assert all(_is_openai_function_tool(t) for t in tools)


def test_http_none_returns_builtin():
    tools = get_mcp_tools_from_http(None)
    assert isinstance(tools, list) and len(tools) > 0
