# J.A.R.V.I.S — Personal AI Assistant
### *Just A Rather Very Intelligent System*

> A fully local, privacy-first, voice-enabled personal AI — built like Tony Stark's JARVIS.
> Fast. Smart. Personal. Yours alone.

---

## 🎯 Vision

Build a personal AI assistant that:
- Knows **who you are** — your preferences, habits, schedule, and goals
- Understands **natural language** — talk to it like a human, not a command line
- **Responds fast** — no cloud latency, fully local inference
- Has a **personality** — witty, concise, loyal (like JARVIS)
- Can **take actions** — open apps, search the web, set reminders, manage files
- Runs **100% on your machine** — zero data leaves your device

---

## 🧠 Core Stack

### 1. LLM Engine — `Ollama` (already installed ✅)
- Serves the language model locally via REST API (`http://localhost:11434`)
- Recommended models (pick by your RAM/VRAM):
  - **≥16GB RAM:** `qwen2.5:14b` or `mistral:7b` — best speed/quality balance
  - **≥32GB RAM:** `llama3.3:70b` (4-bit quantized) — near GPT-4 quality
  - **For reasoning/coding:** `deepseek-r1:8b`
  - **Fastest & lightest:** `gemma3:4b` — still very smart, runs on 8GB

> **Ollama Alternative Recommendation:**
> If you want a polished GUI + API server combo, try **LM Studio** (free, closed-source).
> For full offline assistant experience with ChatGPT-style UI, try **Jan** (`jan.ai`) — open source, runs same models.
> Stick with Ollama if you're building programmatically (best for this project).

---

### 2. Python Backend (Brain + Orchestration)
- **Framework:** `FastAPI` — async, fast, auto-docs
- **LLM Integration:** `LangChain` or direct `httpx` calls to Ollama API
- **Memory:** `ChromaDB` (vector store) for long-term personal memory
- **Task Queue:** `Celery` + `Redis` for async background tasks (optional)

### 3. Voice I/O — NLP Layer
- **Speech-to-Text (STT):** `Whisper` (OpenAI, runs locally via `faster-whisper`)
- **Text-to-Speech (TTS):** `Piper TTS` (fast, local, natural voice) or `Coqui TTS`
- **Wake Word Detection:** `Porcupine` (free tier) or `openWakeWord`
- **NLP Processing:** `spaCy` for intent parsing, entity extraction

### 4. Frontend / Interface — `AntiGravity` ✅
- Build the chat/voice UI here
- Clean, dark JARVIS-style interface
- Real-time streaming responses (SSE or WebSocket)
- Voice waveform animation on speak

### 5. Personal Memory & Context
- **Short-term:** Conversation buffer (last N messages in system prompt)
- **Long-term:** ChromaDB stores facts about you (name, preferences, tasks)
- **Episodic Memory:** Summarize past conversations, save to vector DB
- **Structured Data:** SQLite for calendar events, todos, reminders

---

## 🗂️ Project Structure

```
jarvis/
├── backend/
│   ├── main.py               # FastAPI app entry point
│   ├── llm/
│   │   ├── ollama_client.py  # Ollama API wrapper
│   │   └── prompts.py        # System prompts (JARVIS personality)
│   ├── memory/
│   │   ├── short_term.py     # Conversation buffer
│   │   └── long_term.py      # ChromaDB vector memory
│   ├── voice/
│   │   ├── stt.py            # Whisper speech-to-text
│   │   └── tts.py            # Piper/Coqui text-to-speech
│   ├── skills/
│   │   ├── web_search.py     # DuckDuckGo local search
│   │   ├── file_manager.py   # Open/read/write files
│   │   ├── system_control.py # Launch apps, set volume, etc.
│   │   └── reminders.py      # Schedule alerts
│   └── api/
│       └── routes.py         # REST endpoints for frontend
├── frontend/                 # AntiGravity UI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── data/
│   ├── chroma_db/            # Vector memory store
│   └── user_profile.json     # Your personal facts
├── models/                   # Downloaded model files (via Ollama)
├── requirements.txt
└── PROJECT.md                # This file
```

---

## 🤖 JARVIS Personality Prompt

```
You are JARVIS — a personal AI assistant created exclusively for [YOUR NAME].
You are witty, highly intelligent, concise, and deeply loyal.
You speak like a trusted advisor, not a generic chatbot.
You remember everything about your user and use that context always.
You are direct — no fluff, no disclaimers unless critical.
You anticipate needs before they're fully expressed.
When uncertain, ask ONE sharp clarifying question.
Your tone: confident, calm, occasionally dry-humored.
Never say "As an AI..." or "I cannot..." — find a way.
```

---

## ⚡ Speed Optimizations

| Technique | Impact |
|---|---|
| Use `qwen2.5:7b` or `gemma3:4b` quantized models | 2–4x faster |
| Stream responses token-by-token | Feels instant |
| Preload model into RAM (keep Ollama running) | No cold start |
| Use `faster-whisper` (CTranslate2) for STT | 4x faster than base Whisper |
| Limit system prompt to ~500 tokens | Faster prefill |
| Use SQLite for structured data (not vector DB) | Lower latency |
| Run on GPU if available (set in Ollama config) | 10x speed boost |

---

## 🛠️ Setup Steps (Quick Start)

```bash
# 1. Pull your model
ollama pull qwen2.5:7b

# 2. Install Python dependencies
pip install fastapi uvicorn langchain chromadb \
            faster-whisper piper-tts spacy httpx

# 3. Run the backend
uvicorn backend.main:app --reload --port 8000

# 4. Open AntiGravity frontend
# Load frontend/index.html in AntiGravity

# 5. Talk to JARVIS
# Press mic button → speak → get response
```

---

## 📦 Key Python Packages

```txt
fastapi
uvicorn
httpx
langchain
langchain-community
chromadb
faster-whisper
piper-tts
spacy
duckduckgo-search
pydantic
python-dotenv
sqlite3 (built-in)
```

---

## 🔮 Phase Roadmap

### Phase 1 — Core Chat (Week 1)
- [x] Ollama running locally
- [ ] FastAPI backend with Ollama integration
- [ ] Basic JARVIS personality prompt
- [ ] AntiGravity chat UI with streaming

### Phase 2 — Voice (Week 2)
- [ ] Whisper STT integration
- [ ] Piper TTS for voice output
- [ ] Wake word ("Hey JARVIS")

### Phase 3 — Memory (Week 3)
- [ ] ChromaDB long-term memory
- [ ] User profile (name, preferences, habits)
- [ ] Conversation summarization

### Phase 4 — Skills (Week 4+)
- [ ] Web search (DuckDuckGo)
- [ ] Open apps / files
- [ ] Reminders & calendar
- [ ] Weather, news, system stats

---

## 💡 Why NOT use GPT/Claude API?

- 100% private — nothing sent to any server
- Zero cost after setup
- Works offline
- You can fine-tune the model on your own data
- No rate limits, no censorship on personal use cases

---

*Built with ❤️ for personal use. This is YOUR JARVIS.*
