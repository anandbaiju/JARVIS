"""
JARVIS — FastAPI application entry point.
Initialises CORS, memory, reminders, and the API router.
"""

import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.memory.short_term import ConversationBuffer
from backend.memory.long_term import LongTermMemory
from backend.llm.ollama_client import check_ollama_online
from backend.skills.reminders import start_reminder_checker

load_dotenv()

# ── ASCII Banner ──────────────────────────────────────────────────

BANNER = r"""
    ____________________________
   |  J . A . R . V . I . S    |
   |  Just A Rather Very        |
   |  Intelligent System        |
   |____________________________|
   Online. Awaiting your orders.
"""


# ── Lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the JARVIS backend."""
    # ── Startup ──
    print(BANNER)

    # Initialise memory systems
    app.state.conversation_buffer = ConversationBuffer()
    try:
        app.state.long_term_memory = LongTermMemory()
        print("  [OK] Long-term memory (ChromaDB) online")
    except Exception as exc:
        print(f"  [X] Long-term memory failed to initialise: {exc}")
        app.state.long_term_memory = None

    # Start reminder background checker
    start_reminder_checker()
    print("  [OK] Reminder checker active")

    # Check Ollama connection
    online = await check_ollama_online()
    if online:
        model = os.getenv("OLLAMA_MODEL", "unknown")
        print(f"  [OK] Ollama connected — model: {model}")
    else:
        print("  [!] Ollama is OFFLINE — start it with: ollama serve")
        print("      JARVIS will still run, but LLM responses won't work.")

    port = os.getenv("JARVIS_PORT", "8000")
    print(f"\n  Backend : http://localhost:{port}")
    print(f"  API Docs: http://localhost:{port}/docs")
    print()

    yield  # ── App is running ──

    # ── Shutdown ──
    print("\n  JARVIS shutting down. Goodbye, Sir.")


# ── App Factory ───────────────────────────────────────────────────

app = FastAPI(
    title="J.A.R.V.I.S",
    description="Just A Rather Very Intelligent System — Personal AI Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the frontend (opened as file:// or localhost) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routes
app.include_router(router)
