# 🚀 AntiGravity Prompt — Build JARVIS Personal AI (Windows)

> Paste this entire prompt into AntiGravity to scaffold and run the full JARVIS project.

---

## PROMPT (Copy everything below this line)

---

You are an expert full-stack AI engineer. Your task is to build a complete, working, local personal AI assistant called **JARVIS** — inspired by Iron Man's AI — that runs 100% on my Windows machine using Ollama as the LLM backend and a Python FastAPI server.

**My setup:**
- OS: Windows 10/11
- Already installed: `AntiGravity`, `Ollama` (running at http://localhost:11434)
- Python 3.10+ available (accessible via `python` or `python3` in terminal)
- Shell: PowerShell and/or Command Prompt
- Goal: Fast, smart, personal AI with voice + chat interface

---

### PHASE 1 — Build the Core Backend

Create the full project at `C:\Users\%USERNAME%\jarvis\` — use `pathlib.Path.home() / "jarvis"` in all Python code for portability. Exact structure:

```
jarvis/
├── backend/
│   ├── main.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── ollama_client.py
│   │   └── prompts.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── short_term.py
│   │   └── long_term.py
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── stt.py
│   │   └── tts.py
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── web_search.py
│   │   ├── system_control.py
│   │   └── reminders.py
│   └── api/
│       ├── __init__.py
│       └── routes.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── data/
│   └── user_profile.json
├── .env
├── requirements.txt
└── run.bat
```

---

### FILE SPECIFICATIONS

#### `requirements.txt`
```
fastapi
uvicorn[standard]
httpx
chromadb
faster-whisper
pydantic
python-dotenv
duckduckgo-search
sounddevice
numpy
pyaudio
psutil
pyttsx3
```

#### `.env`
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
USER_NAME=ANAND
JARVIS_PORT=8000
```

---

#### `backend/llm/prompts.py`
Write the JARVIS system prompt. It must:
- Address the user by name loaded from `.env`
- Have a sharp, witty, loyal JARVIS personality — like the movie
- Be concise — under 400 tokens
- Never say "As an AI..." or "I cannot..." — always find a way
- Anticipate needs, ask ONE clarifying question when uncertain
- Include a `{memory_context}` placeholder for injected long-term memories
- Include a `{current_datetime}` placeholder injected at runtime

Example JARVIS tone:
> "Of course. Running diagnostics now. Your RAM is at 78% — largely your fault, I'd say."
NOT:
> "Hello! I am an AI assistant. How can I help you today? 😊"

---

#### `backend/llm/ollama_client.py`
- Load `OLLAMA_BASE_URL` and `OLLAMA_MODEL` from `.env`
- Async function `chat_stream(messages: list, system: str)` — yields tokens via `httpx` AsyncClient from Ollama `/api/chat` with `"stream": true`
- Async function `chat(messages: list, system: str) -> str` — non-streaming, full response
- On connection error: return JARVIS-style message: `"Sir, it appears the neural core is offline. Ensure Ollama is running."`

#### `backend/memory/short_term.py`
- Class `ConversationBuffer`:
  - `add(role: str, content: str)` — appends message
  - `get_messages() -> list` — returns last 20 messages as list of dicts
  - `clear()` — resets buffer
  - Keep it simple, in-memory only (list of dicts)

#### `backend/memory/long_term.py`
- Uses `chromadb` with persistent local store at `Path.home() / "jarvis" / "data" / "chroma_db"`
- Class `LongTermMemory`:
  - `save(text: str)` — embeds and stores memory with timestamp metadata
  - `recall(query: str, top_k=3) -> str` — returns top matching memories as formatted string
  - `load_user_profile() -> str` — reads `data/user_profile.json`, returns formatted string

#### `data/user_profile.json`
```json
{
  "name": "Tony",
  "location": "Kerala, India",
  "occupation": "Developer / Builder",
  "interests": ["AI", "tech", "Iron Man", "building things"],
  "assistant_name": "JARVIS",
  "wake_word": "hey jarvis",
  "preferred_model": "qwen2.5:7b",
  "personality_notes": "Direct, no fluff. Treat me like a smart adult."
}
```

#### `backend/voice/stt.py`
- Use `faster_whisper` with model `"base"` (fast, works on CPU)
- Function `transcribe_audio(audio_path: str) -> str`
- Function `record_and_transcribe(duration=5) -> str`:
  - Record from default Windows mic using `sounddevice`
  - Save to temp WAV file in `%TEMP%` folder using `tempfile`
  - Transcribe and return text
- Import guard: wrap sounddevice in try/except, fallback message if mic unavailable

#### `backend/voice/tts.py`
- Use `pyttsx3` (works natively on Windows with SAPI5 voices — no install needed)
- Function `speak(text: str)` — non-blocking, runs in a `threading.Thread`
- Strip markdown before speaking: remove `**`, `*`, `#`, `` ` ``, `>` characters
- Set voice rate to 185 (slightly fast, feels sharp like JARVIS)

#### `backend/skills/web_search.py`
- Function `search(query: str, max_results=3) -> str`
- Use `duckduckgo_search` DDGS client
- Return formatted string: `"Search Results:\n1. [Title] — Snippet\n2. ..."`

#### `backend/skills/system_control.py`
- Use `psutil` for system stats
- Use `os.startfile()` for opening files/apps on Windows (NOT subprocess with xdg-open)
- Function `get_system_info() -> str` — CPU%, RAM used/total, disk usage on C:\
- Function `open_app(app_name: str) -> str`:
  - Map common names to Windows executables: `"notepad"`, `"chrome"`, `"explorer"`, `"cmd"`, `"powershell"`, `"vscode"` → `code`
  - Use `subprocess.Popen` with the executable name
  - Return confirmation string
- Function `set_volume(level: int)` — use `pycaw` if available, else skip with friendly message

#### `backend/skills/reminders.py`
- SQLite database at `Path.home() / "jarvis" / "data" / "reminders.db"`
- Function `add_reminder(text: str, remind_at_str: str) -> str` — parse time with `datetime`
- Function `get_upcoming(limit=5) -> str` — return next N reminders
- Background thread: check every 60 seconds, call `tts.speak()` for due reminders

#### `backend/api/routes.py`
FastAPI router with:
- `POST /chat` — body: `{"message": str}`, returns `{"response": str}`
- `GET /chat/stream` — SSE via `StreamingResponse`, query param `?message=...`, streams tokens
- `POST /voice/listen` — records 5s audio, transcribes, chats, returns `{"heard": str, "response": str}`
- `GET /memory/recall` — query param `?q=...`, returns memories
- `POST /memory/save` — body: `{"text": str}`
- `GET /status` — returns `{"ollama_online": bool, "model": str, "user": str}`
- `GET /reminders` — upcoming reminders
- `POST /reminders` — body: `{"text": str, "remind_at": str}`

#### `backend/main.py`
- FastAPI app with CORS middleware: allow all origins, methods, headers
- Include router from `api/routes.py`
- Attach `ConversationBuffer` and `LongTermMemory` to `app.state` on startup
- On startup: print this ASCII banner to console:
```
    ____________________________
   |  J . A . R . V . I . S    |
   |  Just A Rather Very        |
   |  Intelligent System        |
   |____________________________|
   Online. Awaiting your orders.
```
- Check Ollama connection on startup, warn if offline (don't crash)

---

### PHASE 2 — Build the Frontend (JARVIS HUD)

#### `frontend/index.html` + `frontend/style.css` + `frontend/app.js`

Build a stunning JARVIS-style dark HUD interface. All in plain HTML/CSS/JS — no build tools, no npm, no frameworks. Must open directly as a file in any browser.

**Visual Design:**
- Background: deep space black `#050A0E` with subtle scanline CSS overlay
- Primary accent: neon cyan `#00D4FF` with `box-shadow` glow effect
- Secondary accent: amber/gold `#FFB300`
- Fonts via Google Fonts CDN: `Orbitron` (headings/labels), `Share Tech Mono` (chat text)
- Animated arc reactor pulse ring: a CSS `@keyframes` animated concentric circle in top-center — pure CSS, no images
- Glowing cyan borders on all panels using `box-shadow: 0 0 10px #00D4FF`
- Subtle background grid using CSS `background-image: linear-gradient` repeating lines

**Layout (single page, no scrollbar on body):**
- **Header**: "J.A.R.V.I.S" in Orbitron + tagline "Just A Rather Very Intelligent System"
- **Status Bar**: model name pill, connection dot (green=online/red=offline), live clock updated every second
- **Chat Window**: scrollable `div`, fills most of screen
  - User messages: right-aligned, amber `#FFB300`, background `rgba(255,179,0,0.08)`
  - JARVIS messages: left-aligned, cyan `#00D4FF`, prefix `› JARVIS:`, background `rgba(0,212,255,0.05)`
  - Typing indicator: 3 animated dots shown while awaiting response
- **Input Bar** (pinned to bottom):
  - Text input with glowing cyan border on focus
  - `SEND` button — cyan glow
  - `MIC` button — amber, pulses red while recording
- **Side Panel** (right, collapsible on small screens):
  - Quick buttons: `SYSTEM INFO`, `WEB SEARCH`, `REMINDERS`, `CLEAR CHAT`

**JavaScript (`app.js`):**
- API base URL: `const API = "http://localhost:8000"` at top — easy to change
- On load: `GET /status` → update connection dot and model name in status bar
- **Text chat**: `POST /chat`, render response with typewriter effect (add one char every 18ms)
- **SSE streaming** (preferred): use `EventSource` on `/chat/stream?message=...`, append tokens live to chat
- **Mic button**: `POST /voice/listen`, show "LISTENING..." animation (pulsing red mic), display both heard text and response
- `Enter` key sends message; `Escape` clears input
- Auto-scroll chat window to bottom after each message
- `SYSTEM INFO` button: calls `/status` extended or a dedicated skill endpoint, shows result in chat as JARVIS response
- Subtle startup sound on page load: generate a short 3-note ascending tone using Web Audio API (no external audio files needed)
- Show timestamp (HH:MM) on each message bubble

---

### PHASE 3 — Windows Launch Script

#### `run.bat`
```bat
@echo off
title JARVIS - Startup Sequence
echo.
echo  ============================
echo   J . A . R . V . I . S
echo   Starting systems...
echo  ============================
echo.

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [JARVIS] Starting Ollama...
    start "" ollama serve
    timeout /t 4 /nobreak >nul
)

REM Pull model if not present
echo [JARVIS] Verifying model...
ollama pull qwen2.5:7b

REM Install Python dependencies
echo [JARVIS] Checking dependencies...
pip install -r requirements.txt -q

REM Start FastAPI backend
echo [JARVIS] Bringing neural core online...
start "JARVIS Backend" cmd /k "cd /d %~dp0 && uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak >nul

REM Open frontend in default browser
echo [JARVIS] Launching interface...
start "" "%~dp0frontend\index.html"

echo.
echo  [ONLINE] Backend : http://localhost:8000
echo  [ONLINE] API Docs: http://localhost:8000/docs
echo  [ONLINE] Frontend: frontend\index.html
echo.
echo  JARVIS is ready, Sir.
pause
```

---

### EXECUTION INSTRUCTIONS FOR ANTIGRAVITY

Execute in this exact order:

1. **Create all files** — write complete, working code for every file listed. No placeholders, no `pass`, no `# TODO`.
2. **Install dependencies:**
   ```
   pip install -r C:\Users\%USERNAME%\jarvis\requirements.txt
   ```
3. **Pull Ollama model:**
   ```
   ollama pull qwen2.5:7b
   ```
4. **Start backend:**
   ```
   cd C:\Users\%USERNAME%\jarvis
   uvicorn backend.main:app --reload --port 8000
   ```
5. **Open frontend:** double-click `frontend\index.html` or open in browser
6. **Test:** Type `"JARVIS, are you online?"` — expect a sharp, in-character response

---

### WINDOWS-SPECIFIC RULES (CRITICAL)

- **NEVER use `os.system('open ...')` or `xdg-open`** — use `os.startfile()` or `subprocess.Popen` on Windows
- **NEVER use `amixer` or `pactl`** for volume — use `pyttsx3` or `pycaw`
- **NEVER use Linux paths** like `/tmp/` — use `tempfile.gettempdir()` which resolves to `%TEMP%` on Windows
- **NEVER use `~` in shell scripts** — use `%USERPROFILE%` in `.bat` or `Path.home()` in Python
- **NEVER use `pip3`** — use `pip` (standard on Windows Python installs)
- **Always use `pathlib.Path`** for all file paths — never hardcode forward/back slashes
- **PyAudio on Windows**: wrap in try/except — if install fails, fallback to sounddevice only
- **ChromaDB**: use `chromadb.PersistentClient(path=str(...))` — pass path as string, not Path object
- **faster-whisper**: requires Microsoft Visual C++ Redistributable on Windows — add a note in README

---

### QUALITY BAR

- All Python must be fully async in FastAPI routes
- SSE streaming must actually stream — tokens appear one by one
- The frontend must feel like a real JARVIS HUD, not a generic chat app
- Voice must work: mic → transcribe → respond → speak out loud
- Everything must work by double-clicking `run.bat` — zero manual steps after that
- Code must be production quality — typed, commented where non-obvious, no debug prints left in

---

Begin now. Create every file with complete code. Start with `requirements.txt` and `.env`, then backend modules bottom-up (memory → llm → voice → skills → api → main), then frontend, then `run.bat`. After all files are created, run the install and startup commands and confirm JARVIS responds.
