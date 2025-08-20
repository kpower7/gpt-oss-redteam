import json
import os
import time
from typing import Dict, List, Optional

from openai import OpenAI

from .tools import get_fake_tools


DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")


def _client() -> OpenAI:
    return OpenAI(base_url=DEFAULT_OLLAMA_BASE_URL, api_key=os.getenv("OLLAMA_API_KEY", "ollama"))


def build_messages(user_prompt: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
    msgs: List[Dict[str, str]] = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.append({"role": "user", "content": user_prompt})
    return msgs


def call_ollama(
    prompt: str,
    system: Optional[str] = None,
    model: str = DEFAULT_OLLAMA_MODEL,
    tools: Optional[List[dict]] = None,
    tool_choice: Optional[str] = "auto",
    temperature: Optional[float] = None,
    request_interval_s: float = 0.0,
) -> Dict:
    """Call Ollama chat.completions and return dict with response and parsed text.

    We pass a fake tools manifest to encourage tool thoughts without executing them.
    """
    client = _client()
    msgs = build_messages(prompt, system)
    kwargs = {
        "model": model,
        "messages": msgs,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    if tools is None:
        tools = get_fake_tools()
    if tools:
        kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

    resp = client.chat.completions.create(**kwargs)
    # Text content may be empty if the model tried to call tools
    text = (resp.choices[0].message.content or "").strip()
    obj = resp.model_dump()
    if request_interval_s > 0:
        time.sleep(request_interval_s)
    return {
        "text": text,
        "raw": obj,
    }
