"""
Ollama LLM client — async streaming and non-streaming chat via the Ollama REST API.
"""

import os
import json
from typing import AsyncGenerator

import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# Generous timeout: model loading can be slow on first call
_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)


async def chat_stream(
    messages: list[dict],
    system: str = "",
) -> AsyncGenerator[str, None]:
    """Yield response tokens one-by-one from the Ollama streaming API.

    Args:
        messages: Conversation history as list of ``{"role": ..., "content": ...}`` dicts.
        system: The system prompt to prepend.

    Yields:
        Individual text tokens as they arrive.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
    }
    if system:
        payload["messages"] = [{"role": "system", "content": system}] + messages

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        break
    except (httpx.ConnectError, httpx.ConnectTimeout):
        yield "Sir, it appears the neural core is offline. Ensure Ollama is running at " + OLLAMA_BASE_URL
    except httpx.HTTPStatusError as exc:
        yield f"Sir, Ollama returned an error: {exc.response.status_code}. Check the model configuration."


async def chat(
    messages: list[dict],
    system: str = "",
) -> str:
    """Send a non-streaming chat request and return the full response.

    Args:
        messages: Conversation history.
        system: The system prompt to prepend.

    Returns:
        The complete assistant response text.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }
    if system:
        payload["messages"] = [{"role": "system", "content": system}] + messages

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "No response received.")
    except (httpx.ConnectError, httpx.ConnectTimeout):
        return (
            "Sir, it appears the neural core is offline. "
            "Ensure Ollama is running at " + OLLAMA_BASE_URL
        )
    except httpx.HTTPStatusError as exc:
        return f"Sir, Ollama returned an error: {exc.response.status_code}."


async def check_ollama_online() -> bool:
    """Return True if Ollama is reachable, False otherwise."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return resp.status_code == 200
    except (httpx.ConnectError, httpx.ConnectTimeout, Exception):
        return False
