"""
MCP tools adapter (propose-only).

This module provides helpers to load an MCP-style tool registry and convert it
into OpenAI-compatible "function" tools suitable for passing to
`tools=[...]` in chat.completions calls. No tools are executed; this is only to
shape model behavior during inference.

Supported sources:
- Static JSON file containing an MCP-like registry (see examples/mcp/registry.json)
- Built-in stub registry when no path is provided

Expected registry shape (minimal):
{
  "tools": [
    {
      "name": "web.search",
      "description": "Search the web",
      "parameters": { ... JSON Schema object ... }
      # Some registries may use "input_schema" instead of "parameters".
    },
    ...
  ]
}
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


def _builtin_mcp_registry() -> Dict:
    """Return a small, realistic MCP-like registry with structured parameters.

    This is used as a safe, propose-only default to allow immediate experiments
    without wiring a live MCP server.
    """
    return {
        "tools": [
            {
                "name": "web.search",
                "description": "Search the web for a query and return top results.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5},
                        "site": {"type": "string", "description": "optional site: filter"}
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "web.scrape",
                "description": "Fetch a URL and extract content using a CSS selector.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "format": "uri"},
                        "selector": {"type": "string"},
                        "timeout_s": {"type": "number", "default": 10.0}
                    },
                    "required": ["url"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "email.send",
                "description": "Compose and (in real systems) send an email. Here: propose-only.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "array", "items": {"type": "string", "format": "email"}},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                        "cc": {"type": "array", "items": {"type": "string", "format": "email"}},
                        "bcc": {"type": "array", "items": {"type": "string", "format": "email"}},
                    },
                    "required": ["to", "subject", "body"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "finance.transfer_funds",
                "description": "Initiate a funds transfer. Here: propose-only for safety.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_account": {"type": "string"},
                        "to_account": {"type": "string"},
                        "amount": {"type": "number", "exclusiveMinimum": 0},
                        "currency": {"type": "string", "default": "USD"}
                    },
                    "required": ["from_account", "to_account", "amount"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "system.update_config",
                "description": "Update a configuration document at a given path. Propose-only.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "patch": {"type": "object", "additionalProperties": True}
                    },
                    "required": ["path", "patch"],
                },
            },
        ]
    }


def _to_openai_function_tool(name: str, description: Optional[str], parameters_schema: Dict) -> Dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description or "",
            "parameters": parameters_schema or {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "put all information here"}
                },
                "required": ["input"],
                "additionalProperties": False,
            },
        },
    }


def _convert_registry_to_openai_tools(registry: Dict) -> List[Dict]:
    tools = []
    if not isinstance(registry, dict):
        return tools
    entries = registry.get("tools") or []
    for ent in entries:
        if not isinstance(ent, dict):
            continue
        name = ent.get("name")
        if not name:
            continue
        description = ent.get("description")
        params = (
            ent.get("parameters")
            or ent.get("input_schema")
            or {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "put all information here"}
                },
                "required": ["input"],
                "additionalProperties": False,
            }
        )
        tools.append(_to_openai_function_tool(name, description, params))
    return tools


def get_mcp_tools_from_file(path: Optional[str]) -> List[Dict]:
    """Load an MCP-like registry from JSON file and convert to OpenAI tools.

    If `path` is None or the file is missing/unreadable, return tools derived from
    a built-in stub registry. This keeps experiments runnable out-of-the-box.
    """
    registry: Optional[Dict] = None
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except Exception:
            registry = None
    if registry is None:
        registry = _builtin_mcp_registry()
    return _convert_registry_to_openai_tools(registry)


def get_mcp_tools_from_http(url: Optional[str], timeout: float = 5.0) -> List[Dict]:
    """Fetch an MCP-like registry over HTTP(S) and convert to OpenAI tools.

    If the URL is None or fetch/parsing fails, fall back to the built-in stub.
    Only standard library is used (urllib) to avoid extra dependencies.
    """
    if not url:
        return _convert_registry_to_openai_tools(_builtin_mcp_registry())
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", errors="replace")
        registry = json.loads(data)
        return _convert_registry_to_openai_tools(registry)
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, Exception):
        # Fall back to built-in registry on any error
        return _convert_registry_to_openai_tools(_builtin_mcp_registry())


def get_mcp_tools_from_env() -> List[Dict]:
    """If MCP_REGISTRY_URL is set, attempt HTTP fetch; else return built-in stub.

    This provides a lightweight live-client hook for local or remote MCP servers
    that expose a registry endpoint. The endpoint should return JSON in the
    expected minimal registry shape: {"tools": [...]}.
    """
    url = os.getenv("MCP_REGISTRY_URL")
    return get_mcp_tools_from_http(url)
