import json
import os
from typing import List, Dict

from gpt_oss_redteam.mcp_tools import get_mcp_tools_from_file


def _is_openai_function_tool(tool: Dict) -> bool:
    if not isinstance(tool, dict):
        return False
    if tool.get("type") != "function":
        return False
    fn = tool.get("function")
    if not isinstance(fn, dict):
        return False
    if not isinstance(fn.get("name"), str):
        return False
    params = fn.get("parameters")
    if not isinstance(params, dict):
        return False
    # Minimal shape: JSON Schema object
    if params.get("type") != "object":
        return False
    if "properties" not in params:
        return False
    return True


def test_builtin_registry_conversion_returns_non_empty_openai_tools() -> None:
    tools = get_mcp_tools_from_file(None)
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert all(_is_openai_function_tool(t) for t in tools)


def test_loading_sample_registry_file() -> None:
    here = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(here, os.pardir))
    sample_path = os.path.join(repo_root, "examples", "mcp", "registry.json")
    tools = get_mcp_tools_from_file(sample_path)
    assert isinstance(tools, list)
    assert len(tools) > 0
    names = [t["function"]["name"] for t in tools if t.get("type") == "function" and isinstance(t.get("function"), dict)]
    assert "web.search" in names


def test_invalid_path_falls_back_to_builtin() -> None:
    tools = get_mcp_tools_from_file("__does_not_exist__.json")
    assert isinstance(tools, list)
    assert len(tools) > 0
