"""
FastAPI routes — REST + SSE endpoints for the JARVIS frontend.
"""

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.llm.ollama_client import chat, chat_stream, check_ollama_online, OLLAMA_MODEL
from backend.llm.prompts import get_system_prompt
from backend.voice.stt import record_and_transcribe
from backend.voice.tts import speak
from backend.skills.web_search import search as web_search
from backend.skills.system_control import get_system_info, open_app
from backend.skills.reminders import add_reminder, get_upcoming

router = APIRouter()


# ── Request / Response Models ──────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


class MemorySaveRequest(BaseModel):
    text: str


class ReminderRequest(BaseModel):
    text: str
    remind_at: str


# ── Helpers ────────────────────────────────────────────────────────

def _build_system_prompt(request: Request) -> str:
    """Construct the full system prompt with memory context and datetime."""
    memory = getattr(request.app.state, "long_term_memory", None)
    memory_context = "No prior memories loaded."
    if memory:
        profile = memory.load_user_profile()
        memory_context = f"User Profile:\n{profile}"

    return get_system_prompt(
        memory_context=memory_context,
        current_datetime=datetime.now().strftime("%A, %B %d, %Y at %I:%M %p"),
    )


# ── Chat Endpoints ────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest, request: Request):
    """Non-streaming chat: send a message, get a complete response."""
    buffer = request.app.state.conversation_buffer
    buffer.add("user", body.message)

    system = _build_system_prompt(request)
    messages = buffer.get_messages()
    response_text = await chat(messages, system=system)

    buffer.add("assistant", response_text)

    # Save significant exchanges to long-term memory
    ltm = getattr(request.app.state, "long_term_memory", None)
    if ltm:
        ltm.save(f"User said: {body.message}\nJARVIS replied: {response_text[:200]}")

    # Speak the response aloud
    speak(response_text)

    return ChatResponse(response=response_text)


@router.get("/chat/stream")
async def chat_stream_endpoint(
    request: Request,
    message: str = Query(..., description="The user's message"),
):
    """SSE streaming chat: tokens arrive one-by-one via Server-Sent Events."""
    buffer = request.app.state.conversation_buffer
    buffer.add("user", message)

    system = _build_system_prompt(request)
    messages = buffer.get_messages()

    async def event_generator():
        full_response: list[str] = []
        async for token in chat_stream(messages, system=system):
            full_response.append(token)
            # SSE format: data: <payload>\n\n
            payload = json.dumps({"token": token})
            yield f"data: {payload}\n\n"

        # Final event signals completion
        complete_text = "".join(full_response)
        buffer.add("assistant", complete_text)

        # Persist to long-term memory
        ltm = getattr(request.app.state, "long_term_memory", None)
        if ltm:
            ltm.save(f"User said: {message}\nJARVIS replied: {complete_text[:200]}")

        # Speak the full response
        speak(complete_text)

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Voice Endpoints ───────────────────────────────────────────────

@router.post("/voice/listen")
async def voice_listen(request: Request):
    """Record 5s of audio from the mic, transcribe, chat, and return both."""
    # Run blocking STT in a thread to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    heard = await loop.run_in_executor(None, record_and_transcribe, 5)

    if heard.startswith("["):
        # Error message from STT
        return {"heard": heard, "response": heard}

    buffer = request.app.state.conversation_buffer
    buffer.add("user", heard)

    system = _build_system_prompt(request)
    messages = buffer.get_messages()
    response_text = await chat(messages, system=system)

    buffer.add("assistant", response_text)
    speak(response_text)

    return {"heard": heard, "response": response_text}


# ── Memory Endpoints ──────────────────────────────────────────────

@router.get("/memory/recall")
async def memory_recall(request: Request, q: str = Query(..., description="Search query")):
    """Recall relevant memories from long-term storage."""
    ltm = getattr(request.app.state, "long_term_memory", None)
    if not ltm:
        return {"memories": "Long-term memory not initialised."}
    result = ltm.recall(q)
    return {"memories": result}


@router.post("/memory/save")
async def memory_save(body: MemorySaveRequest, request: Request):
    """Save a fact or note to long-term memory."""
    ltm = getattr(request.app.state, "long_term_memory", None)
    if not ltm:
        return {"status": "Long-term memory not initialised."}
    ltm.save(body.text)
    return {"status": "Memory saved."}


# ── Status Endpoint ───────────────────────────────────────────────

@router.get("/status")
async def status():
    """Health check: Ollama status, model info, user name."""
    import os
    from dotenv import load_dotenv
    load_dotenv()

    online = await check_ollama_online()
    return {
        "ollama_online": online,
        "model": OLLAMA_MODEL,
        "user": os.getenv("USER_NAME", "Unknown"),
    }


# ── System Info Endpoint ─────────────────────────────────────────

@router.get("/system/info")
async def system_info():
    """Return current system diagnostics."""
    info = get_system_info()
    return {"info": info}


@router.post("/system/open")
async def system_open(body: dict):
    """Launch an application by name."""
    app_name = body.get("app", "")
    result = open_app(app_name)
    return {"result": result}


# ── Web Search Endpoint ──────────────────────────────────────────

@router.get("/search")
async def search_endpoint(q: str = Query(..., description="Search query")):
    """Search the web via DuckDuckGo."""
    results = web_search(q)
    return {"results": results}


# ── Reminder Endpoints ───────────────────────────────────────────

@router.get("/reminders")
async def reminders_list():
    """Get upcoming reminders."""
    upcoming = get_upcoming()
    return {"reminders": upcoming}


@router.post("/reminders")
async def reminders_add(body: ReminderRequest):
    """Add a new reminder."""
    result = add_reminder(body.text, body.remind_at)
    return {"result": result}
